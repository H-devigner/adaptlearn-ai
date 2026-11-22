# AdaptLearn AI — conversation context and agent handoff

Prepared on 2026-11-22 for another agent to resume this project.

**Read the current-state section first.** The conversation record below is chronological: some earlier answers describe implementations that were subsequently replaced. In particular, the repository is now public, the initial shared profile was replaced by private accounts, and TF-IDF/extractive generation was replaced by semantic LangChain RAG.

This file records every user request in this conversation and the substance of every final assistant response. User wording is preserved, with line wrapping normalized. Assistant answers are summarized rather than presented as a byte-for-byte chat export. Intermediate progress messages and tool logs are consolidated into the implementation notes. Local file links are normalized to repository-relative paths; credentials and personal machine paths are omitted.

## 1. Current state: start here

- Project: **AdaptLearn AI**, a French-language academic prototype of an adaptive learning platform.
- Public repository: <https://github.com/H-devigner/adaptlearn-ai>.
- Default branch: `main`.
- Latest application release at handoff preparation: **`v1.1.0`**.
- Application baseline: commit [`71c6933`](https://github.com/H-devigner/adaptlearn-ai/commit/71c69331af0a78fd772ccca191f5e37af5a19d4b). This handoff and its README link are documentation changes after that baseline.
- The user wants **simple, understandable code**, an application they can explain in a project progress presentation, and documentation they can review and correct.
- The user explicitly requested a **real RAG**, suggested LangChain, asked for code simplification, and authorized pushing the changes to GitHub.
- The user subsequently requested that the repository be made **public**. This was done and anonymous HTTP access returned 200. Do not treat the earlier private-repository answers as the current visibility.
- No new application feature has been specified after the RAG delivery. The latest request is to save the conversation context in the GitHub project for a future agent.

### Read these existing documents instead of reconstructing the project

| Document | Purpose |
| --- | --- |
| [README.md](README.md) | Installation, current stack, module map, test commands |
| [EXPLICATION_PROJET.md](EXPLICATION_PROJET.md) | Main French explanation for the user, algorithms and review checklist |
| [docs/RAG.md](docs/RAG.md) | Current semantic RAG, configuration, local Ollama setup and limitations |
| [docs/VERIFICATION.md](docs/VERIFICATION.md) | Actual test evidence and observed model-quality problems |
| [docs/DEMONSTRATION.md](docs/DEMONSTRATION.md) | Presentation walkthrough |
| [docs/DEPLOIEMENT.md](docs/DEPLOIEMENT.md) | Docker, PostgreSQL, model preloading, HTTPS and cloud procedure |
| [docs/CONCEPTION.md](docs/CONCEPTION.md) | Original eight-stage design; historical initial scope |
| [RAG specification](docs/superpowers/specs/2026-11-22-rag-semantique.md) | Scope of the latest functional change |
| [RAG implementation plan](docs/superpowers/plans/2026-11-22-rag-semantique.md) | Completed work breakdown |

## 2. User preferences and working agreement

1. Keep the implementation and explanations accessible to a learner. Avoid adding infrastructure or abstractions without a concrete need.
2. The initial intention was to build stage by stage. The user later explicitly expanded the task to complete all remaining stages; do not restart from stage 1.
3. The application UI and most project documentation are in French. The user has also made requests in English; respond in the language of the current request.
4. Explain what the code actually does. Distinguish rules from machine learning, embeddings from generation, structural JSON validation from factual accuracy, and a deployment configuration from a real public deployment.
5. Keep the written project explanation current when behavior changes. The user wants to review it and request corrections.
6. Preserve accounts, user data and historical productions when evolving the application.
7. Push the requested project work to the existing repository. Do not create another repository unless asked.
8. The repository is public: never commit `.env`, passwords, API keys, private documents, database files, model weights or cached indexes.

## 3. Complete chronological question-and-answer record

### Exchange 1 — original project request and staged delivery

**User:**

> 1. Conception d'une plateforme d'apprentissage adaptatif exploitant l'intelligence artificielle.
> générative pour la personnalisation des parcours pédagogiques et la génération automatique de
> contenus éducatifs
> Objectifs :
> • Génération automatique de quiz, résumés et fiches de révision.
> • Personnalisation des parcours selon le profil de l'apprenant.
> • Recommandation intelligente de ressources pédagogiques.
> • Analyse et suivi de la progression des apprenants.
> Technologies : LLM, RAG, Learning Analytics, Recommender Systems, Microservices, Cloud
> Computing, Bases de données SQL/NoSQL.
>
> creer le projet dans un nouveau dossier ,et push dans une nouvelle github repo; ecrit un code simple et facile a comprendre , mon objectif est de presenter un etat d avancement de projet donc on va le diviser en etqpes et raliser etape par etape ; liste moi les etapes aussi

**Assistant response:**

- Created a new `adaptlearn-ai` directory and [proposed design](docs/CONCEPTION.md).
- Recommended **Flask + HTML/CSS + SQLite** to keep the code easy to understand and present.
- Proposed eight deliveries:
  1. Persistent learner profile and course catalogue.
  2. Quizzes, scores and history.
  3. Adaptive path based on level and results.
  4. LLM-generated quizzes, summaries and revision cards.
  5. RAG over educational documents with sources.
  6. Explained resource recommendations.
  7. Learning Analytics dashboard.
  8. Authentication, cloud deployment preparation and evolution toward microservices.
- Proposed implementing stage 1 first and asked the user to approve the design, as required by the brainstorming workflow used in that session.
- Initially reported an invalid GitHub authentication token. Later verification outside the restricted network showed authentication was valid; this was not a lasting account problem.

### Exchange 2 — design approval and stage 1 implementation

**User:**

> ok continue a developer , jaccepte la conception

**Assistant response:**

- Implemented stage 1 and pushed it to the newly created **private** GitHub repository.
- Delivered creation/modification of one demonstration learner profile, persistent SQLite storage, five Python course catalogue cards, French UI and form validation.
- Reported five passing tests and a visual check of the initial home page in Chrome.
- Started the application at `http://127.0.0.1:5050`.
- Provided the README, the eight-stage roadmap and a five-minute presentation guide.
- Identified predefined quizzes, correction and result history as the next stage.

**Historical note:** The single shared demonstration profile was later replaced by authenticated per-account profiles. Its legacy SQL table is retained rather than automatically assigning it to a new account.

### Exchange 3 — authorization to complete all remaining stages

**User:**

> ok complete tout le reste et donne a la fin un fichier qui explique le tout pour que je le verifie et corriger apres

**Assistant response:**

- Completed and pushed an academic prototype as **`v1.0.0`**.
- Added private accounts, corrected quizzes, adaptive paths, recommendations, progression statistics and a document studio.
- Supplied [EXPLICATION_PROJET.md](EXPLICATION_PROJET.md) with installation, module descriptions, algorithms, limitations, a verification checklist and a corrections table.
- Reported successful Python, PostgreSQL and Docker checks.
- Explained that the local demonstration generator was extractive, that a real LLM required provider configuration, and that cloud deployment files were prepared without provisioning a public cloud instance.

**Historical note:** This first full version used lexical TF-IDF retrieval and an extractive local generation mode. Both were subsequently removed at the user's request. Do not restore them as the default behavior.

### Exchange 4 — unique usernames

**User:**

> pour la creation de compte? le nom d utilisateur est unique?

**Assistant response:**

- Yes: the SQL `users.username` field has a `UNIQUE` constraint.
- Names are normalized to lowercase, so `Sara` and `sara` refer to the same username.
- Duplicate registration displays **« Ce nom d’utilisateur est déjà utilisé. »**
- Usernames contain 3–40 characters: unaccented letters, digits, `-` or `_`.
- The learner profile's display name/pseudonym is separate and does not have to be unique.

### Exchange 5 — understanding the implementation

**User:**

> maint je veux comprendre ce que tas fait

**Assistant response:**

Explained the application through a learner's journey:

1. Create an account; the password is hashed. Complete a profile with level and learning objective. Documents, results and productions belong to that account.
2. Read one of five Python lessons and answer its four-question quiz. Python was chosen as the initial demonstration subject.
3. The server calculates the score. Example: three correct answers out of four gives 75%.
4. The last course score determines mastery, using a 70% threshold. An insufficient score triggers a revision recommendation; prerequisites guide the next lesson.
5. Recommendations prioritize revision and the next course, then use the declared level and objective. The dashboard uses real stored attempts.
6. Import text or a text-based PDF, retrieve passages, and produce revision materials.
7. Described the then-current local extractive mode versus the configurable LLM mode, and explicitly said the path adaptation was programmed rules, not a trained model.
8. Mapped the code to application/configuration, authentication, SQL storage, pedagogy, retrieval/generation, templates and CSS. Suggested reading `courses.py` → `pedagogy.py` → `learning.py` first.

**Historical note:** The account, quiz and rules explanations still apply. The TF-IDF/extractive explanation described the implementation before Exchange 8.

### Exchange 6 — technology stack

**User:**

> stack utilise?

**Assistant response:**

Listed the stack and responsibilities:

| Part | Answer at the time |
| --- | --- |
| Backend | Python + Flask |
| Frontend | HTML + CSS + Jinja2, without React |
| Local SQL | SQLite |
| Distributed SQL | PostgreSQL |
| LLM integration | OpenAI-compatible API |
| Retrieval at that point | TF-IDF and cosine similarity implemented in Python |
| PDF extraction | pypdf |
| Authentication | Werkzeug password hashing and Flask sessions |
| Tests | unittest |
| Application server | Gunicorn |
| Containers | Docker and Docker Compose |
| CI | GitHub Actions |
| Source control | Git and GitHub |

The answer clarified that the then-current local configuration used extractive generation and no LLM by default, and that no public cloud deployment had been performed.

**Current correction:** Retrieval now uses LangChain, FastEmbed/ONNX and a vector index. Generation uses ChatOpenAI and a strict Pydantic JSON schema. There is no current extractive-generation fallback.

### Exchange 7 — where SQL writes happen

**User:**

> ou le code des enregistrement en bqse de donnees

**Assistant response:**

- Pointed to [database.py](database.py), where SQL is written directly without an ORM.
- Explained the writing functions:

| Function | Stored data |
| --- | --- |
| `create_user()` | User account |
| `save_profile()` | Learner profile |
| `save_attempt()` | Quiz result, submitted answers and correction |
| `add_document()` | Imported document text |
| `save_generation()` | Generated material and source snapshot |

- Used account creation as the example:

```python
with connect(path) as db:
    db.execute(
        'INSERT INTO users VALUES (?, ?, ?, ?)',
        (user_id, username.lower(), password_hash, now()),
    )
```

- Explained that the values are the UUID, normalized username, password hash and creation date; parameters are kept separate from SQL.
- Showed that `auth.py` calls `create_user(..., generate_password_hash(password))` after validating the form.
- Described the flow: registration form → validation/hash in `auth.py` → SQL insert in `database.py` → `commit()` in `connect()`.
- Explained `rollback()` on error and connection closure.
- Located the local database at `instance/adaptlearn.sqlite`.

**Navigation note:** Formatting/refactoring has changed line numbers. Locate functions by name rather than using line numbers from old chat links.

### Exchange 8 — explicit request for semantic LangChain RAG and simpler code

**User:**

> pour le rag je veux un vrai rag (peut etre avec langchain) , et si tu peux rendre tout le code plus simple et push le tout dqns github

**Assistant response:**

- Implemented and pushed **`v1.1.0`** on `main`.
- Replaced TF-IDF with semantic retrieval using:
  - LangChain document splitting and generation composition.
  - Local multilingual neural embeddings through FastEmbed.
  - A private vector index per account and source scope.
  - A real configurable LLM, with Ollama prepared on the user's machine.
- Removed the extractive demonstration generator.
- Reorganized and formatted the code; separated document imports and the optional AI-service HTTP client from studio routes.
- Reported five successful CI jobs covering Python, PostgreSQL, actual multilingual embeddings and Docker.
- Tested real summary, flashcard and quiz generation with Ollama, while explicitly noting that small models can produce incorrect content and need review.
- Linked the revised [project explanation](EXPLICATION_PROJET.md) and [RAG guide](docs/RAG.md).
- Left the app available at `http://127.0.0.1:5050` during the session.

**Important implementation/test details not to lose:**

- This uses LangChain's **`InMemoryVectorStore` persisted as private JSON**, not FAISS, Chroma or a hosted vector database. It is still vector retrieval over real neural embeddings.
- The embedding model is `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, loaded through FastEmbed/ONNX. Token-aware splitting uses a 120-token budget to respect the model's 128-token input capacity, plus the service's character limit.
- The generation path uses `ChatPromptTemplate`, `ChatOpenAI`, strict JSON schemas and Pydantic validation. Provider compatibility requires the structured JSON response format used by the code.
- Existing historical productions remain readable. The application adds `retrieval_method='semantic'` to new saved materials, after provider validation.
- A real `qwen2.5:1.5b` run completed all three formats structurally, but review found a factual confusion and a repeated quiz question. Do not equate valid JSON with correct educational content. Details are in [docs/VERIFICATION.md](docs/VERIFICATION.md).
- RAG scores are cosine similarities, not confidence probabilities. The threshold needs evaluation on the user's documents.
- The code and final CI were verified before the documentation-only release commit; no paid API key or public cloud instance was used.

### Exchange 9 — GitHub link appeared broken

**User:**

> le lien github no fontionne pas, avez cous la pusher dans github ?

**Assistant response:**

- Rechecked the repository through authenticated GitHub access.
- Confirmed that `main` contained commit `71c6933` and that tag `v1.1.0` existed remotely.
- Explained that the repository was private at that moment and needed access from the owning GitHub account; another account or anonymous access could see a 404.
- Supplied the correct repository link.

### Exchange 10 — make the repository public

**User:**

> peut etre public svp

**Assistant response:**

- Changed `H-devigner/adaptlearn-ai` from private to **public**, as explicitly requested.
- Verified `isPrivate=false` and anonymous HTTP 200 access.
- Provided the public repository link.

**Current status:** Public visibility was checked again while preparing this handoff. Keep it public unless the user asks otherwise.

### Exchange 11 — this handoff request

**User:**

> can u write an md file and attach it to the github project files, where you note all the questions/responses of the conversation to act as a context for an other Agent to resume project building

**Assistant response/work for this request:**

- Acknowledged the request to create and push a Markdown handoff.
- Applied the handoff workflow, honoring the user's explicit destination in the GitHub project rather than a temporary-only handoff.
- Checked the working tree, current code, documentation, published commit, repository visibility and latest main-branch CI.
- Created this root-level **`AGENT_CONTEXT.md`** and added a discoverable README link.
- This documentation change does not alter application behavior. The final chat reply links to the published file.

## 4. Current implementation map for the next agent

Use source files and the linked guides as the authority for implementation details; the conversation explains why the choices were made.

| Area | Entry points |
| --- | --- |
| App/configuration/profile | `app.py:create_app()` |
| Registration/login/session/CSRF | `auth.py` |
| SQLite/PostgreSQL and parameterized writes | `database.py` |
| Five Python lessons and editorial quizzes | `courses.py` |
| Quiz correction, 70% mastery, path, recommendations, analytics | `pedagogy.py`, `learning.py` |
| Neural embeddings, token-aware splitting, index cache, search | `retrieval.py:search_documents()` |
| LangChain prompt and structured LLM generation | `generation.py:generate_material()` |
| Authenticated document/material/quiz routes | `studio.py` |
| UTF-8 text and PDF extraction | `document_import.py` |
| Optional separate generation service | `ai_client.py`, `ai_service.py` |
| Frontend | `templates/`, `static/style.css` |
| Exact dependency snapshot / development formatting | `requirements-lock.txt`, `requirements-dev.txt`, `pyproject.toml` |

Current design deliberately keeps these distinctions:

- Adaptive path and resource ranking are explained rules, not a trained recommender model.
- Editorial quiz attempts determine course mastery; generated quiz attempts are separate practice.
- The latest editorial score controls mastery, not the best-ever score. Courses remain freely accessible; prerequisites guide recommendations.
- Document imports are private to an account. Persisted vector indexes are scoped to account and corpus selection.
- The provider receives selected excerpts and the request, not the learner's password or full results history.
- New generation requires a real configured LLM; legacy local-mode data is supported for viewing, not as a new fallback generator.
- SQL stores the structured relationships and JSON material. No extra NoSQL service was added without a concrete need.

## 5. Environment and verification handoff

### Reproduce from a clone

Follow the [README](README.md) and [RAG guide](docs/RAG.md). Model weights and local configuration are deliberately not included in Git.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_model.py
python -m flask --app app run --port 5050
```

Configure a compatible LLM before using the studio. Use [.env.example](.env.example) as a template; do not ask the user to publish their private `.env`.

The original machine had an isolated Ollama server on localhost port **11435**, models under `instance/ollama`, and a local `.env` pointing to `qwen2.5:1.5b`. The usual Ollama examples use port **11434**. The distinction and restart command are in [docs/RAG.md](docs/RAG.md). Running background processes are session-specific: check whether they still exist rather than assuming they survived a new agent/session.

Private runtime locations include `instance/adaptlearn.sqlite`, `instance/secret.key`, embedding weights, vector indexes and `instance/rag-verification.json`. Preserve them on the original machine; do not commit them. A fresh clone will not contain them.

### Verification evidence, not a promise of future results

- The recorded full local suite reported **101 tests, 100 passed, 1 skipped**. PostgreSQL was skipped locally and exercised in CI.
- Three integration tests ran the actual multilingual embedding model. The fast tests use explicitly injected doubles, never an application fallback.
- Actual Ollama calls completed the three JSON formats; their educational accuracy is not guaranteed.
- A real Flask-route smoke test covered registration, CSRF, import, embeddings, generation, SQLite persistence, rendering and private export.
- All five CI jobs passed for the corrected application revision: SQLite Python 3.12, SQLite Python 3.14, PostgreSQL 17, real multilingual retrieval, and Docker Compose with model preloading.
- The latest application-baseline run was checked again during this handoff: [successful main CI for `71c6933`](https://github.com/H-devigner/adaptlearn-ai/actions/runs/45054972213). More evidence is linked from [docs/VERIFICATION.md](docs/VERIFICATION.md).
- Ruff, Python compilation, Jinja template compilation and relevant configuration checks passed during the functional delivery. Do not report these as fresh verification after later code changes without rerunning them.

Useful commands:

```bash
python -m unittest discover -s tests -v
RUN_SEMANTIC_TESTS=1 python -m unittest discover -s tests -p test_semantic_integration.py -v
python scripts/verify_rag.py
```

The last command makes real calls to the configured LLM. `HF_HUB_OFFLINE=1` is useful only when the model is already cached. `TEST_DATABASE_URL` enables the optional PostgreSQL integration test against a dedicated test database.

### Deployment details that were fixed and must not regress

- Preload embeddings with `scripts/download_model.py` before the first studio request under Gunicorn; a cold model download can exceed the web worker timeout.
- Docker must include `scripts/` in the build context and give the non-root application user a writable home for the model download libraries.
- The web model/index volume is separate from PostgreSQL data. Use the documented backup and deployment procedure.
- `compose.test.yaml` supplies a clearly labeled fake provider only for CI. It is not a demonstration mode or a production LLM.
- No public cloud application has been provisioned. Public GitHub source code is not a publicly deployed application.

## 6. Known limits and reasonable next work

These are observations or possible follow-ups, not newly approved feature requirements:

1. **Generated educational quality:** small local models produced factual mistakes, duplicated quiz questions and occasionally invalid answers. Existing controls validate format, types, lengths, choices and reference bounds; they do not prove factual entailment or pedagogical quality. Improve evaluation and/or select a stronger model without silently fabricating a fallback.
2. **Retrieval evaluation:** the real-model evidence covers a small French fixture. Evaluate on the user's own educational corpus; tune the threshold based on measured retrieval quality. Do not report a cosine score as accuracy.
3. **Concurrent cache invalidation:** import/deletion purges the relevant index, but a request already working on an older corpus snapshot can rewrite a stale cache. Fingerprints prevent reuse for a different corpus. There is no strong immediate-erasure guarantee during concurrent requests.
4. **Source retention:** saved productions intentionally retain excerpt snapshots after an imported document is deleted. Changing that policy needs an explicit design decision.
5. **Prototype operations:** no teacher/admin roles, password-reset email, distributed login throttling, full audit trail, LLM spending limits, isolated PDF processing or versioned schema migrations. Do not describe the app as production-hardened.
6. **Scale:** exact in-memory cosine search with JSON persistence is intentional for a small corpus. Do not add a hosted vector service or extra database just because the project mentions cloud/microservices.
7. **Presentation/user learning:** keep the user's explanation and review checklist up to date. The user has been asking where functions live and how the stack works; explain changes with concrete examples.

## 7. Suggested skills for a resuming agent

Use these only if available in the next environment and applicable to the next task:

- **Git workflow and versioning:** inspect status/history, preserve user changes, keep commits focused, and verify the push.
- **Brainstorming / writing plans:** for genuinely new functionality or a change in architecture, using the already accepted requirements as context.
- **Test-driven development:** reproduce a behavioral defect or specify a new behavior before implementation. Documentation-only changes do not need artificial application tests.
- **Systematic debugging / diagnosing bugs:** for runtime, retrieval, provider or deployment failures.
- **Requesting code review:** before integrating substantial changes.
- **Verification before completion:** run appropriate fresh checks and distinguish real-model evidence from mocks and skipped tests.
- **Docker expertise:** if changing the image, model cache, Compose networking, volumes or deployment.
- **Handoff:** keep this record accurate when preparing another transfer. The user explicitly requested this handoff to live in the GitHub project.

## 8. Resume checklist

- [ ] Read this file, README, EXPLICATION_PROJET.md, docs/RAG.md and docs/VERIFICATION.md.
- [ ] Inspect the actual checkout, `git status`, active branch, latest remote commit and applicable repository instructions.
- [ ] Recheck runtime/configuration without printing or publishing secrets.
- [ ] Understand that semantic LangChain RAG is the accepted current implementation; do not rebuild the superseded TF-IDF/extractive version.
- [ ] Establish an appropriate test baseline for the next code change.
- [ ] Continue with the user's next requested improvement; no additional functional task is implicitly assigned by this handoff.
- [ ] Preserve simple explanations, French UI, existing data, privacy checks and source attribution.
- [ ] Update the explanatory documents and verify any requested GitHub publication.
