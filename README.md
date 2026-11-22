# AdaptLearn AI

Plateforme d’apprentissage adaptatif en français : comptes privés, cours Python, quiz corrigés, parcours personnalisé, recommandations et progression. Le studio produit des résumés, fiches et quiz avec un **RAG sémantique LangChain**, des **embeddings neuronaux locaux** et un **véritable LLM configurable**.

Lire [EXPLICATION_PROJET.md](EXPLICATION_PROJET.md) pour comprendre le code et [docs/RAG.md](docs/RAG.md) pour configurer le RAG.

## Lancer

Python 3.12 ou supérieur recommandé.

```bash
git clone https://github.com/H-devigner/adaptlearn-ai.git
cd adaptlearn-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/download_model.py
python -m flask --app app run --port 5050
```

Ouvrir http://127.0.0.1:5050 puis créer un compte. Les profils, cours et quiz éditoriaux fonctionnent sans fournisseur IA. **Le studio exige un LLM configuré** ; l’ancien générateur extractif a été supprimé.

Les données SQLite, modèles et index sont locaux dans `instance/`, exclu de Git. Les données des versions précédentes sont conservées. Pour reproduire les versions de dépendances vérifiées : installer `requirements-lock.txt` (inclut aussi les dépendances de déploiement).

## Configurer le LLM

Exemple Ollama installé localement :

```bash
ollama pull qwen2.5:1.5b
```

Créer `.env` à la racine :

```dotenv
AI_MODE=llm
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:1.5b
```

Ollama doit être en cours d’exécution. Pour un fournisseur distant, remplacer l’URL, le modèle et la clé par ses paramètres. Aucun secret ne doit être suivi par Git. Redémarrer Flask après configuration.

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

- [Explication et liste de vérification](EXPLICATION_PROJET.md)
- [Détails du RAG](docs/RAG.md)
- [Déploiement Docker et cloud](docs/DEPLOIEMENT.md)
- [Démonstration](docs/DEMONSTRATION.md)
- [Résultats des vérifications](docs/VERIFICATION.md)
