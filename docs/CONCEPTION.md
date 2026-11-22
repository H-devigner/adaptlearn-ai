# AdaptLearn AI — proposition de conception

Statut : conception acceptée le 22 novembre 2026. La demande suivante étend la livraison aux étapes 2 à 8. Voir `../EXPLICATION_PROJET.md` pour le fonctionnement actuel et les limites. Les sections ci-dessous conservent la conception initiale et son premier périmètre.

## Objectif

Construire progressivement une plateforme pédagogique en français, avec un code simple à expliquer lors des présentations d'avancement.

## Choix possibles

1. Flask, pages HTML et SQLite : recommandé pour comprendre facilement le fonctionnement complet et limiter les dépendances.
2. FastAPI et React : séparation frontend/backend plus nette, mais davantage de code et d'outillage.
3. Streamlit : démonstration rapide, mais moins adapté à une plateforme web structurée à terme.

## Architecture proposée

Une application Flask organisée en modules : profils, cours, évaluations, génération, recommandations et statistiques. HTML/CSS pour les pages, SQLite pour les données structurées. Les services restent dans une application au début ; leur extraction en microservices et le cloud appartiennent à la dernière étape. Une base NoSQL ne sera ajoutée que si un besoin concret le justifie.

## Livraisons successives

| Étape | Contenu | Démonstration attendue |
| --- | --- | --- |
| 1 | Socle Flask, SQLite, profil de démonstration, catalogue initial | Enregistrer un niveau et un objectif, consulter les cours, retrouver le profil après redémarrage |
| 2 | Quiz prédéfinis et suivi des tentatives | Répondre à un quiz, obtenir un score calculé côté serveur, retrouver son historique |
| 3 | Parcours adaptatif à règles explicites | Obtenir la prochaine leçon selon le niveau et les résultats, avec une explication |
| 4 | Génération par LLM | Produire un quiz, un résumé et une fiche depuis un cours, avec validation des réponses et gestion des erreurs |
| 5 | RAG sur les supports pédagogiques | Importer des documents, rechercher leurs passages et afficher les sources des contenus générés |
| 6 | Recommandation de ressources | Classer les ressources selon les objectifs et les difficultés, expliquer chaque recommandation |
| 7 | Learning Analytics | Afficher les scores, les compétences travaillées et leur évolution à partir des tentatives réelles |
| 8 | Industrialisation | Ajouter authentification, isolation des données, PostgreSQL, conteneurs, services séparés si nécessaire et déploiement cloud |

## Périmètre de la première étape

Application locale avec un seul profil de démonstration, sans authentification. Champs : prénom ou pseudonyme, niveau et objectif pédagogique. Catalogue initial de cours d'introduction à Python. Pages : accueil, profil et catalogue. Les données du profil sont persistées dans SQLite ; les cours sont chargés depuis un petit jeu de données initial.

Aucune génération IA n'est annoncée comme réalisée dans cette livraison. Les étapes futures sont indiquées explicitement dans la documentation.

## Qualité et erreurs

Valider les champs obligatoires et les niveaux acceptés côté serveur. Afficher des messages compréhensibles pour les entrées invalides. Utiliser des requêtes SQL paramétrées. Exclure la base locale, les environnements virtuels et les secrets du dépôt.

Vérifier le lancement, les pages, l'enregistrement et la persistance du profil ainsi que le rejet des valeurs invalides. À l'étape LLM, conserver les clés hors du code et traiter les délais, erreurs du fournisseur et sorties mal formées.

## Organisation et présentation

Dossier : /Users/houcine/Desktop/Random/adaptlearn-ai.
Dépôt GitHub proposé : adaptlearn-ai, privé par défaut.
Chaque livraison aura un commit identifiable, un README de lancement et une courte procédure de démonstration. La première présentation montrera le besoin, l'architecture cible, le socle réalisé, ses limites et la prochaine étape.

## Condition de publication

La session GitHub CLI du compte H-devigner fonctionne avec l’accès réseau autorisé. Le dépôt sera privé par défaut.
