import sys
import os
from pathlib import Path
from dotenv import load_dotenv
import logging
import typer
from typing_extensions import Annotated

from pdf_anonymizer.core import anonymize_pdf
from pdf_anonymizer.utils import save_results
from pdf_anonymizer.prompts import detailed, simple
from pdf_anonymizer.conf import (
    PromptEnum,
    ModelProvider,
    ModelName,
    DEFAULT_CHARACTERS_TO_ANONYMIZE,
    DEFAULT_PROMPT_NAME,
    DEFAULT_MODEL_NAME,
)


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

app = typer.Typer()


@app.command()
def run(
    pdf_path: Annotated[
        Path,
        typer.Argument(
            help="The path to the PDF file to anonymize.",
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
        typer.Option(
            help="Number of characters to send for anonymization in one go."
        ),
    ] = DEFAULT_CHARACTERS_TO_ANONYMIZE,
    prompt_name: Annotated[
        PromptEnum,
        typer.Option(
            help="Can be 'simple' or 'detailed'.",
        ),
    ] = DEFAULT_PROMPT_NAME,
    model_name: Annotated[
        ModelName,
        typer.Option(
            help="The model to use for anonymization.",
        ),
    ] = DEFAULT_MODEL_NAME,
):
    """
    Main function to run the PDF anonymization process.
    """
    load_dotenv()
    if model_name.provider == ModelProvider.GOOGLE:
        if "gemini" in model_name.value:
            if not os.getenv("GOOGLE_API_KEY"):
                logging.error("Error: GOOGLE_API_KEY not found. Please set it in the .env file.")
                sys.exit(1)

    logging.info(f"  --pdf-path: {pdf_path}")
    logging.info(f"  --characters-to-anonymize: {characters_to_anonymize}")
    logging.info(f"  --model-name: {model_name.value}")

    prompt_mapping = {"simple": simple.prompt_template, "detailed": detailed.prompt_template}
    prompt_template = prompt_mapping[prompt_name.value]
    logging.info(f"  --prompt-name: {prompt_name.value}")

    full_anonymized_text, final_mapping = anonymize_pdf(
        pdf_path,
        characters_to_anonymize,
        prompt_template,
        model_name.value
    )

    if full_anonymized_text:
        anonymized_output_file, mapping_file = save_results(
            full_anonymized_text,
            final_mapping,
            pdf_path
        )
        logging.info("Anonymization complete!")
        logging.info(f"Anonymized text saved into '{anonymized_output_file}'")
        logging.info(f"Mapping vocabulary saved into '{mapping_file}'")


if __name__ == "__main__":
    app()
