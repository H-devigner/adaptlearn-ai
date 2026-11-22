# AdaptLearn AI

Plateforme d’apprentissage adaptatif en français, développée progressivement avec un code Python organisé en modules simples. Elle associe cours, quiz, parcours personnalisés, recommandations, suivi de progression et génération de supports depuis des documents.

**Le document à lire pour vérifier et corriger le projet est [EXPLICATION_PROJET.md](EXPLICATION_PROJET.md).**

## Démarrage local

Python 3.12 ou supérieur recommandé (tests prévus sur 3.12 et 3.14).

```bash
git clone https://github.com/H-devigner/adaptlearn-ai.git
cd adaptlearn-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m flask --app app run --port 5050
```

Ouvrir **http://127.0.0.1:5050**, créer un compte puis compléter le profil. Aucun compte ni mot de passe prédéfini. Le mode local fonctionne sans clé API. Les données sont conservées dans `instance/adaptlearn.sqlite`, exclu de Git.

Pour utiliser les versions exactes de l’environnement vérifié, installer `requirements-lock.txt` à la place de `requirements.txt` (inclut les dépendances de déploiement).

## Fonctionnalités

| Étape | Fonction livrée |
| --- | --- |
| 1 | Profil apprenant persistant et catalogue |
| 2 | Cinq leçons Python, quiz corrigés côté serveur et historique |
| 3 | Parcours adaptatif : dernier score, seuil de maîtrise de 70 %, prérequis |
| 4 | Résumés, fiches et quiz : mode local extractif et connecteur LLM configurable |
| 5 | Import `.txt`, `.md`, PDF textuels ; recherche TF-IDF et extraits sources conservés |
| 6 | Ressources classées selon difficultés, niveau et objectif, avec explications |
| 7 | Scores, moyennes, maîtrise par cours et évolution chronologique |
| 8 | Comptes privés, CSRF, PostgreSQL optionnel, service IA indépendant, Docker Compose et CI |

L’intégration LLM se vérifie avec un fournisseur configuré ; aucun appel payant n’est requis pour les tests. Les fichiers de déploiement cloud sont fournis ; aucune VM publique n’a été créée. Les détails des vérifications et limites figurent dans le document explicatif.

## Studio et LLM

Le mode par défaut `AI_MODE=local` découpe et sélectionne les textes, crée des fiches et des quiz à trous. **Il n’utilise pas de LLM.** Pour activer un fournisseur compatible Chat Completions, créer un `.env` local :

```dotenv
AI_MODE=llm
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=votre-cle-privee
LLM_MODEL=identifiant-du-modele-de-votre-fournisseur
LLM_TIMEOUT=45
```

Redémarrer l’application. La requête et les extraits retrouvés seront envoyés au fournisseur choisi. Le mode réel est affiché sur chaque production. Une erreur du fournisseur est signalée ; aucun repli local silencieux.

Le studio recherche dans les leçons intégrées, les documents du compte ou les deux. Les fichiers sont limités à 1 Mio, 50 000 caractères extraits et 30 documents par compte. Les PDF scannés sans texte nécessitent un OCR externe. Les productions sont exportables en JSON ; les corrigés de quiz ne sont pas inclus dans l’export public de l’entraînement.

## Architecture

```text
app.py          Configuration, accueil, profil et santé
 auth.py        Comptes, sessions et CSRF
 database.py    Stockage SQLite / PostgreSQL
 courses.py     Cinq leçons et leurs questions éditoriales
 pedagogy.py    Correction, adaptation, recommandations, statistiques
 learning.py    Routes cours, quiz, résultats, parcours et progression
 retrieval.py   Segmentation et recherche lexicale TF-IDF
 generation.py  Génération locale / connecteur LLM et validation
 ai_service.py  Service HTTP IA facultatif, protégé par jeton
 studio.py      Imports, productions privées et quiz générés
 templates/     Pages HTML Jinja
 static/        Styles CSS sans framework frontend
 tests/         Tests de comportement, sécurité et intégration
```

Le mode local exécute tout dans Flask. Le mode Compose sépare le web, le service IA et PostgreSQL. Le service IA et la base n’exposent pas de port sur l’hôte.

## Vérifier

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
python -m compileall -q *.py tests
```

Le test PostgreSQL exige `TEST_DATABASE_URL` vers une base de test dédiée et `pip install -r requirements-deploy.txt`. Sans cette variable, il est explicitement ignoré. Les tests HTTP fournisseur utilisent un serveur factice local et n’appellent aucun LLM externe. Ils sont ignorés si l’environnement interdit l’ouverture d’un port local.

Les tests CI couvrent Python 3.12/3.14, PostgreSQL 17 et le démarrage Docker Compose. Voir l’onglet Actions pour le résultat de chaque exécution.

## Déployer et présenter

- [Explication complète et liste de vérification](EXPLICATION_PROJET.md)
- [Scénario de démonstration](docs/DEMONSTRATION.md)
- [Déploiement Docker / VM cloud avec HTTPS](docs/DEPLOIEMENT.md)
- [Conception initiale et huit étapes](docs/CONCEPTION.md)

## Références techniques

- [Flask : tutoriel et sécurité](https://flask.palletsprojects.com/en/stable/tutorial/)
- [Psycopg : utilisation de PostgreSQL](https://www.psycopg.org/psycopg3/docs/basic/usage.html)
- [Docker Compose : variables d’environnement](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/)
- [API Chat Completions](https://developers.openai.com/api/reference/resources/chat)
