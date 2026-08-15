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
    PromptEnum,
    get_config_for_profile,
    get_provider_and_model_name,
)
from pdf_anonymizer_core.core import anonymize_file
from pdf_anonymizer_core.llm_provider import configure_cache
from pdf_anonymizer_core.mapping_crypto import resolve_mapping_passphrase
from pdf_anonymizer_core.operators import parse_operator_specs
from pdf_anonymizer_core.prompts import detailed, simple
from pdf_anonymizer_core.utils import (
    consolidate_mapping,
    deanonymize_file,
    save_results,
)
from pdf_anonymizer_core.risk import assess_linkage_risk, write_risk_report
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
            help="The configuration profile to use (best-quality, best-speed, best-cost).",
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
    mapping_passphrase: Annotated[
        Optional[str],
        typer.Option(
            "--mapping-passphrase",
            help=(
                "Lock the mapping file with AES-256-GCM. "
                "Also read from ANONYMIZER_MAPPING_KEY. "
                "Without this, the mapping is stored as plain JSON."
            ),
        ),
    ] = None,
    operator: Annotated[
        Optional[List[str]],
        typer.Option(
            "--operator",
            help=(
                "How to write one type: TYPE=replace|mask|hash|generalize|shift. "
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
) -> None:
    """
    Anonymize one or more files by replacing PII with anonymized placeholders.
    """
    load_environment()

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
    if country_list:
        logging.info(f"  --countries: {country_list}")
        logging.info(f"  --regex-patterns: {len(config.regex_patterns)} after country filter")
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
            entities_to_anonymize = [line.strip() for line in f.readlines()]
        logging.info(f"  --anonymized-entities: {entities_to_anonymize}")

    logging.info(f"Found {len(file_paths)} file(s) to process.")

    for i, file_path in enumerate(file_paths, 1):
        logging.info("=" * 40)
        logging.info(f"Processing file {i}/{len(file_paths)}: {file_path}")
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
        )

        if full_anonymized_text and final_mapping:
            # The mapping from anonymize_file is original -> placeholder.
            # We will standardize on placeholder -> original for subsequent steps.
            placeholder_to_original = {v: k for k, v in final_mapping.items()}

            logging.info("Consolidating mapping...")
            full_anonymized_text, consolidated_placeholder_map = consolidate_mapping(
                full_anonymized_text, placeholder_to_original
            )

            anonymized_output_file, mapping_file = save_results(
                full_anonymized_text,
                consolidated_placeholder_map,
                str(file_path),
                mapping_passphrase=resolve_mapping_passphrase(mapping_passphrase),
            )
            logging.info(f"Anonymization for {file_path} complete!")
            logging.info(f"Anonymized text saved into '{anonymized_output_file}'")
            if mapping_file.endswith(".enc"):
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

    text = anonymized_file.read_text(encoding="utf-8")
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
    text = anonymized_file.read_text(encoding="utf-8")
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


if __name__ == "__main__":
    app()
