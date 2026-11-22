# Vérification de la recherche sémantique

Les tests ont utilisé FastEmbed 0.9.1 sur CPU avec le modèle multilingue `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. L'index LangChain classe les passages par similarité cosinus. Le seuil par défaut est de 0,35. [Modèles pris en charge par FastEmbed](https://qdrant.github.io/fastembed/examples/Supported_Models/)

| Question | Résultat | Score cosinus |
| --- | --- | ---: |
| Comment obtenir de l’électricité grâce à la lumière du soleil ? | Passage sur les cellules photovoltaïques, premier résultat | 0,5703 |
| Par quel mécanisme les plantes produisent-elles des sucres ? | Passage sur la photosynthèse, premier résultat | 0,6626 |
| Combien de planètes orbitent autour de Jupiter ? | Aucun passage retenu | 0,1734 au maximum |

Le test d’un document long retrouve aussi la note photovoltaïque en fin de document, après un paragraphe hors sujet. Le découpage garde les extraits sous 1 200 caractères et utilise le tokenizer du modèle sans troncature pour limiter l’entrée à 120 tokens de texte. Le modèle dispose de 128 tokens d’entrée. [Fiche du modèle](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)

```bash
.venv/bin/python -m unittest discover -s tests -p test_retrieval.py -v
HF_HUB_OFFLINE=1 RUN_SEMANTIC_TESTS=1 .venv/bin/python -m unittest discover -s tests -p test_semantic_integration.py -v
```

La deuxième commande suppose les poids déjà téléchargés dans `instance/models/` ou dans `EMBEDDING_CACHE_DIR`. Le test a utilisé la révision Qdrant `faf4aa4225822f3bc6376869cb1164e8e3feedd0`. Une révision différente sélectionnée dans le cache entraîne une reconstruction de l’index au démarrage suivant. [Révision du modèle ONNX](https://huggingface.co/Qdrant/paraphrase-multilingual-MiniLM-L12-v2-onnx-Q/tree/faf4aa4225822f3bc6376869cb1164e8e3feedd0)

Cette mesure couvre deux paraphrases françaises et une question hors sujet. Un sujet secondaire au milieu d’un extrait peut être sous-représenté. En retirant le saut de paragraphe dans le test long, le meilleur score a baissé de 0,5703 à 0,2867. L’index exact parcourt tous les vecteurs et est dimensionné pour les petits corpus du studio. Les fichiers d’index locaux contiennent les extraits en clair et doivent rester sur le volume privé de l’application.
