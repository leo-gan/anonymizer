import sys
import json
from pathlib import Path
import os
from dotenv import load_dotenv
import logging
import time
import typer
from typing_extensions import Annotated
from enum import Enum

from pdf_anonymizer.call_llm import anonymize_text_with_llm
from pdf_anonymizer.load_and_extract_pdf import load_and_extract_text
from pdf_anonymizer.prompts import detailed, simple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

app = typer.Typer()


class PromptEnum(str, Enum):
    simple = "simple"
    detailed = "detailed"


class ModelName(str, Enum):
    gemini_2_5_pro = "gemini-2.5-pro"
    gemini_2_5_flash = "gemini-2.5-flash"
    gemini_2_5_flash_lite = "gemini-2.5-flash-lite"
    gemma = "gemma"
    phi = "phi"


def main(
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
    ] = 100000,
    prompt_name: Annotated[
        PromptEnum,
        typer.Option(
            help="Can be 'simple' or 'detailed'.",
        ),
    ] = PromptEnum.simple,
    model_name: Annotated[
        ModelName,
        typer.Option(
            help="The model to use for anonymization.",
        ),
    ] = ModelName.gemini_2_5_flash_lite,
):
    """
    Main function to run the PDF anonymization process.
    """
    load_dotenv()
    if "gemini" in model_name.value:
        if not os.getenv("GOOGLE_API_KEY"):
            logging.error("Error: GOOGLE_API_KEY not found. Please set it in the .env file.")
            sys.exit(1)

    logging.info(f"  --pdf_path: {pdf_path}")
    logging.info(f"  --characters_to_anonymize: {characters_to_anonymize}")
    logging.info(f"  --model_name: {model_name.value}")

    prompt_mapping = {"simple": simple.prompt_template, "detailed": detailed.prompt_template}
    prompt_template = prompt_mapping[prompt_name.value]
    logging.info(f"  --prompt_name: {prompt_name.value}")

    # PDF file: chunk and convert to text
    pdf_file_size = os.path.getsize(pdf_path)
    text_pages = load_and_extract_text(pdf_path, characters_to_anonymize)

    if not text_pages:
        logging.warning("No text could be extracted from the PDF.")
        return

    extracted_text_size = sum(len(page) for page in text_pages)

    logging.info(f"Starting anonymization for: {pdf_path}")
    logging.info(f"  - PDF file size: {pdf_file_size / 1024:.2f} KB")
    logging.info(f"  - Extracted text size: {extracted_text_size / 1024:.2f} KB")

    # Anonymization:
    anonymized_chunks = []
    final_mapping = {}

    for i, text_page in enumerate(text_pages):
        logging.info(f"Anonymizing part {i+1}/{len(text_pages)}...")
        start_time = time.time()

        anonymized_text, final_mapping = anonymize_text_with_llm(
            text_page,
            final_mapping,
            prompt_template,
            model_name.value
        )

        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        logging.info(f"   duration: {minutes}:{seconds:02d}")

        anonymized_chunks.append(anonymized_text)

    # Save the results
    # Each chunk is already a block of text. We join these blocks.
    # The separator used here will now separate the processed chunks.
    full_anonymized_text = "\n\n--- Page Break ---\n\n".join(anonymized_chunks)

    pdf_file_name = Path(pdf_path).stem
    anonymized_output_file = f"{pdf_file_name}.anonymized_output.txt"
    with open(anonymized_output_file, "w", encoding="utf-8") as f:
        f.write(full_anonymized_text)

    mapping_file = f"{pdf_file_name}.mapping.json"
    # fix some glitch:
    final_mapping = {k: v for k, v in final_mapping.items() if k != v}
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(final_mapping, f, indent=4)

    logging.info("Anonymization complete!")
    logging.info(f"Anonymized text saved into '{anonymized_output_file}'")
    logging.info(f"Mapping vocabulary saved into '{mapping_file}'")


if __name__ == "__main__":
    app.command()(main)
    app()
