import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import typer
from dotenv import load_dotenv
from pdf_anonymizer_core.conf import (
    DEFAULT_LOG_FILE,
    ConfigProfile,
    EntityProfile,
    PromptEnum,
    get_config_for_profile,
    get_provider_and_model_name,
    operators_for_entity_profile,
    types_for_entity_profile,
)
from pdf_anonymizer_core.core import (
    anonymize_docx_file,
    anonymize_file,
    anonymize_tabular_file,
)
from pdf_anonymizer_core.span_ner import resolve_semantic_stages
from pdf_anonymizer_core.gazetteers import load_phrase_list
from pdf_anonymizer_core.llm_provider import configure_cache
from pdf_anonymizer_core.mapping_crypto import resolve_mapping_passphrase
from pdf_anonymizer_core.operators import parse_operator_specs
from pdf_anonymizer_core.prompts import detailed, hipaa, simple
from pdf_anonymizer_core.tables import is_tabular_path, load_review_text
from pdf_anonymizer_core.word import is_word_path
from pdf_anonymizer_core.utils import (
    consolidate_mapping,
    deanonymize_file,
    load_seed_mapping,
    mapping_to_original_to_written,
    save_results,
)
from pdf_anonymizer_core.risk import assess_linkage_risk, write_risk_report
from pdf_anonymizer_core.apply_residuals import (
    apply_residual_hits,
    default_mapping_out,
    guess_mapping_path,
    hits_from_report,
    load_decision_list,
    load_residual_report,
    seed_mapping_from_path,
    select_residual_hits,
)
from pdf_anonymizer_core.verify import verify_anonymized_text, write_residual_report
from typing_extensions import Annotated

# Setup logging using log file configured in conf.py
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(DEFAULT_LOG_FILE), logging.StreamHandler()],
)

app = typer.Typer()


