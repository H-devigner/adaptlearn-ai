# AdaptLearn AI — setup from a fresh clone

This guide runs the project locally with SQLite, local embeddings and Ollama. Docker, PostgreSQL and a paid API key are not required for this setup.

Commands use a macOS/Linux terminal. Windows PowerShell alternatives are provided where needed.

## 1. Install the prerequisites

- Git.
- Python 3.12 or newer; Python 3.12 is recommended.
- [Ollama](https://docs.ollama.com/quickstart), installed and running.
- Internet access for Python dependencies and the initial model downloads.

## 2. Clone the repository and install dependencies

```bash
git clone https://github.com/H-devigner/adaptlearn-ai.git
cd adaptlearn-ai

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt
```

If you have already cloned the repository, open a terminal inside `adaptlearn-ai` and skip the first two commands.

On Windows PowerShell, replace the environment creation and activation commands with:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

Keep the virtual environment active for the following Python commands.

## 3. Start Ollama and download the generation model

Open the Ollama application. If the server is not already running, use a second terminal:

```bash
ollama serve
```

Leave that terminal running. If Ollama is already running, do not start another server on the same port.

In the project terminal, download the model:

```bash
ollama pull qwen2.5:1.5b
```

The model is downloaded once and reused on later runs. `ollama list` shows the installed models.

## 4. Create the local configuration

From the project root, copy the example into a new `.env` file:

```bash
cp .env.example .env
```

PowerShell equivalent:

```powershell
Copy-Item .env.example .env
```

These copy commands are for a fresh clone. If `.env` already exists, edit it instead of overwriting your configuration.

Open `.env` in your editor and set:

```dotenv
AI_MODE=llm
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:1.5b
LLM_TIMEOUT=45
```

- `ollama` is a conventional value required by the compatible client, not a paid API key.
- For this local development setup, the Docker/production secret fields in the example may remain empty. The app creates a local session key automatically.
- Keep `.env` private; it is excluded from Git.
- Use the standard Ollama port **11434** for a fresh setup. Port **11435**, mentioned elsewhere in the project, was used by an isolated test server on the original machine and is not automatically created by cloning.

## 5. Download the embeddings model and start the application

In the project terminal, with `.venv` active:

```bash
python scripts/download_model.py
python -m flask --app app run --port 5050
```

The first command downloads and loads the multilingual embeddings model used by semantic retrieval. This is separate from the Ollama generation model downloaded in step 3. Wait until it completes before starting Flask.

Leave the Flask terminal open. Press `Ctrl+C` to stop the application.

## 6. Open the application and create an account

Open **http://127.0.0.1:5050**.

1. Create your account; there is no default login.
2. Complete your learner profile.
3. Try a lesson and its quiz.
4. Import a document and try the pedagogical studio.

The app creates `instance/adaptlearn.sqlite` and its tables automatically. You do not need to run SQL initialization commands.

A fresh clone does not include the original machine's `.env`, accounts, database, documents, indexes or model weights. The local application creates or downloads what it needs during setup.

## 7. Check the setup

Run the automated suite from the project root:

```bash
python -m unittest discover -s tests -v
```

Some integration checks are intentionally skipped unless their environment variables or services are available. See [docs/VERIFICATION.md](docs/VERIFICATION.md) for the distinction between unit tests, actual embeddings and PostgreSQL checks.

To check the full RAG with actual embeddings and your configured LLM:

```bash
python scripts/verify_rag.py
```

This makes real local model calls and saves the retrieved sources and generated materials to `instance/rag-verification.json`. Successful JSON validation does not guarantee factual or pedagogical accuracy; review the generated content.

## Starting the project again later

Start Ollama if needed. In a terminal inside the project:

```bash
source .venv/bin/activate
python -m flask --app app run --port 5050
```

On PowerShell, activate with `.venv\Scripts\Activate.ps1` instead. You do not need to clone again, reinstall dependencies or redownload models that are already present. Restart Flask after editing `.env`.

## Common setup problems

| Problem | What to check |
| --- | --- |
| `python3` is missing or too old | Install Python 3.12+; on Windows use the Python launcher shown above. |
| `ollama` is not found | Install Ollama and reopen the terminal so its CLI is available. |
| Cannot connect to the LLM | Ensure Ollama is running and `.env` points to the same port. |
| Model not found | Run `ollama list`, then pull the exact model named by `LLM_MODEL`. |
| First embeddings download is slow or fails | Check internet access and rerun `python scripts/download_model.py` before starting the studio. |
| App still uses the old provider settings | Stop and restart Flask after editing `.env`. |
| Generated material is refused or inaccurate | Check the provider/model and review [the recorded small-model limitations](docs/VERIFICATION.md). |

For implementation details, read [EXPLICATION_PROJET.md](EXPLICATION_PROJET.md). For provider settings and the semantic retrieval pipeline, read [docs/RAG.md](docs/RAG.md).
