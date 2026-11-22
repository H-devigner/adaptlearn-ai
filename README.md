# AdaptLearn AI

Plateforme d’apprentissage adaptatif en français : comptes privés, cours Python, quiz corrigés, parcours personnalisé, recommandations et progression. Le studio produit des résumés, fiches et quiz avec un **RAG sémantique LangChain**, des **embeddings neuronaux locaux** et un **véritable LLM configurable**.

Lire [EXPLICATION_PROJET.md](EXPLICATION_PROJET.md) pour comprendre le code et [docs/RAG.md](docs/RAG.md) pour configurer le RAG.

## Lancer

Pour un premier clonage, installer Git, Python 3.12 ou supérieur (3.12 recommandé) et [Ollama](https://docs.ollama.com/quickstart). Le lancement local utilise SQLite : Docker et PostgreSQL ne sont pas nécessaires.

```bash
git clone https://github.com/H-devigner/adaptlearn-ai.git
cd adaptlearn-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ces commandes utilisent un terminal macOS/Linux. Sous Windows PowerShell, créer l’environnement avec `py -3.12 -m venv .venv`, puis l’activer avec `.venv\Scripts\Activate.ps1`.

Configurer ensuite Ollama et `.env` comme indiqué ci-dessous, avant de lancer le studio. Les profils, cours et quiz éditoriaux fonctionnent sans fournisseur IA. **Le studio exige un LLM configuré** ; l’ancien générateur extractif a été supprimé.

Les données SQLite, modèles et index sont locaux dans `instance/`, exclu de Git. Les données des versions précédentes sont conservées. Pour reproduire les versions de dépendances vérifiées : installer `requirements-lock.txt` (inclut aussi les dépendances de déploiement).

## Configurer le LLM

Exemple Ollama installé localement :

Ouvrir l’application Ollama. Si aucun serveur n’est déjà actif, exécuter `ollama serve` dans un autre terminal et le laisser ouvert. Dans le terminal du projet, télécharger le modèle :

```bash
ollama pull qwen2.5:1.5b
```

Depuis la racine du projet, copier l’exemple avec `cp .env.example .env` (PowerShell : `Copy-Item .env.example .env`), puis modifier les quatre valeurs suivantes dans `.env` :

```dotenv
AI_MODE=llm
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:1.5b
```

Ollama doit être en cours d’exécution. La valeur `ollama` est un paramètre conventionnel du client, pas une clé payante. Pour un lancement local en développement, les secrets Docker/production de l’exemple peuvent rester vides : une clé de session locale est créée automatiquement. Pour un fournisseur distant, remplacer l’URL, le modèle et la clé par ses paramètres. Aucun secret ne doit être suivi par Git. Redémarrer Flask après configuration.

Pour un premier clonage, utiliser le port Ollama standard **11434**. Le port **11435** cité dans le guide RAG correspond à un serveur de test préparé sur la machine d’origine ; il n’est pas démarré par le clonage.

Dans le terminal du projet, avec l’environnement virtuel actif :

```bash
python scripts/download_model.py
python -m flask --app app run --port 5050
```

Ouvrir **http://127.0.0.1:5050**, créer un compte puis compléter le profil. La base SQLite et ses tables sont créées automatiquement ; il n’existe pas de compte par défaut. Garder le terminal Flask ouvert. `Ctrl+C` arrête le serveur.

Lors d’un lancement ultérieur, il suffit de démarrer Ollama, réactiver `.venv` et relancer la commande Flask. Il n’est pas nécessaire de recloner ni de retélécharger les modèles déjà présents.

Le premier usage du studio télécharge le modèle d’embeddings multilingue FastEmbed. Il encode ensuite les documents sur la machine. Les passages sélectionnés sont envoyés uniquement au LLM configuré. Voir [la configuration détaillée](docs/RAG.md).

## Comment fonctionne le RAG

```text
Documents du compte + leçons autorisées
  → Découpage LangChain adapté au modèle
  → Embeddings neuronaux multilingues FastEmbed
  → Index vectoriel LangChain persisté en JSON privé
  → Recherche des passages par similarité cosinus
  → Prompt LangChain + ChatOpenAI
  → Support JSON validé, sauvegardé avec les sources [1], [2]…
```

Il n’y a plus de recherche TF-IDF ni de repli extractif. Les anciennes productions restent consultables avec un libellé historique. Le moteur de recommandations du parcours garde ses règles explicites (dernier score, prérequis, niveau et objectif).

## Où lire le code

| Module | Rôle |
| --- | --- |
| `app.py`, `auth.py` | Application, profil, comptes et sessions |
| `database.py` | Stockage SQL paramétré SQLite / PostgreSQL |
| `courses.py`, `pedagogy.py`, `learning.py` | Leçons, quiz, adaptation et statistiques |
| `retrieval.py` | Découpage, embeddings et index vectoriel |
| `generation.py` | Prompt LangChain, appel LLM et validation |
| `studio.py` | Routes du studio, sauvegarde et consultation |
| `document_import.py` | Extraction et validation texte/PDF |
| `ai_client.py`, `ai_service.py` | Service IA indépendant optionnel |
| `templates/`, `static/` | Pages HTML et styles CSS |

## Vérifier

```bash
python -m unittest discover -s tests -v
python -m compileall -q *.py scripts tests
RUN_SEMANTIC_TESTS=1 python -m unittest discover -s tests -p test_semantic_integration.py -v
python scripts/verify_rag.py
```

La suite rapide utilise des doubles explicites. Le test sémantique télécharge et exécute le vrai modèle d’embeddings. Le dernier script effectue de vraies générations avec votre LLM et conserve les résultats dans `instance/rag-verification.json`.

La CI vérifie Python 3.12/3.14, PostgreSQL, Docker et le modèle multilingue. Dans le test Docker seulement, `compose.test.yaml` lance un fournisseur factice, sans clé payante. La configuration normale `compose.yaml` exige votre LLM.

## Guides

- [Agent handoff and conversation context](AGENT_CONTEXT.md)
- [Explication et liste de vérification](EXPLICATION_PROJET.md)
- [Détails du RAG](docs/RAG.md)
- [Déploiement Docker et cloud](docs/DEPLOIEMENT.md)
- [Démonstration](docs/DEMONSTRATION.md)
- [Résultats des vérifications](docs/VERIFICATION.md)
