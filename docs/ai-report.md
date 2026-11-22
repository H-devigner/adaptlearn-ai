# Recherche documentaire et génération pédagogique

## Recherche

`retrieval.search_documents` découpe les documents en extraits de 1 200 caractères au maximum. Deux extraits successifs partagent jusqu’à 180 caractères. Quand un espace se trouve près d’une limite, le découpage le privilégie pour conserver les mots entiers. La recherche normalise la casse, les accents, les ligatures et les séparateurs, puis retire des mots-outils fréquents. Chaque extrait et son titre sont représentés par un vecteur TF-IDF. La similarité cosinus fournit le classement. Un résultat requiert au moins un terme de contenu ou de titre commun avec la requête. Par défaut, la recherche rend au plus quatre extraits avec leur identifiant de document, leur titre, leur index et leur score.

Cette approche lexicale traite `énergie` et `energie` de la même façon. Les synonymes et les variantes morphologiques peuvent nécessiter une reformulation. Le calcul s’effectue en mémoire sur les documents transmis à la recherche.

## Génération

Le mode `local` sélectionne des passages et les classe selon les mots de la requête. Il assemble jusqu’à six passages pour un résumé, jusqu’à huit fiches fondées sur des termes de ces passages ou jusqu’à six questions à trous. Dans les quiz, le bon choix complète le passage d’origine. Les autres choix proviennent en priorité du vocabulaire des extraits et utilisent des termes génériques si le vocabulaire disponible est trop court. Des indices grammaticaux peuvent rendre certains faux choix faciles à éliminer.

Le mode `llm` utilise `LLM_BASE_URL` (par défaut `https://api.openai.com/v1`), `LLM_MODEL`, `LLM_API_KEY` et `LLM_TIMEOUT` (45 secondes par défaut). Il envoie la requête et le texte des extraits à un fournisseur compatible avec `POST /chat/completions`. Le prompt place ces données dans le message utilisateur et les identifie comme non fiables dans le message système. La validation exige un objet JSON dont les champs, les quantités et les longueurs respectent le format choisi. Elle contrôle notamment les quatre choix distincts du quiz et l’indice entier de la bonne réponse. `validate_material` expose la même validation au client du service IA. Les erreurs de transport et de réponse utilisent des messages dépourvus des détails du fournisseur. La validation contrôle la structure du support. Le texte du modèle reste à relire et l’application appelante associe les extraits originaux à chaque production.

## Service HTTP

La fabrique `ai_service.create_app` exige `AI_SERVICE_TOKEN` au démarrage. `GET /health` retourne `{"status":"ok"}`. `POST /generate` exige `Authorization: Bearer <jeton>` et reçoit un objet `kind`, `query`, `sources` de 200 Kio au maximum. La requête accepte jusqu’à 1 000 caractères et jusqu’à 16 extraits. Chaque extrait contient `document_id`, `title`, `text`, `chunk_index` et `score`. Les erreurs sont des objets `{"error":"…"}` avec le code `400` pour les entrées invalides, `401` pour le jeton, `413` pour la taille ou `502` pour la génération LLM indisponible ou invalide.

## Vérification

- `.venv/bin/python -m unittest discover -s tests -p test_ai.py -v` a exécuté 19 tests avec succès. Les tests couvrent la recherche française, le chevauchement, les trois formats locaux, les sorties invalides, les erreurs fournisseur, l’authentification et les limites HTTP.
- `.venv/bin/python -m compileall -q retrieval.py generation.py ai_service.py tests/test_ai.py` a réussi.
- Le banc d’essai remplace le transport `urllib` pour inspecter la requête HTTP construite et injecter des réponses fournisseur. Le bac à sable a refusé l’ouverture d’un socket local et aucun fournisseur LLM réel n’a été appelé.
