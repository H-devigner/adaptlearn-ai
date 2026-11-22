# Démontrer la plateforme en dix minutes

## Avant la présentation

Lancer le projet suivant le README et ouvrir http://127.0.0.1:5050. Préparer deux comptes de démonstration pour montrer l’isolation. Configurer un véritable LLM (Ollama local ou fournisseur compatible) et vérifier le téléchargement du modèle d’embeddings avant la présentation. Voir docs/RAG.md.

## 1. Besoin et architecture — une minute

Expliquer le besoin : un apprenant veut identifier sa prochaine leçon, s’évaluer et réviser à partir de ses propres documents. Montrer les modules et les deux configurations : Flask/SQLite local, ou web/service IA/PostgreSQL avec Compose.

## 2. Compte et profil — une minute

Créer un compte, renseigner le pseudonyme « Lina », niveau « Débutant », objectif « Comprendre les variables Python ». Montrer que le profil est conservé au redémarrage et propre à ce compte.

## 3. Leçon et évaluation — deux minutes

Ouvrir « Premiers pas avec Python », lire la leçon, passer son quiz. Faire une erreur pour montrer le score et l’explication. Revenir au parcours : la leçon est à revoir. Repasser avec les bonnes réponses : le dernier score atteint le seuil et les variables deviennent la prochaine leçon.

## 4. Adaptation et statistiques — une minute

Montrer la raison donnée par le parcours, la page Ressources puis la progression. Expliquer la différence entre dernier résultat, meilleur résultat et moyenne de toutes les tentatives. La maîtrise correspond au dernier score supérieur ou égal à 70 %, pas au temps passé.

## 5. RAG et génération — trois minutes

Dans « Mes documents », coller ce texte sous le titre « Énergie solaire » :

> L’énergie solaire provient du rayonnement du Soleil. Les panneaux photovoltaïques transforment une partie de ce rayonnement en électricité. Un onduleur transforme le courant continu en courant alternatif. L’orientation et l’ensoleillement influencent la production. Une batterie peut stocker une partie de l’électricité pour un usage ultérieur.

Dans le studio, sélectionner « Mes documents », saisir « énergie solaire » et générer un résumé. Montrer les extraits retrouvés par similarité sémantique, leurs numéros et les références dans le résumé. Générer ensuite des fiches et un quiz, répondre au quiz et retrouver l’essai dans l’historique. Expliquer que cet entraînement généré ne remplace pas les évaluations éditoriales du parcours.

Exporter le résumé en JSON. Chercher « tectonique abyssale » dans les documents personnels : montrer l’absence de contexte pertinent, sans contenu inventé. Les sources aident à vérifier les supports ; elles ne garantissent pas automatiquement leur exactitude pédagogique.

Reformuler la demande avec des synonymes pour montrer la recherche sémantique. Expliquer le rôle distinct des embeddings, de l’index vectoriel et du LLM. Une génération appelle désormais toujours le LLM : le générateur extractif n’existe plus.

## 6. Isolation, limites et suite — deux minutes

Se déconnecter, ouvrir le second compte et constater l’absence des documents et résultats du premier. Montrer le rapport EXPLICATION_PROJET.md et sa liste de vérification. Expliquer les limites : petit catalogue, seuil de similarité sémantique à évaluer, absence d’OCR, nécessité de relire les sorties LLM et déploiement cloud à réaliser dans l’environnement choisi.
