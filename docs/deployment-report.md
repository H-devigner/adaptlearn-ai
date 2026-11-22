# Vérifications du lot déploiement

- `podman-compose config -q` a accepté `compose.yaml` avec des valeurs de test. La validation a refusé une configuration sans secrets renseignés. L’inspection du résultat a confirmé la publication du seul port web sur `127.0.0.1:5050`, ainsi que les réseaux distincts du service IA et de PostgreSQL.
- Le workflow GitHub Actions a été analysé avec un lecteur YAML local. Il exécute la suite SQLite sur Python 3.12 et 3.14, compile les fichiers Python et lance le test d’intégration sous PostgreSQL 17. Son troisième job démarre la pile Compose et essaie une génération authentifiée entre les conteneurs web et IA.
- `pip` a résolu Gunicorn 27.0.1 et Psycopg 3.3.9 sur Python 3.14 et les a installés sur Python 3.12 dans un environnement temporaire.
- Les deux commandes Gunicorn ont passé `--check-config`. En démarrant les processus sur des sockets Unix temporaires, les deux routes `/health` ont répondu HTTP 200. Le site utilisait SQLite dans ce test. La génération IA locale avec le jeton de test a répondu HTTP 200.
- Le binaire Docker est absent sur cette machine. Le moteur Podman local refuse la connexion. Le démarrage des conteneurs reste couvert par le workflow CI. Aucune instance cloud n’a été créée.
