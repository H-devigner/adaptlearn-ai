"""Petit catalogue éditorial : aucune génération IA à cette étape."""
LEVELS = ('Débutant', 'Intermédiaire', 'Avancé')

COURSES = [
    {'title': 'Premiers pas avec Python', 'level': 'Débutant', 'duration': 20,
     'description': 'Découvrir Python et écrire son premier programme.',
     'topics': ['print()', 'Exécution', 'Commentaires']},
    {'title': 'Les variables', 'level': 'Débutant', 'duration': 25,
     'description': 'Stocker et manipuler des nombres et du texte.',
     'topics': ['Variables', 'Types', 'Calculs']},
    {'title': 'Conditions et boucles', 'level': 'Intermédiaire', 'duration': 35,
     'description': 'Prendre des décisions et répéter des instructions.',
     'topics': ['if / else', 'for', 'while']},
    {'title': 'Fonctions et collections', 'level': 'Intermédiaire', 'duration': 40,
     'description': 'Organiser ses traitements et manipuler des ensembles de données.',
     'topics': ['def', 'Listes', 'Dictionnaires']},
    {'title': 'Compréhensions et générateurs', 'level': 'Avancé', 'duration': 45,
     'description': 'Transformer des collections et produire des valeurs à la demande.',
     'topics': ['Compréhensions', 'yield', 'Itérateurs']},
]
