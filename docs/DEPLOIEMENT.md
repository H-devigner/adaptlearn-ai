# Déployer AdaptLearn AI

La pile Docker Compose lance le site web Flask avec Gunicorn, un service IA Flask privé et PostgreSQL 17. Le seul port publié sur l’hôte est `127.0.0.1:5050`. Le service IA reçoit les requêtes du site sur le réseau Compose, avec le même `AI_SERVICE_TOKEN` côté client et côté serveur. PostgreSQL se trouve sur un réseau interne auquel seul le site est raccordé.

## Démarrer sur sa machine

Installez Docker Engine avec le plugin Docker Compose v2, ou Docker Desktop. Depuis la racine du dépôt, copiez le fichier d’exemple en conservant un éventuel fichier `.env` existant, puis limitez son accès.

```sh
cp -n .env.example .env
chmod 600 .env
```

Exécutez `openssl rand -hex 32` trois fois et reportez une valeur distincte dans `SECRET_KEY`, `AI_SERVICE_TOKEN` et `POSTGRES_PASSWORD`. La configuration Compose exige ces trois valeurs. Gardez `.env` privé. Le mot de passe hexadécimal s’insère directement dans l’URL PostgreSQL. Conservez les noms de compte et de base proposés, ou choisissez des noms composés de lettres ASCII, de chiffres et de `_`.

```sh
docker compose config --quiet
docker compose up --build --wait
docker compose ps
curl --fail http://127.0.0.1:5050/health
```

Ouvrez `http://127.0.0.1:5050`, créez un compte et essayez une génération dans le studio. Le contrôle `/health` du site interroge PostgreSQL. Le contrôle du service IA vérifie son démarrage. Le mode local génère à partir des extraits retrouvés et fonctionne sans clé ni appel à un fournisseur.

Pour utiliser un modèle distant, renseignez `AI_MODE=llm`, `LLM_MODEL` et `LLM_API_KEY` dans `.env`. `LLM_BASE_URL` désigne la racine d’une API compatible OpenAI. Le service IA transmet au fournisseur la demande et les extraits utilisés comme contexte. Choisissez les documents en fonction des règles de traitement des données du fournisseur et de votre organisation. `LLM_TIMEOUT=45` fixe le délai fournisseur par défaut, en secondes. Appliquez les changements avec `docker compose up --wait`.

Arrêtez la pile avec `docker compose down`. Le volume PostgreSQL conserve les données entre les démarrages. `docker compose down --volumes` efface le volume de la pile.

## Publier sur une VM avec HTTPS

1. Préparez une VM Linux avec Docker Engine, Compose v2 et Caddy installé comme service système. Déployez une révision identifiée du dépôt sur la VM et appliquez les étapes de configuration locale avec des secrets propres à cet environnement.
2. Faites pointer le DNS du domaine vers la VM et ouvrez les ports 80 et 443 dans son pare-feu et celui du fournisseur. Gardez SSH limité aux administrateurs et le port 5050 sur l’interface locale. [Documentation HTTPS de Caddy](https://caddyserver.com/docs/automatic-https)
3. Renseignez `COOKIE_SECURE=true` dans `.env`, puis lancez `docker compose up --build --wait`. Le navigateur enverra le cookie de session à travers HTTPS.
4. Remplacez `adaptlearn.example.org` par le domaine de la VM dans le fichier `Caddyfile` du service. Validez puis rechargez Caddy. [Guide du proxy inverse Caddy](https://caddyserver.com/docs/quick-starts/reverse-proxy)

   ```caddyfile
   adaptlearn.example.org {
       reverse_proxy 127.0.0.1:5050
   }
   ```

   ```sh
   sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
   sudo systemctl reload caddy
   curl --fail https://adaptlearn.example.org/health
   ```

5. Depuis l’URL HTTPS, vérifiez la création d’un compte, la connexion, le studio et la persistance des données après un redémarrage de la pile.

## Sauvegarder et mettre à jour

Exportez régulièrement la base vers un fichier de sauvegarde hors du volume. Conservez une copie chiffrée hors VM. Cette archive contient les données des comptes, les documents et les productions.

```sh
umask 077
mkdir -p "$HOME/adaptlearn-backups"
docker compose exec -T db sh -c 'pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$HOME/adaptlearn-backups/adaptlearn-$(date +%Y%m%d-%H%M%S).dump"
```

Utilisez un nom de fichier unique pour chaque export. Pour répéter une restauration, utilisez une pile isolée et une base neuve `adaptlearn_restore` dans son service PostgreSQL, puis contrôlez le résultat avant une reprise réelle.

```sh
docker compose exec -T db sh -c 'createdb -U "$POSTGRES_USER" adaptlearn_restore'
docker compose exec -T db sh -c 'pg_restore --exit-on-error -U "$POSTGRES_USER" -d adaptlearn_restore' < /chemin/vers/la-sauvegarde.dump
```

Avant une mise à jour, sauvegardez la base et notez la révision active. Déployez la nouvelle révision avec `docker compose up --build --wait` et vérifiez `/health` ainsi que le parcours de connexion. En cas d’échec, réutilisez une révision compatible avec le schéma de la base, ou restaurez la sauvegarde dans une nouvelle base. Le changement d’un mot de passe dans `.env` exige aussi la mise à jour du rôle PostgreSQL dans un volume déjà initialisé. [Image officielle PostgreSQL](https://hub.docker.com/_/postgres)

## Limites du prototype

Une installation Compose repose sur une seule VM. Le compte PostgreSQL utilisé par le site possède les droits du rôle d’initialisation de l’image officielle sur cette instance dédiée. Pour une exploitation durable, prévoyez un rôle applicatif moins privilégié, des sauvegardes testées et une supervision. Le guide décrit une procédure reproductible pour une VM disposant d’un domaine. Aucune instance cloud n’a été provisionnée dans le cadre du projet.
