# Génération des supports avec LangChain

`generation.py` enchaîne `ChatPromptTemplate`, `ChatOpenAI` et `StrOutputParser`. Le modèle reçoit la requête, les titres, les extraits sélectionnés et leurs références `[1]`, `[2]`, etc. Les scores et identifiants internes restent dans l’application. Le prompt demande un support en français fondé sur les extraits et place les données de recherche dans le message utilisateur. L’appel isole les callbacks de LangChain et désactive le traçage LangSmith. [Documentation ChatOpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai)

Les modèles Pydantic définissent un schéma JSON strict pour chaque format et valident la réponse reçue. Le corps de la réponse est limité à 128 Kio pendant sa lecture. Le parseur refuse les doublons de clés et les constantes JSON non standard. L’application ajoute `mode: llm` au résultat. Chaque référence citée doit correspondre à un extrait fourni. Un modèle peut omettre les références, même si le prompt les demande. Les supports historiques portant `mode: local` passent toujours la validation.

La génération utilise `LLM_API_KEY` et `LLM_MODEL`. Le fournisseur doit prendre en charge `response_format: json_schema`. `LLM_BASE_URL` peut cibler `http://localhost:11434/v1` avec `LLM_API_KEY=ollama` et un modèle installé dans Ollama. `LLM_TIMEOUT` vaut 45 secondes par défaut. Le SDK reçoit une limite de 1 800 jetons et effectue une seule tentative. Le client bloque les redirections et les erreurs utilisateur ne contiennent ni clé ni réponse brute du fournisseur. [Schémas de sortie OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs) · [Compatibilité Ollama](https://docs.ollama.com/api/openai-compatibility)

Les 25 tests ciblés passent avec Python 3.14.5. Ils couvrent le contrat des trois formats avec un serveur HTTP OpenAI factice sur `127.0.0.1`, les réponses invalides, les limites de taille, le délai, les redirections, l’isolation du traçage et la route du service IA.

La vérification avec FastEmbed et Ollama 0.17.7 a retrouvé le passage solaire attendu. `qwen2.5:0.5b` a produit un résumé et des fiches valides. Le quiz est resté irrégulier. Une réponse brute contenait des choix en double, et la validation a rejeté le quiz lors du dernier essai. Le schéma encadre la structure. La pertinence du texte et l’exactitude de la réponse dépendent du modèle. La configuration du guide propose `qwen2.5:1.5b`. [Modèles Qwen2.5 dans Ollama](https://ollama.com/library/qwen2.5)

```sh
.venv/bin/python -m unittest discover -s tests -p test_ai.py -v
```
