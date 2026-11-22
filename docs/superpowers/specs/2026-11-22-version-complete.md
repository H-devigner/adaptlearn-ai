# Version complète pédagogique

Le 22 novembre 2026, l’utilisateur demande de réaliser toutes les étapes restantes de la conception acceptée, puis de fournir un fichier explicatif pour vérification et correction. Cette instruction autorise l’exécution continue et la publication dans le dépôt existant.

## Périmètre

Conserver Flask, HTML/CSS et SQLite localement. Ajouter des comptes avec mots de passe hachés et données isolées, des leçons Python, quiz corrigés côté serveur et historique, adaptation par score récent et prérequis, recommandations expliquées et statistiques réelles. Importer du texte UTF-8 et des PDF textuels pour une recherche documentaire lexicale (TF-IDF), puis fournir le contexte retrouvé à un LLM configurable pour générer résumé, fiches ou quiz. Un mode local extractif explicitement étiqueté permet une démonstration sans clé ; il ne se prétend pas LLM.

Le studio conserve les productions et leurs sources par utilisateur. Les quiz générés sont répondables et corrigés séparément des évaluations éditoriales du parcours. Les données du modèle doivent être validées, les erreurs affichées sans secrets. L’authentification, la protection CSRF et le contrôle de propriété s’appliquent aux routes concernées.

## Architecture

- `app.py` : configuration, initialisation et pages de base.
- `auth.py` : comptes, sessions, CSRF et protection des routes.
- `database.py` : accès SQL SQLite/PostgreSQL avec paramètres, schéma additif et dépôts simples.
- `courses.py`, `pedagogy.py`, `learning.py` : contenus, calculs purs et routes pédagogiques.
- `retrieval.py`, `generation.py`, `ai_service.py` : recherche, génération locale/LLM et service HTTP IA indépendant optionnel.
- `studio.py` : import, génération, sauvegarde et consultation des productions.
- Docker Compose : application web, service IA privé, PostgreSQL. Le mode local reste possible en un processus avec SQLite.

Le passage à PostgreSQL est configurable par DATABASE_URL. Les documents et productions sont stockés en SQL/JSON ; une base NoSQL supplémentaire ne présente pas d’intérêt pour cette taille de projet.

## Critères d’acceptation

Inscription/connexion/déconnexion, profil privé, impossibilité de lire les productions d’un autre compte, CSRF sur tous les POST, score calculé côté serveur, aucun corrigé dans le formulaire initial, refus des réponses invalides sans tentative, parcours modifié par résultats, statistiques calculées depuis les tentatives persistées, recherche ne rapportant pas de source sans pertinence, génération structurée validée, limitation des imports et erreurs LLM, conservation des contenus et de leurs extraits sources. Tests SQLite, tests de contrat du service IA, vérification PostgreSQL/Docker si les outils sont disponibles.

## Livrables

Code, tests, README, configuration d’environnement sans secrets, conteneurs et procédure cloud reproductible. Fichier final `EXPLICATION_PROJET.md` : périmètre réalisé, installation, configuration, architecture, schéma des données, algorithmes, routes, scénario de démonstration, résultats des vérifications, limites et liste de points à corriger.

Aucune ressource cloud payante n’est créée sans destination fournie. La configuration et la procédure seront livrées ; l’absence de déploiement réel sera indiquée précisément.
