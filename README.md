# EURES beta app

Projet dédié au déploiement de `eures-beta` sur Scalingo.

## Contenu

- serveur Flask pour les routes `/forms/eures-beta/*`
- API `/api/forms/eures-beta/record`
- API `/api/forms/eures-beta/public-stats`
- interface admin `/admin/eures-beta/`

## Variables d'environnement

Copier `.env.example` vers `.env` puis renseigner :

- `GRIST_API_KEY`
- `GRIST_DOC_EURES_BETA`
- `GRIST_TABLE_EURES_BETA_CANDIDATE`
- `GRIST_TABLE_EURES_BETA_EMPLOYER`
- `GRIST_TABLE_EURES_BETA_STATS`
- `ADMIN_USERNAME_EURES_BETA`
- `ADMIN_PASSWORD_EURES_BETA`

## Lancer en local

```bash
uv run flask --app app.py run -p 5005
```

## Tests

```bash
uv run python -m unittest tests.test_public_stats tests.test_eures_beta_only_mode
```
