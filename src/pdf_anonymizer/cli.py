import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import typer
from dotenv import load_dotenv
from typing_extensions import Annotated

from pdf_anonymizer.conf import (
    DEFAULT_CHARACTERS_TO_ANONYMIZE,
    DEFAULT_MODEL_NAME,
    DEFAULT_PROMPT_NAME,
    ModelName,
    ModelProvider,
    PromptEnum,
    get_enum_value,
)
from pdf_anonymizer.core import anonymize_file
from pdf_anonymizer.prompts import detailed, simple
from pdf_anonymizer.utils import (
    consolidate_mapping,
    deanonymize_file,
    save_results,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()],
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
    characters_to_anonymize: Annotated[
        int,
        typer.Option(help="Number of characters to send for anonymization in one go."),
    ] = DEFAULT_CHARACTERS_TO_ANONYMIZE,
    prompt_name: Annotated[
        PromptEnum,
        typer.Option(
            help="The name of the prompt to use for anonymization.",
            case_sensitive=False,
        ),
    ] = get_enum_value(PromptEnum, DEFAULT_PROMPT_NAME),
    model_name: Annotated[
        ModelName,
        typer.Option(
            help="The name of the model to use for anonymization.",
            case_sensitive=False,
        ),
    ] = get_enum_value(ModelName, DEFAULT_MODEL_NAME),
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

    Args:
        file_paths: List of paths to files to process.
        characters_to_anonymize: Number of characters to process in each chunk.
        prompt_name: The prompt template to use for anonymization.
        model_name: The language model to use for anonymization.
        anonymized_entities: A file with a list of entities to anonymize.
    """
    load_environment()

    if model_name.provider == ModelProvider.GOOGLE:
        if "gemini" in model_name.value and not os.getenv("GOOGLE_API_KEY"):
            logging.error(
                "Error: GOOGLE_API_KEY not found. Please set it in the .env file."
            )
            sys.exit(1)

    logging.info(f"  --file-paths: {file_paths}")
    logging.info(f"  --characters-to-anonymize: {characters_to_anonymize}")
    logging.info(f"  --model-name: {model_name.value}")

    # Select the appropriate prompt template
    prompt_templates: Dict[str, str] = {
        PromptEnum.simple: simple.prompt_template,
        PromptEnum.detailed: detailed.prompt_template,
    }
    prompt_template: str = prompt_templates[prompt_name]
    logging.info(f"  --prompt-name: {prompt_name.value}")

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
            str(file_path),
            characters_to_anonymize,
            prompt_template,
            model_name.value,
            entities_to_anonymize,
        )

        if full_anonymized_text and final_mapping:
            # Consolidate mapping before saving
            logging.info("Consolidating mapping...")
            full_anonymized_text, final_mapping = consolidate_mapping(
                full_anonymized_text, final_mapping
            )

            anonymized_output_file, mapping_file = save_results(
                full_anonymized_text, final_mapping, str(file_path)
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

    Args:
        anonymized_file: Path to the anonymized file.
        mapping_file: Path to the mapping file.
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