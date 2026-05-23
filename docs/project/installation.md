# Installation & Setup

This guide details how to set up PDF Anonymizer for development or programmatic usage.

---

## 1. Development Installation (Monorepo)

The repository uses **`uv`**, a fast Python package installer and resolver. Ensure you have `uv` installed. If not, follow the [official Astral installation instructions](https://astral.sh/docs/uv#installation).

### Steps
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/LeoGan/anonymizer.git
    cd anonymizer
    ```

2.  **Sync the workspace**:
    Run `uv sync` to create a virtual environment and install all development tools alongside workspace members:
    ```bash
    uv sync --group dev
    ```
    This sync command will install the CLI, core library, and the dependencies for all supported LLM providers (`google`, `ollama`, `huggingface`, `openrouter`, `openai`, `anthropic`).

3.  **Activate the virtual environment**:
    ```bash
    source .venv/bin/activate
    ```

---

## 2. Installing as a Library Dependency

If you are using `pdf-anonymizer-core` or `pdf-anonymizer-cli` in a separate external project, you can install them via `pip` or `uv`.

To keep the installation footprint small, the core package uses **PEP 508 Extras** for specific LLM providers. Install only the providers you plan to use:

```bash
# Base package only (no provider dependencies)
pip install pdf-anonymizer-core

# Install specific provider support
pip install "pdf-anonymizer-core[google]"
pip install "pdf-anonymizer-core[ollama]"
pip install "pdf-anonymizer-core[openai,anthropic]"
```

### Available Extras
*   `[google]`: Installs the Google GenAI SDK (`google-genai`).
*   `[ollama]`: Installs the Ollama integration library.
*   `[huggingface]`: Installs libraries to connect to Hugging Face Hub models.
*   `[openrouter]`: Installs client tools to query OpenRouter.
*   `[openai]`: Installs the official OpenAI API SDK.
*   `[anthropic]`: Installs the official Anthropic API SDK.

---

## 3. Environment Variables Configuration

To run the anonymizer with cloud providers, you must supply API credentials. The CLI automatically loads a `.env` file from the directory where the command is executed or any parent directory. 

Create a `.env` file at the root of the repository:

```env
# Google GenAI (Gemini Models)
GOOGLE_API_KEY="AIzaSy..."

# OpenAI
OPENAI_API_KEY="sk-proj-..."

# Anthropic (Claude Models)
ANTHROPIC_API_KEY="sk-ant-..."

# Hugging Face Hub
HUGGING_FACE_TOKEN="hf_..."

# OpenRouter
OPENROUTER_API_KEY="sk-or-v1-..."

# Ollama Local Host (Optional, defaults to localhost:11434)
OLLAMA_HOST="http://localhost:11434"
```

---

## 4. Verifying the Setup

To verify that the installation succeeded and all package internal references are valid, run the automated test suite:

```bash
uv run pytest
```

If the tests pass, you are ready to use the CLI tool!
