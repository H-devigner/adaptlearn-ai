# AdaptLearn AI

Plateforme d’apprentissage adaptatif construite étape par étape pour un projet académique. L’objectif final est de personnaliser les parcours et de générer des contenus éducatifs avec des LLM et du RAG.

**Livraison actuelle : étape 1 — profil apprenant et catalogue.**

## Lancer le projet

Python 3.10 ou supérieur recommandé (vérifié avec Python 3.14).

```bash
git clone https://github.com/H-devigner/adaptlearn-ai.git
cd adaptlearn-ai
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m flask --app app run --port 5050
```

Ouvrir http://127.0.0.1:5050. Arrêter avec `Ctrl+C`. Pour les prochains lancements, activer l’environnement puis relancer la dernière commande. La base SQLite est créée automatiquement dans `instance/` et conservée après arrêt.

## Ce qui fonctionne

- Accueil présentant le profil et l’état du projet.
- Création et modification d’un profil : pseudonyme, niveau et objectif.
- Validation côté serveur et messages d’erreur en français.
- Persistance du profil dans SQLite.
- Catalogue de cinq fiches de cours Python avec niveau, thèmes et durée estimée.
- Interface française adaptée aux petits écrans.

Le catalogue présente les cours : les leçons détaillées ne sont pas encore disponibles. Cette version locale utilise **un profil partagé, sans connexion utilisateur**. Elle ne calcule pas encore de progression et ne génère aucun contenu par IA. Aucune clé API n’est nécessaire.

## Comprendre le code

```text
app.py                  Création de Flask, routes et validation
courses.py              Catalogue initial et niveaux autorisés
database.py             Lecture et écriture SQLite
templates/              Pages HTML Jinja
static/style.css        Présentation et adaptation mobile
tests/test_app.py       Tests HTTP avec une base temporaire
docs/CONCEPTION.md      Architecture et feuille de route
docs/DEMONSTRATION.md   Scénario de présentation
```

Un formulaire valide passe par `app.py`, puis `save_profile()` dans `database.py`. La route relit ensuite le profil pour remplir la page HTML. Les requêtes SQL sont paramétrées et Jinja échappe les textes affichés.

L’architecture commence dans une seule application organisée en fichiers simples. Les microservices et le cloud seront abordés après validation des fonctions pédagogiques. SQLite couvre les premiers besoins SQL ; une base NoSQL ne sera ajoutée que si nécessaire.

## Étapes du projet

| Étape | Livrable | État |
| --- | --- | --- |
| 1 | Profil apprenant, catalogue, stockage SQLite | Réalisée |
| 2 | Quiz prédéfinis, correction et historique des résultats | À réaliser |
| 3 | Parcours adaptatif fondé sur le niveau et les scores | À réaliser |
| 4 | Génération de quiz, résumés et fiches avec un LLM | À réaliser |
| 5 | RAG sur les documents avec références aux sources | À réaliser |
| 6 | Recommandation expliquée de ressources | À réaliser |
| 7 | Tableau de bord Learning Analytics | À réaliser |
| 8 | Authentification, cloud et évolution vers les microservices | À réaliser |

Chaque étape sera réalisée et vérifiée séparément. La prochaine livraison portera sur les quiz prédéfinis, avant d’ajouter la génération IA.

## Vérifier

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

Les tests utilisent une base temporaire indépendante des données de démonstration. Ils vérifient les pages, la sauvegarde après recréation de l’application, la modification, le refus des entrées invalides et l’échappement des textes.

## Références techniques

- [Installation officielle de Flask](https://flask.palletsprojects.com/en/stable/installation/)
- [SQLite dans le tutoriel Flask](https://flask.palletsprojects.com/en/stable/tutorial/database/)
