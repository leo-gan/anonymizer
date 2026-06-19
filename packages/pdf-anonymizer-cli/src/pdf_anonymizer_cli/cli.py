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
from pdf_anonymizer_core.prompts import detailed, simple
from pdf_anonymizer_core.utils import (
    consolidate_mapping,
    deanonymize_file,
    save_results,
)
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
            help="Override prompt template to use for anonymization.",
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
) -> None:
    """
    Anonymize one or more files by replacing PII with anonymized placeholders.
    """
    load_environment()

    # Get configuration based on profile and optional user overrides
    config = get_config_for_profile(
        profile=config_profile,
        model_name=model_name,
        prompt_name=prompt_name,
        chunk_size=characters_to_anonymize,
    )

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
                full_anonymized_text, consolidated_placeholder_map, str(file_path)
            )
            logging.info(f"Anonymization for {file_path} complete!")
            logging.info(f"Anonymized text saved into '{anonymized_output_file}'")
            logging.info(f"Mapping vocabulary saved into '{mapping_file}'")


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
) -> None:
    """
    Deanonymize a file using a mapping file.
    """
    logging.info(f"Deanonymizing '{anonymized_file}' using '{mapping_file}'")
    deanonymized_output_file, stats_file = deanonymize_file(
        str(anonymized_file), str(mapping_file)
    )
    logging.info("Deanonymization complete!")
    logging.info(f"Deanonymized text saved into '{deanonymized_output_file}'")
    logging.info(f"Deanonymization statistics saved into '{stats_file}'")


if __name__ == "__main__":
    app()
