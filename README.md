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

## Suivi projet EURES

Le module de suivi projet est intégré nativement dans l'admin EURES via `/admin/eures-beta/suivi`.

### Modèle de carte

Chaque carte possède une référence visible de type `EURES-123` et s'appuie sur les champs métier suivants :

- `titre`
- `responsable`
- `source`
- `description`
- `observe`
- `attendu`
- `contexte`
- `indicateurs_suivi`
- `priorite`
- `type`
- `statut`
- `taille_dev`
- `images`
- `liens`
- `commentaires`
- `historique`
- informations GitHub / PR / déploiement

### Règles métier

- `Fait` reste une colonne active du kanban.
- `Archiver` sort la carte du flux actif sans la supprimer.
- `Supprimer` efface définitivement la carte.
- il n'existe pas de champ séparé `Bloquant` ; utiliser la priorité `critique`.

### CRUD et persistance

Le module réutilise les helpers CRUD Grist du projet :

- lecture par table et par id
- `update_table_record_by_id`
- contrat de suppression identique aux autres suppressions Grist du projet

### Texte libre

La création rapide crée directement une carte. Le titre est condensé avant enregistrement et les validations métier sont les mêmes que pour une création manuelle.

### Images jointes

- compression côté navigateur avant envoi
- volume et nombre limités
- aperçu, ouverture et retrait dans le drawer
- historisation de l'ajout et du retrait d'image

### GitHub, PR et déploiement

- webhook GitHub signé HMAC : `/api/forms/eures-beta/tracking/github/webhook`
- webhook de déploiement : `/api/forms/eures-beta/tracking/deployments/webhook`
- compatibilité actuelle :
  - signature HMAC `X-Tracking-Signature-256` recommandée
  - ancien secret d'en-tête `X-Tracking-Webhook-Secret` encore accepté pour migration douce

La carte conserve :

- branche GitHub
- URL de PR
- état de PR
- dernière activité GitHub
- URL de déploiement
- environnement
- date de déploiement

### i18n et fallbacks

L'interface est disponible en FR / EN / DE. Les messages visibles côté backend utilisés par le module de suivi sont également localisés. Si la traduction automatique n'est pas configurée, un fallback manuel explicite est affiché.

### Idempotence et hypothèses

L'anti double-enregistrement repose aujourd'hui sur :

- un garde-fou frontend
- un verrou mémoire côté backend

Avec le `Procfile` actuel (`gunicorn app:app` sans nombre de workers forcé), l'hypothèse de base est un déploiement simple compatible avec ce verrou process-local. Si `WEB_CONCURRENCY` ou un mode multi-worker est activé plus tard, il faudra durcir l'idempotence au niveau de la persistance.
