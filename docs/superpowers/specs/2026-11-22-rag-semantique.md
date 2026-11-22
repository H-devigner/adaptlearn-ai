# RAG sémantique et simplification

L’utilisateur demande de remplacer le RAG lexical par un RAG avec LangChain, de simplifier le code et de publier sur GitHub. Cette évolution met en œuvre le module RAG de la conception déjà acceptée.

## Choix

LangChain fournit les Documents, le découpage récursif, un index vectoriel InMemoryVectorStore (cosinus exact, adapté au petit corpus) et le prompt de génération. FastEmbed exécute localement un modèle neuronal multilingue `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. L’index est persistant en JSON dans instance/rag, séparé par compte et périmètre, invalidé lorsque le corpus change. Aucun document privé n’est envoyé à un service d’embeddings.

Le générateur utilise ChatOpenAI et un prompt LangChain pour produire du JSON validé. Le mode extractif de démonstration est retiré : une génération nécessite un LLM configuré (fournisseur compatible ou Ollama local). Aucune clé API n’est disponible au départ ; ne pas prétendre avoir testé un fournisseur payant. Les anciennes productions restent consultables et leurs modes historiques identifiables.

Le flux reste lisible : charger les documents autorisés → découper → calculer les embeddings → indexer → retrouver les passages → prompt + LLM → valider → sauvegarder avec sources. La recherche sémantique doit retrouver des paraphrases françaises même sans mots identiques. Les scores sont des similarités cosinus, pas des probabilités d’exactitude.

## Simplification

Supprimer TF-IDF et le générateur local, remplacer l’appel HTTP fournisseur artisanal par ChatOpenAI. Garder les interfaces des modules, les protections comptes/SQL/CSRF et les fonctions pédagogiques claires. Extraire les opérations d’import de studio dans document_import.py et le client du service IA dans ai_client.py pour que studio expose surtout ses routes. Conserver le service IA optionnel et les comptes existants.

## Vérification

Tests d’abord : recherche sémantique avec embeddings déterministes injectés pour tests rapides, index réellement LangChain, isolation/invalidation, seuil et erreurs de modèle. Test séparé avec véritable modèle multilingue téléchargé. Tests LLM contre fournisseur HTTP factice, validation et absence de repli local. Régressions comptes/quiz/SQL, CI Python3.12/3.14, PostgreSQL et Compose. Mettre à jour EXPLICATION_PROJET.md, README et guide RAG pour expliquer le code débutant et les réglages.
