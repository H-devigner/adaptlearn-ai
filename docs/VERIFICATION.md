# Vérification du RAG LangChain et de la simplification

Date : 22 novembre 2026.

## Suite complète locale

```sh
RUN_SEMANTIC_TESTS=1 HF_HUB_OFFLINE=1 .venv/bin/python -m unittest discover -s tests -v
```

Résultat après intégration : **101 tests rapportés, 100 réussis, 1 ignoré**. Seul le test PostgreSQL est ignoré faute de serveur local ; il est exécuté dans GitHub Actions.

Les trois tests sémantiques utilisent le véritable modèle multilingue FastEmbed téléchargé depuis son dépôt officiel. Les deux paraphrases françaises retrouvent le passage attendu en premier, avec des scores observés de 0.5703 et 0.6626. La question hors sujet ne renvoie aucune source. Un test vérifie aussi qu’un fait situé à la fin d’une longue note reste indexé sans troncature silencieuse.

Les tests rapides injectent des embeddings déterministes et un fournisseur HTTP factice ; ils ne sont jamais utilisés comme moteur de l’application. Ils couvrent les index privés, leur invalidation, les erreurs et limites de transport, les références, les imports PDF/texte, les profils, les quiz et la protection des comptes.

Les commandes `ruff check .`, `python -m compileall -q *.py scripts tests`, `pip check`, `git diff --check`, la compilation de tous les templates Jinja et la validation des deux fichiers Compose ont réussi.

## Vrai LLM local

Un serveur Ollama dédié au projet a été lancé sur `127.0.0.1:11435`, avec ses modèles dans `instance/ollama`, exclu de Git. Le petit modèle `qwen2.5:0.5b` a produit un résumé et des fiches valides à partir des sources réellement retrouvées par FastEmbed et LangChain.

Ses essais de quiz sont peu fiables : des choix en double et un mauvais indice ont été observés. Les contrôles n’ont pas été assouplis pour accepter ces réponses. Le dernier quiz invalide est refusé explicitement. Le guide recommande un modèle plus capable pour la présentation et une relecture pédagogique dans tous les cas.

Un second essai avec **`qwen2.5:1.5b`** a terminé les trois formats de bout en bout avec les vrais embeddings et le vrai LLM local. Le résultat est conservé dans `instance/rag-verification.json`. Le format JSON est valide ; la relecture a néanmoins trouvé une confusion factuelle dans le résumé (rôle des panneaux et de l’onduleur) et une question de quiz répétée. Ces observations sont des limites de qualité du petit modèle, pas une preuve d’exactitude pédagogique. Choisir un modèle plus capable et relire les productions avant de les présenter comme des contenus validés.

Les trois formats sont couverts avec un vrai transport HTTP de test et un schéma JSON strict Pydantic. Cela vérifie leur raccordement et la validation, sans prétendre mesurer la qualité générale d’un modèle.

## Revue indépendante

La revue a conduit à corriger :

- Découpage adapté aux 128 tokens du modèle, avec budget de 120 tokens au lieu d’un seul plafond en caractères.
- Purge des index personnels après import et suppression, y compris le dernier document.
- Reconstruction d’un index JSON incomplet ou corrompu.
- Exclusion des scores nuls et empreinte du modèle/cache/corpus.
- Refus des références numériques hors du contexte et isolation du traçage LangChain.
- Préchargement du modèle avant le premier POST du studio sous Docker, pour éviter le délai d’expiration du worker.

La purge ne garantit pas l’effacement instantané des fichiers réécrits par une requête déjà engagée sur son instantané. Les empreintes empêchent leur réutilisation pour un corpus différent. Les extraits sauvegardés avec les productions sont conservés volontairement.

## GitHub Actions

Le workflow vérifie SQLite sur Python 3.12 et 3.14, PostgreSQL, l’intégration avec le modèle multilingue et la pile Docker Compose. Le test Compose précharge le modèle dans le même volume que le web et utilise un fournisseur factice déclaré uniquement dans `compose.test.yaml`. Il n’appelle pas de fournisseur payant.

Consulter [les exécutions du dépôt](https://github.com/H-devigner/adaptlearn-ai/actions) pour les résultats de la révision publiée. Les anciens rapports `*-report.md` décrivent les étapes intermédiaires ; ce document et docs/RAG.md décrivent la nouvelle architecture.

Aucune clé payante n’a été utilisée et aucune VM cloud publique n’a été créée.
