# Agent Instructions for pdf-anonymizer

This document provides instructions for agents and developers working on the `pdf-anonymizer` codebase.

## Project Overview

This project is a Python application that anonymizes PDF and text files using Large Language Models (LLMs). It is designed to be modular, extensible, and production-ready.

## Development Setup

1.  **Install `uv`**: Follow the official instructions at [https://astral.sh/docs/uv#installation](https://astral.sh/docs/uv#installation).
2.  **Clone the repository**: `git clone <repository_url>`
3.  **Install dependencies**: `uv sync`
4.  **Set up environment variables**: Create a `.env` file in the root directory. You can use `.env.template` as a starting point.

## Running Tests

To ensure code quality and prevent regressions, all tests must pass before submitting changes. To run the test suite, use the following command:

```bash
uv run python -m unittest discover tests
```

## Error Handling

The application has a robust error handling mechanism to prevent the accidental leakage of sensitive information.

-   The `anonymize_text_with_llm` function in `src/pdf_anonymizer/call_llm.py` will attempt to call the LLM up to 3 times.
-   If all retries fail, it will raise an `AnonymizationError` exception.
-   This exception is caught in `src/pdf_anonymizer/core.py`, which will halt the anonymization process for the current file.

**Important**: When modifying the error handling logic, ensure that the application never fails silently and returns un-anonymized text.

## Model Configuration

All model definitions are centralized in `src/pdf_anonymizer/conf.py`.

-   The `ModelName` enum defines the available models.
-   The `ModelProvider` enum distinguishes between Google and Ollama models.
-   The `provider` property of the `ModelName` enum is used to determine which LLM API to call.

When adding a new model, update the `ModelName` enum and the `provider` property accordingly. Do not hardcode model names elsewhere in the codebase.

## Containerization

This project includes a `Dockerfile` for building a container image. To build the image, run:

```bash
docker build -t pdf-anonymizer .
```

To run the application in a container:

```bash
docker run pdf-anonymizer run /path/to/your/document.pdf
```
