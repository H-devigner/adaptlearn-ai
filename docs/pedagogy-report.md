# Lot A — Contenus et pédagogie

Le catalogue conserve ses cinq cours et leurs informations d’origine. Chaque leçon contient des explications, des exemples Python exécutables, un exercice et quatre questions à quatre choix, avec un corrigé expliqué.

Le parcours retient la tentative la plus récente pour chaque leçon. À 70 % ou plus, la leçon est maîtrisée. Le premier cours accessible à maîtriser passe en priorité, avec une révision si un score insuffisant existe. Les prérequis du catalogue couvrent les bases des leçons suivantes. Le niveau déclaré affine les explications et les recommandations.

Les recommandations placent les révisions accessibles et la prochaine leçon en tête. Elles peuvent signaler une leçon ultérieure qui correspond au niveau ou à l’objectif et indiquer les prérequis à maîtriser. Le rapprochement avec l’objectif compare les mots du titre, de la description et des thèmes, en tenant compte des accents et des pluriels simples.

Les statistiques calculent une moyenne des pourcentages par tentative et un taux de maîtrise sur le catalogue. Le détail par leçon distingue le dernier score du meilleur. La chronologie conserve une entrée par tentative, de la plus ancienne à la plus récente.

## Vérifications

| Commande | Résultat |
| --- | --- |
| `.venv/bin/python -m unittest discover -s tests -p test_pedagogy.py` avant implémentation | 12 erreurs attendues pour fonctions ou module absents. |
| `.venv/bin/python -m unittest discover -s tests -p test_pedagogy.py` après implémentation | 12 tests réussis. Les cas couvrent le catalogue, la validation des réponses, le seuil de maîtrise, les prérequis, l’ordre et l’explication des recommandations, l’historique et l’absence de données. |
| `git diff --check -- courses.py` | Aucun problème d’espacement signalé. |

Les 13 blocs de code indentés des leçons ont aussi été exécutés dans une session Python par leçon. Les sorties obtenues correspondaient aux exemples, du premier affichage à l’épuisement d’un générateur.
