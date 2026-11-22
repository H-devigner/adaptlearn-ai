# RAG sémantique — plan d’implémentation

Objectif : RAG LangChain avec embeddings neuronaux multilingues, code plus lisible et publication vérifiée.

- [x] A. retrieval.py et tests/test_retrieval.py : splitter récursif, adaptation FastEmbed vers LangChain, index InMemoryVectorStore persisté JSON privé, cache par corpus et compte, recherche cosinus et seuil configurable. Embeddings déterministes uniquement injectés dans les tests ; intégration séparée avec vrai modèle.
- [x] B. generation.py et tests/test_ai.py : conserver contrat du résultat et contrôles des champs, supprimer extraction locale et transport fournisseur manuel, construire prompt LangChain | ChatOpenAI | parseur JSON, délais bornés, erreurs sans secrets et absence de fallback.
- [x] C. studio.py, document_import.py, ai_client.py : extraire import et client HTTP du service, appeler retrieval avec configuration et namespace privé, conserver validation/propriété et exports. Mettre à jour tests de route avec injections explicites de doubles IA.
- [x] D. Configuration et déploiement : variables embeddings/index/LLM, volume d’index, préchargement optionnel du modèle, CI avec tests rapides et intégration sémantique explicite.
- [x] E. Simplification restante : noms explicites et commentaires pédagogiques, templates structurés, pas de suppression des contrôles de sécurité ni d’API pédagogiques existantes. Documenter les modules et les réglages dans EXPLICATION_PROJET.md et docs/RAG.md.
- [x] F. Vrai modèle d’embeddings, fournisseur local si disponible, revue indépendante, suite complète, CI, fusion main et push GitHub.

Chaque lot est vérifié avant intégration. Exécution continue autorisée par la demande utilisateur.

Livraison vérifiée : 101 tests locaux avec modèle réel, 100 réussis et PostgreSQL ignoré localement puis réussi en CI. Cinq jobs CI verts pour47b173b. Vrai parcours Flask/SQLite/Ollama et trois formatsJSON réels vérifiés. Les limites pédagogiques du petitLLM sont consignées dans docs/VERIFICATION.md.
