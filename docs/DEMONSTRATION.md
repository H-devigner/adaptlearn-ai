# Présenter l’étape 1 en cinq minutes

## 1. Besoin et objectif — une minute

« Nous construisons une plateforme qui vise à adapter les apprentissages au profil et aux résultats. À terme, elle générera des quiz, des résumés et des fiches à partir des supports pédagogiques. »

## 2. Architecture — une minute

Montrer `app.py`, `database.py`, `courses.py` et `templates/` : le navigateur envoie un formulaire à Flask, Flask valide les données et SQLite les conserve. Expliquer que cette première structure privilégie la lisibilité et prépare des modules séparables.

## 3. Démonstration — deux minutes

1. Lancer l’application avec les commandes du README.
2. Ouvrir l’accueil puis « Mon profil ».
3. Saisir le pseudonyme « Lina », le niveau « Débutant » et l’objectif « Comprendre Python pour analyser des données ».
4. Enregistrer et montrer le message de confirmation.
5. Revenir à l’accueil : le pseudonyme et l’objectif sont affichés.
6. Modifier le niveau dans le profil puis enregistrer.
7. Arrêter et relancer le serveur : le profil est conservé.
8. Ouvrir le catalogue : cinq fiches, leurs niveaux, thèmes et durées estimées.

Les champs obligatoires sont contrôlés par le navigateur et par le serveur ; les tests automatisés vérifient aussi les requêtes invalides envoyées directement au serveur.

## 4. Bilan et suite — une minute

Acquis : application fonctionnelle, interface, profil persistant et catalogue. Montrer le tableau des huit étapes dans le README.

Limites actuelles : un seul profil local, fiches de présentation des cours, aucun quiz, aucune génération IA et aucun score de progression. Les chiffres de l’accueil décrivent le catalogue et l’étape du projet, pas la progression pédagogique.

Prochaine livraison : répondre à un quiz prédéfini, calculer le score côté serveur, conserver les tentatives et consulter leur historique. Les résultats serviront ensuite à adapter le parcours.