def load_environment() -> None:
    """Load environment variables from .env file if it exists."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)


@app.command()
def run(
    file_paths: Annotated[
        List[Path],
        typer.Argument(
            help="A list of paths to files to anonymize.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    config_profile: Annotated[
        ConfigProfile,
        typer.Option(
            "--config-profile",
            "-p",
            help="The configuration profile to use (best-quality, best-speed, best-cost, regex-only).",
            case_sensitive=False,
        ),
    ] = ConfigProfile.BEST_SPEED,
    characters_to_anonymize: Annotated[
        Optional[int],
        typer.Option(
            help="Override number of characters to send for anonymization in one go (chunk size)."
        ),
    ] = None,
    prompt_name: Annotated[
        Optional[PromptEnum],
        typer.Option(
            help="Override prompt template. 'detailed' also hides identity clues (phrases that point to one person without naming them). 'simple' does not.",
            case_sensitive=False,
        ),
    ] = None,
    model_name: Annotated[
        Optional[str],
        typer.Option(
            help="Override the language model to use for anonymization.",
        ),
    ] = None,
    anonymized_entities: Annotated[
        Optional[Path],
        typer.Option(
            "--anonymized-entities",
            help="A file with a list of entities to anonymize.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    countries: Annotated[
        Optional[str],
        typer.Option(
            "--countries",
            help=(
                "ISO-2 country codes for national-ID regexes, comma-separated "
                "(e.g. US,GB). Universal patterns such as email and IBAN always "
                "stay. Default: all countries."
            ),
        ),
    ] = None,
    verify: Annotated[
        bool,
        typer.Option(
            "--verify/--no-verify",
            help=(
                "After masking, scan the result for leftover personal details "
                "(cheap regex). Writes data/stats/<stem>.residual_pii.json. "
                "Does not rewrite the file."
            ),
        ),
    ] = True,
    verify_llm: Annotated[
        bool,
        typer.Option(
            "--verify-llm/--no-verify-llm",
            help="Also ask the language model to hunt for leftovers (slower).",
        ),
    ] = False,
    apply_residuals: Annotated[
        bool,
        typer.Option(
            "--apply-residuals/--no-apply-residuals",
            help=(
                "After the leftover scan, hide every leftover on this run. "
                "Off by default. The scan still runs (implies --verify)."
            ),
        ),
    ] = False,
    no_llm: Annotated[
        bool,
        typer.Option(
            "--no-llm",
            help=(
                "Skip the language model. Only the RE2 regex stage runs. "
                "Checksums, country filter, operators, leftover scan, and "
                "risk still run. Names and identity clues will be missed. "
                "Same as -p regex-only. Default: use the model."
            ),
        ),
    ] = False,
    mapping_passphrase: Annotated[
        Optional[str],
        typer.Option(
            "--mapping-passphrase",
            help=(
                "Lock the mapping file with AES-256-GCM and Argon2id. "
                "Also read from ANONYMIZER_MAPPING_KEY. "
                "Without this, the mapping is stored as plain JSON."
            ),
        ),
    ] = None,
    ephemeral_mapping: Annotated[
        bool,
        typer.Option(
            "--ephemeral-mapping/--persist-mapping",
            help=(
                "Keep the mapping only in this process. Nothing is written "
                "under data/mappings/. Later deanonymization is impossible "
                "unless you already saved the map yourself. Default: persist."
            ),
        ),
    ] = False,
    operator: Annotated[
        Optional[List[str]],
        typer.Option(
            "--operator",
            help=(
                "How to write one type: TYPE=replace|mask|hash|generalize|shift|fake. "
                "Repeatable. Default for every type is replace (PERSON_1)."
            ),
        ),
    ] = None,
    risk: Annotated[
        bool,
        typer.Option(
            "--risk/--no-risk",
            help=(
                "After masking, score identity-clue clumps (job+company+place). "
                "Writes data/stats/<stem>.risk.json. Does not change the file."
            ),
        ),
    ] = True,
    keep_list: Annotated[
        Optional[Path],
        typer.Option(
            "--keep-list",
            help="Phrases to leave visible (one per line). Wins over --deny-list.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    deny_list: Annotated[
        Optional[Path],
        typer.Option(
            "--deny-list",
            help="Phrases that must be hidden even if detection missed them (one per line).",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    mapping_in: Annotated[
        Optional[Path],
        typer.Option(
            "--mapping-in",
            help=(
                "Existing mapping file so the same person stays PERSON_1 "
                "across documents. Also used as the starting map for a batch."
            ),
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    fake_secret: Annotated[
        Optional[str],
        typer.Option(
            "--fake-secret",
            help=(
                "Seed for --operator TYPE=fake. Also ANONYMIZER_FAKE_SECRET. "
                "Same person always gets the same fake. Default is a built-in constant."
            ),
        ),
    ] = None,
    encrypt_secret: Annotated[
        Optional[str],
        typer.Option(
            "--encrypt-secret",
            help=(
                "Secret for --operator TYPE=encrypt. Also ANONYMIZER_ENCRYPT_SECRET. "
                "Same text always yields the same token. Required when encrypt is used."
            ),
        ),
    ] = None,
    ocr: Annotated[
        bool,
        typer.Option(
            "--ocr/--no-ocr",
            help=(
                "If a PDF has no text layer, OCR it with Tesseract (must be "
                "on PATH). Off by default. A scan with OCR off is an error, "
                "not an empty success file."
            ),
        ),
    ] = False,
    output_pdf: Annotated[
        bool,
        typer.Option(
            "--output-pdf/--no-output-pdf",
            help=(
                "Also write a sanitized native PDF (glyphs excised, metadata "
                "wiped). Markdown is still written. PDF inputs only. "
                "This is not a legal de-identification certificate."
            ),
        ),
    ] = False,
    redact: Annotated[
        bool,
        typer.Option(
            "--redact/--no-redact",
            help=(
                "Irreversible native PDF: black boxes, no stand-in text. "
                "Implies --output-pdf. Deanonymize cannot restore the page."
            ),
        ),
    ] = False,
    ner: Annotated[
        Optional[bool],
        typer.Option(
            "--ner/--no-ner",
            help=(
                "Local span NER (GLiNER extra) for names and organizations. "
                "Default: on for best-speed/best-cost/best-quality when the "
                "[ner] extra is installed; off for regex-only. "
                "best-speed and best-cost then skip the language model."
            ),
        ),
    ] = None,
    min_confidence: Annotated[
        float,
        typer.Option(
            "--min-confidence",
            help=(
                "Drop entities whose recognizer score is below this value "
                "(0–1). Default 0 keeps every hit. Not a calibrated "
                "probability."
            ),
            min=0.0,
            max=1.0,
        ),
    ] = 0.0,
    entity_profile: Annotated[
        Optional[EntityProfile],
        typer.Option(
            "--entity-profile",
            help=(
                "Named type coverage bundle. hipaa-safe-harbor is an aid for "
                "the 18 Safe Harbor identifier classes, not a compliance certificate."
            ),
            case_sensitive=False,
        ),
    ] = None,
) -> None:
    """
    Anonymize one or more files by replacing PII with anonymized placeholders.
    """
    load_environment()
    if apply_residuals:
        verify = True

    country_list = None
    if countries:
        country_list = [part.strip() for part in countries.split(",") if part.strip()]

    # Get configuration based on profile and optional user overrides
    try:
        config = get_config_for_profile(
            profile=config_profile,
            model_name=model_name,
            prompt_name=prompt_name,
            chunk_size=characters_to_anonymize,
            countries=country_list,
        )
    except ValueError as exc:
        logging.error("%s", exc)
        sys.exit(1)

    try:
        operator_map = parse_operator_specs(operator)
    except ValueError as exc:
        logging.error("%s", exc)
        sys.exit(1)
    encrypt_key = encrypt_secret or os.getenv("ANONYMIZER_ENCRYPT_SECRET")
    if "encrypt" in operator_map.values() and not encrypt_key:
        logging.error(
            "The encrypt operator needs --encrypt-secret or ANONYMIZER_ENCRYPT_SECRET."
        )
        sys.exit(1)

    use_llm = bool(config.use_llm) and not no_llm
    replace_llm_when_ner = config_profile in (
        ConfigProfile.BEST_SPEED,
        ConfigProfile.BEST_COST,
    )
    try:
        use_ner, use_llm = resolve_semantic_stages(
            use_llm=use_llm,
            use_ner=ner,
            replace_llm_when_ner=replace_llm_when_ner,
        )
    except ValueError as exc:
        logging.error("%s", exc)
        sys.exit(1)
    if not use_llm:
        if use_ner:
            logging.info(
                "Local span NER: skipping the language model. "
                "Identity clues will be missed."
            )
        else:
            logging.info(
                "Regex-only / offline mode: skipping the language model. "
                "Names and identity clues will be missed."
            )
        if verify_llm:
            logging.warning("--verify-llm is ignored when the language model is off.")
            verify_llm = False

    if use_llm:
        # Configure LLM caching with values from configuration
        configure_cache(
            enabled=config.enable_cache,
            cache_dir=config.cache_dir,
            cache_file=config.cache_file,
        )

        provider_name, _ = get_provider_and_model_name(config.model_name)
        if provider_name == "google":
            if "gemini" in config.model_name and not os.getenv("GOOGLE_API_KEY"):
                logging.error(
                    "Error: GOOGLE_API_KEY not found. Please set it in the .env file."
                )
                sys.exit(1)

    logging.info(f"Using configuration profile: {config_profile.value}")
    logging.info(f"  --file-paths: {file_paths}")
    logging.info(f"  --chunk-size: {config.chunk_size}")
    logging.info(f"  --chunk-overlap: {config.chunk_overlap}")
    logging.info(f"  --model-name: {config.model_name}")
    logging.info(f"  --use-llm: {use_llm}")
    if country_list:
        logging.info(f"  --countries: {country_list}")
        logging.info(
            f"  --regex-patterns: {len(config.regex_patterns)} after country filter"
        )
    if operator_map:
        logging.info(f"  --operator: {operator_map}")

    # Select the appropriate prompt template
    prompt_templates: Dict[str, str] = {
        PromptEnum.simple.value: simple.prompt_template,
        PromptEnum.detailed.value: detailed.prompt_template,
    }
    prompt_template: str = prompt_templates[config.prompt_name]
    logging.info(f"  --prompt-name: {config.prompt_name}")

    entities_to_anonymize = None
    if anonymized_entities:
        with open(anonymized_entities, "r") as f:
            entities_to_anonymize = [
                line.strip() for line in f.readlines() if line.strip()
            ]
        logging.info(f"  --anonymized-entities: {entities_to_anonymize}")

    if entity_profile is not None:
        profile_types = types_for_entity_profile(entity_profile) or []
        profile_ops = operators_for_entity_profile(entity_profile)
        operator_map = {**profile_ops, **operator_map}
        if entities_to_anonymize:
            entities_to_anonymize = list(
                dict.fromkeys([*profile_types, *entities_to_anonymize])
            )
        else:
            entities_to_anonymize = profile_types
        if entity_profile == EntityProfile.HIPAA_SAFE_HARBOR and prompt_name is None:
            prompt_template = hipaa.prompt_template
        logging.info(
            "  --entity-profile: %s (aid, not a compliance certificate)",
            entity_profile.value,
        )
        logging.info("  --operator after profile: %s", operator_map)

    keep_phrases = load_phrase_list(str(keep_list)) if keep_list else None
    deny_phrases = load_phrase_list(str(deny_list)) if deny_list else None
    if keep_phrases:
        logging.info("  --keep-list: %s phrase(s)", len(keep_phrases))
    if deny_phrases:
        logging.info("  --deny-list: %s phrase(s)", len(deny_phrases))

    logging.info(f"Found {len(file_paths)} file(s) to process.")

    seed_mapping = None
    passphrase = resolve_mapping_passphrase(mapping_passphrase)
    if mapping_in is not None:
        try:
            seed_mapping = load_seed_mapping(str(mapping_in), passphrase)
        except ValueError as exc:
            logging.error("%s", exc)
            sys.exit(1)
        logging.info("  --mapping-in: %s (%s entries)", mapping_in, len(seed_mapping))

    for i, file_path in enumerate(file_paths, 1):
        logging.info("=" * 40)
        logging.info(f"Processing file {i}/{len(file_paths)}: {file_path}")
        entity_texts = None
        try:
            if is_word_path(str(file_path)):
                full_anonymized_text, final_mapping, entity_texts = anonymize_docx_file(
                    file_path=str(file_path),
                    characters_to_anonymize=config.chunk_size,
                    prompt_template=prompt_template,
                    model_name=config.model_name,
                    anonymized_entities=entities_to_anonymize,
                    chunk_overlap=config.chunk_overlap,
                    regex_patterns=config.regex_patterns,
                    max_retries=config.max_retries,
                    base_retry_delay=config.base_retry_delay,
                    max_retry_delay=config.max_retry_delay,
                    operators=operator_map or None,
                    fake_secret=fake_secret or os.getenv("ANONYMIZER_FAKE_SECRET"),
                    encrypt_secret=encrypt_key,
                    seed_mapping=seed_mapping,
                    keep_list=keep_phrases,
                    deny_list=deny_phrases,
                    use_llm=use_llm,
                    use_ner=use_ner,
                    min_confidence=min_confidence,
                )
            elif is_tabular_path(str(file_path)):
                full_anonymized_text, final_mapping, entity_texts = (
                    anonymize_tabular_file(
                        file_path=str(file_path),
                        characters_to_anonymize=config.chunk_size,
                        prompt_template=prompt_template,
                        model_name=config.model_name,
                        anonymized_entities=entities_to_anonymize,
                        chunk_overlap=config.chunk_overlap,
                        regex_patterns=config.regex_patterns,
                        max_retries=config.max_retries,
                        base_retry_delay=config.base_retry_delay,
                        max_retry_delay=config.max_retry_delay,
                        operators=operator_map or None,
                        fake_secret=fake_secret or os.getenv("ANONYMIZER_FAKE_SECRET"),
                        encrypt_secret=encrypt_key,
                        seed_mapping=seed_mapping,
                        keep_list=keep_phrases,
                        deny_list=deny_phrases,
                        use_llm=use_llm,
                        use_ner=use_ner,
                        min_confidence=min_confidence,
                    )
                )
            else:
                full_anonymized_text, final_mapping = anonymize_file(
                    file_path=str(file_path),
                    characters_to_anonymize=config.chunk_size,
                    prompt_template=prompt_template,
                    model_name=config.model_name,
                    anonymized_entities=entities_to_anonymize,
                    chunk_overlap=config.chunk_overlap,
                    regex_patterns=config.regex_patterns,
                    max_retries=config.max_retries,
                    base_retry_delay=config.base_retry_delay,
                    max_retry_delay=config.max_retry_delay,
                    operators=operator_map or None,
                    fake_secret=fake_secret or os.getenv("ANONYMIZER_FAKE_SECRET"),
                    encrypt_secret=encrypt_key,
                    seed_mapping=seed_mapping,
                    keep_list=keep_phrases,
                    deny_list=deny_phrases,
                    use_llm=use_llm,
                    use_ner=use_ner,
                    ocr=ocr,
                    min_confidence=min_confidence,
                )
        except ValueError as exc:
            logging.error("%s", exc)
            sys.exit(1)

        if full_anonymized_text is not None and final_mapping is not None:
            seed_mapping = final_mapping
            # The mapping from anonymize_file is original -> placeholder.
            # We will standardize on placeholder -> original for subsequent steps.
            placeholder_to_original = {v: k for k, v in final_mapping.items()}

            logging.info("Consolidating mapping...")
            full_anonymized_text, consolidated_placeholder_map = consolidate_mapping(
                full_anonymized_text, placeholder_to_original
            )

            want_pdf = output_pdf or redact
            pdf_orig_to_written = {
                original: placeholder
                for placeholder, original in consolidated_placeholder_map.items()
            }
            anonymized_output_file, mapping_file = save_results(
                full_anonymized_text,
                consolidated_placeholder_map,
                str(file_path),
                mapping_passphrase=passphrase,
                ephemeral_mapping=ephemeral_mapping,
                entity_texts=entity_texts,
                orig_to_written=(
                    final_mapping
                    if is_tabular_path(str(file_path)) or is_word_path(str(file_path))
                    else (pdf_orig_to_written if want_pdf else None)
                ),
                output_pdf=want_pdf,
                redact=redact,
            )
            logging.info(f"Anonymization for {file_path} complete!")
            logging.info(f"Anonymized text saved into '{anonymized_output_file}'")
            if ephemeral_mapping or not mapping_file:
                logging.info("Ephemeral mapping: vocabulary was not written to disk.")
            elif mapping_file.endswith(".enc"):
                logging.info(f"Encrypted mapping saved into '{mapping_file}'")
            else:
                logging.info(f"Mapping vocabulary saved into '{mapping_file}'")

            if verify or verify_llm:
                report = verify_anonymized_text(
                    full_anonymized_text,
                    anonymized_file=anonymized_output_file,
                    regex_patterns=config.regex_patterns,
                    use_llm=verify_llm,
                    model_name=config.model_name if verify_llm else None,
                    max_retries=config.max_retries,
                    base_retry_delay=config.base_retry_delay,
                    max_retry_delay=config.max_retry_delay,
                )
                report_path = write_residual_report(report, anonymized_output_file)
                logging.info(
                    "Residual check: %s leftover hit(s). Report: %s",
                    report["residual_count"],
                    report_path,
                )
                if apply_residuals and report["residual_count"]:
                    applied = apply_residual_hits(
                        anonymized_output_file,
                        hits_from_report(report),
                        seed_mapping=mapping_to_original_to_written(
                            consolidated_placeholder_map
                        ),
                        mapping_out=mapping_file or None,
                        mapping_passphrase=passphrase,
                        write_mapping=not ephemeral_mapping and bool(mapping_file),
                    )
                    report["rewritten"] = True
                    report["applied"] = applied["applied"]
                    report["skipped"] = []
                    write_residual_report(report, anonymized_output_file)
                    logging.info(
                        "Applied %s leftover(s) to %s",
                        len(applied["applied"]),
                        anonymized_output_file,
                    )

            if risk:
                risk_report = assess_linkage_risk(full_anonymized_text)
                risk_path = write_risk_report(risk_report, anonymized_output_file)
                logging.info(
                    "Linkage risk: %s (%s high / %s medium windows). Report: %s",
                    risk_report["overall"],
                    risk_report["high_count"],
                    risk_report["medium_count"],
                    risk_path,
                )


@app.command()
def deanonymize(
    anonymized_file: Annotated[
        Path,
        typer.Argument(
            help="Path to the anonymized file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    mapping_file: Annotated[
        Path,
        typer.Argument(
            help="Path to the mapping file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    mapping_passphrase: Annotated[
        Optional[str],
        typer.Option(
            "--mapping-passphrase",
            help=(
                "Passphrase for an encrypted mapping file. "
                "Also read from ANONYMIZER_MAPPING_KEY."
            ),
        ),
    ] = None,
    source_sha256: Annotated[
        Optional[str],
        typer.Option(
            "--source-sha256",
            help=(
                "Expected SHA-256 of the original source document. "
                "Rejects a mapping that was locked for a different file."
            ),
        ),
    ] = None,
    encrypt_secret: Annotated[
        Optional[str],
        typer.Option(
            "--encrypt-secret",
            help=(
                "Secret used by --operator TYPE=encrypt. "
                "Also ANONYMIZER_ENCRYPT_SECRET."
            ),
        ),
    ] = None,
) -> None:
    """
    Deanonymize a file using a mapping file.
    """
    logging.info(f"Deanonymizing '{anonymized_file}' using '{mapping_file}'")
    try:
        deanonymized_output_file, stats_file = deanonymize_file(
            str(anonymized_file),
            str(mapping_file),
            mapping_passphrase=resolve_mapping_passphrase(mapping_passphrase),
            expected_source_sha256=source_sha256,
            encrypt_secret=encrypt_secret or os.getenv("ANONYMIZER_ENCRYPT_SECRET"),
        )
    except ValueError as exc:
        logging.error("%s", exc)
        sys.exit(1)
    logging.info("Deanonymization complete!")
    logging.info(f"Deanonymized text saved into '{deanonymized_output_file}'")
    logging.info(f"Deanonymization statistics saved into '{stats_file}'")


@app.command()
def verify(
    anonymized_file: Annotated[
        Path,
        typer.Argument(
            help="Path to an already anonymized file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    countries: Annotated[
        Optional[str],
        typer.Option(
            "--countries",
            help="ISO-2 country codes for the regex scan, comma-separated (e.g. US,GB).",
        ),
    ] = None,
    verify_llm: Annotated[
        bool,
        typer.Option(
            "--verify-llm/--no-verify-llm",
            help="Also ask the language model to hunt for leftovers.",
        ),
    ] = False,
    config_profile: Annotated[
        ConfigProfile,
        typer.Option(
            "--config-profile",
            "-p",
            help="Profile used only when --verify-llm is set.",
            case_sensitive=False,
        ),
    ] = ConfigProfile.BEST_SPEED,
    model_name: Annotated[
        Optional[str],
        typer.Option(help="Override model when --verify-llm is set."),
    ] = None,
) -> None:
    """Scan an anonymized file for leftover personal details. Does not rewrite it."""
    load_environment()
    country_list = None
    if countries:
        country_list = [part.strip() for part in countries.split(",") if part.strip()]

    try:
        config = get_config_for_profile(
            profile=config_profile,
            model_name=model_name,
            countries=country_list,
        )
    except ValueError as exc:
        logging.error("%s", exc)
        sys.exit(1)

    try:
        text = load_review_text(str(anonymized_file))
    except ValueError as exc:
        logging.error("%s", exc)
        sys.exit(1)
    report = verify_anonymized_text(
        text,
        anonymized_file=str(anonymized_file),
        regex_patterns=config.regex_patterns,
        use_llm=verify_llm,
        model_name=config.model_name if verify_llm else None,
        max_retries=config.max_retries,
        base_retry_delay=config.base_retry_delay,
        max_retry_delay=config.max_retry_delay,
    )
    report_path = write_residual_report(report, str(anonymized_file))
    logging.info(
        "Residual check: %s leftover hit(s). Report: %s",
        report["residual_count"],
        report_path,
    )
    if report["residual_count"]:
        for hit in report["regex_hits"] + report["llm_hits"]:
            logging.info("  leftover %s: %s", hit["type"], hit["text"])


@app.command("report")
def report_risk(
    anonymized_file: Annotated[
        Path,
        typer.Argument(
            help="Path to an already anonymized file.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ],
) -> None:
    """Score identity-clue clumps in a masked file. Does not change the file."""
    try:
        text = load_review_text(str(anonymized_file))
    except ValueError as exc:
        logging.error("%s", exc)
        sys.exit(1)
    risk_report = assess_linkage_risk(text)
    risk_path = write_risk_report(risk_report, str(anonymized_file))
    logging.info(
        "Linkage risk: %s (%s high / %s medium windows). Report: %s",
        risk_report["overall"],
        risk_report["high_count"],
        risk_report["medium_count"],
        risk_path,
    )
    for window in risk_report["windows"]:
        if window["level"] in {"high", "medium"}:
            logging.info(
                "  %s: %s — %s",
                window["level"],
                ", ".join(window["types"]),
                window["reason"],
            )


@app.command()
def apply(
    stats_file: Annotated[
        Path,
        typer.Argument(
            help="Path to a residual report (*.residual_pii.json).",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    accept_all: Annotated[
        bool,
        typer.Option(
            "--accept-all/--no-accept-all",
            help="Hide every leftover in the report (non-interactive).",
        ),
    ] = False,
    accept: Annotated[
        Optional[Path],
        typer.Option(
            "--accept",
            help="JSON list or one-phrase-per-line file of leftovers to hide.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    skip: Annotated[
        Optional[Path],
        typer.Option(
            "--skip",
            help="JSON list or one-phrase-per-line file of leftovers to leave.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
    mapping_file: Annotated[
        Optional[Path],
        typer.Option(
            "--mapping",
            help="Mapping file to extend. Default: data/mappings/<stem>.mapping.json.",
        ),
    ] = None,
    mapping_passphrase: Annotated[
        Optional[str],
        typer.Option(
            "--mapping-passphrase",
            help=(
                "Passphrase for an encrypted mapping. "
                "Also read from ANONYMIZER_MAPPING_KEY."
            ),
        ),
    ] = None,
    file_path: Annotated[
        Optional[Path],
        typer.Option(
            "--file",
            help="Anonymized file to rewrite. Default: anonymized_file in the report.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
) -> None:
    """Hide leftovers listed in a residual report. Default is still report-only."""
    load_environment()
    try:
        report = load_residual_report(str(stats_file))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        logging.error("%s", exc)
        sys.exit(1)

    anonymized = str(file_path) if file_path else report.get("anonymized_file")
    if not anonymized:
        logging.error("Report has no anonymized_file. Pass --file.")
        sys.exit(1)

    hits = hits_from_report(report)
    if not hits:
        logging.info("No leftovers in the report.")
        return

    accept_list = load_decision_list(str(accept)) if accept else None
    skip_list = load_decision_list(str(skip)) if skip else None

    if not accept_all and accept_list is None:
        if sys.stdin.isatty():
            chosen: List[str] = []
            for hit in hits:
                if typer.confirm(
                    f"Hide leftover {hit['type']} {hit['text']!r}?",
                    default=True,
                ):
                    chosen.append(hit["text"])
            accept_list = chosen
        else:
            logging.error("Non-interactive apply needs --accept-all or --accept FILE.")
            sys.exit(1)

    accepted, skipped = select_residual_hits(
        hits,
        accept=accept_list,
        skip=skip_list,
        accept_all=accept_all,
    )
    if not accepted:
        logging.info("Nothing to apply.")
        return

    passphrase = resolve_mapping_passphrase(mapping_passphrase)
    mapping_path = str(mapping_file) if mapping_file else guess_mapping_path(anonymized)
    try:
        seed = seed_mapping_from_path(mapping_path, passphrase)
        result = apply_residual_hits(
            anonymized,
            accepted,
            seed_mapping=seed,
            mapping_out=mapping_path or default_mapping_out(anonymized),
            mapping_passphrase=passphrase,
        )
    except ValueError as exc:
        logging.error("%s", exc)
        sys.exit(1)

    report["rewritten"] = True
    report["applied"] = result["applied"]
    report["skipped"] = [hit["text"] for hit in skipped]
    write_residual_report(report, anonymized)
    logging.info(
        "Applied %s leftover(s) to %s (skipped %s).",
        len(result["applied"]),
        anonymized,
        len(skipped),
    )
    for text in result["applied"]:
        logging.info("  hid %s", text)


if __name__ == "__main__":
    app()
