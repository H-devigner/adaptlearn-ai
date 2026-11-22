# Studio pédagogique

Le studio est accessible aux comptes connectés. Les formulaires POST utilisent le jeton CSRF de la session. Les requêtes SQL des documents, productions et résultats utilisent l’identifiant du compte courant.

## Importer et générer un support

Dans **Mes documents**, indiquez un titre et collez du texte ou joignez un fichier `.txt`, `.md` ou `.pdf`. Les fichiers texte sont décodés en UTF-8, avec prise en charge du marqueur BOM. Pour les PDF, le texte est extrait page par page. Les PDF chiffrés, illisibles et sans texte extractible sont refusés. Le quota de 30 documents est contrôlé à l’insertion. Chaque fichier est limité à 1 Mio, chaque texte à 50 000 caractères et chaque titre à 500 caractères.

Dans **Studio pédagogique**, choisissez un résumé, des fiches ou un quiz, puis recherchez dans vos documents, les leçons Python ou les deux. Le studio appelle le moteur lorsque la recherche trouve un extrait pertinent. Si `AI_SERVICE_URL` est configurée, l’appel HTTP utilise le jeton `AI_SERVICE_TOKEN`, sans suivre les redirections. Le client vérifie la taille et la structure de la réponse et affiche un message générique si le service échoue.

La page de production indique le mode déclaré dans le résultat et affiche le texte des extraits et leur score de similarité lexicale. Les extraits sont sauvegardés avec le support. Une suppression ultérieure du document conserve cet instantané dans les productions déjà créées. La qualité du support se vérifie en relisant le texte associé.

## Consulter, exporter et répondre

| Route | Fonction |
| --- | --- |
| `GET` et `POST /documents` | Lister et importer les documents privés |
| `POST /documents/<id>/supprimer` | Supprimer un document du compte |
| `GET` et `POST /studio` | Voir l’historique et créer une production |
| `GET /productions/<id>` | Consulter le support et les extraits |
| `GET /productions/<id>/export.json` | Télécharger la production et les extraits |
| `GET` et `POST /productions/<id>/quiz` | Répondre au quiz et enregistrer une tentative valide |

Pour un quiz, l’aperçu et le fichier JSON contiennent les questions et les choix. Après validation des réponses, la correction est accessible sur la page de résultat privée. Les tentatives générées apparaissent dans l’historique et sont exclues des mesures de maîtrise du catalogue.

## Vérification

- `.venv/bin/python -m unittest discover -s tests -p test_studio.py -v` exécute 10 tests du studio. Ils couvrent l’authentification et le CSRF, les trois formats, les périmètres, les imports UTF-8 et PDF, le quota, l’isolation, le quiz, la confidentialité du corrigé et les erreurs du service.
- `.venv/bin/python -m unittest discover -s tests -v` a rapporté 70 tests au total avec deux exclusions dans cet environnement. Le serveur PostgreSQL de test n’était pas configuré et le bac à sable bloquait l’ouverture d’un port de boucle locale.
- `.venv/bin/python -m compileall -q studio.py tests/test_studio.py` a réussi.
