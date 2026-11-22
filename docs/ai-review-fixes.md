# Corrections après la revue du lot IA

- La validation des textes refuse les caractères NUL et les substituts Unicode isolés avant l’enregistrement d’un support.
- Le quiz local choisit un terme qui apparaît une seule fois dans le passage, après normalisation de la casse et des accents. Le mot attendu reste masqué dans la question.
- La recherche exige un terme commun avec la requête dans le corps de l’extrait. Le titre continue de contribuer au classement des extraits admissibles.
- La recherche rapproche `variable` et `variables` avec une règle simple qui retire le `s` final des mots de plus de quatre caractères. Les pluriels irréguliers et les autres formes fléchies peuvent demander une formulation différente de la requête.
- Deux tests exercent le transport LLM avec un faux fournisseur HTTP sur `127.0.0.1`. Ils vérifient la limite de 128 Kio et le refus d’une redirection avant tout transfert du jeton au point de destination. Le corps d’une réponse d’erreur HTTP est fermé avant de remonter une erreur de génération.

Les tests de régression ont d’abord reproduit les écarts. Après correction, `python -m unittest discover -s tests -p test_ai.py -v` a réussi ses 26 tests avec Python 3.12, dont les deux tests HTTP locaux. Aucun fournisseur externe n’a été appelé.
