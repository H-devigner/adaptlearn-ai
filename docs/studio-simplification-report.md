# Simplification du Studio pédagogique

`studio.py` passe de 248 à 178 lignes. Les routes gardent la validation des formulaires, le filtrage des documents par compte, la sauvegarde et l’accès aux productions. `document_import.py` regroupe la lecture des documents et les limites d’import. `ai_client.py` regroupe le transport HTTP du service IA optionnel et la validation de ses réponses.

À chaque génération, le Studio transmet le corpus autorisé et la configuration Flask à `search_documents`. L’espace d’index est propre au compte et au périmètre de recherche. La route renvoie un statut 400 en l’absence d’extrait pertinent et 502 si la recherche ou la génération est indisponible. Le Studio affiche les besoins de configuration sans exposer les clés ni les jetons.

Après chaque import ou suppression, le Studio purge les index du compte pour « Mes documents » et « Toutes les sources ». Si une purge échoue, la modification en base reste enregistrée et un message signale l’échec. Une recherche déjà lancée peut encore écrire son instantané dans le cache. La prochaine recherche compare l’empreinte du corpus avant de réutiliser l’index. Les productions sauvegardées conservent les extraits utilisés lors de leur création.

Les productions locales sauvegardées restent consultables et exportables sous leur mode d’origine. Elles portent le libellé « Génération historique ». Pour chaque nouvelle production, le Studio ajoute `retrieval_method: semantic` au moment de la sauvegarde. Cette métadonnée distingue la similarité sémantique des scores historiques, y compris pour les productions LLM antérieures. La numérotation des extraits correspond aux références demandées au modèle.

## Vérification

`.venv/bin/python -m unittest discover -s tests -p test_studio.py` exécute 20 tests avec succès sur Python 3.14. Les tests couvrent les comptes, la protection CSRF, les identifiants UUID, les imports texte et PDF, les quotas, les exports et la correction des quiz. Ils vérifient aussi la séparation des corpus, la prise en compte des ajouts et suppressions, la gestion d’une erreur de recherche, l’accès à l’historique et les réponses du service IA. Les tests de routes injectent des doubles pour la recherche et la génération, et simulent le transport du service IA. Un test construit de vrais index LangChain avec des embeddings déterministes, puis vérifie que la suppression du dernier document efface les fichiers des deux périmètres privés avant toute nouvelle recherche.
