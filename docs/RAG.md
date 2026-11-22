# Comprendre le RAG LangChain du projet

Le studio suit maintenant une chaîne RAG sémantique : les passages sont sélectionnés grâce à un véritable modèle d’embeddings, puis transmis à un LLM. L’ancien TF-IDF et le générateur extractif de démonstration ont été retirés.

## Le chemin à lire dans le code

```text
studio.py : liste uniquement les documents autorisés du compte
    ↓
retrieval.py : découpe → embeddings FastEmbed → index vectoriel LangChain → recherche
    ↓
generation.py : prompt LangChain → ChatOpenAI → JSON validé
    ↓
database.py : sauvegarde du support et de la copie des extraits
    ↓
templates/material.html : support + références [1], [2]…
```

Les imports sont traités dans `document_import.py`. Le mode distribué appelle `ai_client.py`, puis le même générateur dans `ai_service.py`.

## Pourquoi ces bibliothèques

- **LangChain** fournit les documents, le découpage, l’index vectoriel et la composition du prompt avec le modèle.
- **FastEmbed / ONNX Runtime** exécute localement le modèle neuronal multilingue `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
- **InMemoryVectorStore** conserve les vecteurs et calcule une similarité cosinus. L’application sauvegarde son contenu dans un fichier JSON pour le retrouver au redémarrage. À l’échelle de 30 documents par compte, un serveur vectoriel supplémentaire n’est pas nécessaire.
- **ChatOpenAI** communique avec une API compatible Chat Completions : fournisseur distant ou Ollama local.

Les embeddings représentent le sens d’un passage par une liste de nombres. Une question parlant d’« électricité issue de la lumière du soleil » peut ainsi retrouver un passage qui parle de « cellules photovoltaïques », sans exiger les mêmes mots.

## Deux modèles distincts

| Modèle | Rôle | Où il s’exécute |
| --- | --- | --- |
| Modèle d’embeddings multilingue | Transformer les textes en vecteurs pour les retrouver | Localement, avec FastEmbed |
| Modèle de génération, par exemple Qwen via Ollama | Produire le résumé, les fiches ou le quiz | Localement avec Ollama ou chez le fournisseur configuré |

L’index vectoriel n’est pas un LLM. LangChain n’est pas non plus un modèle : il relie les étapes.

## Configurer un fournisseur distant

Créer `.env`, puis redémarrer Flask :

```dotenv
AI_MODE=llm
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=votre-cle-privee
LLM_MODEL=identifiant-du-modele-compatible
LLM_TIMEOUT=45
```

Ne pas ajouter `.env` à Git. Le modèle doit accepter Chat Completions et `response_format=json_schema`. Le code affiche une erreur si le fournisseur n’est pas configuré ; il ne remplace plus l’appel par des phrases extraites.

## Configurer Ollama localement

Avec Ollama installé :

```bash
ollama serve
ollama pull qwen2.5:1.5b
```

Si Ollama tourne déjà comme application, la commande `serve` n’est pas nécessaire. Le téléchargement du modèle demande un accès réseau et de l’espace disque. Un modèle plus petit peut être utilisé pour tester le raccordement, mais sa qualité sera plus limitée.

```dotenv
AI_MODE=llm
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:1.5b
```

La valeur `ollama` remplit le paramètre du client compatible OpenAI ; ce n’est pas une clé payante. Dans un conteneur, `127.0.0.1` désigne le conteneur lui-même : adapter l’adresse du serveur Ollama, par exemple `host.docker.internal` avec Docker Desktop.

## Réglages de recherche

```dotenv
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_CACHE_DIR=instance/models
RAG_INDEX_DIR=instance/rag
RAG_MIN_SCORE=0.35
```

Précharger le modèle avec `python scripts/download_model.py` avant une présentation ou un déploiement. Le premier chargement télécharge le modèle depuis sa source publique. Les requêtes suivantes utilisent le cache. Les documents privés sont encodés sur la machine ; ils ne sont pas envoyés au service de téléchargement du modèle.

Le découpage respecte la limite de tokens du modèle et la taille maximale d’un extrait acceptée par le service. Les index sont séparés par compte et périmètre (`all`, `personal`, `courses`). Leur empreinte dépend du corpus et des paramètres d’indexation : une modification du corpus provoque une reconstruction. L’import et la suppression nettoient les index personnels concernés.

Le score est une similarité cosinus, pas une probabilité de vérité. Le seuil `0.35` est un réglage initial à évaluer sur vos propres documents. Un seuil trop bas apporte du bruit ; un seuil trop haut peut éliminer des passages utiles. La recherche retient au plus quatre passages.

Une requête déjà démarrée travaille sur le corpus qu’elle a chargé. Le projet ne garantit pas un effacement physique instantané de tous les caches pendant des opérations concurrentes. Les extraits copiés dans des productions existantes sont conservés afin de pouvoir relire leurs sources.

## Sources et limites

Le prompt numérote les extraits `[1]`, `[2]`… et demande au modèle de citer les références. Les mêmes numéros figurent sous le support. Les contrôles JSON vérifient la structure ; il faut encore relire la fidélité pédagogique du contenu et des citations. Un modèle peut produire une explication erronée même si son JSON est valide.

Les anciennes productions restent lisibles. Une métadonnée `retrieval_method=semantic`, ajoutée par l’application après validation, distingue les nouveaux supports des générations historiques.

## Vérifier avec de vrais modèles

Tests rapides sans téléchargement ni appel payant :

```bash
python -m unittest discover -s tests -v
```

Les doubles d’embeddings et de LLM y sont injectés explicitement ; ce sont des outils de test, absents du fonctionnement réel du studio.

Test du véritable modèle multilingue :

```bash
RUN_SEMANTIC_TESTS=1 python -m unittest discover -s tests -p test_semantic_integration.py -v
```

Vérification complète, avec le LLM réellement configuré dans `.env` :

```bash
python scripts/verify_rag.py
```

Ce script utilise de vrais embeddings et effectue trois générations réelles. Il sauvegarde les sources et les supports dans `instance/rag-verification.json`, sans clé API.

## Références

- [Index vectoriel LangChain](https://reference.langchain.com/python/langchain-core/vectorstores/in_memory/InMemoryVectorStore)
- [Modèles FastEmbed pris en charge](https://qdrant.github.io/fastembed/examples/Supported_Models/)
- [Modèle multilingue MiniLM](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
- [ChatOpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai)

## Configuration préparée sur cette machine

Le dossier local contient un `.env` privé configuré pour `qwen2.5:1.5b` sur le port Ollama dédié **11435**. Les modèles Ollama de cet essai sont dans `instance/ollama`. Pour redémarrer ce serveur depuis la racine du projet :

```bash
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_MODELS="$PWD/instance/ollama" ollama serve
```

La configuration standard des exemples utilise le port Ollama 11434 ; le port 11435 évite de modifier une éventuelle installation personnelle déjà présente. Les modèles ne sont pas inclus dans le dépôt GitHub.
