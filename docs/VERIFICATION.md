# Rapport final de vérification

Date : 22 novembre 2026.

## Vérification locale de la version complète

Commande exécutée après corrections de la revue :

```sh
.venv/bin/python -m unittest discover -s tests -v
```

Résultat : **76 tests rapportés, 75 réussis, 1 ignoré**. Le seul test ignoré est l’intégration PostgreSQL, faute de serveur PostgreSQL local et de `TEST_DATABASE_URL`. Les deux tests de transport HTTP fonctionnent avec un fournisseur factice de boucle locale, sans appel externe payant.

`python -m compileall -q *.py tests`, `pip check` et `git diff --check` ont également réussi. L’environnement local utilise Python 3.14 et les versions de `requirements-lock.txt`.

## Vérification sur GitHub Actions

La [première exécution de la version complète](https://github.com/H-devigner/adaptlearn-ai/actions/runs/45038633108), sur la révision `134af4c`, a réussi dans les quatre jobs :

- Suite SQLite sur Python 3.12.
- Suite SQLite sur Python 3.14.
- Véritable test de stockage et d’isolation sur PostgreSQL 17.
- Construction de l’image, démarrage des trois services Docker Compose, vérification du web connecté à PostgreSQL et génération authentifiée sur le réseau privé du service IA.

Les trois corrections ultérieures issues de la revue sont couvertes localement : réponses multiples au quiz éditorial, validation UUID des routes privées et traitement des refus métier du service IA. La [seconde exécution complète](https://github.com/H-devigner/adaptlearn-ai/actions/runs/45039097650), sur la révision corrigée `0e78601`, a également réussi dans les quatre jobs : SQLite Python 3.12/3.14, PostgreSQL 17 et pile Compose. Le code de la livraison finale est identique à cette révision ; les modifications suivantes concernent uniquement le présent compte rendu.

## Revue et démonstration

Une revue indépendante a identifié trois anomalies P2, reproduites dans des tests puis corrigées. La contre-revue a confirmé leur résolution. Les tests du studio vérifient aussi les pages HTML rendues, les imports texte/PDF, les trois formats, l’export sans corrigé et l’isolation des comptes.

Le serveur local de la version complète a été lancé sur `http://127.0.0.1:5050`. Le navigateur a atteint la page d’inscription ; l’outil de capture de l’écran n’a ensuite pas permis une inspection visuelle complète de cette version. La relecture visuelle sur petit écran reste dans la liste de vérification manuelle. L’accueil de la première livraison avait été contrôlé visuellement.

## Ce qui n’a pas été exécuté

- Aucun appel réel à un modèle distant : il faut configurer une clé et un modèle pour valider la qualité de leurs productions.
- Aucun provisionnement ni déploiement public sur un fournisseur cloud : la procédure est fournie dans DEPLOIEMENT.md.
- Aucune étude avec de vrais apprenants, mesure de qualité pédagogique ou évaluation statistique du système de recommandation.

Le succès des tests confirme les comportements couverts. Il ne remplace pas une revue pédagogique des contenus ni les vérifications d’exploitation avant une ouverture publique.
