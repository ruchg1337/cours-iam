# Kit du labo : Keycloak + une application cliente OIDC

Ce dossier contient tout ce qu'il faut pour le labo du cours IAM. Le guide pas à pas (les parties 1 à 4
et les questions) se trouve sur le site du cours, section **Labo**. Ses sources sont dans le dossier
parent (`labo/*.qmd`).

## Démarrer

```bash
cp .env.example .env
docker compose up --build
```

- Console d'administration Keycloak : http://localhost:8080 (admin / admin)
- Application : http://localhost:8000

Pour tout remettre à zéro : `docker compose down -v`.

## Contenu

```
docker-compose.yml          Keycloak 26.7 + PostgreSQL + l'application
.env.example                variables à copier dans .env (identifiant et secret du client OIDC)
app/                        l'application cliente (Python Flask + Authlib), environ 150 lignes commentées
solution/                   le corrigé : realm Keycloak prêt à importer, réponses et notes pour l'enseignant
```

## Charger le realm déjà configuré

```bash
docker compose -f docker-compose.yml -f solution/docker-compose.solution.yml up --build
```

Puis, dans `.env` : `OIDC_CLIENT_SECRET=secret-du-labo-a-changer`. La partie GitHub n'est pas incluse,
elle dépend de votre compte.
