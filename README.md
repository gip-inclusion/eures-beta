# EURES beta app

Projet dédié au déploiement de `eures-beta` sur Scalingo.

## Contenu

- serveur Flask pour les routes `/forms/eures-beta/*`
- API `/api/forms/eures-beta/record`
- API `/api/forms/eures-beta/public-stats`
- interface admin `/admin/eures-beta/`
- interface suivi projet `/admin/eures-beta/suivi`

## Variables d'environnement

Copier `.env.example` vers `.env` puis renseigner :

- `GRIST_API_KEY`
- `GRIST_DOC_EURES_BETA`
- `GRIST_TABLE_EURES_BETA_CANDIDATE`
- `GRIST_TABLE_EURES_BETA_EMPLOYER`
- `GRIST_TABLE_EURES_BETA_STATS`
- `GRIST_TABLE_EURES_BETA_TRACKING` (optionnel, défaut `Suivi_Projet`)
- `ADMIN_USERNAME_EURES_BETA`
- `ADMIN_PASSWORD_EURES_BETA`
- `ADMIN_AUTH_MODE_EURES_BETA` (`basic` ou `magic_link`)
- `ADMIN_ALLOWED_EMAILS_EURES_BETA` (emails autorisés, séparés par des virgules)
- `ADMIN_MAGIC_LINK_TTL_SECONDS_EURES_BETA`
- `ADMIN_MAGIC_LINK_RATE_LIMIT_SECONDS_EURES_BETA`
- `BREVO_API_KEY`
- `BREVO_FROM_EMAIL`
- `BREVO_FROM_NAME`
- `OPENAI_API_KEY` (optionnel, pour la traduction automatique des textes libres)
- `OPENAI_TEXT_MODEL` (optionnel, défaut `gpt-4.1-mini`)

## Lancer en local

```bash
uv run flask --app app.py run -p 5005
```

## Tests

```bash
uv run python -m unittest tests.test_public_stats tests.test_eures_beta_only_mode tests.test_tracking_module
```
