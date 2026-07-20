"""
Grist Custom Forms - Flask API Server

Proxies requests to Grist API with authentication.
Supports multiple forms via form_id in URL path.

Environment variables:
  GRIST_API_KEY - Default API key (or GRIST_API_KEY_<FORM_ID> per form)
  GRIST_DOC_<FORM_ID> - Document ID for each form
  GRIST_TABLE_<FORM_ID> - Table ID for each form (defaults to "Reponses")
  GRIST_BASE_URL - Grist instance URL (defaults to grist.numerique.gouv.fr)
"""

import os
import base64
import re
import json
import time
import csv
import secrets
import unicodedata
from html import escape
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from io import BytesIO, StringIO
from functools import wraps
from pathlib import Path
from urllib.parse import urljoin, urlparse
from itsdangerous import BadSignature, SignatureExpired, URLSafeSerializer, URLSafeTimedSerializer
from dotenv import load_dotenv
import requests
from flask import Flask, request, jsonify, redirect, send_file, send_from_directory, Response, session, url_for
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from eures_beta_email_templates import (
    get_candidate_invitation_template,
    get_candidate_target_job_label,
)

load_dotenv()

BASE_DIR = Path(__file__).parent
FORMS_DIR = BASE_DIR / 'forms'
ASSETS_DIR = BASE_DIR / 'assets'
DOCS_DIR = BASE_DIR / 'docs'

app = Flask(__name__)
app.config.update(
    SECRET_KEY=(
        os.environ.get('SESSION_SECRET')
        or os.environ.get('FLASK_SECRET_KEY')
        or os.environ.get('EURES_EMAIL_ACTION_SECRET')
        or os.environ.get('ADMIN_PASSWORD')
        or secrets.token_urlsafe(32)
    ),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=str(os.environ.get('SESSION_COOKIE_SECURE', 'true')).strip().lower() not in {'0', 'false', 'no', 'off'},
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_REFRESH_EACH_REQUEST=False,
)

_ADMIN_MAGIC_LINK_REQUESTS: dict[tuple[str, str], float] = {}
_ADMIN_MAGIC_LINK_USED: dict[str, float] = {}
_EURES_PUBLIC_WRITE_ATTEMPTS: dict[tuple[str, str], list[float]] = {}

GRIST_BASE_URL = os.environ.get('GRIST_BASE_URL', 'https://grist.numerique.gouv.fr').rstrip('/')
APP_MODE = os.environ.get('APP_MODE', 'eures-beta').strip().lower() or 'eures-beta'
_TABLE_COLUMNS_CACHE: dict[tuple[str, str], dict[str, object]] = {}
_TABLE_COLUMNS_CACHE_TTL_SECONDS = 60
EURES_CANDIDATS_TABLE = 'Candidats'
EURES_BESOINS_TABLE = 'Besoins_Employeurs'
EURES_MATCHINGS_TABLE = 'Matchings'
EURES_INVITATIONS_TABLE_DEFAULT = 'Invitations'
EURES_STATS_TABLE_DEFAULT = 'Pilotage_EURES_Mensuel'
EURES_PUBLIC_PROXY_BASE_URL = os.environ.get('EURES_PUBLIC_PROXY_BASE_URL', 'https://eures-beta.osc-fr1.scalingo.io').rstrip('/')
EURES_MATCHING_FIELDS = {
    'besoin_id',
    'candidat_id',
    'score',
    'score_metier',
    'score_competences',
    'score_langues',
    'score_mobilite',
    'score_disponibilite',
    'score_salaire',
    'statut',
    'raisons',
    'points_faibles',
    'date_calcul',
}
EURES_MATCHING_ADMIN_FIELDS = {
    'admin_status',
    'admin_decision_at',
    'admin_decision_by',
    'admin_decision_note',
    'employer_email_comment',
    'candidate_email_comment',
    'manual_matching_source',
    'manual_matching_created_at',
    'manual_matching_created_by',
    'manual_matching_note',
    'workflow_status',
    'workflow_status_updated_at',
    'workflow_status_updated_by',
    'sent_to_employer_at',
    'sent_to_employer_by',
    'employer_response',
    'employer_response_at',
    'employer_response_source',
    'mise_en_relation_at',
    'mise_en_relation_by',
    'embauche_confirmee_at',
    'embauche_confirmee_by',
}
EURES_NO_MATCH_NOTIFICATION_FIELDS = {
    'no_match_notification_status',
    'no_match_notification_reason',
    'no_match_notification_created_at',
    'no_match_notification_created_by',
    'no_match_notification_sent_at',
    'no_match_notification_sent_by',
    'no_match_notification_dismissed_at',
    'no_match_notification_dismissed_by',
    'no_match_notification_note',
}
EURES_NO_MATCH_ALLOWED_STATUSES = {'pending', 'sent', 'dismissed'}
EURES_NEW_JOB_REQUEST_FIELDS = {
    'new_job_request_status',
    'new_job_request_created_at',
    'new_job_request_created_by',
    'new_job_request_processed_at',
    'new_job_request_processed_by',
    'new_job_request_note',
}
EURES_NEW_JOB_REQUEST_ALLOWED_STATUSES = {'pending', 'processed', 'dismissed'}
EURES_NEW_EMPLOYER_ALERT_FIELDS = {
    'new_employer_alert_status',
    'new_employer_alert_created_at',
    'new_employer_alert_created_by',
    'new_employer_alert_processed_at',
    'new_employer_alert_processed_by',
    'new_employer_alert_note',
    'source_invitation_record_id',
    'source_invitation_email',
    'source_invitation_company',
    'source_invitation_scope',
    'sponsor_email',
    'sponsor_company_name',
}
EURES_NEW_EMPLOYER_ALERT_ALLOWED_STATUSES = {'pending', 'reviewed', 'dismissed'}
EURES_RESPONSE_ADMIN_FIELDS = {
    'response_status',
    'response_received_at',
    'response_status_updated_at',
    'response_status_updated_by',
    'response_disabled_at',
    'response_disabled_by',
    'response_disabled_reason',
    'cv_file_name',
    'cv_file_mime',
    'cv_file_size',
    'cv_file_base64',
    'cv_uploaded_at',
}
EURES_RESPONSE_ALLOWED_STATUSES = {'active', 'disabled'}
EURES_CV_MAX_BYTES = 3 * 1024 * 1024
EURES_CV_ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.oasis.opendocument.text',
}
EURES_INVITATION_FIELDS = {
    'role',
    'email',
    'first_name',
    'last_name',
    'company_name',
    'language',
    'source',
    'external_ref',
    'invite_token',
    'invite_link',
    'invitation_status',
    'invitation_status_updated_at',
    'invitation_status_updated_by',
    'import_batch_id',
    'imported_at',
    'imported_by',
    'sent_at',
    'sent_by',
    'brevo_message_id',
    'reminder_count',
    'last_reminder_at',
    'last_reminder_by',
    'last_reminder_message_id',
    'sponsor_invitation_record_id',
    'sponsor_email',
    'sponsor_company_name',
    'invited_by_type',
    'invite_scope',
    'first_submission_at',
    'last_submission_at',
    'submission_count',
    'answered_at',
    'linked_form_role',
    'linked_record_id',
    'linked_record_key',
    'matching_status',
    'matching_status_updated_at',
    'matching_status_updated_by',
    'duplicate_followup_status',
    'duplicate_followup_type',
    'duplicate_followup_target_record_id',
    'duplicate_followup_target_status',
    'duplicate_followup_message',
    'duplicate_followup_created_at',
    'duplicate_followup_created_by',
    'duplicate_followup_processed_at',
    'duplicate_followup_processed_by',
    'duplicate_followup_note',
    'target_job_keys',
    'notes',
}
EURES_INVITATION_ALLOWED_ROLES = {'candidate', 'employer'}
EURES_INVITATION_ALLOWED_STATUSES = {
    'invitation_a_envoyer',
    'invitation_envoyee',
    'questionnaire_recu',
    'rapprochement_a_confirmer',
    'rapprochee',
    'matching_calcule',
    'traitee',
    'erreur_envoi',
    'desactivee',
}
EURES_INVITATION_SENDABLE_STATUSES = {'invitation_a_envoyer', 'erreur_envoi'}
EURES_DUPLICATE_FOLLOWUP_ALLOWED_STATUSES = {'pending', 'reminded', 'ignored'}
EURES_SECTOR_CANONICAL_MAP = {
    'vente': 'vente',
    'commerce': 'vente',
    'sales': 'vente',
    'retail': 'vente',
    'nettoyage': 'nettoyage',
    'entretien': 'nettoyage',
    'cleaning': 'nettoyage',
    'maintenance': 'nettoyage',
    'hôtellerie': 'hotellerie',
    'hotellerie': 'hotellerie',
    'restauration': 'hotellerie',
    'hospitality': 'hotellerie',
    'catering': 'hotellerie',
    'agriculture': 'agriculture',
    'récolte': 'agriculture',
    'recolte': 'agriculture',
    'harvesting': 'agriculture',
    'industrie': 'industrie_production',
    'industry': 'industrie_production',
    'production': 'industrie_production',
    'opérateur de production': 'industrie_production',
    'operateur de production': 'industrie_production',
    'production operator': 'industrie_production',
    'polyvalent': 'polyvalent',
    'multi': 'polyvalent',
    'accessible rapidement': 'polyvalent',
}
EURES_CANDIDAT_SECTOR_SALARY_FIELDS = {
    'vente': ('tally_q20_salary_type', 'tally_q20_salary_min'),
    'nettoyage': ('tally_q22_salary_type', 'tally_q22_salary_min'),
    'hotellerie': ('tally_q25_salary_type', 'tally_q25_salary_min'),
    'agriculture': ('tally_q27_salary_type', 'tally_q27_salary_min'),
    'polyvalent': ('tally_q29_salary_type', 'tally_q29_salary_min'),
    'industrie_production': ('tally_q38_salary_type', 'tally_q38_salary_min'),
}
EURES_CANDIDAT_SECTOR_JOB_TITLE_FIELDS = {
    'vente': 'tally_q20_job_title',
    'nettoyage': 'tally_q22_job_title',
    'hotellerie': 'tally_q25_job_title',
    'agriculture': 'tally_q27_job_title',
    'polyvalent': 'tally_q29_job_title',
    'industrie_production': 'tally_q38_job_title',
}
EURES_EMPLOYEUR_SECTOR_SALARY_FIELDS = {
    'vente': ('tally_q10_salary_type', 'tally_q10_salary_min', 'tally_q10_salary_max'),
    'nettoyage': ('tally_q11_salary_type', 'tally_q11_salary_min', 'tally_q11_salary_max'),
    'hotellerie': ('tally_q12_salary_type', 'tally_q12_salary_min', 'tally_q12_salary_max'),
    'agriculture': ('tally_q13_salary_type', 'tally_q13_salary_min', 'tally_q13_salary_max'),
    'polyvalent': ('tally_q14_salary_type', 'tally_q14_salary_min', 'tally_q14_salary_max'),
    'industrie_production': ('tally_q40_salary_type', 'tally_q40_salary_min', 'tally_q40_salary_max'),
}
EURES_EMPLOYEUR_SECTOR_JOB_TITLE_FIELDS = {
    'vente': 'tally_q10_job_title',
    'nettoyage': 'tally_q11_job_title',
    'hotellerie': 'tally_q12_job_title',
    'agriculture': 'tally_q13_job_title',
    'polyvalent': 'tally_q14_job_title',
    'industrie_production': 'tally_q40_job_title',
}
EURES_PUBLIC_SECTOR_LABELS = {
    'vente': 'Vente et commerce',
    'nettoyage': 'Nettoyage et entretien',
    'hotellerie': 'Hôtellerie et restauration',
    'agriculture': 'Agriculture et récolte',
    'polyvalent': 'Missions polyvalentes',
    'industrie_production': 'Production industrielle (assemblage, fabrication, conditionnement, contrôle qualité)',
}
EURES_INVITATION_CANDIDATE_TARGET_OPTIONS = [
    'vente',
    'nettoyage',
    'hotellerie',
    'agriculture',
    'polyvalent',
    'industrie_production',
]
EURES_WORK_CONDITION_CANONICAL_MAP = {
    'travail tot le matin ou en horaire decales': 'matin_decale',
    'travail tôt le matin ou en horaire décalés': 'matin_decale',
    'early morning work or staggered hours': 'matin_decale',
    'arbeit fruh am morgen oder zu versetzten zeiten': 'matin_decale',
    'arbeit früh am morgen oder zu versetzten zeiten': 'matin_decale',
    'travail en soiree ou la nuit': 'soir_nuit',
    'travail en soirée ou la nuit': 'soir_nuit',
    'evening or night work': 'soir_nuit',
    'arbeit am abend oder in der nacht': 'soir_nuit',
    'travail le week-end ou les jours feries': 'weekend_feries',
    'travail le week-end ou les jours fériés': 'weekend_feries',
    'weekend or public holiday work': 'weekend_feries',
    'arbeit am wochenende oder an feiertagen': 'weekend_feries',
    'horaires variables': 'horaires_variables',
    'variable hours': 'horaires_variables',
    'variable arbeitszeiten': 'horaires_variables',
    'travail poste': 'travail_poste',
    'travail posté': 'travail_poste',
    'shift work': 'travail_poste',
    'schichtarbeit': 'travail_poste',
    'travail physique': 'travail_physique',
    'physical work': 'travail_physique',
    'korperliche arbeit': 'travail_physique',
    'körperliche arbeit': 'travail_physique',
    'travail debout prolonge': 'debout_prolonge',
    'travail debout prolongé': 'debout_prolonge',
    'prolonged standing work': 'debout_prolonge',
    'langeres stehen': 'debout_prolonge',
    'längeres stehen': 'debout_prolonge',
    'travail en exterieur': 'exterieur',
    'travail en extérieur': 'exterieur',
    'outdoor work': 'exterieur',
    'arbeit im freien': 'exterieur',
    'deplacements frequents': 'deplacements_frequents',
    'déplacements fréquents': 'deplacements_frequents',
    'frequent travel': 'deplacements_frequents',
    'haufige fahrten': 'deplacements_frequents',
    'häufige fahrten': 'deplacements_frequents',
    'travail en equipe': 'travail_equipe',
    'travail en équipe': 'travail_equipe',
    'teamwork': 'travail_equipe',
    'teamarbeit': 'travail_equipe',
    'aucune condition particuliere': 'aucune_condition',
    'aucune condition particulière': 'aucune_condition',
    'no particular condition': 'aucune_condition',
    'keine besonderen bedingungen': 'aucune_condition',
    'je ne sais pas encore': 'inconnu',
    'i do not know yet': 'inconnu',
    'ich weiss es noch nicht': 'inconnu',
    'ich weiß es noch nicht': 'inconnu',
}
EURES_WORK_CONDITION_PARTIAL_COMPATIBILITY = {
    'travail_poste': {'matin_decale', 'soir_nuit', 'horaires_variables'},
    'matin_decale': {'travail_poste', 'horaires_variables'},
    'soir_nuit': {'travail_poste', 'horaires_variables'},
    'horaires_variables': {'travail_poste', 'matin_decale', 'soir_nuit'},
}
EURES_PERMIT_CANONICAL_MAP = {
    'permis b': 'permis_b',
    'category b driving licence': 'permis_b',
    'fuhrerschein b': 'permis_b',
    'führerschein b': 'permis_b',
    'permis c': 'permis_c',
    'category c driving licence': 'permis_c',
    'fuhrerschein c': 'permis_c',
    'führerschein c': 'permis_c',
    'permis ce': 'permis_ce',
    'category ce driving licence': 'permis_ce',
    'fuhrerschein ce': 'permis_ce',
    'führerschein ce': 'permis_ce',
    'permis d': 'permis_d',
    'category d driving licence': 'permis_d',
    'fuhrerschein d': 'permis_d',
    'führerschein d': 'permis_d',
    'permis de': 'permis_de',
    'category de driving licence': 'permis_de',
    'fuhrerschein de': 'permis_de',
    'führerschein de': 'permis_de',
    'caces': 'caces',
    'autre': 'autre',
    'other': 'autre',
    'andere': 'autre',
}
WIZARD_STATE_KEY = '__wizard_v3_state'
JSON_EXPORT_COLUMNS = {
    'metiers_json',
    'prestations_orp_json',
    'prestations_indirectes_json',
    'prestations_json',
    'catalogue_formations_json',
    'emploi_indicateurs_json',
    'prestations_details_json',
    'finess_json',
}
FIELD_LABELS = {
    'uuid': 'Identifiant de reprise',
    'es_nom': "Nom de l'établissement",
    'es_departement': 'Département',
    'finess_main': 'FINESS principal',
    'validateur_nom': 'Nom du validateur',
    'validateur_prenom': 'Prénom du validateur',
    'validateur_email': 'Email du validateur',
    'saisie_terminee': 'Saisie terminée',
    'check_esrp': 'Dispositif ESRP',
    'check_espo': 'Dispositif ESPO',
    'check_ueros': 'Dispositif UEROS',
    'check_deac': 'Dispositif DEAc',
    'etp_esrp': 'ETP ESRP',
    'etp_espo': 'ETP ESPO',
    'etp_ueros': 'ETP UEROS',
    'etp_deac': 'ETP DEAc',
    'q32_implantation': "Contexte social - Zone d'implantation",
    'q33_transports': 'Contexte social - Transports',
    'q33_pmr': 'Contexte social - Accessibilité PMR',
    'q33_alternatif': 'Contexte social - Transport alternatif',
    'q34_prefecture': 'Contexte social - Préfecture',
    'q35_hebergement': 'Contexte social - Hébergement',
    'q35_places': 'Contexte social - Nombre de places',
    'q35_weekend': 'Contexte social - Hébergement le week-end',
    'q36_restaurant': 'Contexte social - Restauration',
    'q37_cuisine': 'Contexte social - Cuisine',
    'q38_dui': 'Contexte social - DUI',
    'q40_remuneration': 'Contexte social - Rémunération',
    'q40_operateur': 'Contexte social - Opérateur rémunération',
    'autre_dispositif_eval': "Autre dispositif d'évaluation",
    'autre_dispositif_eval_avec_orp_cdaph': "Autre dispositif d'évaluation avec ORP CDAPH",
    'autre_dispositif_eval_sans_orp_cdaph': "Autre dispositif d'évaluation sans ORP CDAPH",
}
COH_LABELS = {
    'genre': ('Genre', ['Hommes', 'Femmes', 'Autre']),
    'age': ('Âge', ['16-17 ans', '18-19 ans', '20-24 ans', '25-29 ans', '30-34 ans', '35-39 ans', '40-44 ans', '45-49 ans', '50-54 ans', '55-59 ans', '60 ans et +', 'Je ne sais pas']),
    'niveau_entree': ("Niveau de formation à l'entrée", ['Niveau 2 (CEP, sans formation)', 'Niveau 3 (CAP, BEP)', 'Niveau 4 (Bac, Bac pro)', 'Niveau 5 (Bac +2, BTS)', 'Niveau 6 (Bac +3, Bac +4)', 'Niveau 7 (Bac +5)', 'Je ne sais pas']),
    'situation_entree': ("Situation à l'entrée", ['En emploi du secteur privé', 'Dont entreprises adaptées', 'Dont alternance (secteur privé)', 'En emploi secteur public', 'FPT', 'Dont contractuels (FPT)', 'Dont alternance (FPT)', 'FPH', 'Dont contractuels (FPH)', 'Dont alternance (FPH)', 'FPE', 'Dont contractuels (FPE)', 'Dont alternance (FPE)', 'En activité non salariée', "Travailleurs d'ESAT", "Sans emploi depuis moins d'1 an", 'Sans emploi depuis 1 à 2 ans', 'Sans emploi depuis 2 ans ou plus', "N'avaient jamais travaillé", 'En formation', 'Je ne sais pas']),
    'ressources_entree': ("Ressources à l'entrée", ['Salaire', 'AAH', 'Allocations chômage', 'RSA', 'Indemnités Journalières', 'Rentes AT/MP / Pension invalidité', 'Autres', 'Aucune', 'Je ne sais pas']),
    'pathologies': ('Pathologies', ['1 pathologie', '2 pathologies', '3 pathologies et plus', 'Non connu']),
    'origine_handicap': ('Origine du handicap', ['Congénitale', 'Maladie', 'Accident de vie privée', 'Accident travail / Pro', 'Maladie professionnelle', 'Autres', 'Non connue']),
    'lesion_origine': ('Origine de la lésion cérébrale (UEROS)', ['Traumatisme crânien', 'AVC', 'Tumeur cérébrale', 'Epilepsie', 'Autres pathologies neuro', 'Non connue']),
}
HANDICAP_TYPES = [
    'Déficiences intellectuelles',
    'Autisme et autres TED',
    'Troubles psychiques',
    'Troubles langage/apprentissages',
    'Déficiences auditives',
    'Déficiences visuelles',
    'Déficiences motrices',
    'Déficiences métaboliques/nutritionnelles',
    'Cérébro-lésions',
    'Polyhandicap',
    'TCC (comportement/com.)',
    'Diagnostics en cours',
    'Autres types de déficiences',
    'Je ne sais pas',
]
EXPORT_KEY_LABELS = {
    'done': 'Statut complété',
    'fileActive': 'File active',
    'preaccueilSansSuite': 'Pré-accueils sans suite',
    'sortiesAvantTerme': 'Sorties définitives avant le terme de la prestation',
    'sortiesTerme': 'Sorties au terme de la prestation',
    'sorties': 'Sorties définitives en 2025',
    'journees': 'Journées réalisées',
    'journeesTheoriques': 'Journées théoriques',
    'enabled': 'Activé',
    'beneficiaires': 'Nombre de personnes bénéficiaires',
    'discontinue_personnes': 'Nombre de personnes accompagnées en discontinue',
    'presentiel_total': 'Présentiel - total',
    'presentiel_complet': 'Présentiel - temps complet',
    'presentiel_partiel': 'Présentiel - temps partiel',
    'hybride_total': 'Hybride - total',
    'hybride_complet': 'Hybride - temps complet',
    'hybride_partiel': 'Hybride - temps partiel',
    'distanciel_total': 'Distanciel - total',
    'distanciel_complet': 'Distanciel - temps complet',
    'distanciel_partiel': 'Distanciel - temps partiel',
    'hors_murs_personnes': 'Hors les murs - personnes accompagnées',
    'hors_murs_journees': 'Hors les murs - journées',
    'hebergees_personnes': 'Hébergement - personnes hébergées',
    'hebergees_journees': 'Hébergement - journées',
    'hebergees_nuitees': 'Hébergement - nuitées',
    'activites_intermediaires_site': 'Activité intermédiaire - sur site',
    'activites_intermediaires_ambulatoire': 'Activité intermédiaire - en ambulatoire',
    'activites_sortie_parcours_site': 'Suite de parcours - sur site',
    'activites_sortie_parcours_ambulatoire': 'Suite de parcours - en ambulatoire',
    'droit_commun': 'Droit commun',
    'sante_social': 'Santé / Social',
    'readaptation_professionnelle': 'Réadaptation professionnelle',
    'readaptation_ueros': 'Réadaptation professionnelle - UEROS',
    'readaptation_espo': 'Réadaptation professionnelle - ESPO',
    'readaptation_esrp': 'Réadaptation professionnelle - ESRP',
    'readaptation_dfa': 'Réadaptation professionnelle - DFA',
    'inconnu': 'Situations inconnues',
    'autre': 'Autre préconisation',
    'autres': 'Autres',
    'autres_precision': 'Précision',
    'je_ne_sais_pas': 'Je ne sais pas',
    'dept': 'Département',
    'count': 'Effectif',
    'principal': 'Principal',
    'associe': 'Associé',
}

# Public mount for the daily capture tool.
try:
    from tools.fagerh_suivi_local.app import app as fagerh_suivi_app
except Exception:
    fagerh_suivi_app = None


def is_eures_beta_only_mode() -> bool:
    """Return True when this deployment must only expose EURES beta."""
    return APP_MODE in {'eures-beta', 'eures_beta', 'eures-only', 'eures_only'}


def is_form_enabled(form_id: str) -> bool:
    """Restrict exposed forms for single-purpose deployments."""
    if is_eures_beta_only_mode():
        return form_id == 'eures-beta'
    return True


def _resolve_form_path(form_id: str, raw_path: str) -> str | None:
    """
    Resolve friendly form URLs.
    Supports:
    - explicit file path (existing)
    - "<name>" -> "<name>.html"
    - "<name>/" -> "<name>/index.html" then "<name>.html"
    """
    safe_form_dir = FORMS_DIR / form_id
    candidate = (raw_path or '').strip().lstrip('/')
    if not candidate:
        return None

    candidates: list[str] = []
    candidates.append(candidate)
    if candidate.endswith('/'):
        base = candidate.rstrip('/')
        candidates.append(f"{base}/index.html")
        candidates.append(f"{base}.html")
    else:
        if '.' not in Path(candidate).name:
            candidates.append(f"{candidate}.html")
            candidates.append(f"{candidate}/index.html")

    for c in candidates:
        if (safe_form_dir / c).is_file():
            return c
    return None


def _admin_env_name(base: str, form_id: str) -> list[str]:
    normalized = str(form_id or '').strip().replace('-', '_').upper()
    names = []
    if normalized:
        names.append(f'{base}_{normalized}')
    names.append(base)
    return names


def _admin_env_value(base: str, form_id: str, default: str = '') -> str:
    for name in _admin_env_name(base, form_id):
        value = str(os.environ.get(name) or '').strip()
        if value:
            return value
    return default


def get_admin_auth_mode(form_id: str) -> str:
    mode = _admin_env_value('ADMIN_AUTH_MODE', form_id, default='basic').strip().lower().replace('-', '_')
    if mode not in {'basic', 'magic_link', 'hybrid'}:
        return 'basic'
    return mode


def get_admin_allowed_emails(form_id: str) -> set[str]:
    raw = _admin_env_value('ADMIN_ALLOWED_EMAILS', form_id)
    return {
        normalize_email(part)
        for part in raw.split(',')
        if normalize_email(part)
    }


def get_admin_magic_link_ttl_seconds(form_id: str) -> int:
    raw = _admin_env_value('ADMIN_MAGIC_LINK_TTL_SECONDS', form_id, default='900')
    try:
        ttl = int(raw)
    except Exception:
        ttl = 900
    return max(60, min(ttl, 86400))


def get_admin_magic_link_rate_limit_seconds(form_id: str) -> int:
    raw = _admin_env_value('ADMIN_MAGIC_LINK_RATE_LIMIT_SECONDS', form_id, default='60')
    try:
        seconds = int(raw)
    except Exception:
        seconds = 60
    return max(0, min(seconds, 3600))


def get_admin_session_ttl_seconds(form_id: str) -> int:
    raw = _admin_env_value('ADMIN_SESSION_TTL_SECONDS', form_id, default='3600')
    try:
        ttl = int(raw)
    except Exception:
        ttl = 3600
    return max(300, min(ttl, 86400))


def is_admin_session_persistent(form_id: str) -> bool:
    raw = _admin_env_value('ADMIN_SESSION_PERSISTENT', form_id, default='false').strip().lower()
    return raw in {'1', 'true', 'yes', 'on'}


def get_admin_magic_link_serializer(form_id: str) -> URLSafeTimedSerializer:
    secret = (
        os.environ.get('SESSION_SECRET', '').strip()
        or os.environ.get('FLASK_SECRET_KEY', '').strip()
        or os.environ.get('EURES_EMAIL_ACTION_SECRET', '').strip()
        or os.environ.get('BREVO_API_KEY', '').strip()
    )
    if not secret:
        raise RuntimeError('Missing admin magic link secret configuration.')
    return URLSafeTimedSerializer(secret_key=secret, salt=f'admin-magic-link:{form_id}')


def _get_admin_magic_link_serializer(form_id: str) -> URLSafeTimedSerializer:
    """Compatibility wrapper for existing tests and older call sites."""
    return get_admin_magic_link_serializer(form_id)


def _admin_session_key(form_id: str) -> str:
    return f'admin_session:{form_id}'


def _current_admin_session(form_id: str) -> dict | None:
    payload = session.get(_admin_session_key(form_id))
    if not isinstance(payload, dict):
        return None
    email = normalize_email(payload.get('email'))
    if not email or email not in get_admin_allowed_emails(form_id):
        return None
    authenticated_at_raw = str(payload.get('authenticated_at') or '')
    try:
        authenticated_at = datetime.fromisoformat(authenticated_at_raw.replace('Z', '+00:00'))
    except Exception:
        _clear_admin_session(form_id)
        return None
    session_age = datetime.now(timezone.utc) - authenticated_at.astimezone(timezone.utc)
    if session_age.total_seconds() > get_admin_session_ttl_seconds(form_id):
        _clear_admin_session(form_id)
        return None
    return {
        'email': email,
        'authenticated_at': authenticated_at_raw,
    }


def _set_admin_session(form_id: str, email: str):
    session.permanent = is_admin_session_persistent(form_id)
    session[_admin_session_key(form_id)] = {
        'email': normalize_email(email),
        'authenticated_at': _now_iso_utc(),
    }
    session.modified = True


def _clear_admin_session(form_id: str):
    session.pop(_admin_session_key(form_id), None)


def _consume_admin_magic_link_jti(jti: str, ttl_seconds: int) -> bool:
    now = time.time()
    expired_before = now - max(ttl_seconds, 60)
    for key, used_at in list(_ADMIN_MAGIC_LINK_USED.items()):
        if used_at < expired_before:
            _ADMIN_MAGIC_LINK_USED.pop(key, None)
    if jti in _ADMIN_MAGIC_LINK_USED:
        return False
    _ADMIN_MAGIC_LINK_USED[jti] = now
    return True


def get_admin_actor(form_id: str, fallback: str = 'admin') -> str:
    session_identity = _current_admin_session(form_id)
    if session_identity and session_identity.get('email'):
        return str(session_identity['email'])
    auth = request.authorization
    if auth and auth.username:
        return auth.username
    return fallback


def _admin_auth_error_response(form_id: str):
    login_url = url_for('admin_login', form_id=form_id)
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Authentication required',
            'login_url': login_url,
        }), 401
    return redirect(login_url)


def _require_admin_basic_auth(form_id: str):
    """HTTP Basic auth guard for admin endpoints."""
    username = _admin_env_value('ADMIN_USERNAME', form_id)
    password = _admin_env_value('ADMIN_PASSWORD', form_id)
    if not username or not password:
        return Response(
            'Admin access not configured. Set ADMIN_USERNAME and ADMIN_PASSWORD.',
            503,
            {'Content-Type': 'text/plain; charset=utf-8'},
        )

    auth = request.authorization
    if not auth or auth.username != username or auth.password != password:
        return Response(
            'Authentication required',
            401,
            {'WWW-Authenticate': 'Basic realm="Grist Admin"'},
        )
    return None


def _require_admin_magic_link_auth(form_id: str):
    allowed_emails = get_admin_allowed_emails(form_id)
    if not allowed_emails:
        return Response(
            'Admin access not configured. Set ADMIN_ALLOWED_EMAILS.',
            503,
            {'Content-Type': 'text/plain; charset=utf-8'},
        )
    if _current_admin_session(form_id):
        return None
    return _admin_auth_error_response(form_id)


def build_admin_magic_link_email(form_id: str, email: str, login_link: str) -> tuple[str, str, str, str]:
    title = f'Connexion admin {form_id}'
    subject = f'[{form_id}] Votre lien de connexion admin'
    text_body = (
        "Bonjour,\n\n"
        f"Voici votre lien de connexion pour l'espace d'administration {form_id}.\n\n"
        f"{login_link}\n\n"
        f"Ce lien expire dans {get_admin_magic_link_ttl_seconds(form_id) // 60} minutes.\n"
        "Si vous n'etes pas a l'origine de cette demande, ignorez cet email.\n\n"
        "Cordialement,\n"
        f"{get_eures_mail_signature_name()}\n"
        "EURES beta\n"
    )
    html_body = f"""
<!doctype html>
<html lang="fr">
  <body style="margin:0;padding:0;background:#f4efe6;font-family:Georgia,'Times New Roman',serif;color:#1f1f1f;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4efe6;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;background:#fffdf9;border:1px solid #e7dcc7;border-radius:18px;overflow:hidden;">
            <tr>
              <td style="padding:28px 32px;background:linear-gradient(135deg,#0f2742 0%,#004494 100%);color:#ffffff;">
                <div style="font-size:13px;letter-spacing:1.6px;text-transform:uppercase;opacity:0.82;">Administration securisee</div>
                <h1 style="margin:10px 0 0;font-size:30px;line-height:1.2;font-weight:700;">{escape(title)}</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 32px;">
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">Bonjour,</p>
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">
                  Voici votre lien de connexion pour l'espace d'administration <strong>{escape(form_id)}</strong>.
                </p>
                <p style="margin:0 0 24px;">
                  <a href="{escape(login_link)}" style="display:inline-block;padding:14px 18px;border-radius:12px;background:#004494;color:#ffffff;text-decoration:none;font-size:16px;font-weight:700;">Se connecter a l'administration</a>
                </p>
                <p style="margin:0 0 12px;font-size:15px;line-height:1.7;color:#3b3b3b;">
                  Ce lien expire dans <strong>{get_admin_magic_link_ttl_seconds(form_id) // 60} minutes</strong>.
                </p>
                <p style="margin:0;font-size:14px;line-height:1.7;color:#6a645c;">
                  Si vous n'etes pas a l'origine de cette demande, ignorez cet email.
                </p>
                <p style="margin:22px 0 0;font-size:15px;line-height:1.7;">
                  Cordialement,<br><br>{escape(get_eures_mail_signature_name())}<br>EURES beta
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
    return normalize_email(email), subject, text_body, html_body


def _render_admin_login_page(form_id: str, message: str = '', error: str = '') -> Response:
    html = f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Connexion admin {escape(form_id)}</title>
  </head>
  <body style="margin:0;background:#f4efe6;font-family:Georgia,'Times New Roman',serif;color:#1f1f1f;">
    <main style="max-width:620px;margin:64px auto;padding:0 20px;">
      <section style="background:#fffdf9;border:1px solid #e7dcc7;border-radius:20px;overflow:hidden;box-shadow:0 10px 30px rgba(15,39,66,0.08);">
        <header style="padding:28px 32px;background:linear-gradient(135deg,#0f2742 0%,#004494 100%);color:#fff;">
          <div style="font-size:13px;letter-spacing:1.6px;text-transform:uppercase;opacity:0.82;">Administration securisee</div>
          <h1 style="margin:10px 0 0;font-size:34px;line-height:1.1;">EURES beta</h1>
        </header>
        <div style="padding:28px 32px;">
          <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">
            Saisissez votre adresse email autorisee pour recevoir un lien de connexion a usage limite dans le temps.
          </p>
          {f'<p style="margin:0 0 16px;padding:12px 14px;border-radius:12px;background:#eef6ed;color:#215732;font-size:15px;line-height:1.6;">{escape(message)}</p>' if message else ''}
          {f'<p style="margin:0 0 16px;padding:12px 14px;border-radius:12px;background:#fbebeb;color:#7c2222;font-size:15px;line-height:1.6;">{escape(error)}</p>' if error else ''}
          <form method="post" action="{escape(url_for('admin_login', form_id=form_id))}">
            <label for="email" style="display:block;margin:0 0 8px;font-size:14px;font-weight:700;">Adresse email</label>
            <input id="email" name="email" type="email" required autocomplete="email" style="width:100%;box-sizing:border-box;border:1px solid #d9ccb4;border-radius:12px;padding:14px 16px;font-size:16px;">
            <button type="submit" style="margin-top:18px;border:0;border-radius:12px;background:#004494;color:#fff;padding:14px 18px;font-size:16px;font-weight:700;cursor:pointer;">Recevoir un lien de connexion</button>
          </form>
        </div>
      </section>
    </main>
  </body>
</html>"""
    return Response(html, mimetype='text/html')


def admin_required(fn):
    """Decorator to protect admin pages and APIs with basic auth."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        form_id = str(kwargs.get('form_id') or '')
        proxied = maybe_proxy_eures_request(form_id)
        if proxied is not None:
            return proxied
        mode = get_admin_auth_mode(form_id)
        if mode == 'magic_link':
            denied = _require_admin_magic_link_auth(form_id)
        elif mode == 'hybrid':
            denied = _require_admin_magic_link_auth(form_id)
            if denied is not None:
                basic_denied = _require_admin_basic_auth(form_id)
                denied = None if basic_denied is None else denied
        else:
            denied = _require_admin_basic_auth(form_id)
        if denied:
            return denied
        return fn(*args, **kwargs)
    return wrapper


def get_form_config(form_id: str, role: str | None = None) -> dict:
    """Get configuration for a form from environment variables."""
    form_id_upper = form_id.replace('-', '_').upper()
    role_upper = (role or '').strip().replace('-', '_').upper()

    def _env_with_role(base: str) -> str | None:
        if role_upper:
            value = os.environ.get(f'{base}_{form_id_upper}_{role_upper}')
            if value:
                return value
        return os.environ.get(f'{base}_{form_id_upper}')

    doc_id = _env_with_role('GRIST_DOC')
    if not doc_id:
        return None

    return {
        'doc_id': doc_id,
        'table_id': _env_with_role('GRIST_TABLE') or 'Reponses',
        'api_key': _env_with_role('GRIST_API_KEY') or os.environ.get('GRIST_API_KEY'),
    }


def get_form_access_settings(form_id: str) -> dict:
    """Return public access settings for one form."""
    form_id_upper = form_id.replace('-', '_').upper()
    read_only_env = os.environ.get(f'FORM_READONLY_{form_id_upper}')
    default_read_only = form_id == 'fagerh'
    if read_only_env is None:
        read_only = default_read_only
    else:
        read_only = str(read_only_env).strip().lower() in {'1', 'true', 'yes', 'on'}

    default_message = (
        "La période de saisie est close. Vous pouvez désormais uniquement consulter vos réponses."
    )
    message = str(
        os.environ.get(f'FORM_READONLY_MESSAGE_{form_id_upper}')
        or default_message
    ).strip() or default_message

    return {
        'read_only': read_only,
        'message': message,
    }


def get_eures_stats_config() -> dict | None:
    """Get configuration for the optional EURES monthly stats table."""
    base = get_form_config('eures-beta', 'candidate') or get_form_config('eures-beta')
    if not base:
        return None

    return {
        'doc_id': base['doc_id'],
        'table_id': os.environ.get('GRIST_TABLE_EURES_BETA_STATS', EURES_STATS_TABLE_DEFAULT),
        'api_key': base.get('api_key'),
    }


def get_eures_matching_config() -> dict | None:
    """Get configuration for EURES beta matching tables."""
    base = get_form_config('eures-beta', 'candidate') or get_form_config('eures-beta')
    if not base:
        return None
    return {
        'doc_id': base['doc_id'],
        'table_id': EURES_MATCHINGS_TABLE,
        'api_key': base.get('api_key'),
    }


def get_eures_invitations_config() -> dict | None:
    """Get configuration for the optional EURES invitations table."""
    base = get_form_config('eures-beta', 'candidate') or get_form_config('eures-beta')
    if not base:
        return None
    return {
        'doc_id': base['doc_id'],
        'table_id': os.environ.get('GRIST_TABLE_EURES_BETA_INVITATIONS', EURES_INVITATIONS_TABLE_DEFAULT),
        'api_key': base.get('api_key'),
    }


def get_brevo_config() -> dict:
    return {
        'api_key': os.environ.get('BREVO_API_KEY', '').strip(),
        'from_email': os.environ.get('BREVO_FROM_EMAIL', '').strip(),
        'from_name': os.environ.get('BREVO_FROM_NAME', 'EURES beta').strip() or 'EURES beta',
    }


def get_brevo_health(check_api: bool = False, timeout: int = 8) -> dict:
    """Return a sanitized Brevo health snapshot suitable for admin and health checks."""
    brevo = get_brevo_config()
    configured = bool(brevo['api_key'] and brevo['from_email'])
    result = {
        'configured': configured,
        'from_email': brevo['from_email'],
        'from_name': brevo['from_name'],
        'api_ok': None,
        'http_status': None,
        'status': 'ok' if configured else 'missing_config',
        'message': 'Brevo configuration complete.' if configured else 'BREVO_API_KEY or BREVO_FROM_EMAIL is missing.',
    }
    if not configured or not check_api:
        return result

    try:
        response = requests.get(
            'https://api.brevo.com/v3/account',
            headers={
                'accept': 'application/json',
                'api-key': brevo['api_key'],
            },
            timeout=timeout,
        )
        result['http_status'] = response.status_code
        if response.ok:
            result['api_ok'] = True
            result['status'] = 'ok'
            result['message'] = 'Brevo API reachable.'
            return result

        result['api_ok'] = False
        result['status'] = 'api_error'
        try:
            payload = response.json()
        except ValueError:
            payload = {}
        result['message'] = str(payload.get('message') or payload.get('error') or f'Brevo API returned HTTP {response.status_code}.')
        return result
    except requests.RequestException as exc:
        result['api_ok'] = False
        result['status'] = 'request_error'
        result['message'] = str(exc)
        return result


def ensure_brevo_ready(check_api: bool = False) -> dict:
    """Raise a readable error when Brevo is not ready for transactional sends."""
    health = get_brevo_health(check_api=check_api)
    if not health['configured']:
        raise RuntimeError('Brevo configuration is incomplete. Missing BREVO_API_KEY or BREVO_FROM_EMAIL.')
    if check_api and health['api_ok'] is not True:
        raise RuntimeError(f"Brevo API check failed: {health['message']}")
    return health


def _now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def _initial_matching_workflow_status(scoring_status: str) -> str:
    return 'a_valider_admin' if str(scoring_status or '').strip().lower() in {'a_valider', 'auto_envoyable'} else 'calcule'


def _matching_workflow_status(fields: dict) -> str:
    current = str((fields or {}).get('workflow_status') or '').strip().lower()
    if current:
        return current
    if (fields or {}).get('embauche_confirmee_at'):
        return 'embauche_confirmee'
    if (fields or {}).get('mise_en_relation_at'):
        return 'mise_en_relation_faite'
    employer_response = str((fields or {}).get('employer_response') or '').strip().lower()
    if employer_response == 'contact':
        return 'accepte_employeur'
    if employer_response == 'not_contact':
        return 'refuse_employeur'
    if (fields or {}).get('sent_to_employer_at'):
        return 'envoye_employeur'
    admin_status = str((fields or {}).get('admin_status') or '').strip().lower()
    if admin_status == 'accepted':
        return 'envoye_employeur'
    if admin_status == 'refused':
        return 'refuse_admin'
    return _initial_matching_workflow_status((fields or {}).get('statut', ''))


def _matching_workflow_update_fields(target_status: str, actor: str) -> dict:
    now = _now_iso_utc()
    fields = {
        'workflow_status': target_status,
        'workflow_status_updated_at': now,
        'workflow_status_updated_by': actor,
    }
    if target_status == 'envoye_employeur':
        fields['sent_to_employer_at'] = now
        fields['sent_to_employer_by'] = actor
    elif target_status == 'accepte_employeur':
        fields['employer_response'] = 'contact'
        fields['employer_response_at'] = now
        fields['employer_response_source'] = 'email_cta'
    elif target_status == 'refuse_employeur':
        fields['employer_response'] = 'not_contact'
        fields['employer_response_at'] = now
        fields['employer_response_source'] = 'email_cta'
    elif target_status == 'mise_en_relation_faite':
        fields['mise_en_relation_at'] = now
        fields['mise_en_relation_by'] = actor
    elif target_status == 'embauche_confirmee':
        fields['embauche_confirmee_at'] = now
        fields['embauche_confirmee_by'] = actor
    return fields


def _matching_workflow_label(status: str) -> str:
    return {
        'calcule': 'calculé',
        'a_valider_admin': 'à valider',
        'refuse_admin': 'refus admin',
        'valide_admin': 'validé admin',
        'envoye_employeur': 'envoyé employeur',
        'accepte_employeur': 'accepté employeur',
        'refuse_employeur': 'refusé employeur',
        'mise_en_relation_faite': 'mise en relation faite',
        'embauche_confirmee': 'embauche confirmée',
    }.get(str(status or '').strip().lower(), str(status or '').strip() or 'inconnu')


def get_eures_mail_signature_name() -> str:
    return os.environ.get('EURES_SIGNATURE_NAME', 'Eric Barthélémy').strip() or 'Eric Barthélémy'


def get_eures_mail_signature_role() -> str:
    return os.environ.get('EURES_SIGNATURE_ROLE', 'Conseiller EURES - France Travail').strip() or 'Conseiller EURES - France Travail'


def get_eures_privacy_url(lang: str = 'fr') -> str:
    normalized_lang = str(lang or 'fr').strip().lower()
    if normalized_lang not in {'fr', 'en', 'de'}:
        normalized_lang = 'fr'
    return f"{get_public_app_base_url()}/forms/eures-beta/privacy?lang={normalized_lang}"


def get_public_app_base_url() -> str:
    configured = os.environ.get('PUBLIC_APP_BASE_URL', '').strip()
    if configured:
        return configured.rstrip('/')
    if request and request.url_root:
        return request.url_root.rstrip('/')
    return 'https://eures-beta.osc-fr1.scalingo.io'


def get_eures_email_header_image_url() -> str:
    configured = os.environ.get('EURES_EMAIL_HEADER_IMAGE_URL', '').strip()
    if configured:
        return configured
    bundled = ASSETS_DIR / 'eures-email-header.png'
    if bundled.exists():
        return f"{get_public_app_base_url()}/assets/eures-email-header.png"
    return ''


def _proxy_eures_location_header(location: str) -> str:
    """Rewrite absolute redirects back to the current public host."""
    value = str(location or '').strip()
    if not value:
        return value
    if value.startswith(EURES_PUBLIC_PROXY_BASE_URL):
        current_base = request.host_url.rstrip('/')
        return current_base + value[len(EURES_PUBLIC_PROXY_BASE_URL):]
    return value


def proxy_eures_public_request(path: str = '') -> Response:
    """Proxy one public EURES beta request to the dedicated Scalingo app."""
    target_path = '/' + str(path or '').lstrip('/')
    target_url = f'{EURES_PUBLIC_PROXY_BASE_URL}{target_path}'
    if request.query_string:
        target_url = f'{target_url}?{request.query_string.decode("utf-8", errors="ignore")}'

    excluded_headers = {
        'host',
        'content-length',
        'connection',
        'transfer-encoding',
        'accept-encoding',
    }
    upstream_headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in excluded_headers
    }
    upstream_headers['X-Forwarded-Host'] = request.host
    upstream_headers['X-Forwarded-Proto'] = request.scheme
    upstream_headers['X-Forwarded-For'] = request.headers.get('X-Forwarded-For', request.remote_addr or '')

    upstream_response = requests.request(
        method=request.method,
        url=target_url,
        headers=upstream_headers,
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False,
        timeout=60,
    )

    downstream = Response(upstream_response.content, status=upstream_response.status_code)
    hop_by_hop = {
        'content-length',
        'connection',
        'transfer-encoding',
        'content-encoding',
    }
    for key, value in upstream_response.headers.items():
        lowered = key.lower()
        if lowered in hop_by_hop:
            continue
        if lowered == 'location':
            value = _proxy_eures_location_header(value)
        downstream.headers[key] = value
    return downstream


def should_proxy_eures_public_request(form_id: str) -> bool:
    """Enable EURES proxying only on the public Fagerh domain."""
    if is_eures_beta_only_mode():
        return False
    if str(form_id or '').strip().lower() != 'eures-beta':
        return False
    forced = os.environ.get('EURES_PUBLIC_PROXY_ENABLED', '').strip().lower()
    if forced in {'1', 'true', 'yes', 'on'}:
        return True
    if forced in {'0', 'false', 'no', 'off'}:
        return False
    host = str(request.host or '').split(':', 1)[0].strip().lower()
    return host == 'formulaires.inclusion.gouv.fr'


def maybe_proxy_eures_request(form_id: str) -> Response | None:
    """Proxy only the EURES beta public surface when served by Fagerh."""
    if should_proxy_eures_public_request(form_id):
        return proxy_eures_public_request(request.path)
    return None


def get_default_home_form_id() -> str:
    """Resolve which form should be used as the root redirect for the current app."""
    if is_eures_beta_only_mode():
        return 'eures-beta'
    configured = str(os.environ.get('DEFAULT_HOME_FORM_ID') or '').strip()
    if configured:
        return configured

    host = str(request.host or '').split(':', 1)[0].strip().lower()
    if host in {
        'eures-beta.osc-fr1.scalingo.io',
        'www.eures-beta.osc-fr1.scalingo.io',
    }:
        return 'eures-beta'
    return 'fagerh'


def get_eures_email_action_serializer() -> URLSafeSerializer:
    secret = (
        os.environ.get('EURES_EMAIL_ACTION_SECRET', '').strip()
        or os.environ.get('ADMIN_PASSWORD', '').strip()
        or os.environ.get('BREVO_API_KEY', '').strip()
    )
    if not secret:
        raise RuntimeError('Missing EURES email action secret configuration.')
    return URLSafeSerializer(secret_key=secret, salt='eures-email-action')


def get_eures_public_write_serializer() -> URLSafeTimedSerializer:
    secret = (
        os.environ.get('EURES_PUBLIC_WRITE_SECRET', '').strip()
        or app.config.get('SECRET_KEY', '')
    )
    if not secret:
        raise RuntimeError('Missing EURES public write secret configuration.')
    return URLSafeTimedSerializer(secret_key=secret, salt='eures-public-write')


def get_eures_public_write_ttl_seconds() -> int:
    raw = str(os.environ.get('EURES_PUBLIC_WRITE_TTL_SECONDS', '21600')).strip()
    try:
        value = int(raw)
    except Exception:
        value = 21600
    return max(300, value)


def get_eures_public_write_rate_limit() -> tuple[int, int]:
    raw_window = str(os.environ.get('EURES_PUBLIC_WRITE_RATE_LIMIT_WINDOW_SECONDS', '3600')).strip()
    raw_max = str(os.environ.get('EURES_PUBLIC_WRITE_RATE_LIMIT_MAX', '20')).strip()
    try:
        window_seconds = int(raw_window)
    except Exception:
        window_seconds = 3600
    try:
        max_attempts = int(raw_max)
    except Exception:
        max_attempts = 20
    return max(60, window_seconds), max(1, max_attempts)


def _eures_public_write_session_key(role: str) -> str:
    return f'eures_public_write:{role}'


def _get_client_ip() -> str:
    forwarded = str(request.headers.get('X-Forwarded-For') or '').strip()
    if forwarded:
        return forwarded.split(',', 1)[0].strip()
    return str(request.remote_addr or '').strip()


def _issue_eures_public_write_token(role: str) -> str:
    normalized_role = _normalize_eures_invitation_role(role)
    if not normalized_role:
        raise ValueError('Invalid role')
    nonce = secrets.token_urlsafe(18)
    session[_eures_public_write_session_key(normalized_role)] = {
        'nonce': nonce,
        'issued_at': datetime.now(timezone.utc).isoformat(),
    }
    session.modified = True
    return get_eures_public_write_serializer().dumps({
        'form_id': 'eures-beta',
        'role': normalized_role,
        'nonce': nonce,
    })


def _validate_eures_public_write_token(role: str, token: str) -> tuple[bool, str]:
    normalized_role = _normalize_eures_invitation_role(role)
    if not normalized_role:
        return False, 'Role invalide.'
    if not token:
        return False, 'Session du formulaire invalide ou expirée. Rechargez la page avant de renvoyer.'
    try:
        payload = get_eures_public_write_serializer().loads(
            token,
            max_age=get_eures_public_write_ttl_seconds(),
        )
    except SignatureExpired:
        return False, 'Session du formulaire expirée. Rechargez la page avant de renvoyer.'
    except BadSignature:
        return False, 'Session du formulaire invalide. Rechargez la page avant de renvoyer.'
    except Exception:
        app.logger.exception('EURES public write token decode failed')
        return False, 'Impossible de vérifier la session du formulaire. Rechargez la page puis réessayez.'

    if str(payload.get('form_id') or '') != 'eures-beta':
        return False, 'Jeton de formulaire invalide.'
    if _normalize_eures_invitation_role(payload.get('role') or '') != normalized_role:
        return False, 'Jeton de formulaire invalide pour ce parcours.'
    nonce = str(payload.get('nonce') or '').strip()
    session_payload = session.get(_eures_public_write_session_key(normalized_role)) or {}
    if str(session_payload.get('nonce') or '').strip() != nonce:
        return False, 'Session du formulaire expirée. Rechargez la page avant de renvoyer.'
    return True, ''


def _check_eures_public_write_rate_limit(role: str) -> tuple[bool, int]:
    normalized_role = _normalize_eures_invitation_role(role)
    if not normalized_role:
        return False, 0
    window_seconds, max_attempts = get_eures_public_write_rate_limit()
    key = (_get_client_ip(), normalized_role)
    now = time.time()
    bucket = [ts for ts in _EURES_PUBLIC_WRITE_ATTEMPTS.get(key, []) if now - ts < window_seconds]
    if len(bucket) >= max_attempts:
        _EURES_PUBLIC_WRITE_ATTEMPTS[key] = bucket
        return False, int(max(1, window_seconds - (now - bucket[0])))
    bucket.append(now)
    _EURES_PUBLIC_WRITE_ATTEMPTS[key] = bucket
    return True, 0


def _generate_eures_invitation_token() -> str:
    return secrets.token_urlsafe(24)


def _normalize_eures_invitation_role(value: str) -> str:
    role = str(value or '').strip().lower().replace('-', '_')
    if role in {'candidat', 'candidate'}:
        return 'candidate'
    if role in {'employeur', 'employer'}:
        return 'employer'
    return ''


def _normalize_eures_invitation_status(value: str) -> str:
    status = str(value or '').strip().lower().replace(' ', '_')
    if status in EURES_INVITATION_ALLOWED_STATUSES:
        return status
    return ''


def get_eures_invitation_reminder_delay_days() -> int:
    raw = str(os.getenv('EURES_INVITATION_REMINDER_DELAY_DAYS', '7') or '7').strip()
    try:
        value = int(raw)
    except Exception:
        value = 7
    return value if value > 0 else 7


def _build_eures_invitation_link(role: str, language: str, invite_token: str) -> str:
    page = 'candidate' if role == 'candidate' else 'employer'
    lang = str(language or 'fr').strip().lower()
    if lang not in {'fr', 'en', 'de'}:
        lang = 'fr'
    base = get_public_app_base_url()
    return f'{base}/forms/eures-beta/{page}?lang={lang}&invite_token={invite_token}'


def _eures_invitation_lookup_key(role: str, email: str) -> tuple[str, str]:
    return (_normalize_eures_invitation_role(role), normalize_email(email))


def _extract_csv_rows(csv_text: str) -> list[dict]:
    raw_text = str(csv_text or '').replace('\r\n', '\n').replace('\r', '\n').lstrip('\ufeff')
    if not raw_text.strip():
        return []

    sample = '\n'.join(raw_text.splitlines()[:5])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',;')
    except Exception:
        dialect = csv.excel

    buffer = StringIO(raw_text)
    reader = csv.DictReader(buffer, dialect=dialect)
    if reader.fieldnames:
        reader.fieldnames = [str(name or '').strip().lstrip('\ufeff') for name in reader.fieldnames]

    rows = []
    for row in reader:
        if not isinstance(row, dict):
            continue
        cleaned = {
            str(key or '').strip().lstrip('\ufeff'): str(value or '').strip()
            for key, value in row.items()
            if str(key or '').strip().lstrip('\ufeff')
        }
        if any(cleaned.values()):
            rows.append(cleaned)
    return rows


def _coalesce_row_value(row: dict, *keys: str) -> str:
    for key in keys:
        if key in row and str(row.get(key) or '').strip():
            return str(row.get(key) or '').strip()
    return ''


def _coalesce_row_raw_value(row: dict, *keys: str):
    """Return the first non-empty raw value without forcing string conversion."""
    for key in keys:
        if key not in row:
            continue
        value = row.get(key)
        if isinstance(value, list) and value:
            return value
        if value is None:
            continue
        if str(value).strip():
            return value
    return ''


def _parse_eures_invitation_rows(payload: dict) -> list[dict]:
    rows = payload.get('rows')
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]

    csv_text = payload.get('csv_text')
    if isinstance(csv_text, str) and csv_text.strip():
        return _extract_csv_rows(csv_text)

    return []


def _normalize_eures_invitation_target_job_keys(value) -> list[str]:
    """Normalize targeted job keys stored on candidate invitations."""
    candidates = value
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            candidates = []
        else:
            try:
                parsed = json.loads(stripped)
            except Exception:
                parsed = None
            if isinstance(parsed, list):
                candidates = parsed
            else:
                candidates = re.split(r'[,\n;|]+', stripped)
    elif not isinstance(value, list):
        candidates = []

    normalized: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        key = str(item or '').strip().lower()
        if key not in EURES_INVITATION_CANDIDATE_TARGET_OPTIONS or key in seen:
            continue
        seen.add(key)
        normalized.append(key)
    return normalized


def _serialize_eures_invitation_target_job_keys(value) -> str:
    keys = _normalize_eures_invitation_target_job_keys(value)
    return json.dumps(keys, ensure_ascii=False) if keys else ''


def _eures_invitation_target_job_labels(value, language: str = 'fr') -> list[str]:
    return [
        get_candidate_target_job_label(key, language)
        for key in _normalize_eures_invitation_target_job_keys(value)
        if get_candidate_target_job_label(key, language)
    ]


def _normalize_eures_invitation_row(row: dict, actor: str, batch_id: str) -> dict:
    role = _normalize_eures_invitation_role(_coalesce_row_value(row, 'role', 'type', 'profil', 'profile'))
    email = normalize_email(_coalesce_row_value(row, 'email', 'mail', 'contact_email'))
    language = _coalesce_row_value(row, 'language', 'langue', 'lang') or 'fr'
    invitation_status = _normalize_eures_invitation_status(
        _coalesce_row_value(row, 'invitation_status', 'status', 'statut')
    ) or 'invitation_a_envoyer'
    token = _coalesce_row_value(row, 'invite_token', 'token') or _generate_eures_invitation_token()
    return {
        'role': role,
        'email': email,
        'first_name': _coalesce_row_value(row, 'first_name', 'prenom', 'prénom'),
        'last_name': _coalesce_row_value(row, 'last_name', 'nom'),
        'company_name': _coalesce_row_value(row, 'company_name', 'entreprise', 'company'),
        'language': language.lower(),
        'source': _coalesce_row_value(row, 'source', 'origine') or 'csv_import',
        'external_ref': _coalesce_row_value(row, 'external_ref', 'external_id', 'id_externe', 'id'),
        'invite_token': token,
        'invite_link': _build_eures_invitation_link(role, language, token) if role else '',
        'invitation_status': invitation_status,
        'invitation_status_updated_at': _now_iso_utc(),
        'invitation_status_updated_by': actor,
        'import_batch_id': batch_id,
        'imported_at': _now_iso_utc(),
        'imported_by': actor,
        'sponsor_invitation_record_id': _coalesce_row_value(row, 'sponsor_invitation_record_id'),
        'sponsor_email': normalize_email(_coalesce_row_value(row, 'sponsor_email')),
        'sponsor_company_name': _coalesce_row_value(row, 'sponsor_company_name'),
        'invited_by_type': _coalesce_row_value(row, 'invited_by_type') or 'admin',
        'invite_scope': _coalesce_row_value(row, 'invite_scope') or '',
        'target_job_keys': _serialize_eures_invitation_target_job_keys(
            _coalesce_row_raw_value(row, 'target_job_keys', 'target_jobs', 'target_job', 'metier_cible', 'metiers_cibles')
        ) if role == 'candidate' else '',
        'notes': _coalesce_row_value(row, 'notes', 'note', 'comment', 'commentaire'),
    }


def list_eures_invitations() -> list[dict]:
    config = get_eures_invitations_config()
    if not config:
        raise RuntimeError('EURES invitations configuration is incomplete.')
    headers = _eures_admin_headers(config)
    records = fetch_table_records(config['doc_id'], config['table_id'], headers)
    rows = []
    now = datetime.now(timezone.utc)
    for rec in records:
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        days_since_sent = _days_since(fields.get('sent_at'), now=now)
        needs_reminder = _eures_invitation_needs_reminder(fields, now=now)
        rows.append({
            'record_id': rec.get('id'),
            'role': fields.get('role', ''),
            'email': fields.get('email', ''),
            'first_name': fields.get('first_name', ''),
            'last_name': fields.get('last_name', ''),
            'company_name': fields.get('company_name', ''),
            'language': fields.get('language', ''),
            'source': fields.get('source', ''),
            'external_ref': fields.get('external_ref', ''),
            'invite_token': fields.get('invite_token', ''),
            'invite_link': fields.get('invite_link', ''),
            'invitation_status': fields.get('invitation_status', 'invitation_a_envoyer'),
            'sent_at': fields.get('sent_at', ''),
            'answered_at': fields.get('answered_at', ''),
            'reminder_count': _safe_int(fields.get('reminder_count')),
            'last_reminder_at': fields.get('last_reminder_at', ''),
            'last_reminder_by': fields.get('last_reminder_by', ''),
            'sponsor_invitation_record_id': fields.get('sponsor_invitation_record_id', ''),
            'sponsor_email': fields.get('sponsor_email', ''),
            'sponsor_company_name': fields.get('sponsor_company_name', ''),
            'invited_by_type': fields.get('invited_by_type', ''),
            'invite_scope': fields.get('invite_scope', ''),
            'target_job_keys': _normalize_eures_invitation_target_job_keys(fields.get('target_job_keys', '')),
            'target_job_labels': _eures_invitation_target_job_labels(fields.get('target_job_keys', ''), fields.get('language', 'fr')),
            'first_submission_at': fields.get('first_submission_at', ''),
            'last_submission_at': fields.get('last_submission_at', ''),
            'submission_count': _safe_int(fields.get('submission_count')),
            'linked_form_role': fields.get('linked_form_role', ''),
            'linked_record_id': fields.get('linked_record_id', ''),
            'linked_record_key': fields.get('linked_record_key', ''),
            'matching_status': fields.get('matching_status', ''),
            'duplicate_followup_status': fields.get('duplicate_followup_status', ''),
            'duplicate_followup_type': fields.get('duplicate_followup_type', ''),
            'duplicate_followup_target_record_id': fields.get('duplicate_followup_target_record_id', ''),
            'duplicate_followup_target_status': fields.get('duplicate_followup_target_status', ''),
            'duplicate_followup_message': fields.get('duplicate_followup_message', ''),
            'duplicate_followup_created_at': fields.get('duplicate_followup_created_at', ''),
            'duplicate_followup_created_by': fields.get('duplicate_followup_created_by', ''),
            'duplicate_followup_processed_at': fields.get('duplicate_followup_processed_at', ''),
            'duplicate_followup_processed_by': fields.get('duplicate_followup_processed_by', ''),
            'duplicate_followup_note': fields.get('duplicate_followup_note', ''),
            'notes': fields.get('notes', ''),
            'import_batch_id': fields.get('import_batch_id', ''),
            'imported_at': fields.get('imported_at', ''),
            'imported_by': fields.get('imported_by', ''),
            'days_since_sent': days_since_sent,
            'needs_reminder': needs_reminder,
        })
    rows.sort(key=lambda row: (str(row.get('invitation_status') or ''), -int(row.get('record_id') or 0)))
    return rows


def upsert_eures_invitation_rows(rows: list[dict], actor: str) -> dict:
    config = get_eures_invitations_config()
    if not config:
        raise RuntimeError('EURES invitations configuration is incomplete.')
    headers = _eures_admin_headers(config)
    ensure_table_columns(config, EURES_INVITATION_FIELDS, headers)
    existing_records = fetch_table_records(config['doc_id'], config['table_id'], headers)
    by_key: dict[tuple[str, str], dict] = {}
    for rec in existing_records:
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        key = _eures_invitation_lookup_key(fields.get('role', ''), fields.get('email', ''))
        if key[0] and key[1]:
            by_key[key] = rec

    batch_id = f'invite-import-{int(time.time())}'
    to_create = []
    to_update = []
    skipped = []
    for raw_row in rows:
        normalized = _normalize_eures_invitation_row(raw_row, actor=actor, batch_id=batch_id)
        role = normalized['role']
        email = normalized['email']
        if role not in EURES_INVITATION_ALLOWED_ROLES or not email:
            skipped.append({
                'row': raw_row,
                'reason': 'missing_or_invalid_role_or_email',
            })
            continue
        existing = by_key.get((role, email))
        if existing:
            existing_fields = existing.get('fields', {}) if isinstance(existing.get('fields'), dict) else {}
            merged = dict(existing_fields)
            merged.update({
                key: value for key, value in normalized.items()
                if value not in (None, '')
            })
            merged['invite_token'] = existing_fields.get('invite_token') or normalized['invite_token']
            merged['invite_link'] = _build_eures_invitation_link(role, merged.get('language', 'fr'), merged['invite_token'])
            to_update.append({'id': existing['id'], 'fields': merged})
        else:
            to_create.append({'fields': normalized})

    base_url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}/records"
    if to_create:
        resp = write_grist_records('POST', base_url, {'records': to_create}, headers)
        if resp.status_code != 200:
            raise RuntimeError(f'Failed to create invitations: HTTP {resp.status_code} - {resp.text}')
    if to_update:
        resp = write_grist_records('PATCH', base_url, {'records': to_update}, headers)
        if resp.status_code != 200:
            raise RuntimeError(f'Failed to update invitations: HTTP {resp.status_code} - {resp.text}')

    return {
        'ok': True,
        'batch_id': batch_id,
        'created': len(to_create),
        'updated': len(to_update),
        'skipped': skipped,
    }


def update_eures_invitation_record_by_id(record_id: int, fields: dict, headers: dict | None = None):
    """Patch one invitation record by Grist record id."""
    config = get_eures_invitations_config()
    if not config:
        raise RuntimeError('EURES invitations configuration is incomplete.')
    if headers is None:
        headers = _eures_admin_headers(config)
    ensure_table_columns(config, set(fields.keys()) & EURES_INVITATION_FIELDS, headers)
    allowed_columns = get_table_columns(config, headers)
    filtered_fields = {k: v for k, v in fields.items() if k in allowed_columns}
    base_url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}/records"
    resp = write_grist_records('PATCH', base_url, {'records': [{'id': record_id, 'fields': filtered_fields}]}, headers)
    if resp.status_code != 200:
        raise RuntimeError(f'Failed to update invitation: HTTP {resp.status_code} - {resp.text}')
    return resp


def delete_eures_invitation_record_by_id(record_id: int, headers: dict | None = None):
    """Delete one invitation record by Grist record id."""
    config = get_eures_invitations_config()
    if not config:
        raise RuntimeError('EURES invitations configuration is incomplete.')
    if headers is None:
        headers = _eures_admin_headers(config)
    delete_url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}/records/delete"
    resp = write_grist_records('POST', delete_url, [int(record_id)], headers)
    if resp.status_code not in {200, 202, 204}:
        raise RuntimeError(f'Failed to delete invitation: HTTP {resp.status_code} - {resp.text}')
    return resp


def find_eures_invitation_by_token(invite_token: str, headers: dict | None = None) -> dict | None:
    """Find one invitation row by invite token."""
    token = str(invite_token or '').strip()
    if not token:
        return None
    config = get_eures_invitations_config()
    if not config:
        raise RuntimeError('EURES invitations configuration is incomplete.')
    if headers is None:
        headers = _eures_admin_headers(config)
    records = fetch_table_records(config['doc_id'], config['table_id'], headers)
    for rec in records:
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        if str(fields.get('invite_token') or '').strip() == token:
            return rec
    return None


def find_eures_invitation_by_role_email(role: str, email: str, headers: dict | None = None) -> dict | None:
    """Find one invitation row by normalized role and email."""
    normalized_role = _normalize_eures_invitation_role(role)
    normalized_email = normalize_email(email)
    if not normalized_role or not normalized_email:
        return None
    config = get_eures_invitations_config()
    if not config:
        raise RuntimeError('EURES invitations configuration is incomplete.')
    if headers is None:
        headers = _eures_admin_headers(config)
    records = fetch_table_records(config['doc_id'], config['table_id'], headers)
    for rec in records:
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        if _eures_invitation_lookup_key(fields.get('role', ''), fields.get('email', '')) == (normalized_role, normalized_email):
            return rec
    return None


def find_eures_questionnaire_by_role_email(role: str, email: str, headers: dict | None = None) -> dict | None:
    """Find one returned EURES questionnaire by normalized role and email."""
    normalized_role = _normalize_eures_invitation_role(role)
    normalized_email = normalize_email(email)
    if not normalized_role or not normalized_email:
        return None
    config = _get_eures_role_table_config(normalized_role)
    if not config:
        raise RuntimeError('EURES role table configuration is incomplete.')
    if headers is None:
        headers = _eures_admin_headers(config)
    records = fetch_table_records(config['doc_id'], config['table_id'], headers)
    for rec in records:
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        if not isinstance(fields, dict):
            continue
        row_email = (
            normalize_email(fields.get('email', ''))
            if normalized_role == 'candidate'
            else _resolve_employer_recipient(fields)
        )
        if row_email == normalized_email:
            return rec
    return None


def check_eures_invitation_send_conflict(
    role: str,
    email: str,
    *,
    current_record_id: int | None = None,
    invitation_headers: dict | None = None,
    questionnaire_headers: dict | None = None,
) -> dict | None:
    """Return one conflict payload when an invitation should not be sent."""
    normalized_role = _normalize_eures_invitation_role(role)
    normalized_email = normalize_email(email)
    if not normalized_role or not normalized_email:
        return None

    config = get_eures_invitations_config()
    if not config:
        raise RuntimeError('EURES invitations configuration is incomplete.')
    if invitation_headers is None:
        invitation_headers = _eures_admin_headers(config)
    invitation_records = fetch_table_records(config['doc_id'], config['table_id'], invitation_headers)
    for rec in invitation_records:
        record_id = int(rec.get('id') or 0)
        if current_record_id and record_id == int(current_record_id):
            continue
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        if _eures_invitation_lookup_key(fields.get('role', ''), fields.get('email', '')) != (normalized_role, normalized_email):
            continue
        status = str(fields.get('invitation_status') or '').strip().lower()
        if status in {'invitation_envoyee', 'questionnaire_recu', 'rapprochement_a_confirmer', 'rapprochee', 'matching_calcule', 'traitee'}:
            return {
                'type': 'existing_invitation',
                'record_id': record_id,
                'status': status,
                'message': 'Une invitation a déjà été envoyée à cette adresse.',
            }

    questionnaire = find_eures_questionnaire_by_role_email(
        normalized_role,
        normalized_email,
        headers=questionnaire_headers,
    )
    if questionnaire:
        questionnaire_record_id = int(questionnaire.get('id') or 0)
        return {
            'type': 'existing_questionnaire',
            'record_id': questionnaire_record_id,
            'status': 'questionnaire_recu',
            'message': 'Un questionnaire a déjà été retourné avec cette adresse email.',
        }
    return None


def mark_eures_duplicate_followup_pending(
    record_id: int,
    conflict: dict,
    actor: str,
    headers: dict | None = None,
):
    """Store one duplicate invitation follow-up to review in admin."""
    status = 'pending'
    conflict_type = str((conflict or {}).get('type') or '').strip().lower()
    conflict_record_id = int((conflict or {}).get('record_id') or 0)
    conflict_status = str((conflict or {}).get('status') or '').strip().lower()
    conflict_message = str((conflict or {}).get('message') or '').strip()
    note = str((conflict or {}).get('note') or '').strip()
    update_eures_invitation_record_by_id(record_id, {
        'duplicate_followup_status': status,
        'duplicate_followup_type': conflict_type,
        'duplicate_followup_target_record_id': str(conflict_record_id or ''),
        'duplicate_followup_target_status': conflict_status,
        'duplicate_followup_message': conflict_message,
        'duplicate_followup_created_at': _now_iso_utc(),
        'duplicate_followup_created_by': actor,
        'duplicate_followup_processed_at': '',
        'duplicate_followup_processed_by': '',
        'duplicate_followup_note': note,
        'notes': note[:500] if note else '',
    }, headers=headers)


def clear_eures_duplicate_followup(
    record_id: int,
    actor: str,
    *,
    status: str,
    note: str = '',
    headers: dict | None = None,
):
    """Mark one duplicate follow-up as processed."""
    normalized_status = _normalize_eures_duplicate_followup_status(status)
    if not normalized_status:
        raise RuntimeError('Invalid duplicate follow-up status.')
    update_fields = {
        'duplicate_followup_status': normalized_status,
        'duplicate_followup_processed_at': _now_iso_utc(),
        'duplicate_followup_processed_by': actor,
        'duplicate_followup_note': str(note or '').strip(),
    }
    if normalized_status in {'reminded', 'ignored'}:
        update_fields['invitation_status'] = 'traitee'
        update_fields['invitation_status_updated_at'] = _now_iso_utc()
        update_fields['invitation_status_updated_by'] = actor
    update_eures_invitation_record_by_id(record_id, update_fields, headers=headers)


def send_eures_invitation_reminder_by_record_id(record_id: int, actor: str, headers: dict | None = None) -> dict:
    """Send one reminder email for an existing EURES invitation row."""
    config = get_eures_invitations_config()
    if not config:
        raise RuntimeError('EURES invitations configuration is incomplete.')
    if headers is None:
        headers = _eures_admin_headers(config)
    rec = fetch_record_by_id(config['doc_id'], config['table_id'], record_id, headers)
    if not rec:
        raise RuntimeError("Invitation cible introuvable pour la relance.")
    fields = rec.get('fields', {}) if isinstance(rec.get('fields'), dict) else {}
    current_status = str(fields.get('invitation_status') or '').strip().lower()
    if current_status != 'invitation_envoyee':
        raise RuntimeError("La relance n'est possible que pour une invitation déjà envoyée.")
    if str(fields.get('answered_at') or '').strip():
        raise RuntimeError('Le questionnaire a déjà été reçu pour cette invitation.')
    recipient, subject, text_body, html_body, invite_token, invite_link = build_brevo_invitation_email(fields, kind='reminder')
    brevo_result = send_brevo_transactional_email(recipient, subject, text_body, html_body)
    update_eures_invitation_record_by_id(record_id, {
        'invite_token': invite_token,
        'invite_link': invite_link,
        'invitation_status_updated_at': _now_iso_utc(),
        'invitation_status_updated_by': actor,
        'reminder_count': _safe_int(fields.get('reminder_count')) + 1,
        'last_reminder_at': _now_iso_utc(),
        'last_reminder_by': actor,
        'last_reminder_message_id': str((brevo_result or {}).get('messageId') or ''),
    }, headers=headers)
    return {
        'record_id': int(rec.get('id') or 0),
        'email': recipient,
        'brevo_message_id': str((brevo_result or {}).get('messageId') or ''),
    }


def get_eures_active_employer_invitation(invite_token: str) -> tuple[dict | None, str]:
    """Validate one employer invitation link for public self-service actions."""
    config = get_eures_invitations_config()
    if not config:
        return None, 'EURES invitations configuration is incomplete.'
    headers = _eures_admin_headers(config)
    invitation = find_eures_invitation_by_token(invite_token, headers=headers)
    if not invitation:
        return None, "Lien d'invitation introuvable."
    fields = invitation.get('fields', {}) if isinstance(invitation.get('fields'), dict) else {}
    if _normalize_eures_invitation_role(fields.get('role', '')) != 'employer':
        return None, "Ce lien n'autorise pas l'accès employeur."
    if str(fields.get('invitation_status') or '').strip().lower() == 'desactivee':
        return None, 'Ce lien a été désactivé.'
    return invitation, ''


def link_eures_invitation_after_save(role: str, request_fields: dict, saved_record: dict, matching_result: dict | None = None) -> dict:
    """Link a saved EURES questionnaire to its invitation when possible."""
    if _normalize_eures_invitation_role(role) not in EURES_INVITATION_ALLOWED_ROLES:
        return {'linked': False, 'reason': 'unsupported_role'}

    config = get_eures_invitations_config()
    if not config:
        return {'linked': False, 'reason': 'invitations_not_configured'}

    headers = _eures_admin_headers(config)
    invite_token = str((request_fields or {}).get('invite_token') or '').strip()
    saved_fields = saved_record.get('fields', {}) if isinstance(saved_record.get('fields'), dict) else {}
    email = normalize_email(
        (request_fields or {}).get('email')
        or saved_fields.get('email')
        or saved_fields.get('tally_q18')
        or saved_fields.get('tally_q33')
    )

    invitation = None
    link_mode = ''
    if invite_token:
        invitation = find_eures_invitation_by_token(invite_token, headers=headers)
        if invitation:
            link_mode = 'token'

    if invitation is None and email:
        invitation = find_eures_invitation_by_role_email(role, email, headers=headers)
        if invitation:
            link_mode = 'email'

    if not invitation:
        return {
            'linked': False,
            'reason': 'invitation_not_found',
            'invite_token_present': bool(invite_token),
            'email_present': bool(email),
        }

    record_id = invitation.get('id')
    if not record_id:
        return {'linked': False, 'reason': 'invalid_invitation_record'}

    saved_record_key = str(saved_fields.get('id_tally') or saved_fields.get('uuid') or '').strip()
    now = _now_iso_utc()
    invitation_fields = invitation.get('fields', {}) if isinstance(invitation.get('fields'), dict) else {}
    notes = str(invitation_fields.get('notes') or '').strip()
    if link_mode == 'email':
        fallback_note = 'Lien questionnaire/invitation rapproche via email.'
        if fallback_note not in notes:
            notes = f'{notes} | {fallback_note}'.strip(' |')

    update_fields = {
        'answered_at': now,
        'first_submission_at': invitation_fields.get('first_submission_at') or now,
        'last_submission_at': now,
        'submission_count': _safe_int(invitation_fields.get('submission_count')) + 1,
        'linked_form_role': _normalize_eures_invitation_role(role),
        'linked_record_id': str(saved_record.get('id') or ''),
        'linked_record_key': saved_record_key,
        'invitation_status': 'questionnaire_recu',
        'invitation_status_updated_at': now,
        'invitation_status_updated_by': 'system_questionnaire_submission',
        'notes': notes,
    }
    if isinstance(matching_result, dict) and matching_result.get('processed'):
        update_fields['matching_status'] = 'matching_calcule'
        update_fields['matching_status_updated_at'] = now
        update_fields['matching_status_updated_by'] = 'system_matching'

    update_eures_invitation_record_by_id(int(record_id), update_fields, headers=headers)
    return {
        'linked': True,
        'mode': link_mode,
        'invitation_record_id': record_id,
        'linked_record_id': saved_record.get('id'),
        'linked_record_key': saved_record_key,
        'email': email,
        'invite_scope': str(invitation_fields.get('invite_scope') or ''),
        'company_name': str(invitation_fields.get('company_name') or ''),
        'sponsor_email': str(invitation_fields.get('sponsor_email') or ''),
        'sponsor_company_name': str(invitation_fields.get('sponsor_company_name') or ''),
    }


def _render_eures_email_brand_block(header_image_url: str) -> str:
    if header_image_url:
        return (
            f'<img src="{escape(header_image_url)}" alt="République Française · France Travail · EURES" '
            'style="display:block;width:100%;max-width:320px;height:auto;border:0;">'
        )
    return (
        '<div style="font-size:12px;line-height:1.4;color:#51627d;">'
        '<strong>République Française</strong> · <strong>France Travail</strong> · <strong>EURES</strong>'
        '</div>'
    )


def _build_eures_candidate_invitation_email(
    *,
    language: str,
    target_job_key: str,
    kind: str,
    invite_link: str,
    privacy_url: str,
    signature_name: str,
    signature_role: str,
    hello: str,
) -> tuple[str, str, str]:
    template = get_candidate_invitation_template(language, target_job_key=target_job_key, kind=kind)
    subject = str(template.get('subject') or '').strip()
    preheader = str(template.get('preheader') or '').strip()
    eyebrow = str(template.get('eyebrow') or '').strip()
    title = str(template.get('title') or '').strip()
    hook = str(template.get('hook') or '').strip()
    body = [str(item or '').strip() for item in template.get('body', []) if str(item or '').strip()]
    cta_label = str(template.get('cta_label') or 'Voir si mon profil correspond').strip()
    cta_note = str(template.get('cta_note') or '').strip()
    info_title = str(template.get('info_title') or '').strip()
    info_items = [str(item or '').strip() for item in template.get('info_items', []) if str(item or '').strip()]
    legal_intro = str(template.get('legal_intro') or '').strip()
    footer_network = str(template.get('footer_network') or '').strip()
    header_image_url = get_eures_email_header_image_url()

    text_lines = [hello]
    if eyebrow:
        text_lines.extend(['', eyebrow])
    if title:
        text_lines.extend(['', title])
    if hook:
        text_lines.extend(['', hook])
    if body:
        text_lines.extend([''] + body)
    text_lines.extend(['', f"{cta_label} : {invite_link}"])
    if cta_note:
        text_lines.extend(['', cta_note])
    if info_items:
        if info_title:
            text_lines.extend(['', info_title])
        for item in info_items:
            text_lines.append(f"- {item}")
    if legal_intro:
        text_lines.extend(['', legal_intro])
    if footer_network:
        text_lines.extend(['', footer_network])
    text_lines.extend([
        '',
        f'Informations sur vos données : {privacy_url}',
        '',
        'Cordialement,',
        '',
        signature_name,
        signature_role,
        '',
    ])
    text_body = '\n'.join(text_lines)

    body_html = f"""
<!doctype html>
<html lang="{escape(language)}">
  <body style="margin:0;padding:0;background:#f4f7fb;font-family:Arial,'Helvetica Neue',sans-serif;color:#16253d;">
    <div style="display:none;max-height:0;overflow:hidden;opacity:0;mso-hide:all;">
      {escape(preheader)}
    </div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4f7fb;padding:20px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:640px;background:#ffffff;border:1px solid #d9e1ee;border-radius:20px;overflow:hidden;">
            <tr>
              <td style="padding:18px 24px;border-bottom:1px solid #e7ecf4;background:#ffffff;">
                {_render_eures_email_brand_block(header_image_url)}
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 8px;">
                <p style="margin:0 0 10px;font-size:16px;line-height:1.6;color:#324765;">{escape(hello)}</p>
                {f'<div style="display:inline-block;padding:6px 10px;border-radius:999px;background:#edf4ff;color:#004494;font-size:12px;font-weight:700;letter-spacing:0.04em;text-transform:uppercase;">{escape(eyebrow)}</div>' if eyebrow else ''}
                {f'<h1 style="margin:14px 0 10px;font-size:23px;line-height:1.16;font-weight:700;color:#16253d;">{escape(title)}</h1>' if title else ''}
                {f'<p style="margin:0 0 16px;font-size:17px;line-height:1.5;color:#183b66;font-weight:700;">{escape(hook)}</p>' if hook else ''}
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 4px;">
                {''.join(f'<p style="margin:0 0 14px;font-size:16px;line-height:1.6;color:#324765;">{escape(item)}</p>' for item in body)}
              </td>
            </tr>
            <tr>
              <td style="padding:2px 28px 12px;">
                <a href="{escape(invite_link)}" style="display:block;width:100%;box-sizing:border-box;padding:16px 18px;border-radius:12px;background:#004494;color:#ffffff;text-decoration:none;font-size:16px;font-weight:700;text-align:center;">{escape(cta_label)}</a>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 18px;">
                <p style="margin:0;font-size:14px;line-height:1.6;color:#627892;">{escape(cta_note)}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 18px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border:1px solid #e7ecf4;border-radius:14px;background:#f8fbff;">
                  <tr>
                    <td style="padding:16px 18px;">
                      {f'<p style="margin:0 0 10px;font-size:14px;line-height:1.5;color:#183b66;font-weight:700;">{escape(info_title)}</p>' if info_title else ''}
                      {''.join(f'<p style="margin:0 0 8px;font-size:14px;line-height:1.5;color:#51627d;">• {escape(item)}</p>' for item in info_items)}
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 28px 24px;border-top:1px solid #e7ecf4;">
                {f'<p style="margin:0 0 10px;font-size:13px;line-height:1.6;color:#627892;">{escape(legal_intro)}</p>' if legal_intro else ''}
                {f'<p style="margin:0 0 10px;font-size:13px;line-height:1.6;color:#627892;">{escape(footer_network)}</p>' if footer_network else ''}
                <p style="margin:0 0 10px;font-size:13px;line-height:1.6;color:#627892;">Informations sur le traitement de vos données : <a href="{escape(privacy_url)}" style="color:#004494;">consulter la notice de confidentialité</a>.</p>
                <p style="margin:0;font-size:13px;line-height:1.6;color:#627892;">Cordialement,<br><br>{escape(signature_name)}<br>{escape(signature_role)}</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
    return subject, text_body, body_html


def build_brevo_invitation_email(invitation_row: dict, kind: str = 'initial') -> tuple[str, str, str, str]:
    """Build recipient, subject, text body and HTML body for one invitation."""
    role = _normalize_eures_invitation_role(invitation_row.get('role', ''))
    if role not in EURES_INVITATION_ALLOWED_ROLES:
        raise RuntimeError('Invitation role is missing or invalid.')
    recipient = normalize_email(invitation_row.get('email', ''))
    if not recipient:
        raise RuntimeError('Invitation email is missing.')

    language = str(invitation_row.get('language') or 'fr').strip().lower()
    if language not in {'fr', 'en', 'de'}:
        language = 'fr'
    invite_token = str(invitation_row.get('invite_token') or '').strip() or _generate_eures_invitation_token()
    invite_link = str(invitation_row.get('invite_link') or '').strip() or _build_eures_invitation_link(role, language, invite_token)
    signature_name = get_eures_mail_signature_name()
    signature_role = get_eures_mail_signature_role()
    privacy_url = get_eures_privacy_url(language)
    reminder_mode = kind == 'reminder'
    target_job_keys = _normalize_eures_invitation_target_job_keys(invitation_row.get('target_job_keys', '')) if role == 'candidate' else []
    target_job_labels = _eures_invitation_target_job_labels(target_job_keys, language) if role == 'candidate' else []
    if language == 'en':
        hello = "Hello,"
    elif language == 'de':
        hello = "Guten Tag,"
    else:
        hello = "Bonjour,"

    if role == 'employer':
        if language == 'en':
            if reminder_mode:
                subject = "[EURES / France Travail] Reminder: employer questionnaire"
                preheader = "A short follow-up if you still have a recruitment need to share with EURES beta."
                body_lines = [
                    "I am following up on my previous message regarding EURES beta.",
                    "If you still have a recruitment need to share, this short questionnaire helps us understand your criteria and identify potentially relevant profiles more quickly.",
                    "Completing it takes about 5 minutes.",
                ]
                title = "Employer questionnaire reminder"
                cta = "Access the questionnaire"
                cta_note = f"This questionnaire helps describe your recruitment need, your constraints and the proposed conditions. If the button does not work, copy this address into your browser: {invite_link}"
            else:
                subject = "[EURES / France Travail] Recruitment: identifying profiles suited to your need"
                preheader = "As part of my role as an EURES adviser within France Travail, I am contacting you to help identify suitable profiles more quickly."
                body_lines = [
                    "I am contacting you as part of my role as an EURES adviser within France Travail.",
                    "As part of an experiment carried out with EURES in the Greater Region, we support employers with recruitment needs by helping identify potentially suitable profiles more quickly.",
                    "If you have a current or upcoming recruitment need, I invite you to complete the short form below. It only takes a few minutes.",
                ]
                title = ""
                cta = "Access the questionnaire"
                cta_note = f"This questionnaire helps describe your recruitment need, your constraints and the proposed conditions in order to review possible introductions with relevant candidates. If the button does not work, copy this address into your browser: {invite_link}"
            footer = "EURES beta is an experimental service supported by EURES and France Travail to facilitate recruitment and professional mobility in the Greater Region."
        elif language == 'de':
            if reminder_mode:
                subject = "[EURES / France Travail] Erinnerung: Arbeitgeberfragebogen"
                preheader = "Kurze Erinnerung, falls Sie weiterhin einen Personalbedarf mit EURES beta teilen möchten."
                body_lines = [
                    "Ich melde mich erneut zu meiner vorherigen Nachricht zu EURES beta.",
                    "Wenn Sie weiterhin einen Personalbedarf haben, hilft uns dieser kurze Fragebogen dabei, Ihre Kriterien besser zu verstehen und schneller passende Profile zu identifizieren.",
                    "Das Ausfüllen dauert ungefähr 5 Minuten.",
                ]
                title = "Erinnerung zum Arbeitgeberfragebogen"
                cta = "Zum Fragebogen"
                cta_note = f"Mit diesem Fragebogen können Ihr Personalbedarf, Ihre Rahmenbedingungen und die angebotenen Bedingungen präzisiert werden. Falls die Schaltfläche nicht funktioniert, kopieren Sie diese Adresse in Ihren Browser: {invite_link}"
            else:
                subject = "[EURES / France Travail] Rekrutierung: passende Profile für Ihren Bedarf"
                preheader = "Im Rahmen meiner Tätigkeit als EURES-Berater bei France Travail kontaktiere ich Sie, um passende Profile schneller zu identifizieren."
                body_lines = [
                    "Ich kontaktiere Sie im Rahmen meiner Tätigkeit als EURES-Berater bei France Travail.",
                    "Im Rahmen eines gemeinsamen Experiments mit EURES in der Großregion unterstützen wir Arbeitgeber mit Personalbedarf dabei, potenziell passende Profile schneller zu identifizieren.",
                    "Wenn Sie einen aktuellen oder kommenden Personalbedarf haben, lade ich Sie ein, den kurzen Fragebogen unten auszufüllen. Das dauert nur wenige Minuten.",
                ]
                title = ""
                cta = "Zum Fragebogen"
                cta_note = f"Mit diesem Fragebogen können Ihr Personalbedarf, Ihre Rahmenbedingungen und die angebotenen Bedingungen präzisiert werden, um anschließend mögliche Vermittlungen mit passenden Kandidaten zu prüfen. Falls die Schaltfläche nicht funktioniert, kopieren Sie diese Adresse in Ihren Browser: {invite_link}"
            footer = "EURES beta ist ein experimenteller Service von EURES und France Travail zur Unterstützung von Rekrutierung und beruflicher Mobilität in der Großregion."
        else:
            if reminder_mode:
                subject = "[EURES / France Travail] Relance : questionnaire employeur"
                preheader = "Je me permets de revenir vers vous si vous avez toujours un besoin de recrutement a partager dans EURES beta."
                body_lines = [
                    "Je me permets de revenir vers vous concernant mon précédent message relatif à EURES beta.",
                    "Si vous avez toujours un besoin de recrutement à partager, ce court questionnaire nous permet de mieux comprendre vos critères et d'identifier plus rapidement des profils susceptibles de correspondre.",
                    "Il vous prendra seulement quelques minutes.",
                ]
                title = ""
                cta = "Accéder au questionnaire"
                cta_note = "Ce questionnaire permet de préciser votre besoin, vos contraintes de recrutement et les conditions proposées, afin d'étudier ensuite d'éventuelles mises en relation avec des candidats pertinents."
            else:
                subject = "[EURES / France Travail] Recrutement : identification de profils adaptes a votre besoin"
                preheader = "Dans le cadre de ma mission de conseiller EURES au sein de France Travail, je vous contacte pour vous proposer un repérage plus rapide de profils susceptibles de correspondre."
                body_lines = [
                    "Je me permets de vous contacter dans le cadre de ma mission de conseiller EURES au sein de France Travail.",
                    "Dans le cadre d'une expérimentation menée avec EURES dans la Grande Région, nous accompagnons des employeurs ayant des besoins de recrutement en leur proposant un repérage plus rapide de profils susceptibles de correspondre.",
                    "Si vous avez un besoin de recrutement en cours ou à venir, je vous invite à compléter le court formulaire ci-dessous. Il vous prendra seulement quelques minutes.",
                ]
                title = ""
                cta = "Accéder au formulaire"
                cta_note = "Ce questionnaire permet de préciser votre besoin, vos contraintes de recrutement et les conditions proposées, afin d'étudier ensuite d'éventuelles mises en relation avec des candidats pertinents."
            footer = (
                "EURES est le réseau européen de coopération pour l'emploi, qui facilite les recrutements "
                "et les opportunités professionnelles en Europe."
            )

        title_block = f"{title}\n\n" if title else ""
        title_html = (
            f'<h1 style="margin:0;font-size:28px;line-height:1.18;font-weight:700;color:#16253d;">{escape(title)}</h1>'
            if title else ''
        )
        text_body = (
            f"{hello}\n\n"
            f"{title_block}"
            + "\n\n".join(body_lines)
            + f"\n\n{cta}: {invite_link}\n\n{cta_note}\n\n{footer}\n\nInformations sur vos données : {privacy_url}\n\nCordialement,\n\n{signature_name}\n{signature_role}\n"
        )
        body_html = f"""
<!doctype html>
<html lang="{escape(language)}">
  <body style="margin:0;padding:0;background:#f5f7fb;font-family:Arial,'Helvetica Neue',sans-serif;color:#16253d;">
    <div style="display:none;max-height:0;overflow:hidden;opacity:0;mso-hide:all;">
      {escape(preheader)}
    </div>
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f5f7fb;padding:20px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:640px;background:#ffffff;border:1px solid #d9e1ee;border-radius:18px;overflow:hidden;">
            <tr>
              <td style="padding:22px 28px;background:#0f2742;color:#ffffff;">
                <div style="font-size:12px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;opacity:0.9;">EURES beta</div>
                <div style="margin-top:6px;font-size:14px;line-height:1.5;opacity:0.92;">EURES • France Travail</div>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 28px 8px;">
                <p style="margin:0 0 10px;font-size:16px;line-height:1.6;color:#324765;">{escape(hello)}</p>
                {title_html}
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 4px;">
                <p style="margin:0 0 14px;font-size:16px;line-height:1.55;color:#324765;">{escape(body_lines[0])}</p>
                <p style="margin:0 0 14px;font-size:16px;line-height:1.55;color:#324765;">{escape(body_lines[1])}</p>
                <p style="margin:0 0 22px;font-size:16px;line-height:1.55;color:#324765;">{escape(body_lines[2])}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 12px;">
                <a href="{escape(invite_link)}" style="display:block;width:100%;box-sizing:border-box;padding:15px 18px;border-radius:12px;background:#004494;color:#ffffff;text-decoration:none;font-size:16px;font-weight:700;text-align:center;">{escape(cta)}</a>
              </td>
            </tr>
            <tr>
              <td style="padding:0 28px 22px;">
                <p style="margin:0;font-size:14px;line-height:1.6;color:#627892;">{escape(cta_note)}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:18px 28px 24px;border-top:1px solid #e7ecf4;">
                <p style="margin:0 0 10px;font-size:13px;line-height:1.6;color:#627892;">{escape(footer)}</p>
                <p style="margin:0 0 10px;font-size:13px;line-height:1.6;color:#627892;">Informations sur le traitement de vos données : <a href="{escape(privacy_url)}" style="color:#004494;">consulter la notice de confidentialité</a>.</p>
                <p style="margin:0;font-size:13px;line-height:1.6;color:#627892;">Cordialement,<br><br>{escape(signature_name)}<br>{escape(signature_role)}</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
        return recipient, subject, text_body, body_html, invite_token, invite_link

    target_job_key = target_job_keys[0] if target_job_keys else ''
    subject, text_body, html_body = _build_eures_candidate_invitation_email(
        language=language,
        target_job_key=target_job_key,
        kind='reminder' if reminder_mode else 'initial',
        invite_link=invite_link,
        privacy_url=privacy_url,
        signature_name=signature_name,
        signature_role=signature_role,
        hello=hello,
    )
    return recipient, subject, text_body, html_body, invite_token, invite_link


def get_table_columns(config: dict, headers: dict) -> set[str]:
    """Fetch and cache table column ids to avoid sending unknown fields to Grist."""
    cache_key = (str(config.get('doc_id') or ''), str(config.get('table_id') or ''))
    cached = _TABLE_COLUMNS_CACHE.get(cache_key)
    now = time.time()
    if cached and (now - float(cached.get('loaded_at', 0))) < _TABLE_COLUMNS_CACHE_TTL_SECONDS:
        return set(cached.get('columns', set()))

    url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}/columns"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f'Failed to read table columns: HTTP {resp.status_code} - {resp.text}')
    payload = resp.json()
    columns = set()
    for col in payload.get('columns', []):
        col_id = (col or {}).get('id')
        if col_id:
            columns.add(str(col_id))
    _TABLE_COLUMNS_CACHE[cache_key] = {
        'columns': columns,
        'loaded_at': now,
    }
    return columns


def ensure_table_columns(config: dict, columns: set[str], headers: dict):
    """Create missing text columns in a Grist table, then refresh cache."""
    if not columns:
        return
    existing = get_table_columns(config, headers)
    missing = sorted(col for col in columns if col not in existing)
    if not missing:
        return

    url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}/columns"
    payload = {
        'columns': [
            {
                'id': column_id,
                'fields': {'label': column_id},
                'type': 'Text',
            }
            for column_id in missing
        ]
    }
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f'Failed to create columns in {config["table_id"]}: HTTP {resp.status_code} - {resp.text}')

    cache_key = (str(config.get('doc_id') or ''), str(config.get('table_id') or ''))
    _TABLE_COLUMNS_CACHE.pop(cache_key, None)


def _as_bool(value) -> bool:
    """Normalize truthy values from Grist fields."""
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    txt = str(value).strip().lower()
    return txt in {'1', 'true', 'vrai', 'oui', 'yes'}


def _has_value(value) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip() != ''


def _safe_json(value, fallback):
    if isinstance(value, str):
        txt = value.strip()
        if not txt:
            return fallback
        try:
            return json.loads(txt)
        except Exception:
            return fallback
    return value if value is not None else fallback


def _details_payload(fields: dict) -> dict:
    """Return parsed prestations_details_json payload as dict."""
    payload = _safe_json((fields or {}).get('prestations_details_json'), {})
    return payload if isinstance(payload, dict) else {}


def _details_get(payload: dict, path: tuple[str, ...], fallback=None):
    """Safely navigate a nested dict payload."""
    cur = payload
    for key in path:
        if not isinstance(cur, dict):
            return fallback
        cur = cur.get(key)
    return cur if cur is not None else fallback


def _has_any_checked(data: dict) -> bool:
    if not isinstance(data, dict):
        return False
    for v in data.values():
        if isinstance(v, dict):
            if _has_any_checked(v):
                return True
        elif _as_bool(v):
            return True
    return False


def _has_any_number_data(data) -> bool:
    if isinstance(data, dict):
        return any(_has_any_number_data(v) for v in data.values())
    if isinstance(data, list):
        return any(_has_any_number_data(v) for v in data)
    if data is None:
        return False
    txt = str(data).strip()
    if txt == '':
        return False
    try:
        return float(txt) >= 0
    except Exception:
        return False


def _format_conditional_display_name(raw_name: str) -> str:
    """Short admin-friendly label for conditional steps."""
    raw = str(raw_name or '').strip()
    if not raw:
        return ''
    parts = [part.strip() for part in raw.split(' - ') if part.strip()]
    if not parts:
        return raw
    if parts[0] == 'Directes ORP CDAPH':
        return 'Prestations directes: ' + ' > '.join(parts[1:]) if len(parts) > 1 else 'Prestations directes'
    if parts[0] == 'Directes hors ORP CDAPH':
        return 'Prestations directes sans ORP CDAPH: ' + ' > '.join(parts[1:]) if len(parts) > 1 else 'Prestations directes sans ORP CDAPH'
    if parts[0] == 'Indirectes':
        return 'Prestations indirectes: ' + ' > '.join(parts[1:]) if len(parts) > 1 else 'Prestations indirectes'
    return raw


def _split_export_path(path: str) -> list[str]:
    """Split flattened paths while keeping list indexes with their segment."""
    return [part for part in str(path or '').split('.') if part]


def _array_index(segment: str) -> tuple[str, int | None]:
    if '[' not in segment or not segment.endswith(']'):
        return segment, None
    name, _, raw_index = segment.partition('[')
    try:
        return name, int(raw_index[:-1]) - 1
    except Exception:
        return name, None


def humanize_export_field(key: str) -> str:
    """Label top-level Grist/export fields with user-facing wording where known."""
    raw = str(key or '')
    if raw in FIELD_LABELS:
        return FIELD_LABELS[raw]
    if raw.startswith('q') and '_' in raw:
        return raw.replace('_', ' ').upper()
    return raw.replace('_', ' ')


def humanize_export_path(path: str) -> str:
    """Turn flattened JSON paths into labels close to the form wording."""
    raw = str(path or '').strip()
    if not raw:
        return ''
    parts = _split_export_path(raw)
    if not parts:
        return humanize_export_field(raw)

    if parts[0] == 'coh' and len(parts) >= 2:
        block_key, index = _array_index(parts[1])
        title, labels = COH_LABELS.get(block_key, (humanize_export_field(block_key), []))
        if index is not None and 0 <= index < len(labels):
            return f'{title} - {labels[index]}'
        return title

    first_name, first_index = _array_index(parts[0])

    if first_name == 'geoRows' and len(parts) >= 2:
        _, index = _array_index(parts[0])
        suffix = EXPORT_KEY_LABELS.get(parts[1], humanize_export_field(parts[1]))
        prefix = f'Géographie ligne {index + 1}' if index is not None else 'Géographie'
        return f'{prefix} - {suffix}'

    if first_name == 'handicapMatrix' and len(parts) >= 2:
        handicap = HANDICAP_TYPES[first_index] if first_index is not None and 0 <= first_index < len(HANDICAP_TYPES) else 'Type de handicap'
        col = EXPORT_KEY_LABELS.get(parts[1], humanize_export_field(parts[1]))
        return f'Type de handicap principal et associé - {handicap} - {col}'

    if parts[0] in {'directAvecOrp', 'directSansOrp', 'indirect', 'pecFileActive', 'preconisationsBloc', 'sortiesBloc', 'suspensionsBloc', 'orienteursBloc', 'formationsSelection'}:
        group_labels = {
            'directAvecOrp': 'Prestations directes avec ORP CDAPH',
            'directSansOrp': 'Prestations directes sans ORP CDAPH',
            'indirect': 'Prestations indirectes',
            'pecFileActive': 'File active PEC',
            'preconisationsBloc': 'Préconisations lors de la sortie définitive',
            'sortiesBloc': 'Sortie définitive avant le terme de la prestation',
            'suspensionsBloc': 'Suspensions',
            'orienteursBloc': 'Orienteurs',
            'formationsSelection': 'Sélection des formations',
        }
        cleaned = []
        for part in parts[1:]:
            name, index = _array_index(part)
            if name in {'row', 'rows', 'raisons'}:
                continue
            label = EXPORT_KEY_LABELS.get(name, humanize_export_field(name))
            if index is not None:
                label = f'{label} {index + 1}'
            cleaned.append(label)
        return ' - '.join([group_labels[parts[0]], *cleaned])

    if len(parts) == 1:
        name, index = _array_index(parts[0])
        label = EXPORT_KEY_LABELS.get(name, humanize_export_field(name))
        return f'{label} {index + 1}' if index is not None else label

    return ' - '.join(EXPORT_KEY_LABELS.get(_array_index(part)[0], humanize_export_field(_array_index(part)[0])) for part in parts)


def should_skip_readable_export_path(path: str) -> bool:
    """Hide internal navigation/state fields that are not useful in a user-readable export."""
    first = _array_index(_split_export_path(path)[0])[0] if _split_export_path(path) else ''
    return first in {
        'visitedBlocks',
        'currentConditionalId',
        'focusedConditionalStepId',
        'focusedConditionalBlockKey',
        'autoCollapsePrimaryAfterPrestations',
    }


def _xlsx_safe_value(value):
    """Return a spreadsheet-friendly scalar without raw JSON objects."""
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Oui' if value else 'Non'
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _flatten_for_xlsx(value, prefix=''):
    """Flatten nested JSON as readable path/value rows."""
    rows = []
    if isinstance(value, dict):
        if not value:
            rows.append((prefix, ''))
        for key, child in value.items():
            path = f'{prefix}.{key}' if prefix else str(key)
            rows.extend(_flatten_for_xlsx(child, path))
    elif isinstance(value, list):
        if not value:
            rows.append((prefix, ''))
        for idx, child in enumerate(value, start=1):
            path = f'{prefix}[{idx}]' if prefix else f'[{idx}]'
            rows.extend(_flatten_for_xlsx(child, path))
    else:
        rows.append((prefix, _xlsx_safe_value(value)))
    return rows


def _append_table(ws, headers, rows):
    ws.append(headers)
    for row in rows:
        ws.append([_xlsx_safe_value(cell) for cell in row])
    for cell in ws[1]:
        cell.style = 'Headline 4'
    ws.freeze_panes = 'A2'
    for column_cells in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in column_cells)
        width = min(max(max_len + 2, 12), 80)
        ws.column_dimensions[column_cells[0].column_letter].width = width


def _new_sheet(workbook, title):
    safe = ''.join(ch for ch in str(title or 'Feuille') if ch not in r'[]:*?/\\')[:31] or 'Feuille'
    if safe in workbook.sheetnames:
        base = safe[:27]
        i = 2
        while f'{base} {i}' in workbook.sheetnames:
            i += 1
        safe = f'{base} {i}'
    return workbook.create_sheet(safe)


def build_readable_xlsx(payload: dict) -> BytesIO:
    """Build a human-readable workbook from the current form payload, leaving Grist JSON intact."""
    from openpyxl import Workbook

    fields = payload.get('fields') if isinstance(payload, dict) else {}
    fields = fields if isinstance(fields, dict) else {}

    wb = Workbook()
    wb.remove(wb.active)

    summary_rows = [
        ('Date export', payload.get('exported_at', '')),
        ('UUID', payload.get('uuid', fields.get('uuid', ''))),
        ('Formulaire', payload.get('form_id', '')),
    ]
    for key in sorted(fields):
        if key in JSON_EXPORT_COLUMNS:
            continue
        summary_rows.append((humanize_export_field(key), fields.get(key)))
    _append_table(_new_sheet(wb, 'Synthese'), ['Champ', 'Valeur'], summary_rows)

    metiers = _safe_json(fields.get('metiers_json'), [])
    if isinstance(metiers, list):
        rows = [
            (
                item.get('metier', ''),
                item.get('mode', ''),
                item.get('etp', ''),
                item.get('etpCdi', ''),
                item.get('etpCdd', ''),
            )
            for item in metiers
            if isinstance(item, dict)
        ]
        _append_table(_new_sheet(wb, 'Metiers'), ['Métier', 'Mode', 'ETP', 'ETP CDI', 'ETP CDD'], rows)

    formations = _safe_json(fields.get('catalogue_formations_json'), [])
    if isinstance(formations, list):
        rows = [
            (
                item.get('nom', ''),
                item.get('niveau', ''),
                item.get('secteur', ''),
                item.get('nb', ''),
            )
            for item in formations
            if isinstance(item, dict)
        ]
        _append_table(_new_sheet(wb, 'Formations'), ['Formation', 'Niveau', 'Secteur', 'Nombre'], rows)

    prestations = _safe_json(fields.get('prestations_json'), {})
    prestation_rows = []
    if isinstance(prestations, dict):
        for section_key, section in prestations.items():
            if not isinstance(section, dict):
                continue
            label = _format_conditional_display_name(section_key)
            prestation_rows.append((label, humanize_export_path('done'), section.get('done', '')))
            for path, value in _flatten_for_xlsx(section):
                if path in {'done'} or should_skip_readable_export_path(path):
                    continue
                prestation_rows.append((label, humanize_export_path(path), value))
    _append_table(_new_sheet(wb, 'Prestations'), ['Section', 'Champ', 'Valeur'], prestation_rows)

    details = _details_payload(fields)
    wizard = details.get(WIZARD_STATE_KEY) if isinstance(details, dict) else {}
    runtime = wizard.get('runtime') if isinstance(wizard, dict) else {}
    conditional_defs = runtime.get('conditionalDefs') if isinstance(runtime, dict) else []
    conditional_state = runtime.get('conditionalState') if isinstance(runtime, dict) else {}
    conditional_rows = []
    if isinstance(conditional_defs, list) and isinstance(conditional_state, dict):
        for item in conditional_defs:
            if not isinstance(item, dict):
                continue
            cond_id = str(item.get('id') or '')
            name = _format_conditional_display_name(item.get('name') or cond_id)
            state = conditional_state.get(cond_id, {})
            if not isinstance(state, dict):
                continue
            conditional_rows.append((name, humanize_export_path('done'), state.get('done', '')))
            for path, value in _flatten_for_xlsx(state):
                if path == 'done' or should_skip_readable_export_path(path):
                    continue
                conditional_rows.append((name, humanize_export_path(path), value))
    _append_table(_new_sheet(wb, 'Etapes conditionnelles'), ['Étape', 'Champ', 'Valeur'], conditional_rows)

    selection_rows = []
    for column in ['prestations_orp_json', 'prestations_indirectes_json', 'finess_json']:
        parsed = _safe_json(fields.get(column), {})
        for path, value in _flatten_for_xlsx(parsed, column):
            selection_rows.append((humanize_export_path(path), value))
    _append_table(_new_sheet(wb, 'Selections'), ['Champ', 'Valeur'], selection_rows)

    out = BytesIO()
    wb.save(out)
    out.seek(0)
    return out


def compute_quick_step_progress(fields: dict) -> dict:
    """
    Fast progress estimator by major sections.
    Returns counts + list of done/remaining step labels.
    """
    finess_values = extract_finess_values(fields)
    identification_done = (
        _has_value(fields.get('es_nom'))
        and _has_value(fields.get('validateur_email'))
        and _has_value(fields.get('es_departement'))
        and len(finess_values) > 0
    )

    selected_dispositifs = [
        _as_bool(fields.get('check_esrp')),
        _as_bool(fields.get('check_espo')),
        _as_bool(fields.get('check_ueros')),
        _as_bool(fields.get('check_deac')),
    ]
    rh_done = any(selected_dispositifs) and _has_value(fields.get('metiers_json'))

    details_json = _details_payload(fields)
    prestations_orp_legacy = _safe_json(fields.get('prestations_orp_json'), {})
    prestations_orp_canonical = _details_get(details_json, ('prestations', 'selection', 'orp'), {})
    prestations_orp = {}
    if isinstance(prestations_orp_canonical, dict):
        prestations_orp.update(prestations_orp_canonical)
    if isinstance(prestations_orp_legacy, dict):
        prestations_orp.update(prestations_orp_legacy)
    vos_prestations_done = _has_value(fields.get('pec')) or _has_any_checked(prestations_orp)

    contexte_done = (
        _has_value(fields.get('q32_implantation'))
        and _has_value(fields.get('q33_transports'))
        and _has_value(fields.get('q53_afpa'))
    )

    steps = [
        ('Identification', identification_done),
        ('Volet RH', rh_done),
        ('Vos prestations', vos_prestations_done),
        ('Contexte écologique', contexte_done),
    ]

    # Conditional quick estimator.
    cond_expected_labels = []
    cond_done_labels = []
    wizard_runtime = _details_get(details_json, (WIZARD_STATE_KEY, 'runtime'), {})

    if isinstance(wizard_runtime, dict):
        runtime_defs = wizard_runtime.get('conditionalDefs')
        runtime_state = wizard_runtime.get('conditionalState')
        if isinstance(runtime_defs, list) and isinstance(runtime_state, dict):
            for item in runtime_defs:
                if not isinstance(item, dict):
                    continue
                cond_id = str(item.get('id') or '').strip()
                cond_name = _format_conditional_display_name(str(item.get('name') or '').strip())
                if not cond_id or not cond_name:
                    continue
                cond_expected_labels.append(cond_name)
                state = runtime_state.get(cond_id)
                if isinstance(state, dict) and (_as_bool(state.get('done')) or _as_bool(state.get('__completed'))):
                    cond_done_labels.append(cond_name)

    if not cond_expected_labels:
        if _as_bool(fields.get('check_esrp')):
            cond_expected_labels.append('Prestations totales ESRP')
        if _as_bool(fields.get('check_espo')):
            cond_expected_labels.append('Prestations totales ESPO')
        if _as_bool(fields.get('check_ueros')):
            cond_expected_labels.append('Prestations totales UEROS')
        if _as_bool(fields.get('check_deac')):
            cond_expected_labels.append('Prestations totales DEAc')

        prestations_json = _safe_json(fields.get('prestations_json'), {})
        prestations_json_canonical = _details_get(details_json, ('prestations', 'conditional', 'state_by_key'), {})
        if (not isinstance(prestations_json, dict) or not prestations_json) and isinstance(prestations_json_canonical, dict):
            prestations_json = prestations_json_canonical
        if isinstance(prestations_json, dict):
            if _has_any_number_data(prestations_json.get('esrp')):
                cond_done_labels.append('Prestations totales ESRP')
            if _has_any_number_data(prestations_json.get('espo')):
                cond_done_labels.append('Prestations totales ESPO')
            if _has_any_number_data(prestations_json.get('ueros')):
                cond_done_labels.append('Prestations totales UEROS')
            if _has_any_number_data(prestations_json.get('deac')):
                cond_done_labels.append('Prestations totales DEAc')

        orp_map = {
            'orp_pec': 'Prestation ORP: PEC',
            'orp_autre_eval': "Prestation ORP: Autre dispositif d'évaluation",
            'orp_orientation_espo': 'Prestation ORP: Orientation ESPO',
            'orp_parcours_sociopro': 'Prestation ORP: Parcours socio-professionnel',
            'orp_autre_parcours': 'Prestation ORP: Autre type de parcours',
            'orp_parcours_qualif': 'Prestation ORP: Parcours certifiant',
            'orp_remise_niveau': 'Prestation ORP: Remise à niveau',
            'orp_formation_pro': 'Prestation ORP: Formation professionnalisante',
            'orp_formation_certif': 'Prestation ORP: Formation certifiante',
            'orp_formation_accomp_pro': 'Prestation ORP: Formation accompagnée pro',
            'orp_formation_accomp_certif': 'Prestation ORP: Formation accompagnée certifiante',
        }
        selected_orp_keys = []
        if isinstance(prestations_orp, dict):
            for key, label in orp_map.items():
                if _as_bool(prestations_orp.get(key)):
                    selected_orp_keys.append((key, label))
                    cond_expected_labels.append(label)

        if isinstance(details_json, dict):
            for key, label in selected_orp_keys:
                state = details_json.get(key, {})
                if not isinstance(state, dict):
                    state = {}
                # New canonical location (schema v2)
                if not state:
                    canonical_state = _details_get(details_json, ('prestations', 'conditional', 'state_by_key', key), {})
                    if isinstance(canonical_state, dict):
                        state = canonical_state
                if isinstance(state, dict) and _as_bool(state.get('__completed')):
                    cond_done_labels.append(label)

    done_main = sum(1 for _, ok in steps if ok)
    total_main = len(steps)
    done_main_labels = [label for label, ok in steps if ok]
    remaining_main = [label for label, ok in steps if not ok]

    cond_expected_labels = list(dict.fromkeys(cond_expected_labels))
    cond_done_labels = list(dict.fromkeys(cond_done_labels))
    remaining_cond = [label for label in cond_expected_labels if label not in cond_done_labels]

    return {
        'main': {
            'done': done_main,
            'total': total_main,
            'done_labels': done_main_labels,
            'remaining_labels': remaining_main,
        },
        'conditional': {
            'done': len(cond_done_labels),
            'total': len(cond_expected_labels),
            'done_labels': cond_done_labels,
            'remaining_labels': remaining_cond,
        },
    }


def fetch_all_records(config: dict, headers: dict):
    """Fetch records for a form table (single pass, up to 5000 rows)."""
    url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}/records"
    resp = requests.get(url, params={'limit': 5000}, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f'Failed to read records: HTTP {resp.status_code} - {resp.text}')
    payload = resp.json()
    return payload.get('records', [])


def _parse_response_json_safe(resp):
    """Return JSON payload when possible, otherwise a readable fallback dict."""
    try:
        return resp.json()
    except Exception:
        body = (resp.text or '').strip()
        return {
            'error': f'Upstream response is not valid JSON (HTTP {resp.status_code}).',
            'raw': body[:500],
        }


def fetch_record_by_field(base_url: str, field_name: str, value: str, headers: dict):
    """Fetch a single record by a unique field from Grist."""
    filter_param = json.dumps({field_name: [value]})
    resp = requests.get(f"{base_url}/records", params={'filter': filter_param}, headers=headers)
    if resp.status_code != 200:
        return None, resp

    payload = _parse_response_json_safe(resp)
    if not isinstance(payload, dict) or not isinstance(payload.get('records'), list):
        raise RuntimeError('Failed to decode Grist record lookup response.')
    return payload['records'][0] if payload['records'] else None, resp


def resolve_record_key(allowed_columns: set[str]) -> str | None:
    """Pick the unique key used to upsert records for a target table."""
    if 'uuid' in allowed_columns:
        return 'uuid'
    if 'id_tally' in allowed_columns:
        return 'id_tally'
    return None


def _grist_write_redirect_response(resp):
    """Return a readable error when an upstream write endpoint redirects."""
    if not 300 <= resp.status_code < 400:
        return None

    source = str(getattr(resp, 'url', '') or '').strip()
    location = str(resp.headers.get('Location') or '').strip()
    source_part = f' Source URL: {source}.' if source else ''
    suffix = f' Redirect target: {location}' if location else ''
    return jsonify({
        'error': (
            f'Grist write endpoint redirected with HTTP {resp.status_code}. '
            f'Check GRIST_BASE_URL in production.{source_part}{suffix}'
        ),
    }), 502


def write_grist_records(method: str, url: str, payload: dict, headers: dict, max_redirects: int = 3):
    """Follow Grist write redirects while preserving the HTTP method and cookies."""
    current_url = url
    with requests.Session() as session:
        for _ in range(max_redirects + 1):
            resp = session.request(
                method,
                current_url,
                json=payload,
                headers=headers,
                allow_redirects=False,
            )
            if not 300 <= resp.status_code < 400:
                return resp

            location = str(resp.headers.get('Location') or '').strip()
            if not location:
                return resp
            current_url = urljoin(current_url, location)

    return resp


def fetch_table_records(doc_id: str, table_id: str, headers: dict, limit: int = 5000):
    """Read records from a Grist table."""
    url = f"{GRIST_BASE_URL}/api/docs/{doc_id}/tables/{table_id}/records"
    resp = requests.get(url, params={'limit': limit}, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f'Failed to read {table_id}: HTTP {resp.status_code} - {resp.text}')
    payload = _parse_response_json_safe(resp)
    return payload.get('records', []) if isinstance(payload, dict) else []


def _month_key(value) -> str | None:
    """Extract YYYY-MM from common timestamp/date values."""
    txt = str(value or '').strip()
    if len(txt) >= 7 and txt[4] == '-':
        return txt[:7]
    for fmt in (
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d',
        '%Y/%m/%d',
        '%d/%m/%Y',
    ):
        try:
            return datetime.strptime(txt, fmt).strftime('%Y-%m')
        except Exception:
            continue
    return None


def _parse_datetime(value) -> datetime | None:
    txt = str(value or '').strip()
    if not txt:
        return None
    try:
        return datetime.fromisoformat(txt.replace('Z', '+00:00'))
    except Exception:
        pass
    for fmt in (
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%d',
    ):
        try:
            return datetime.strptime(txt, fmt)
        except Exception:
            continue
    return None


def _days_since(value, now: datetime | None = None) -> int | None:
    dt = _parse_datetime(value)
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ref = now or datetime.now(timezone.utc)
    return max((ref - dt).days, 0)


def _eures_invitation_needs_reminder(fields: dict, now: datetime | None = None) -> bool:
    if not isinstance(fields, dict):
        return False
    if str(fields.get('invitation_status') or '').strip().lower() != 'invitation_envoyee':
        return False
    if str(fields.get('answered_at') or '').strip():
        return False
    sent_at = fields.get('sent_at')
    days_since_sent = _days_since(sent_at, now=now)
    if days_since_sent is None:
        return False
    return days_since_sent >= get_eures_invitation_reminder_delay_days()


def _duration_hours(start_value, end_value) -> float | None:
    start = _parse_datetime(start_value)
    end = _parse_datetime(end_value)
    if not start or not end:
        return None
    delta_seconds = (end - start).total_seconds()
    if delta_seconds < 0:
        return None
    return delta_seconds / 3600.0


def _duration_summary(values: list[float]) -> dict:
    ordered = sorted(v for v in values if v is not None)
    if not ordered:
        return {'count': 0, 'avg_hours': None, 'median_hours': None, 'min_hours': None, 'max_hours': None}
    count = len(ordered)
    middle = count // 2
    median = ordered[middle] if count % 2 else (ordered[middle - 1] + ordered[middle]) / 2.0
    return {
        'count': count,
        'avg_hours': round(sum(ordered) / count, 1),
        'median_hours': round(median, 1),
        'min_hours': round(ordered[0], 1),
        'max_hours': round(ordered[-1], 1),
    }


def _split_multi_value(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = str(value).split('|')
    return [str(item).strip() for item in raw_items if str(item).strip()]


def _clean_public_label(label: str) -> str:
    return ' '.join(str(label or '').strip().split())


def _public_breakdown_label(kind: str, label: str) -> str:
    """Normalize raw stored values into cleaner public labels."""
    cleaned = _clean_public_label(label)
    lowered = cleaned.lower()
    humanized = cleaned.replace('_', ' ')

    if kind == 'matchings_par_statut':
        return {
            'calcule': 'Calcule',
            'a_valider_admin': 'A valider admin',
            'refuse_admin': 'Refuse admin',
            'valide_admin': 'Valide admin',
            'envoye_employeur': 'Envoye employeur',
            'accepte_employeur': 'Accepte employeur',
            'refuse_employeur': 'Refuse employeur',
            'mise_en_relation_faite': 'Mise en relation faite',
            'embauche_confirmee': 'Embauche confirmee',
            'a_valider': 'A valider',
        }.get(lowered, humanized[:1].upper() + humanized[1:])

    if kind == 'mobilite_candidats':
        if ':' in cleaned:
            prefix, raw_value = [part.strip() for part in cleaned.split(':', 1)]
            prefix_l = prefix.lower()
            if prefix_l == 'type':
                return raw_value
            if prefix_l in {'pays souhaités', 'pays souhaites'}:
                return f'Pays vises : {raw_value}'
            if prefix_l in {'expérience pays', 'experience pays'}:
                return f'Experience dans : {raw_value}'
        return cleaned[:1].upper() + cleaned[1:]

    if kind == 'experience_internationale_candidats':
        if ':' in cleaned:
            prefix, raw_value = [part.strip() for part in cleaned.split(':', 1)]
            prefix_l = prefix.lower()
            if prefix_l in {'expérience pays', 'experience pays'}:
                return f'Experience dans : {raw_value}'
        return cleaned[:1].upper() + cleaned[1:]

    if kind == 'retours_employeurs':
        return {
            'contact': 'Accepté par employeur',
            'not_contact': 'Refusé par employeur',
            'no_response': 'Sans réponse',
        }.get(lowered, cleaned[:1].upper() + cleaned[1:])

    return cleaned


def _counter_to_rows(counter: Counter) -> list[dict]:
    """Convert a counter to public rows without collapsing categories."""
    return [
        {'label': label, 'count': count}
        for label, count in sorted(counter.items(), key=lambda item: (-item[1], str(item[0]).lower()))
    ]


def _add_public_counter(counter: Counter, kind: str, raw_label: str):
    public_label = _public_breakdown_label(kind, raw_label)
    if public_label:
        counter[public_label] += 1


def _eures_public_sector_labels(value) -> list[str]:
    sectors = eures_candidate_sectors(str(value or ''))
    return [
        EURES_PUBLIC_SECTOR_LABELS[sector]
        for sector in EURES_PUBLIC_SECTOR_LABELS
        if sector in sectors
    ]


def _eures_public_mobility_labels(value) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for part in _split_multi_value(value):
        if ':' in part:
            prefix, raw_values = [chunk.strip() for chunk in part.split(':', 1)]
            values = [item.strip() for item in raw_values.split(',') if item.strip()]
            if not values:
                values = [raw_values.strip()] if raw_values.strip() else []
            for item in values:
                if prefix.lower() == 'type':
                    label = item
                elif prefix.lower() in {'pays souhaités', 'pays souhaites'}:
                    label = f'Pays vises : {item}'
                else:
                    continue
                if label and label not in seen:
                    seen.add(label)
                    labels.append(label)
        else:
            for item in [chunk.strip() for chunk in str(part).split(',') if chunk.strip()]:
                if item and item not in seen:
                    seen.add(item)
                    labels.append(item)
    return labels


def _eures_public_experience_labels(value) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    for part in _split_multi_value(value):
        if ':' not in part:
            continue
        prefix, raw_values = [chunk.strip() for chunk in part.split(':', 1)]
        if prefix.lower() not in {'expérience pays', 'experience pays'}:
            continue
        values = [item.strip() for item in raw_values.split(',') if item.strip()]
        if not values:
            values = [raw_values.strip()] if raw_values.strip() else []
        for item in values:
            label = f'Experience dans : {item}'
            if label and label not in seen:
                seen.add(label)
                labels.append(label)
    return labels


def _safe_int(value) -> int:
    try:
        return int(float(value or 0))
    except Exception:
        return 0


def build_eures_public_stats() -> dict:
    """Build a public, non-nominative stats payload for EURES beta."""
    candidate_config = get_form_config('eures-beta', 'candidate')
    employer_config = get_form_config('eures-beta', 'employer')
    if not candidate_config or not employer_config:
        raise RuntimeError('EURES beta candidate/employer Grist configuration is incomplete.')

    candidate_headers = {'Accept': 'application/json'}
    if candidate_config.get('api_key'):
        candidate_headers['Authorization'] = f"Bearer {candidate_config['api_key']}"

    employer_headers = {'Accept': 'application/json'}
    if employer_config.get('api_key'):
        employer_headers['Authorization'] = f"Bearer {employer_config['api_key']}"

    candidats = fetch_table_records(candidate_config['doc_id'], EURES_CANDIDATS_TABLE, candidate_headers)
    besoins = fetch_table_records(employer_config['doc_id'], EURES_BESOINS_TABLE, employer_headers)
    matchings = fetch_table_records(candidate_config['doc_id'], EURES_MATCHINGS_TABLE, candidate_headers)
    invitations = list_eures_invitations()

    monthly: dict[str, dict[str, int | str]] = defaultdict(lambda: {
        'mois': '',
        'candidats': 0,
        'besoins_employeurs': 0,
        'matchings': 0,
        'candidats_contactes': 0,
        'candidatures_transmises_employeur': 0,
        'contacts_acceptes_employeur': 0,
        'contacts_refuses_employeur': 0,
        'contacts_sans_reponse_employeur': 0,
        'embauches': 0,
    })

    besoins_par_pays = Counter()
    secteurs = Counter()
    mobilite_candidats = Counter()
    experience_internationale_candidats = Counter()
    matchings_par_statut = Counter()
    retours_employeurs = Counter()
    delays = {
        'calcul_to_admin': [],
        'admin_to_send': [],
        'send_to_employer_response': [],
        'response_to_relation': [],
        'relation_to_hire': [],
    }
    active_candidate_keys = {
        str((rec.get('fields') or {}).get('id_tally') or (rec.get('fields') or {}).get('uuid') or '').strip()
        for rec in candidats if isinstance(rec, dict) and _is_eures_response_active((rec.get('fields') or {}))
    }
    active_employer_keys = {
        str((rec.get('fields') or {}).get('id_tally') or (rec.get('fields') or {}).get('uuid') or '').strip()
        for rec in besoins if isinstance(rec, dict) and _is_eures_response_active((rec.get('fields') or {}))
    }

    for rec in candidats:
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        month = _month_key(fields.get('tally_submitted_at'))
        if month:
            monthly[month]['mois'] = month
            monthly[month]['candidats'] += 1
        for label in _eures_public_sector_labels(fields.get('metier')):
            _add_public_counter(secteurs, 'secteurs', label)
        for label in _eures_public_mobility_labels(fields.get('mobilite')):
            _add_public_counter(mobilite_candidats, 'mobilite_candidats', label)
        for label in _eures_public_experience_labels(fields.get('mobilite')):
            _add_public_counter(experience_internationale_candidats, 'experience_internationale_candidats', label)

    for rec in besoins:
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        month = _month_key(fields.get('tally_submitted_at'))
        if month:
            monthly[month]['mois'] = month
            monthly[month]['besoins_employeurs'] += 1
        for label in _split_multi_value(fields.get('pays_normalise')):
            _add_public_counter(besoins_par_pays, 'besoins_par_pays', label)
        for label in _eures_public_sector_labels(fields.get('poste')):
            _add_public_counter(secteurs, 'secteurs', label)

    for row in invitations:
        if str(row.get('role') or '').strip().lower() != 'candidate':
            continue
        if str(row.get('invitation_status') or '').strip().lower() != 'invitation_envoyee':
            continue
        sent_month = _month_key(row.get('sent_at'))
        if sent_month:
            monthly[sent_month]['mois'] = sent_month
            monthly[sent_month]['candidats_contactes'] += 1

    for rec in matchings:
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        candidat_id = str(fields.get('candidat_id') or '').strip()
        besoin_id = str(fields.get('besoin_id') or '').strip()
        if candidat_id not in active_candidate_keys or besoin_id not in active_employer_keys:
            continue
        month = _month_key(fields.get('date_calcul'))
        if month:
            monthly[month]['mois'] = month
            monthly[month]['matchings'] += 1
        workflow_status = _matching_workflow_status(fields)
        if workflow_status:
            _add_public_counter(matchings_par_statut, 'matchings_par_statut', workflow_status)

        sent_month = _month_key(fields.get('sent_to_employer_at'))
        if sent_month:
            monthly[sent_month]['mois'] = sent_month
            monthly[sent_month]['candidatures_transmises_employeur'] += 1

        relation_month = _month_key(fields.get('mise_en_relation_at'))
        if relation_month:
            monthly[relation_month]['mois'] = relation_month
            monthly[relation_month]['candidats_contactes'] += 1

        hire_month = _month_key(fields.get('embauche_confirmee_at'))
        if hire_month:
            monthly[hire_month]['mois'] = hire_month
            monthly[hire_month]['embauches'] += 1

        response_bucket = None
        response_month = None
        if workflow_status in {'accepte_employeur', 'mise_en_relation_faite', 'embauche_confirmee'}:
            response_bucket = 'contact'
            response_month = _month_key(fields.get('employer_response_at') or fields.get('mise_en_relation_at') or fields.get('embauche_confirmee_at'))
        elif workflow_status == 'refuse_employeur':
            response_bucket = 'not_contact'
            response_month = _month_key(fields.get('employer_response_at'))
        elif workflow_status == 'envoye_employeur':
            response_bucket = 'no_response'
            response_month = sent_month

        if response_bucket:
            _add_public_counter(retours_employeurs, 'retours_employeurs', response_bucket)
            if response_month:
                monthly[response_month]['mois'] = response_month
                if response_bucket == 'contact':
                    monthly[response_month]['contacts_acceptes_employeur'] += 1
                elif response_bucket == 'not_contact':
                    monthly[response_month]['contacts_refuses_employeur'] += 1
                else:
                    monthly[response_month]['contacts_sans_reponse_employeur'] += 1

        duration = _duration_hours(fields.get('date_calcul'), fields.get('admin_decision_at'))
        if duration is not None:
            delays['calcul_to_admin'].append(duration)
        duration = _duration_hours(fields.get('admin_decision_at'), fields.get('sent_to_employer_at'))
        if duration is not None:
            delays['admin_to_send'].append(duration)
        duration = _duration_hours(fields.get('sent_to_employer_at'), fields.get('employer_response_at'))
        if duration is not None:
            delays['send_to_employer_response'].append(duration)
        duration = _duration_hours(fields.get('employer_response_at'), fields.get('mise_en_relation_at'))
        if duration is not None:
            delays['response_to_relation'].append(duration)
        duration = _duration_hours(fields.get('mise_en_relation_at'), fields.get('embauche_confirmee_at'))
        if duration is not None:
            delays['relation_to_hire'].append(duration)

    manual_stats_available = False
    stats_config = get_eures_stats_config()
    if stats_config:
        stats_headers = {'Accept': 'application/json'}
        if stats_config.get('api_key'):
            stats_headers['Authorization'] = f"Bearer {stats_config['api_key']}"
        try:
            manual_rows = fetch_table_records(stats_config['doc_id'], stats_config['table_id'], stats_headers)
            manual_stats_available = True
        except Exception:
            manual_rows = []
        for rec in manual_rows:
            fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
            month = _month_key(fields.get('mois'))
            if not month:
                continue
            monthly[month]['mois'] = month
            monthly[month]['candidats_contactes'] += _safe_int(fields.get('candidats_contactes'))
            monthly[month]['candidatures_transmises_employeur'] += _safe_int(fields.get('candidatures_transmises_employeur'))
            monthly[month]['contacts_acceptes_employeur'] += _safe_int(fields.get('contacts_acceptes_employeur'))
            monthly[month]['contacts_refuses_employeur'] += _safe_int(fields.get('contacts_refuses_employeur'))
            monthly[month]['contacts_sans_reponse_employeur'] += _safe_int(fields.get('contacts_sans_reponse_employeur'))
            monthly[month]['embauches'] += _safe_int(fields.get('embauches'))

    monthly_rows = [row for _, row in sorted(monthly.items()) if row.get('mois')]

    totals = {
        'candidats': len(candidats),
        'besoins_employeurs': len(besoins),
        'matchings': len(matchings),
        'candidats_contactes': sum(int(row['candidats_contactes']) for row in monthly_rows),
        'candidatures_transmises_employeur': sum(int(row['candidatures_transmises_employeur']) for row in monthly_rows),
        'contacts_acceptes_employeur': sum(int(row['contacts_acceptes_employeur']) for row in monthly_rows),
        'contacts_refuses_employeur': sum(int(row['contacts_refuses_employeur']) for row in monthly_rows),
        'contacts_sans_reponse_employeur': sum(int(row['contacts_sans_reponse_employeur']) for row in monthly_rows),
        'embauches': sum(int(row['embauches']) for row in monthly_rows),
    }

    return {
        'ok': True,
        'generated_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'manual_stats_table': {
            'configured': manual_stats_available,
            'table_id': stats_config['table_id'] if stats_config else None,
        },
        'totals': totals,
        'durations': {
            'calcul_to_admin': _duration_summary(delays['calcul_to_admin']),
            'admin_to_send': _duration_summary(delays['admin_to_send']),
            'send_to_employer_response': _duration_summary(delays['send_to_employer_response']),
            'response_to_relation': _duration_summary(delays['response_to_relation']),
            'relation_to_hire': _duration_summary(delays['relation_to_hire']),
        },
        'monthly': monthly_rows,
        'breakdowns': {
            'besoins_par_pays': _counter_to_rows(besoins_par_pays),
            'secteurs': _counter_to_rows(secteurs),
            'mobilite_candidats': _counter_to_rows(mobilite_candidats),
            'experience_internationale_candidats': _counter_to_rows(experience_internationale_candidats),
            'matchings_par_statut': _counter_to_rows(matchings_par_statut),
            'retours_employeurs': _counter_to_rows(retours_employeurs),
        },
    }


def fetch_matching_record(doc_id: str, besoin_id: str, candidat_id: str, headers: dict):
    """Read one matching by besoin_id/candidat_id pair."""
    url = f"{GRIST_BASE_URL}/api/docs/{doc_id}/tables/{EURES_MATCHINGS_TABLE}/records"
    filter_param = json.dumps({'besoin_id': [besoin_id], 'candidat_id': [candidat_id]})
    resp = requests.get(url, params={'filter': filter_param}, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f'Failed to read Matchings: HTTP {resp.status_code} - {resp.text}')
    payload = _parse_response_json_safe(resp)
    records = payload.get('records', []) if isinstance(payload, dict) else []
    return records[0] if records else None


def upsert_matching_record(doc_id: str, fields: dict, headers: dict):
    """Create or update a matching record from besoin_id/candidat_id."""
    besoin_id = str(fields.get('besoin_id') or '').strip()
    candidat_id = str(fields.get('candidat_id') or '').strip()
    if not besoin_id or not candidat_id:
        raise RuntimeError('Missing besoin_id or candidat_id for matching upsert.')

    table_config = {'doc_id': doc_id, 'table_id': EURES_MATCHINGS_TABLE}
    ensure_table_columns(table_config, set(fields.keys()) & (EURES_MATCHING_FIELDS | EURES_MATCHING_ADMIN_FIELDS), headers)
    existing = fetch_matching_record(doc_id, besoin_id, candidat_id, headers)
    merged_fields = dict(fields)
    if existing and isinstance(existing, dict):
        existing_fields = existing.get('fields', {}) if isinstance(existing.get('fields'), dict) else {}
        for key in EURES_MATCHING_ADMIN_FIELDS:
            if key not in merged_fields and key in existing_fields:
                merged_fields[key] = existing_fields.get(key)
        if not merged_fields.get('workflow_status'):
            merged_fields['workflow_status'] = _matching_workflow_status(existing_fields)
    else:
        merged_fields.setdefault('workflow_status', _initial_matching_workflow_status(fields.get('statut', '')))

    ensure_table_columns(table_config, set(merged_fields.keys()) & (EURES_MATCHING_FIELDS | EURES_MATCHING_ADMIN_FIELDS), headers)
    allowed_columns = get_table_columns(table_config, headers)
    filtered_fields = {k: v for k, v in merged_fields.items() if k in allowed_columns}
    base_url = f"{GRIST_BASE_URL}/api/docs/{doc_id}/tables/{EURES_MATCHINGS_TABLE}/records"

    if existing:
        payload = {'records': [{'id': existing['id'], 'fields': filtered_fields}]}
        resp = write_grist_records('PATCH', base_url, payload, headers)
    else:
        payload = {'records': [{'fields': filtered_fields}]}
        resp = write_grist_records('POST', base_url, payload, headers)

    if resp.status_code != 200:
        raise RuntimeError(f'Failed to write Matchings: HTTP {resp.status_code} - {resp.text}')
    return resp


def update_matching_record_by_id(doc_id: str, record_id: int, fields: dict, headers: dict):
    """Patch a matching record by Grist record id."""
    table_config = {'doc_id': doc_id, 'table_id': EURES_MATCHINGS_TABLE}
    ensure_table_columns(table_config, set(fields.keys()) & (EURES_MATCHING_FIELDS | EURES_MATCHING_ADMIN_FIELDS), headers)
    allowed_columns = get_table_columns(table_config, headers)
    filtered_fields = {k: v for k, v in fields.items() if k in allowed_columns}
    base_url = f"{GRIST_BASE_URL}/api/docs/{doc_id}/tables/{EURES_MATCHINGS_TABLE}/records"
    payload = {'records': [{'id': record_id, 'fields': filtered_fields}]}
    resp = write_grist_records('PATCH', base_url, payload, headers)
    if resp.status_code != 200:
        raise RuntimeError(f'Failed to update Matchings: HTTP {resp.status_code} - {resp.text}')
    return resp


def update_table_record_by_id(config: dict, record_id: int, fields: dict, headers: dict, allowed_fields: set[str] | None = None):
    """Patch one Grist record by id on any configured table."""
    field_names = set(fields.keys()) if allowed_fields is None else (set(fields.keys()) & allowed_fields)
    ensure_table_columns(config, field_names, headers)
    allowed_columns = get_table_columns(config, headers)
    filtered_fields = {k: v for k, v in fields.items() if k in allowed_columns}
    base_url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}/records"
    payload = {'records': [{'id': record_id, 'fields': filtered_fields}]}
    resp = write_grist_records('PATCH', base_url, payload, headers)
    if resp.status_code != 200:
        raise RuntimeError(f'Failed to update {config["table_id"]}: HTTP {resp.status_code} - {resp.text}')
    return resp


def fetch_record_by_id(doc_id: str, table_id: str, record_id: int, headers: dict):
    """Read one Grist record by numeric id."""
    url = f"{GRIST_BASE_URL}/api/docs/{doc_id}/tables/{table_id}/records"
    resp = requests.get(url, params={'filter': json.dumps({'id': [record_id]})}, headers=headers)
    if resp.status_code != 200:
        raise RuntimeError(f'Failed to read {table_id}: HTTP {resp.status_code} - {resp.text}')
    payload = _parse_response_json_safe(resp)
    records = payload.get('records', []) if isinstance(payload, dict) else []
    return records[0] if records else None


def eures_normalize_text(value) -> str:
    return str(value or '').strip().lower()


def eures_fold_text(value) -> str:
    text = str(value or '').strip().lower()
    if not text:
        return ''
    return ''.join(
        char for char in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(char)
    )


def eures_tokenize_text(value) -> list[str]:
    stopwords = {
        'de', 'du', 'des', 'la', 'le', 'les', 'un', 'une', 'et', 'en', 'au', 'aux',
        'pour', 'avec', 'dans', 'sur', 'the', 'and', 'for', 'mit', 'und', 'fur', 'fuer',
    }
    return [
        token for token in re.split(r'[^a-z0-9]+', eures_fold_text(value))
        if len(token) >= 2 and token not in stopwords
    ]


def eures_canonical_sector(value: str) -> str:
    value_l = eures_normalize_text(value)
    for token, sector in EURES_SECTOR_CANONICAL_MAP.items():
        if token in value_l:
            return sector
    return ''


def eures_candidate_sectors(value: str) -> set[str]:
    value_l = eures_normalize_text(value)
    return {sector for token, sector in EURES_SECTOR_CANONICAL_MAP.items() if token in value_l}


def eures_parse_language_requirements(value: str) -> dict[str, int]:
    levels = {
        'pas nécessaire': 0,
        'pas necessaire': 0,
        'not necessary': 0,
        'communication professionelle': 2,
        'communication professionnelle': 2,
        'professional communication': 2,
        'pouvoir communiquer dans la langue locale': 2,
        'très important au quotidien': 3,
        'tres important au quotidien': 3,
        'very important on a daily basis': 3,
    }
    result: dict[str, int] = {}
    for part in str(value or '').split('|'):
        if ':' not in part:
            continue
        lang, raw_level = part.split(':', 1)
        lang_key = eures_normalize_text(lang)
        level_text = eures_normalize_text(raw_level)
        score = next((v for k, v in levels.items() if k in level_text), None)
        if score is not None:
            result[lang_key] = score
    return result


def eures_parse_candidate_languages(value: str) -> dict[str, int]:
    levels = {
        'je ne la pratique pas': 0,
        'i do not speak it': 0,
        "j'utilise un outil de traduction si nécessaire": 0,
        "j'utilise un outil de traduction si necessaire": 0,
        'translation tool': 0,
        'je peux communiquer simplement': 2,
        "je peux échanger à l'oral": 2,
        "je peux echanger a l'oral": 2,
        'simple communication': 2,
        'je peux travailler avec cette langue': 3,
        'langue maternelle': 4,
        'native': 4,
    }
    result: dict[str, int] = {}
    for part in str(value or '').split('|'):
        if ':' not in part:
            continue
        lang, raw_level = part.split(':', 1)
        lang_key = eures_normalize_text(lang)
        level_text = eures_normalize_text(raw_level)
        matched = [v for k, v in levels.items() if k in level_text]
        if matched:
            result[lang_key] = max(matched)
    return result


def eures_availability_rank(value: str) -> int | None:
    value_l = eures_normalize_text(value)
    ordered = [
        ('dès que possible', 0),
        ('des que possible', 0),
        ('dans les prochains jours', 1),
        ('dans les prochaines semaines', 2),
        ('dans 1 à 3 mois', 3),
        ('dans 1 a 3 mois', 3),
        ('je ne sais pas encore', 4),
    ]
    for token, rank in ordered:
        if token in value_l:
            return rank
    return None


def eures_to_float(value):
    if value in (None, '', 0, '0'):
        return None
    try:
        return float(value)
    except Exception:
        return None


def eures_score_sector_fit(expected: str, actual: str) -> tuple[int, str]:
    expected_sector = eures_canonical_sector(expected)
    candidate_sectors = eures_candidate_sectors(actual)
    if not expected_sector:
        return 0, 'metier: secteur employeur absent'
    if not candidate_sectors:
        return 0, 'metier: secteur candidat absent'
    if expected_sector in candidate_sectors:
        if len(candidate_sectors) == 1:
            return 18, f'metier: secteur exact ({expected_sector})'
        return 12, f'metier: secteur present ({expected_sector})'
    return 0, f'metier: secteur non aligne ({expected_sector})'


def eures_score_languages(expected: str, actual: str) -> tuple[int, str]:
    expected_map = eures_parse_language_requirements(expected)
    actual_map = eures_parse_candidate_languages(actual)
    scored = {lang: lvl for lang, lvl in expected_map.items() if lvl > 0}
    if not scored or not actual_map:
        return 0, 'langues: information manquante'
    matched = []
    strong = 0
    partial = 0
    for lang, required_level in scored.items():
        candidate_level = actual_map.get(lang)
        if candidate_level is None:
            continue
        if candidate_level >= required_level:
            strong += 1
            matched.append(lang)
        elif candidate_level >= 2 and candidate_level + 1 >= required_level:
            partial += 1
            matched.append(f'{lang} (partiel)')
    ratio = (strong + 0.5 * partial) / max(len(scored), 1)
    points = round(25 * ratio)
    if points > 0:
        return points, 'langues: ' + ', '.join(matched)
    return 0, 'langues: aucune correspondance'


def eures_score_location(besoin_pays: str, candidat_pays: str, mobilite: str) -> tuple[int, str]:
    besoin_pays_l = eures_normalize_text(besoin_pays)
    candidat_pays_l = eures_normalize_text(candidat_pays)
    mobilite_l = eures_normalize_text(mobilite)
    if besoin_pays_l and candidat_pays_l and (besoin_pays_l == candidat_pays_l or besoin_pays_l in candidat_pays_l):
        return 15, 'pays/mobilite: meme pays'
    if besoin_pays_l and mobilite_l and besoin_pays_l in mobilite_l:
        return 15, 'pays/mobilite: pays souhaite explicite'
    if mobilite_l and any(token in mobilite_l for token in ('transfrontali', 'expatriation', 'pays souhaités', 'pays souhaites')):
        return 10, 'pays/mobilite: mobilite declaree'
    return 0, 'pays/mobilite: contrainte geographique'


def eures_score_availability(date_debut: str, disponibilite: str) -> tuple[int, str]:
    disponibilite_l = str(disponibilite or '').strip()
    if not disponibilite_l:
        return 0, 'disponibilite: information manquante'
    besoin_rank = eures_availability_rank(date_debut)
    candidat_rank = eures_availability_rank(disponibilite)
    if besoin_rank is not None and candidat_rank is not None:
        if candidat_rank <= besoin_rank:
            return 15, 'disponibilite: date compatible'
        if candidat_rank == besoin_rank + 1:
            return 9, 'disponibilite: leger decalage'
        return 0, 'disponibilite: delai trop long'
    if eures_normalize_text(date_debut) and eures_normalize_text(date_debut) in eures_normalize_text(disponibilite):
        return 15, 'disponibilite: date compatible'
    return 7, 'disponibilite: verification manuelle recommandee'


def eures_parse_canonical_multi_values(value: str, mapping: dict[str, str]) -> set[str]:
    parsed = set()
    for part in _split_matching_text(value):
        normalized = eures_normalize_text(part)
        canonical = mapping.get(normalized)
        if canonical:
            parsed.add(canonical)
    return parsed


def eures_score_work_conditions(expected: str, actual: str) -> tuple[int, str]:
    expected_set = eures_parse_canonical_multi_values(expected, EURES_WORK_CONDITION_CANONICAL_MAP)
    actual_set = eures_parse_canonical_multi_values(actual, EURES_WORK_CONDITION_CANONICAL_MAP)
    expected_set.discard('inconnu')
    actual_set.discard('inconnu')
    if not expected_set or expected_set == {'aucune_condition'}:
        return 3, 'conditions: aucune contrainte specifique'
    if 'aucune_condition' in actual_set:
        return 0, 'conditions: candidat sans preference exploitable'
    overlap = expected_set & actual_set
    if expected_set and overlap == expected_set:
        return 3, 'conditions: compatibles'
    if overlap:
        return 1, 'conditions: compatibilite partielle'
    partial_overlap = {
        expected_condition
        for expected_condition in expected_set
        if EURES_WORK_CONDITION_PARTIAL_COMPATIBILITY.get(expected_condition, set()) & actual_set
    }
    if partial_overlap:
        return 1, 'conditions: compatibilite partielle'
    return 0, 'conditions: incompatibilite probable'


def eures_score_permits(expected: str, actual: str) -> tuple[int, str]:
    expected_set = eures_parse_canonical_multi_values(expected, EURES_PERMIT_CANONICAL_MAP)
    actual_set = eures_parse_canonical_multi_values(actual, EURES_PERMIT_CANONICAL_MAP)
    if not expected_set:
        return 3, 'permis: aucun requis'
    overlap = expected_set & actual_set
    if overlap == expected_set:
        return 3, 'permis: requis couverts'
    if overlap:
        return 1, 'permis: couverture partielle'
    return 0, 'permis: exigence non couverte'


def eures_candidate_salary_expectation(secteur: str, fields: dict):
    salary_fields = EURES_CANDIDAT_SECTOR_SALARY_FIELDS.get(secteur)
    if not salary_fields:
        return None
    type_field, min_field = salary_fields
    salary_type = str(fields.get(type_field) or '').strip()
    salary_min = eures_to_float(fields.get(min_field))
    if salary_min is None:
        return None
    return salary_type, salary_min


def eures_candidate_job_title(secteur: str, fields: dict) -> str:
    field_name = EURES_CANDIDAT_SECTOR_JOB_TITLE_FIELDS.get(secteur)
    return str(fields.get(field_name) or '').strip() if field_name else ''


def eures_employer_salary_offer(secteur: str, fields: dict):
    salary_fields = EURES_EMPLOYEUR_SECTOR_SALARY_FIELDS.get(secteur)
    if not salary_fields:
        return None
    type_field, min_field, max_field = salary_fields
    salary_type = str(fields.get(type_field) or '').strip()
    salary_min = eures_to_float(fields.get(min_field))
    salary_max = eures_to_float(fields.get(max_field))
    if salary_min is None and salary_max is None:
        return None
    return salary_type, salary_min, salary_max


def eures_employer_job_title(secteur: str, fields: dict) -> str:
    field_name = EURES_EMPLOYEUR_SECTOR_JOB_TITLE_FIELDS.get(secteur)
    return str(fields.get(field_name) or '').strip() if field_name else ''


def eures_score_job_title(expected: str, actual: str) -> tuple[int, str]:
    expected_tokens = eures_tokenize_text(expected)
    actual_tokens = eures_tokenize_text(actual)
    if not expected_tokens or not actual_tokens:
        return 0, 'intitule: information manquante'

    expected_folded = eures_fold_text(expected)
    actual_folded = eures_fold_text(actual)
    if expected_folded and actual_folded and expected_folded == actual_folded:
        return 12, f'intitule: exact ({expected.strip()})'

    common = sorted(set(expected_tokens) & set(actual_tokens))
    if not common:
        return 0, 'intitule: aucun recoupement'

    ratio = len(common) / max(len(set(expected_tokens)), len(set(actual_tokens)), 1)
    if ratio >= 0.6:
        return 10, 'intitule: proche (' + ', '.join(common) + ')'
    if ratio >= 0.3:
        return 6, 'intitule: partiel (' + ', '.join(common) + ')'
    return 3, 'intitule: faible recoupement (' + ', '.join(common) + ')'


def eures_parse_skill_items(value: str) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for raw_part in re.split(r'[|\n;,]+', str(value or '')):
        part = str(raw_part or '').strip()
        if not part:
            continue
        folded = eures_fold_text(part)
        if not folded or folded in seen:
            continue
        seen.add(folded)
        items.append(part)
    return items


def eures_score_competences(expected: str, actual: str) -> tuple[int, str]:
    expected_items = eures_parse_skill_items(expected)
    actual_items = eures_parse_skill_items(actual)
    if not expected_items or not actual_items:
        return 0, 'competences: information manquante'

    expected_map = {eures_fold_text(item): item for item in expected_items}
    actual_map = {eures_fold_text(item): item for item in actual_items}
    exact_overlap = [expected_map[key] for key in expected_map if key in actual_map]

    if exact_overlap:
        ratio = len(exact_overlap) / max(len(expected_items), 1)
        points = round(20 * ratio)
        if points > 0:
            if ratio >= 0.99:
                return 20, 'competences: couverture complete'
            return points, 'competences: ' + ', '.join(exact_overlap)

    expected_tokens = set(eures_tokenize_text(expected))
    actual_tokens = set(eures_tokenize_text(actual))
    if not expected_tokens or not actual_tokens:
        return 0, 'competences: information insuffisante'

    overlap = sorted(expected_tokens & actual_tokens)
    if not overlap:
        return 0, 'competences: aucune correspondance'

    ratio = len(overlap) / max(len(expected_tokens), 1)
    points = round(20 * ratio * 0.75)
    if ratio >= 0.6:
        return max(points, 12), 'competences: proches (' + ', '.join(overlap) + ')'
    if ratio >= 0.3:
        return max(points, 7), 'competences: partielles (' + ', '.join(overlap) + ')'
    return max(points, 3), 'competences: faible recoupement (' + ', '.join(overlap) + ')'


def eures_score_salary(secteur: str, candidat_fields: dict, besoin_fields: dict) -> tuple[int, str]:
    if not secteur:
        return 0, 'salaire: secteur indetermine'
    candidat_salary = eures_candidate_salary_expectation(secteur, candidat_fields)
    employeur_salary = eures_employer_salary_offer(secteur, besoin_fields)
    if candidat_salary is None or employeur_salary is None:
        return 6, 'salaire: donnees absentes, verification manuelle'
    _, candidat_min = candidat_salary
    _, employeur_min, employeur_max = employeur_salary
    if employeur_max and candidat_min <= employeur_max:
        if employeur_min and candidat_min < employeur_min:
            return 12, 'salaire: attente sous la fourchette proposee'
        return 15, 'salaire: compatible'
    if employeur_min and candidat_min <= employeur_min * 1.1:
        return 8, 'salaire: ecart limite'
    return 0, 'salaire: attente superieure au salaire propose'


def eures_matching_status(score: int) -> str:
    if score >= 75:
        return 'auto_envoyable'
    if score >= 55:
        return 'a_valider'
    return 'a_ecarter'


def compute_eures_matching(besoin_fields: dict, candidat_fields: dict) -> dict:
    """Compute a matching payload for one candidate/employer pair."""
    besoin_country = besoin_fields.get('pays_normalise') or besoin_fields.get('pays') or ''
    candidat_country = candidat_fields.get('pays_normalise') or candidat_fields.get('pays') or ''
    secteur = eures_canonical_sector(str(besoin_fields.get('poste') or ''))
    employeur_job_title = eures_employer_job_title(secteur, besoin_fields)
    candidat_job_title = eures_candidate_job_title(secteur, candidat_fields)

    score_metier_sector, raison_metier_sector = eures_score_sector_fit(
        str(besoin_fields.get('poste') or ''),
        str(candidat_fields.get('metier') or ''),
    )
    score_metier_title, raison_metier_title = eures_score_job_title(
        employeur_job_title,
        candidat_job_title,
    )
    score_metier_raw = min(30, score_metier_sector + score_metier_title)
    score_metier = round(25 * score_metier_raw / 30)
    score_competences, raison_competences = eures_score_competences(
        str(besoin_fields.get('competences_clefs') or ''),
        str(candidat_fields.get('competences') or ''),
    )
    score_langues_raw, raison_langues = eures_score_languages(
        str(besoin_fields.get('langues_requises') or ''),
        str(candidat_fields.get('langues') or ''),
    )
    score_langues = round(20 * score_langues_raw / 25)
    score_mobilite, raison_mobilite = eures_score_location(
        str(besoin_country),
        str(candidat_country),
        str(candidat_fields.get('mobilite') or ''),
    )
    score_disponibilite_base, raison_disponibilite = eures_score_availability(
        str(besoin_fields.get('date_debut') or ''),
        str(candidat_fields.get('disponibilite') or ''),
    )
    score_conditions, raison_conditions = eures_score_work_conditions(
        str(besoin_fields.get('contraintes_travail') or ''),
        str(candidat_fields.get('contraintes_travail') or ''),
    )
    score_permis, raison_permis = eures_score_permits(
        str(besoin_fields.get('permis_autorisations') or ''),
        str(candidat_fields.get('permis_autorisations') or ''),
    )
    score_disponibilite = min(10, round(score_disponibilite_base * 0.35) + score_conditions + score_permis)
    score_salaire_raw, raison_salaire = eures_score_salary(secteur, candidat_fields, besoin_fields)
    score_salaire = round(10 * score_salaire_raw / 15)

    reasons = []
    weaknesses = []
    for points, text in [
        (score_metier_sector, raison_metier_sector),
        (score_metier_title, raison_metier_title),
        (score_competences, raison_competences),
        (score_langues_raw, raison_langues),
        (score_mobilite, raison_mobilite),
        (score_disponibilite_base, raison_disponibilite),
        (score_conditions, raison_conditions),
        (score_permis, raison_permis),
        (score_salaire_raw, raison_salaire),
    ]:
        (reasons if points else weaknesses).append(text)

    score = score_metier + score_competences + score_langues + score_mobilite + score_disponibilite + score_salaire
    return {
        'score': score,
        'score_metier': score_metier,
        'score_competences': score_competences,
        'score_langues': score_langues,
        'score_mobilite': score_mobilite,
        'score_disponibilite': score_disponibilite,
        'score_salaire': score_salaire,
        'statut': eures_matching_status(score),
        'raisons': ' | '.join(reasons),
        'points_faibles': ' | '.join(weaknesses),
        'date_calcul': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
    }


def run_eures_matching_for_saved_record(form_id: str, role: str, saved_record: dict, config: dict, headers: dict):
    """Compute matchings for one newly saved EURES beta record and write them to Matchings."""
    if form_id != 'eures-beta':
        return {'processed': False, 'reason': 'unsupported_form'}
    if role not in {'candidate', 'employer'}:
        return {'processed': False, 'reason': 'unsupported_role'}

    all_candidats = fetch_table_records(config['doc_id'], EURES_CANDIDATS_TABLE, headers)
    all_besoins = fetch_table_records(config['doc_id'], EURES_BESOINS_TABLE, headers)
    saved_fields = saved_record.get('fields', {}) if isinstance(saved_record.get('fields'), dict) else {}
    if not _is_eures_response_active(saved_fields):
        return {'processed': False, 'reason': 'disabled_saved_record', 'role': role}

    writes = 0
    qualifying_matches = 0
    if role == 'candidate':
        for besoin in all_besoins:
            besoin_fields = besoin.get('fields', {}) if isinstance(besoin.get('fields'), dict) else {}
            if not _is_eures_response_active(besoin_fields):
                continue
            candidat_id = str(saved_fields.get('id_tally') or saved_fields.get('uuid') or '')
            besoin_id = str(besoin_fields.get('id_tally') or besoin_fields.get('uuid') or '')
            if not candidat_id or not besoin_id:
                continue
            matching = compute_eures_matching(besoin_fields, saved_fields)
            if str(matching.get('statut') or '').strip().lower() in {'a_valider', 'auto_envoyable'}:
                qualifying_matches += 1
            payload = {'besoin_id': besoin_id, 'candidat_id': candidat_id, **matching}
            upsert_matching_record(config['doc_id'], payload, headers)
            writes += 1
    else:
        for candidat in all_candidats:
            candidat_fields = candidat.get('fields', {}) if isinstance(candidat.get('fields'), dict) else {}
            if not _is_eures_response_active(candidat_fields):
                continue
            candidat_id = str(candidat_fields.get('id_tally') or candidat_fields.get('uuid') or '')
            besoin_id = str(saved_fields.get('id_tally') or saved_fields.get('uuid') or '')
            if not candidat_id or not besoin_id:
                continue
            matching = compute_eures_matching(saved_fields, candidat_fields)
            if str(matching.get('statut') or '').strip().lower() in {'a_valider', 'auto_envoyable'}:
                qualifying_matches += 1
            payload = {'besoin_id': besoin_id, 'candidat_id': candidat_id, **matching}
            upsert_matching_record(config['doc_id'], payload, headers)
            writes += 1

    return {
        'processed': True,
        'writes': writes,
        'role': role,
        'qualifying_matches': qualifying_matches,
        'no_immediate_match': qualifying_matches == 0,
    }


def _eures_admin_headers(config: dict) -> dict:
    headers = {'Accept': 'application/json'}
    if config.get('api_key'):
        headers['Authorization'] = f"Bearer {config['api_key']}"
    return headers


def _eures_admin_status(fields: dict) -> str:
    status = str((fields or {}).get('admin_status') or '').strip().lower()
    if status in {'accepted', 'refused', 'pending'}:
        return status
    return 'pending'


def _eures_workflow_transition_allowed(current_status: str, target_status: str) -> bool:
    allowed = {
        'calcule': {'a_valider_admin', 'refuse_admin'},
        'a_valider_admin': {'valide_admin', 'refuse_admin'},
        'valide_admin': {'envoye_employeur', 'refuse_admin'},
        'envoye_employeur': {'accepte_employeur', 'refuse_employeur', 'mise_en_relation_faite'},
        'accepte_employeur': {'mise_en_relation_faite', 'embauche_confirmee'},
        'mise_en_relation_faite': {'embauche_confirmee'},
        'refuse_employeur': set(),
        'refuse_admin': set(),
        'embauche_confirmee': set(),
    }
    if current_status == target_status:
        return True
    return target_status in allowed.get(current_status, set())


def _split_matching_text(value: str) -> list[str]:
    return [part.strip() for part in str(value or '').split('|') if part.strip()]


def _extract_employer_contact_email(contact_value: str) -> str:
    raw = str(contact_value or '').strip()
    if '@' not in raw:
        return ''
    if '|' in raw:
        for part in [p.strip() for p in raw.split('|') if p.strip()]:
            if '@' in part:
                return part
    return raw


def _extract_first_email(value) -> str:
    raw = str(value or '').strip()
    if not raw or '@' not in raw:
        return ''
    match = re.search(r'([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})', raw, flags=re.IGNORECASE)
    return normalize_email(match.group(1)) if match else ''


def _resolve_employer_recipient(employeur: dict) -> str:
    if not isinstance(employeur, dict):
        return ''

    direct_candidates = [
        employeur.get('contact', ''),
        employeur.get('tally_q18', ''),
        employeur.get('email', ''),
        employeur.get('mail', ''),
        employeur.get('contact_email', ''),
        employeur.get('email_contact', ''),
    ]
    for value in direct_candidates:
        email = _extract_employer_contact_email(value) or _extract_first_email(value)
        if email:
            return email

    for value in employeur.values():
        email = _extract_first_email(value)
        if email:
            return email
    return ''


def _format_email_multiline(value: str) -> str:
    text = str(value or '').strip()
    if not text:
        return 'Non renseigné'
    return '<br>'.join(escape(part.strip()) for part in text.split('|') if part.strip()) or escape(text)


def _normalize_eures_no_match_status(value: str) -> str:
    status = str(value or '').strip().lower()
    return status if status in EURES_NO_MATCH_ALLOWED_STATUSES else ''


def _normalize_eures_new_job_request_status(value: str) -> str:
    status = str(value or '').strip().lower()
    return status if status in EURES_NEW_JOB_REQUEST_ALLOWED_STATUSES else ''


def _normalize_eures_new_employer_alert_status(value: str) -> str:
    status = str(value or '').strip().lower()
    return status if status in EURES_NEW_EMPLOYER_ALERT_ALLOWED_STATUSES else ''


def _normalize_eures_response_status(value: str) -> str:
    status = str(value or '').strip().lower()
    return status if status in EURES_RESPONSE_ALLOWED_STATUSES else ''


def _normalize_eures_duplicate_followup_status(value: str) -> str:
    status = str(value or '').strip().lower()
    return status if status in EURES_DUPLICATE_FOLLOWUP_ALLOWED_STATUSES else ''


def _get_eures_role_table_config(role: str) -> dict | None:
    normalized_role = _normalize_eures_invitation_role(role)
    if not normalized_role:
        return None
    base = get_form_config('eures-beta', normalized_role)
    if not base:
        return None
    return {
        'doc_id': base['doc_id'],
        'table_id': EURES_CANDIDATS_TABLE if normalized_role == 'candidate' else EURES_BESOINS_TABLE,
        'api_key': base.get('api_key'),
    }


def _eures_response_received_at(fields: dict) -> str:
    return (
        str((fields or {}).get('response_received_at') or '').strip()
        or str((fields or {}).get('tally_submitted_at') or '').strip()
        or str((fields or {}).get('created_at') or '').strip()
        or str((fields or {}).get('updated_at') or '').strip()
    )


def _is_eures_response_active(fields: dict) -> bool:
    status = _normalize_eures_response_status((fields or {}).get('response_status', ''))
    return status != 'disabled'


def queue_eures_no_match_notification(role: str, record_id: int):
    """Mark a record for manual follow-up when no immediate match exists."""
    config = _get_eures_role_table_config(role)
    if not config:
        raise RuntimeError('EURES role table configuration is incomplete.')
    headers = _eures_admin_headers(config)
    update_table_record_by_id(
        config,
        record_id,
        {
            'no_match_notification_status': 'pending',
            'no_match_notification_reason': 'no_immediate_match',
            'no_match_notification_created_at': _now_iso_utc(),
            'no_match_notification_created_by': 'system_matching',
            'no_match_notification_note': '',
        },
        headers,
        EURES_NO_MATCH_NOTIFICATION_FIELDS,
    )


def _build_eures_no_match_row(role: str, rec: dict) -> dict | None:
    fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
    if not isinstance(fields, dict):
        return None
    status = _normalize_eures_no_match_status(fields.get('no_match_notification_status', ''))
    if not status:
        return None

    normalized_role = _normalize_eures_invitation_role(role)
    is_candidate = normalized_role == 'candidate'
    recipient = normalize_email(fields.get('email', '')) if is_candidate else _resolve_employer_recipient(fields)
    title = (
        str(fields.get('nom') or fields.get('email') or 'Candidat')
        if is_candidate else
        str(fields.get('employeur') or fields.get('poste') or recipient or 'Employeur')
    )
    subtitle = str(fields.get('metier') or '') if is_candidate else str(fields.get('poste') or '')
    return {
        'role': normalized_role,
        'record_id': rec.get('id'),
        'record_key': fields.get('id_tally') or fields.get('uuid') or '',
        'notification_status': status,
        'reason': fields.get('no_match_notification_reason', ''),
        'created_at': fields.get('no_match_notification_created_at', ''),
        'created_by': fields.get('no_match_notification_created_by', ''),
        'sent_at': fields.get('no_match_notification_sent_at', ''),
        'sent_by': fields.get('no_match_notification_sent_by', ''),
        'dismissed_at': fields.get('no_match_notification_dismissed_at', ''),
        'dismissed_by': fields.get('no_match_notification_dismissed_by', ''),
        'note': fields.get('no_match_notification_note', ''),
        'title': title,
        'subtitle': subtitle,
        'recipient_email': recipient,
        'payload': {
            'nom': fields.get('nom', ''),
            'email': fields.get('email', ''),
            'telephone': fields.get('telephone', ''),
            'pays': fields.get('pays', ''),
            'metier': fields.get('metier', ''),
            'langues': fields.get('langues', ''),
            'mobilite': fields.get('mobilite', ''),
            'disponibilite': fields.get('disponibilite', ''),
            'employeur': fields.get('employeur', ''),
            'contact': fields.get('contact', ''),
            'poste': fields.get('poste', ''),
            'competences_clefs': fields.get('competences_clefs', ''),
            'langues_requises': fields.get('langues_requises', ''),
            'date_debut': fields.get('date_debut', ''),
        },
    }


def list_eures_admin_no_match_notifications(status: str = 'all') -> list[dict]:
    """Return candidate/employer rows needing a no-match email review."""
    rows = []
    for role in ('candidate', 'employer'):
        config = _get_eures_role_table_config(role)
        if not config:
            continue
        headers = _eures_admin_headers(config)
        for rec in fetch_table_records(config['doc_id'], config['table_id'], headers):
            fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
            if not _is_eures_response_active(fields):
                continue
            row = _build_eures_no_match_row(role, rec)
            if not row:
                continue
            if status in EURES_NO_MATCH_ALLOWED_STATUSES and row['notification_status'] != status:
                continue
            rows.append(row)
    rows.sort(key=lambda row: (str(row.get('created_at') or ''), int(row.get('record_id') or 0)), reverse=True)
    return rows


EURES_CANDIDATE_TALLY_LABELS = {
    'tally_q01': 'Projet de mobilité par pays',
    'tally_q01_f01': 'Projet de mobilité par pays · Allemagne',
    'tally_q01_f02': 'Projet de mobilité par pays · France',
    'tally_q01_f03': 'Projet de mobilité par pays · Luxembourg',
    'tally_q01_f04': "Projet de mobilité par pays · Un autre pays de l'UE",
    'tally_q01_f05': 'Projet de mobilité par pays · Un autre pays hors UE',
    'tally_q02': 'Type de mobilité envisagé',
    'tally_q03': 'Expérience sous statut frontalier',
    'tally_q04': 'Temps de trajet maximum accepté',
    'tally_q05': 'Moyens de déplacement envisagés',
    'tally_q06': 'Disponibilités horaires',
    'tally_q07': 'Disponibilités détaillées',
    'tally_q07_f01': 'Disponibilités détaillées · Lundi',
    'tally_q07_f02': 'Disponibilités détaillées · Mardi',
    'tally_q07_f03': 'Disponibilités détaillées · Mercredi',
    'tally_q07_f04': 'Disponibilités détaillées · Jeudi',
    'tally_q07_f05': 'Disponibilités détaillées · Vendredi',
    'tally_q07_f06': 'Disponibilités détaillées · Samedi',
    'tally_q07_f07': 'Disponibilités détaillées · Dimanche',
    'tally_q08': 'Types de contrats acceptés',
    'tally_q09': 'Date de disponibilité',
    'tally_q10': 'Préparation des documents',
    'tally_q10_f01': "Préparation des documents · Carte d'identité ou passeport",
    'tally_q10_f02': 'Préparation des documents · CV à jour',
    'tally_q10_f03': 'Préparation des documents · Diplômes ou qualifications',
    'tally_q10_f04': 'Préparation des documents · Compte bancaire / IBAN',
    'tally_q10_f05': "Préparation des documents · Attestation d'affiliation à la sécurité sociale",
    'tally_q11': 'Sécurité sociale luxembourgeoise',
    'tally_q12': 'Sécurité sociale allemande',
    'tally_q13': 'Sécurité sociale française',
    'tally_q14': "Expérience de vie et de travail dans un autre pays",
    'tally_q15': 'Date de départ souhaitée',
    'tally_q16': 'Conditions de départ',
    'tally_q17': 'Priorités de départ',
    'tally_q18': 'Compétences linguistiques',
    'tally_q18_f01': 'Compétences linguistiques · Allemand',
    'tally_q18_f02': 'Compétences linguistiques · Anglais',
    'tally_q18_f03': 'Compétences linguistiques · Français',
    'tally_q18_f04': 'Compétences linguistiques · Luxembourgeois',
    'tally_q19': 'Secteurs recherchés',
    'tally_q20': 'Atouts recherchés · Vente et commerce',
    'tally_q20_job_title': 'Intitulé du poste visé · Vente et commerce',
    'tally_q21': 'Expérience · Vente et commerce',
    'tally_q22': 'Atouts recherchés · Nettoyage et entretien',
    'tally_q22_job_title': 'Intitulé du poste visé · Nettoyage et entretien',
    'tally_q23': 'Expérience · Nettoyage et entretien',
    'tally_q24': 'Casier judiciaire de moins de 3 mois',
    'tally_q25': 'Atouts recherchés · Hôtellerie et restauration',
    'tally_q25_job_title': 'Intitulé du poste visé · Hôtellerie et restauration',
    'tally_q26': 'Expérience · Hôtellerie et restauration',
    'tally_q27': 'Atouts recherchés · Agriculture et récolte',
    'tally_q27_job_title': 'Intitulé du poste visé · Agriculture et récolte',
    'tally_q28': 'Expérience · Agriculture et récolte',
    'tally_q29': 'Atouts recherchés · Missions polyvalentes et emplois accessibles rapidement',
    'tally_q29_job_title': 'Intitulé du poste visé · Missions polyvalentes et emplois accessibles rapidement',
    'tally_q30': 'Expérience · Missions polyvalentes et emplois accessibles rapidement',
    'tally_q38': 'Atouts recherchés · Production industrielle (assemblage, fabrication, conditionnement, contrôle qualité)',
    'tally_q38_job_title': 'Intitulé du poste visé · Production industrielle (assemblage, fabrication, conditionnement, contrôle qualité)',
    'tally_q39': 'Expérience · Production industrielle (assemblage, fabrication, conditionnement, contrôle qualité)',
    'tally_q41': 'Permis / autorisation particulière',
    'tally_q42': 'Permis / autorisations possédés',
    'tally_q42_extra': 'Permis / autorisation · précision',
    'tally_q43': 'Conditions de travail acceptées',
    'tally_q31': 'Prénom',
    'tally_q32': 'Nom',
    'tally_q33': 'Adresse e-mail',
    'tally_q34': 'Téléphone',
    'tally_q35': 'Ville de résidence actuelle',
    'tally_q36': 'CV transmis',
    'tally_q37': 'Consentement RGPD',
}

EURES_EMPLOYER_TALLY_LABELS = {
    'tally_q01': 'Secteur de recrutement',
    'tally_q02': 'Langues impératives',
    'tally_q02_f01': 'Langues impératives · Allemand',
    'tally_q02_f02': 'Langues impératives · Anglais',
    'tally_q02_f03': 'Langues impératives · Français',
    'tally_q02_f04': 'Langues impératives · Luxembourgeois',
    'tally_q03': 'Nombre de recrutements souhaités',
    'tally_q04': 'Date de besoin',
    'tally_q05': 'Durée de contrat proposée',
    'tally_q06': 'Volume hebdomadaire proposé',
    'tally_q07': 'Profils que vous êtes prêt à recruter',
    'tally_q08': "Aides à l'arrivée ou à l'installation",
    'tally_q09': 'Critères indispensables',
    'tally_q10': 'Priorités métier · Vente et commerce',
    'tally_q10_job_title': 'Intitulé du poste proposé · Vente et commerce',
    'tally_q11': 'Priorités métier · Nettoyage et entretien',
    'tally_q11_job_title': 'Intitulé du poste proposé · Nettoyage et entretien',
    'tally_q12': 'Priorités métier · Hôtellerie et restauration',
    'tally_q12_job_title': 'Intitulé du poste proposé · Hôtellerie et restauration',
    'tally_q13': 'Priorités métier · Agriculture et récolte',
    'tally_q13_job_title': 'Intitulé du poste proposé · Agriculture et récolte',
    'tally_q14': 'Priorités métier · Missions polyvalentes et emplois accessibles rapidement',
    'tally_q14_job_title': 'Intitulé du poste proposé · Missions polyvalentes et emplois accessibles rapidement',
    'tally_q40': 'Priorités métier · Production industrielle (assemblage, fabrication, conditionnement, contrôle qualité)',
    'tally_q40_job_title': 'Intitulé du poste proposé · Production industrielle (assemblage, fabrication, conditionnement, contrôle qualité)',
    'tally_q15': 'Conditions de travail à connaître',
    'tally_q22': 'Permis / autorisation requis',
    'tally_q23': 'Permis / autorisations nécessaires',
    'tally_q23_extra': 'Permis / autorisation nécessaire · précision',
    'tally_q16': 'Prénom du contact',
    'tally_q17': "Nom de l'entreprise",
    'tally_q18': 'Adresse e-mail',
    'tally_q19': 'Téléphone',
    'tally_q20': 'Lieux de travail',
    'tally_q20_extra': 'Autres métiers souhaités à l’avenir',
    'tally_q21': 'Consentement RGPD',
}

EURES_TALLY_SECTOR_LABELS = {
    'tally_q10': 'Vente et commerce',
    'tally_q11': 'Nettoyage et entretien',
    'tally_q12': 'Hôtellerie et restauration',
    'tally_q13': 'Agriculture et récolte',
    'tally_q14': 'Missions polyvalentes et emplois accessibles rapidement',
    'tally_q40': 'Production industrielle (assemblage, fabrication, conditionnement, contrôle qualité)',
    'tally_q20': 'Vente et commerce',
    'tally_q22': 'Nettoyage et entretien',
    'tally_q25': 'Hôtellerie et restauration',
    'tally_q27': 'Agriculture et récolte',
    'tally_q29': 'Missions polyvalentes et emplois accessibles rapidement',
    'tally_q38': 'Production industrielle (assemblage, fabrication, conditionnement, contrôle qualité)',
}


def _eures_questionnaire_field_label(key: str, role: str = '') -> str:
    labels = {
        'id_tally': 'Identifiant',
        'uuid': 'UUID',
        'nom': 'Nom',
        'email': 'Email',
        'telephone': 'Téléphone',
        'ville': 'Ville',
        'pays': 'Pays',
        'metier': 'Métier',
        'langues': 'Langues',
        'mobilite': 'Mobilité',
        'disponibilite': 'Disponibilité',
        'competences': 'Compétences',
        'employeur': 'Entreprise',
        'contact': 'Contact',
        'poste': 'Poste',
        'langues_requises': 'Langues requises',
        'date_debut': 'Date de début',
        'competences_clefs': 'Compétences clefs',
        'contraintes_travail': 'Contraintes de travail',
        'permis_autorisations': 'Permis / autorisations',
        'permis_autorisations_autre': 'Permis / autorisations · précision',
        'response_status': 'Statut de la réponse',
        'response_received_at': 'Réponse reçue le',
        'cv_file_name': 'CV · nom du fichier',
        'cv_file_mime': 'CV · format',
        'cv_file_size': 'CV · taille (octets)',
        'cv_uploaded_at': 'CV · reçu le',
        'created_at': 'Créé le',
        'updated_at': 'Mis à jour le',
        'tally_submitted_at': 'Soumis le',
    }
    if key in labels:
        return labels[key]
    tally_labels = EURES_CANDIDATE_TALLY_LABELS if role == 'candidate' else EURES_EMPLOYER_TALLY_LABELS if role == 'employer' else {}
    if key in tally_labels:
        return tally_labels[key]
    salary_match = re.match(r'^(tally_q\d+)_salary_(type|min|max|note)$', str(key or ''))
    if salary_match:
        sector_label = EURES_TALLY_SECTOR_LABELS.get(salary_match.group(1), salary_match.group(1))
        suffix_label = {
            'type': 'Type de salaire',
            'min': 'Salaire minimum',
            'max': 'Salaire maximum',
            'note': 'Précision salaire',
        }.get(salary_match.group(2), salary_match.group(2))
        return f"Salaire · {sector_label} · {suffix_label}"
    job_title_match = re.match(r'^(tally_q\d+)_job_title$', str(key or ''))
    if job_title_match:
        sector_label = EURES_TALLY_SECTOR_LABELS.get(job_title_match.group(1), job_title_match.group(1))
        prefix = 'Intitulé du poste'
        if role == 'candidate':
            prefix = 'Intitulé du poste visé'
        elif role == 'employer':
            prefix = 'Intitulé du poste proposé'
        return f"{prefix} · {sector_label}"
    return str(key or '').replace('_', ' ').strip().capitalize()


def _eures_questionnaire_field_value(value) -> str:
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'Oui' if value else 'Non'
    if isinstance(value, (list, tuple)):
        return ', '.join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def _safe_int_value(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def infer_eures_cv_mime(filename: str, mime: str = '') -> str:
    normalized = str(mime or '').strip().lower()
    if normalized in EURES_CV_ALLOWED_MIME_TYPES:
        return normalized
    ext = Path(str(filename or '').strip()).suffix.lower()
    return {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.odt': 'application/vnd.oasis.opendocument.text',
    }.get(ext, normalized)


def normalize_eures_candidate_cv_fields(fields: dict) -> dict:
    """Validate and normalize candidate CV payload stored inline in Grist."""
    cv_base64 = str((fields or {}).get('cv_file_base64') or '').strip()
    cv_name = str((fields or {}).get('cv_file_name') or '').strip()
    cv_mime = infer_eures_cv_mime(
        cv_name,
        str((fields or {}).get('cv_file_mime') or '').strip().lower(),
    )
    cv_size = _safe_int_value((fields or {}).get('cv_file_size'), 0)
    if not cv_base64:
        for key in ('cv_file_name', 'cv_file_mime', 'cv_file_size', 'cv_uploaded_at'):
            fields.pop(key, None)
        return fields

    if not cv_name:
        raise RuntimeError('Le CV doit avoir un nom de fichier.')
    if cv_mime not in EURES_CV_ALLOWED_MIME_TYPES:
        raise RuntimeError('Format de CV non autorisé. Utilisez PDF, DOC, DOCX ou ODT.')
    if cv_size <= 0 or cv_size > EURES_CV_MAX_BYTES:
        raise RuntimeError('Le CV dépasse la taille autorisée (3 Mo maximum).')

    try:
        decoded = base64.b64decode(cv_base64, validate=True)
    except Exception as exc:
        raise RuntimeError('Le CV transmis est invalide.') from exc

    if len(decoded) != cv_size:
        raise RuntimeError('La taille du CV transmis ne correspond pas au contenu reçu.')

    fields['cv_file_name'] = cv_name
    fields['cv_file_mime'] = cv_mime
    fields['cv_file_size'] = len(decoded)
    fields['cv_uploaded_at'] = str((fields or {}).get('cv_uploaded_at') or _now_iso_utc()).strip()
    fields['tally_q36'] = cv_name
    return fields


def get_candidate_cv_attachment(fields: dict) -> dict | None:
    """Return a Brevo attachment payload for a stored candidate CV."""
    cv_base64 = str((fields or {}).get('cv_file_base64') or '').strip()
    cv_name = str((fields or {}).get('cv_file_name') or '').strip()
    if not cv_base64 or not cv_name:
        return None
    return {
        'name': cv_name,
        'content': cv_base64,
    }


def _eures_questionnaire_field_order(role: str) -> list[str]:
    if role == 'candidate':
        return [
            'nom', 'email', 'telephone', 'ville', 'pays', 'metier', 'competences',
            'langues', 'mobilite', 'disponibilite', 'contraintes_travail', 'permis_autorisations', 'permis_autorisations_autre',
            'cv_file_name', 'cv_uploaded_at',
            'response_received_at', 'response_status', 'id_tally', 'uuid',
            'tally_submitted_at', 'created_at', 'updated_at',
        ]
    return [
        'employeur', 'contact', 'email', 'telephone', 'pays', 'poste',
        'competences_clefs', 'langues_requises', 'date_debut', 'contraintes_travail', 'permis_autorisations', 'permis_autorisations_autre',
        'response_received_at', 'response_status',
        'id_tally', 'uuid', 'tally_submitted_at', 'created_at', 'updated_at',
    ]


def _build_eures_questionnaire_response_row(role: str, rec: dict) -> dict | None:
    fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
    if not isinstance(fields, dict):
        return None

    normalized_role = _normalize_eures_invitation_role(role)
    if normalized_role not in {'candidate', 'employer'}:
        return None

    hidden_exact = {
        'tally_raw_json',
        'matchings_json',
        'cv_file_base64',
        'cv_file_mime',
        'cv_file_size',
    }
    hidden_prefixes = (
        'admin_',
        'no_match_notification_',
        'new_job_request_',
        'new_employer_alert_',
        'linked_invitation_',
        'reminder_',
        'source_invitation_',
    )
    hidden_suffixes = (
        '_by',
        '_note',
        '_status',
    )

    preferred = _eures_questionnaire_field_order(normalized_role)
    candidate_keys = []
    seen = set()
    for key in fields.keys():
        key_str = str(key or '').strip()
        if not key_str or key_str in hidden_exact:
            continue
        if any(key_str.startswith(prefix) for prefix in hidden_prefixes):
            continue
        if key_str.startswith('employer_response'):
            continue
        if key_str not in {'tally_submitted_at', 'created_at', 'updated_at', 'response_status'} and any(key_str.endswith(suffix) for suffix in hidden_suffixes):
            continue
        if key_str in seen:
            continue
        seen.add(key_str)
        candidate_keys.append(key_str)

    ordered_keys = [key for key in preferred if key in candidate_keys]
    ordered_keys.extend(sorted(key for key in candidate_keys if key not in preferred))

    field_items = []
    for key in ordered_keys:
        value = _eures_questionnaire_field_value(fields.get(key))
        if not value:
            continue
        field_items.append({
            'key': key,
            'label': _eures_questionnaire_field_label(key, normalized_role),
            'value': value,
        })

    if normalized_role == 'candidate':
        title = str(fields.get('nom') or fields.get('email') or 'Candidat').strip()
        subtitle_parts = [fields.get('metier', ''), fields.get('pays', '')]
        summary_parts = [fields.get('langues', ''), fields.get('mobilite', ''), fields.get('disponibilite', '')]
    else:
        title = str(fields.get('employeur') or fields.get('poste') or _resolve_employer_recipient(fields) or 'Employeur').strip()
        subtitle_parts = [fields.get('poste', ''), fields.get('pays', '')]
        summary_parts = [fields.get('langues_requises', ''), fields.get('date_debut', ''), fields.get('competences_clefs', '')]

    submitted_at = _eures_response_received_at(fields)
    response_status = _normalize_eures_response_status(fields.get('response_status', '')) or 'active'
    cv_file_name = str(fields.get('cv_file_name') or '').strip()
    cv_available = normalized_role == 'candidate' and bool(cv_file_name and str(fields.get('cv_file_base64') or '').strip())

    row = {
        'role': normalized_role,
        'record_id': rec.get('id'),
        'record_key': fields.get('id_tally') or fields.get('uuid') or '',
        'title': title or ('Candidat' if normalized_role == 'candidate' else 'Employeur'),
        'subtitle': ' · '.join(str(part).strip() for part in subtitle_parts if str(part).strip()),
        'summary': ' · '.join(str(part).strip() for part in summary_parts if str(part).strip()),
        'submitted_at': submitted_at,
        'response_received_at': submitted_at,
        'response_status': response_status,
        'is_active': response_status == 'active',
        'response_disabled_at': str(fields.get('response_disabled_at') or '').strip(),
        'response_disabled_reason': str(fields.get('response_disabled_reason') or '').strip(),
        'updated_at': str(fields.get('updated_at') or '').strip(),
        'fields': field_items,
    }
    if cv_available:
        row['cv_download_url'] = f"/api/forms/eures-beta/admin/questionnaires/candidate/{rec.get('id')}/cv"
        row['cv_file_name'] = cv_file_name
    return row


def list_eures_admin_questionnaire_responses(role: str) -> list[dict]:
    """Return raw questionnaire responses from the candidate/employer Grist tables."""
    config = _get_eures_role_table_config(role)
    normalized_role = _normalize_eures_invitation_role(role)
    if not config or normalized_role not in {'candidate', 'employer'}:
        raise RuntimeError('EURES role table configuration is incomplete.')

    headers = _eures_admin_headers(config)
    rows = []
    for rec in fetch_table_records(config['doc_id'], config['table_id'], headers):
        row = _build_eures_questionnaire_response_row(normalized_role, rec)
        if row:
            rows.append(row)

    matching_rows = list_eures_admin_matchings(status='all')
    matching_map: dict[str, list[dict]] = {}
    for matching in matching_rows:
        candidate_key = str(matching.get('candidat_id') or '').strip()
        employer_key = str(matching.get('besoin_id') or '').strip()
        if normalized_role == 'candidate' and candidate_key:
            matching_map.setdefault(candidate_key, []).append({
                'matching_record_id': matching.get('record_id'),
                'score': _safe_int(matching.get('score')),
                'scoring_status': matching.get('scoring_status', ''),
                'admin_status': matching.get('admin_status', ''),
                'workflow_status': matching.get('workflow_status', ''),
                'counterpart_name': str((matching.get('employeur') or {}).get('employeur') or '').strip(),
                'counterpart_subtitle': str((matching.get('employeur') or {}).get('poste') or '').strip(),
            })
        if normalized_role == 'employer' and employer_key:
            matching_map.setdefault(employer_key, []).append({
                'matching_record_id': matching.get('record_id'),
                'score': _safe_int(matching.get('score')),
                'scoring_status': matching.get('scoring_status', ''),
                'admin_status': matching.get('admin_status', ''),
                'workflow_status': matching.get('workflow_status', ''),
                'counterpart_name': str((matching.get('candidat') or {}).get('nom') or '').strip(),
                'counterpart_subtitle': str((matching.get('candidat') or {}).get('metier') or '').strip(),
            })

    for row in rows:
        key = str(row.get('record_key') or '').strip()
        related = matching_map.get(key, [])
        related.sort(key=lambda item: (-int(item.get('score') or 0), -int(item.get('matching_record_id') or 0)))
        row['matchings'] = related
        row['matching_count'] = len(related)

    rows.sort(
        key=lambda row: (
            _parse_iso_datetime(row.get('submitted_at')) or datetime.min.replace(tzinfo=timezone.utc),
            int(row.get('record_id') or 0),
        ),
        reverse=True,
    )
    return rows


def delete_table_record_by_id(config: dict, record_id: int, headers: dict):
    """Delete one Grist record by id on any configured table."""
    delete_url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}/records/delete"
    resp = write_grist_records('POST', delete_url, [int(record_id)], headers)
    if resp.status_code not in {200, 202, 204}:
        raise RuntimeError(f'Failed to delete {config["table_id"]}: HTTP {resp.status_code} - {resp.text}')
    return resp


def delete_matching_records_for_response(role: str, response_key: str):
    """Delete Matchings rows linked to one candidate or employer response."""
    normalized_role = _normalize_eures_invitation_role(role)
    key_value = str(response_key or '').strip()
    if normalized_role not in {'candidate', 'employer'} or not key_value:
        return 0
    config = get_eures_matching_config()
    if not config:
        return 0
    headers = _eures_admin_headers(config)
    records = fetch_table_records(config['doc_id'], EURES_MATCHINGS_TABLE, headers)
    field_name = 'candidat_id' if normalized_role == 'candidate' else 'besoin_id'
    to_delete = [
        int(rec.get('id') or 0)
        for rec in records
        if str(((rec.get('fields') or {}).get(field_name) or '')).strip() == key_value
    ]
    to_delete = [record_id for record_id in to_delete if record_id]
    if not to_delete:
        return 0
    delete_url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{EURES_MATCHINGS_TABLE}/records/delete"
    resp = write_grist_records('POST', delete_url, to_delete, headers)
    if resp.status_code not in {200, 202, 204}:
        raise RuntimeError(f'Failed to delete related Matchings: HTTP {resp.status_code} - {resp.text}')
    return len(to_delete)


def queue_eures_new_job_request(record_id: int):
    """Mark an employer need when additional desired jobs were requested."""
    config = _get_eures_role_table_config('employer')
    if not config:
        raise RuntimeError('EURES employer table configuration is incomplete.')
    headers = _eures_admin_headers(config)
    update_table_record_by_id(
        config,
        record_id,
        {
            'new_job_request_status': 'pending',
            'new_job_request_created_at': _now_iso_utc(),
            'new_job_request_created_by': 'system_questionnaire_submission',
            'new_job_request_note': '',
        },
        headers,
        EURES_NEW_JOB_REQUEST_FIELDS,
    )


def _build_eures_new_job_request_row(rec: dict) -> dict | None:
    fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
    if not isinstance(fields, dict):
        return None
    status = _normalize_eures_new_job_request_status(fields.get('new_job_request_status', ''))
    requested_jobs = str(fields.get('autres_metiers_souhaites') or '').strip()
    if not status or not requested_jobs:
        return None
    recipient = _resolve_employer_recipient(fields)
    return {
        'record_id': rec.get('id'),
        'record_key': fields.get('id_tally') or fields.get('uuid') or '',
        'request_status': status,
        'created_at': fields.get('new_job_request_created_at', ''),
        'created_by': fields.get('new_job_request_created_by', ''),
        'processed_at': fields.get('new_job_request_processed_at', ''),
        'processed_by': fields.get('new_job_request_processed_by', ''),
        'note': fields.get('new_job_request_note', ''),
        'employeur': fields.get('employeur', ''),
        'contact': fields.get('contact', ''),
        'email': recipient,
        'poste': fields.get('poste', ''),
        'pays': fields.get('pays', ''),
        'requested_jobs': requested_jobs,
    }


def list_eures_admin_new_job_requests(status: str = 'all') -> list[dict]:
    """Return employer rows requesting additional job families."""
    config = _get_eures_role_table_config('employer')
    if not config:
        return []
    headers = _eures_admin_headers(config)
    rows = []
    for rec in fetch_table_records(config['doc_id'], config['table_id'], headers):
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        if not _is_eures_response_active(fields):
            continue
        row = _build_eures_new_job_request_row(rec)
        if not row:
            continue
        if status in EURES_NEW_JOB_REQUEST_ALLOWED_STATUSES and row['request_status'] != status:
            continue
        rows.append(row)
    rows.sort(key=lambda row: (str(row.get('created_at') or ''), int(row.get('record_id') or 0)), reverse=True)
    return rows


def queue_eures_new_employer_alert(record_id: int, invitation_linking: dict | None = None):
    """Mark an employer need submitted from a referred new company for admin vigilance."""
    config = _get_eures_role_table_config('employer')
    if not config:
        raise RuntimeError('EURES employer table configuration is incomplete.')
    headers = _eures_admin_headers(config)
    invitation_linking = invitation_linking if isinstance(invitation_linking, dict) else {}
    update_table_record_by_id(
        config,
        record_id,
        {
            'new_employer_alert_status': 'pending',
            'new_employer_alert_created_at': _now_iso_utc(),
            'new_employer_alert_created_by': 'system_questionnaire_submission',
            'new_employer_alert_note': '',
            'source_invitation_record_id': str(invitation_linking.get('invitation_record_id') or ''),
            'source_invitation_email': str(invitation_linking.get('email') or ''),
            'source_invitation_company': str(invitation_linking.get('company_name') or ''),
            'source_invitation_scope': str(invitation_linking.get('invite_scope') or ''),
            'sponsor_email': str(invitation_linking.get('sponsor_email') or ''),
            'sponsor_company_name': str(invitation_linking.get('sponsor_company_name') or ''),
        },
        headers,
        EURES_NEW_EMPLOYER_ALERT_FIELDS,
    )


def _build_eures_new_employer_alert_row(rec: dict) -> dict | None:
    fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
    if not isinstance(fields, dict):
        return None
    status = _normalize_eures_new_employer_alert_status(fields.get('new_employer_alert_status', ''))
    if not status:
        return None
    return {
        'record_id': rec.get('id'),
        'alert_status': status,
        'created_at': fields.get('new_employer_alert_created_at', ''),
        'created_by': fields.get('new_employer_alert_created_by', ''),
        'processed_at': fields.get('new_employer_alert_processed_at', ''),
        'processed_by': fields.get('new_employer_alert_processed_by', ''),
        'note': fields.get('new_employer_alert_note', ''),
        'employeur': fields.get('employeur', ''),
        'contact': fields.get('contact', ''),
        'email': _resolve_employer_recipient(fields),
        'poste': fields.get('poste', ''),
        'pays': fields.get('pays', ''),
        'source_invitation_record_id': fields.get('source_invitation_record_id', ''),
        'source_invitation_email': fields.get('source_invitation_email', ''),
        'source_invitation_company': fields.get('source_invitation_company', ''),
        'source_invitation_scope': fields.get('source_invitation_scope', ''),
        'sponsor_email': fields.get('sponsor_email', ''),
        'sponsor_company_name': fields.get('sponsor_company_name', ''),
    }


def list_eures_admin_new_employer_alerts(status: str = 'all') -> list[dict]:
    """Return employer needs submitted by newly referred employers."""
    config = _get_eures_role_table_config('employer')
    if not config:
        return []
    headers = _eures_admin_headers(config)
    rows = []
    for rec in fetch_table_records(config['doc_id'], config['table_id'], headers):
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        if not _is_eures_response_active(fields):
            continue
        row = _build_eures_new_employer_alert_row(rec)
        if not row:
            continue
        if status in EURES_NEW_EMPLOYER_ALERT_ALLOWED_STATUSES and row['alert_status'] != status:
            continue
        rows.append(row)
    rows.sort(key=lambda row: (str(row.get('created_at') or ''), int(row.get('record_id') or 0)), reverse=True)
    return rows


def _build_eures_feedback_url(record_id: int, response: str) -> str:
    token = get_eures_email_action_serializer().dumps({
        'record_id': int(record_id),
        'response': response,
    })
    return f"{get_public_app_base_url()}/eures-beta/matching-feedback?token={token}"


def _matching_outgoing_comment(row: dict, recipient: str) -> str:
    """Return the optional admin comment to inject into outgoing matching emails."""
    if not isinstance(row, dict):
        return ''
    recipient_key = 'employer_email_comment' if recipient == 'employer' else 'candidate_email_comment'
    if recipient_key in row:
        return str(row.get(recipient_key) or '').strip()
    # Backward compatibility only for legacy row payloads that do not expose
    # recipient-specific fields yet.
    comment = str(row.get('admin_decision_note') or '').strip()
    if comment:
        return comment
    return str(row.get('manual_matching_note') or '').strip()


def _format_email_comment_text(comment: str) -> str:
    return '\n'.join(line.strip() for line in str(comment or '').splitlines()).strip()


def _format_email_comment_html(comment: str) -> str:
    lines = [escape(line.strip()) for line in str(comment or '').splitlines() if line.strip()]
    return '<br>'.join(lines)


def build_brevo_matching_email(row: dict) -> tuple[str, str, str, str]:
    """Build recipient, subject, text body and HTML body for one accepted matching."""
    candidat = row.get('candidat', {}) if isinstance(row.get('candidat'), dict) else {}
    employeur = row.get('employeur', {}) if isinstance(row.get('employeur'), dict) else {}
    recipient = _resolve_employer_recipient(employeur)
    if not recipient:
        raise RuntimeError('Employer contact email is missing for accepted matching.')

    poste = employeur.get('poste', '') or 'Poste non renseigné'
    employeur_name = employeur.get('employeur', '') or 'votre structure'
    subject = f"[EURES beta] Proposition de candidature pour votre besoin - {poste}"

    reasons = row.get('raisons', [])
    if not isinstance(reasons, list):
        reasons = _split_matching_text(reasons)

    reasons_text = '\n'.join(f"- {item}" for item in reasons) if reasons else "- Profil cohérent avec votre besoin"
    reasons_html = ''.join(
        f"<li style=\"margin:0 0 8px;\">{escape(item)}</li>" for item in reasons
    ) or "<li style=\"margin:0 0 8px;\">Profil cohérent avec votre besoin</li>"

    candidate_name = str(candidat.get('nom') or 'Profil candidat')
    candidate_phone = str(candidat.get('telephone') or 'Non renseigné')
    candidate_city = str(candidat.get('ville') or 'Non renseignée')
    cv_file_name = str(candidat.get('cv_file_name') or '').strip()
    cv_line = f"- CV joint : {cv_file_name}\n" if cv_file_name else ""
    cv_html = (
        f"<p style=\"margin:10px 0 0;font-size:14px;line-height:1.7;color:#e6efe9;\">CV joint : {escape(cv_file_name)}</p>"
        if cv_file_name else ""
    )
    outgoing_comment = _matching_outgoing_comment(row, 'employer')
    outgoing_comment_text = _format_email_comment_text(outgoing_comment)
    outgoing_comment_html = _format_email_comment_html(outgoing_comment)
    comment_block_text = (
        f"Commentaire du conseiller EURES\n{outgoing_comment_text}\n\n"
        if outgoing_comment_text else ""
    )
    comment_block_html = (
        f"""
                <div style="background:#f3f7fc;border:1px solid #d7e2f0;border-radius:12px;padding:18px 20px;margin:18px 0 0;">
                  <div style="font-size:12px;letter-spacing:1.3px;text-transform:uppercase;color:#35557a;margin-bottom:10px;">Commentaire du conseiller EURES</div>
                  <p style="margin:0;font-size:15px;line-height:1.7;color:#22374f;">{outgoing_comment_html}</p>
                </div>
        """.strip()
        if outgoing_comment_html else ""
    )
    signature_name = get_eures_mail_signature_name()
    privacy_url = get_eures_privacy_url('fr')
    contact_yes_url = _build_eures_feedback_url(int(row.get('record_id') or 0), 'contact')
    contact_no_url = _build_eures_feedback_url(int(row.get('record_id') or 0), 'not_contact')
    body_text = (
        f"Bonjour,\n\n"
        f"Nous vous proposons un profil susceptible de correspondre à votre besoin de recrutement pour le poste : {poste}.\n\n"
        f"Entreprise : {employeur_name}\n"
        f"Poste recherché : {poste}\n"
        f"Date de début souhaitée : {employeur.get('date_debut', 'Non renseignée')}\n\n"
        f"Candidat\n"
        f"- Nom : {candidate_name}\n"
        f"- Email : {candidat.get('email', 'Non renseigné')}\n"
        f"- Téléphone : {candidate_phone}\n"
        f"- Ville actuelle : {candidate_city}\n"
        f"- Pays de résidence : {candidat.get('pays', 'Non renseigné')}\n"
        f"- Métier / secteur : {candidat.get('metier', 'Non renseigné')}\n"
        f"- Compétences : {candidat.get('competences', 'Non renseigné')}\n"
        f"- Langues : {candidat.get('langues', 'Non renseigné')}\n"
        f"- Mobilité : {candidat.get('mobilite', 'Non renseigné')}\n"
        f"- Disponibilité : {candidat.get('disponibilite', 'Non renseigné')}\n"
        f"{cv_line}\n"
        f"Pourquoi ce profil a été retenu\n"
        f"{reasons_text}\n\n"
        f"{comment_block_text}"
        "Actions rapides\n"
        f"- Je vais le contacter : {contact_yes_url}\n"
        f"- Je ne vais pas le contacter : {contact_no_url}\n\n"
        "Vous pouvez aussi répondre directement à cet email afin que nous poursuivions la mise en relation.\n\n"
        f"Informations sur vos données : {privacy_url}\n\n"
        "Cordialement,\n"
        f"{signature_name}\n"
        "EURES beta\n"
    )

    body_html = f"""
<!doctype html>
<html lang="fr">
  <body style="margin:0;padding:0;background:#f4efe6;font-family:Georgia,'Times New Roman',serif;color:#1f1f1f;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4efe6;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:720px;background:#fffdf9;border:1px solid #e7dcc7;border-radius:18px;overflow:hidden;">
            <tr>
              <td style="padding:28px 32px;background:linear-gradient(135deg,#103a2b 0%,#1f5a45 100%);color:#ffffff;">
                <div style="font-size:13px;letter-spacing:1.6px;text-transform:uppercase;opacity:0.82;">EURES beta</div>
                <h1 style="margin:10px 0 0;font-size:30px;line-height:1.2;font-weight:700;">Proposition de candidature</h1>
                <p style="margin:12px 0 0;font-size:16px;line-height:1.6;max-width:560px;">
                  Nous vous transmettons un profil pouvant correspondre à votre besoin de recrutement pour le poste de
                  <strong>{escape(poste)}</strong>.
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 32px 12px;">
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">
                  Bonjour,
                </p>
                <p style="margin:0 0 22px;font-size:16px;line-height:1.7;">
                  Après analyse de votre besoin, nous avons identifié un profil candidat qui nous semble pertinent pour
                  <strong>{escape(employeur_name)}</strong>.
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:0 32px 28px;">
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                  <tr>
                    <td valign="top" width="50%" style="padding:0 10px 0 0;">
                      <div style="height:100%;background:#f8f4ec;border:1px solid #eadfcb;border-radius:14px;padding:20px;">
                        <div style="font-size:12px;letter-spacing:1.3px;text-transform:uppercase;color:#6a5a42;margin-bottom:10px;">Votre besoin</div>
                        <h2 style="margin:0 0 14px;font-size:22px;line-height:1.3;color:#103a2b;">{escape(poste)}</h2>
                        <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Entreprise :</strong><br>{escape(employeur_name)}</p>
                        <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Lieu / pays :</strong><br>{escape(str(employeur.get('pays') or 'Non renseigné'))}</p>
                        <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Langues attendues :</strong><br>{_format_email_multiline(employeur.get('langues_requises', ''))}</p>
                        <p style="margin:0;font-size:15px;line-height:1.6;"><strong>Date de début :</strong><br>{escape(str(employeur.get('date_debut') or 'Non renseignée'))}</p>
                      </div>
                    </td>
                    <td valign="top" width="50%" style="padding:0 0 0 10px;">
                      <div style="height:100%;background:#fffaf2;border:1px solid #eadfcb;border-radius:14px;padding:20px;">
                        <div style="font-size:12px;letter-spacing:1.3px;text-transform:uppercase;color:#6a5a42;margin-bottom:10px;">Profil proposé</div>
                        <h2 style="margin:0 0 14px;font-size:22px;line-height:1.3;color:#103a2b;">{escape(candidate_name)}</h2>
                        <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Email :</strong><br>{escape(str(candidat.get('email') or 'Non renseigné'))}</p>
                        <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Téléphone :</strong><br>{escape(candidate_phone)}</p>
                        <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Ville actuelle :</strong><br>{escape(candidate_city)}</p>
                        <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Pays de résidence :</strong><br>{escape(str(candidat.get('pays') or 'Non renseigné'))}</p>
                        <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Métier / secteur :</strong><br>{_format_email_multiline(candidat.get('metier', ''))}</p>
                        <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Langues :</strong><br>{_format_email_multiline(candidat.get('langues', ''))}</p>
                        <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Mobilité :</strong><br>{_format_email_multiline(candidat.get('mobilite', ''))}</p>
                        <p style="margin:0;font-size:15px;line-height:1.6;"><strong>Disponibilité :</strong><br>{_format_email_multiline(candidat.get('disponibilite', ''))}</p>
                      </div>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
            <tr>
              <td style="padding:0 32px 12px;">
                <div style="background:#fbf7ef;border-left:4px solid #c6932d;border-radius:12px;padding:18px 20px;">
                  <div style="font-size:12px;letter-spacing:1.3px;text-transform:uppercase;color:#7a6232;margin-bottom:10px;">Pourquoi ce profil</div>
                  <ul style="margin:0;padding-left:20px;font-size:15px;line-height:1.7;">
                    {reasons_html}
                  </ul>
                </div>
                {comment_block_html}
              </td>
            </tr>
            <tr>
              <td style="padding:12px 32px 0;">
                <div style="background:#103a2b;border-radius:14px;padding:22px;color:#ffffff;">
                  <p style="margin:0 0 10px;font-size:17px;line-height:1.6;"><strong>Suite proposée</strong></p>
                  <p style="margin:0;font-size:15px;line-height:1.7;">
                    Si ce profil retient votre attention, vous pouvez le contacter directement ou nous répondre par email.
                  </p>
                  <table role="presentation" cellspacing="0" cellpadding="0" style="margin-top:18px;">
                    <tr>
                      <td style="padding:0 12px 12px 0;">
                        <a href="{escape(contact_yes_url)}" style="display:inline-block;padding:12px 18px;border-radius:999px;background:#f2c04c;color:#173a2a;text-decoration:none;font-size:14px;font-weight:700;">Je vais le contacter</a>
                      </td>
                      <td style="padding:0 0 12px 0;">
                        <a href="{escape(contact_no_url)}" style="display:inline-block;padding:12px 18px;border-radius:999px;background:#ffffff;color:#173a2a;text-decoration:none;font-size:14px;font-weight:700;">Je ne vais pas le contacter</a>
                      </td>
                    </tr>
                  </table>
                  <p style="margin:4px 0 0;font-size:14px;line-height:1.7;color:#e6efe9;">
                    Coordonnées directes du candidat : {escape(str(candidat.get('email') or 'Non renseigné'))}
                    {' - ' if candidate_phone and candidate_phone != 'Non renseigné' else ''}
                    {escape(candidate_phone) if candidate_phone and candidate_phone != 'Non renseigné' else ''}
                  </p>
                  {cv_html}
                </div>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 32px 32px;">
                <p style="margin:0;font-size:15px;line-height:1.7;">
                  Cordialement,<br>
                  <strong>{escape(signature_name)}</strong><br>
                  EURES beta
                </p>
                <p style="margin:18px 0 0;font-size:13px;line-height:1.7;color:#6b6256;">
                  Informations sur le traitement de vos données :
                  <a href="{escape(privacy_url)}" style="color:#103a2b;">consulter la notice de confidentialité</a>.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
    return recipient, subject, body_text, body_html


def build_brevo_candidate_matching_notification_email(row: dict) -> tuple[str, str, str, str]:
    """Build the candidate notification email once the profile is sent to the employer."""
    candidat = row.get('candidat', {}) if isinstance(row.get('candidat'), dict) else {}
    employeur = row.get('employeur', {}) if isinstance(row.get('employeur'), dict) else {}
    recipient = normalize_email(candidat.get('email', ''))
    if not recipient:
        raise RuntimeError('Candidate email is missing for accepted matching notification.')

    employeur_name = str(employeur.get('employeur') or 'un employeur partenaire').strip() or 'un employeur partenaire'
    candidate_name = str(candidat.get('nom') or '').strip()
    hello = "Bonjour,"
    if candidate_name:
        hello = "Bonjour,"
    outgoing_comment = _matching_outgoing_comment(row, 'candidate')
    outgoing_comment_text = _format_email_comment_text(outgoing_comment)
    outgoing_comment_html = _format_email_comment_html(outgoing_comment)
    comment_block_text = (
        f"Commentaire de votre conseiller EURES\n{outgoing_comment_text}\n\n"
        if outgoing_comment_text else ""
    )
    comment_block_html = (
        f"""
                <div style="border:1px solid #d7e2f0;border-radius:14px;background:#f3f7fc;padding:18px 20px;margin:0 0 18px;">
                  <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Commentaire de votre conseiller EURES</strong></p>
                  <p style="margin:0;font-size:15px;line-height:1.7;color:#22374f;">{outgoing_comment_html}</p>
                </div>
        """.strip()
        if outgoing_comment_html else ""
    )
    privacy_url = get_eures_privacy_url('fr')

    subject = f"[EURES beta] Votre candidature a ete transmise a {employeur_name}"
    body_text = (
        f"{hello}\n\n"
        f"Nous vous informons que votre candidature a ete transmise a {employeur_name}.\n\n"
        f"{comment_block_text}"
        "Si cet employeur souhaite echanger avec vous, il pourra vous contacter directement.\n\n"
        "Nous vous invitons a :\n"
        "- repondre aux appels masques ou aux numeros inconnus,\n"
        "- verifier regulierement votre boite e-mail,\n"
        "- consulter egalement vos courriers indesirables ou spams.\n\n"
        f"Informations sur vos donnees : {privacy_url}\n\n"
        "Cordialement,\n"
        f"{get_eures_mail_signature_name()}\n"
        "EURES beta\n"
    )

    body_html = f"""
<!doctype html>
<html lang="fr">
  <body style="margin:0;padding:0;background:#f4efe6;font-family:Georgia,'Times New Roman',serif;color:#1f1f1f;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4efe6;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;background:#fffdf9;border:1px solid #e7dcc7;border-radius:18px;overflow:hidden;">
            <tr>
              <td style="padding:28px 32px;background:linear-gradient(135deg,#0f2742 0%,#004494 100%);color:#ffffff;">
                <div style="font-size:13px;letter-spacing:1.6px;text-transform:uppercase;opacity:0.82;">EURES beta</div>
                <h1 style="margin:10px 0 0;font-size:30px;line-height:1.2;font-weight:700;">Candidature transmise</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 32px;">
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">Bonjour,</p>
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">
                  Nous vous informons que votre candidature a ete transmise a
                  <strong>{escape(employeur_name)}</strong>.
                </p>
                {comment_block_html}
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">
                  Si cet employeur souhaite echanger avec vous, il pourra vous contacter directement.
                </p>
                <div style="border:1px solid #e7dcc7;border-radius:14px;background:#f8f4ec;padding:18px 20px;">
                  <p style="margin:0 0 10px;font-size:15px;line-height:1.6;"><strong>Nous vous invitons a :</strong></p>
                  <ul style="margin:0;padding-left:20px;font-size:15px;line-height:1.7;color:#3b3b3b;">
                    <li>repondre aux appels masques ou aux numeros inconnus,</li>
                    <li>verifier regulierement votre boite e-mail,</li>
                    <li>consulter egalement vos courriers indesirables ou spams.</li>
                  </ul>
                </div>
                <p style="margin:22px 0 0;font-size:15px;line-height:1.7;">
                  Cordialement,<br><br>{escape(get_eures_mail_signature_name())}<br>EURES beta
                </p>
                <p style="margin:18px 0 0;font-size:13px;line-height:1.7;color:#6b6256;">
                  Informations sur le traitement de vos données :
                  <a href="{escape(privacy_url)}" style="color:#004494;">consulter la notice de confidentialité</a>.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
    return recipient, subject, body_text, body_html


def send_brevo_transactional_email(
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str,
    attachments: list[dict] | None = None,
):
    """Send one transactional email via Brevo."""
    brevo = get_brevo_config()
    if not brevo['api_key'] or not brevo['from_email']:
        raise RuntimeError('Brevo configuration is incomplete.')

    payload = {
        'sender': {
            'email': brevo['from_email'],
            'name': brevo['from_name'],
        },
        'to': [{'email': to_email}],
        'subject': subject,
        'textContent': text_body,
        'htmlContent': html_body,
    }
    if attachments:
        payload['attachment'] = attachments
    resp = requests.post(
        'https://api.brevo.com/v3/smtp/email',
        headers={
            'accept': 'application/json',
            'content-type': 'application/json',
            'api-key': brevo['api_key'],
        },
        json=payload,
        timeout=30,
    )
    if resp.status_code not in {200, 201, 202}:
        raise RuntimeError(f'Brevo send failed: HTTP {resp.status_code} - {resp.text}')
    return _parse_response_json_safe(resp)


def build_brevo_candidate_no_match_email(row: dict) -> tuple[str, str, str, str]:
    payload = row.get('payload', {}) if isinstance(row.get('payload'), dict) else {}
    recipient = normalize_email(payload.get('email', ''))
    if not recipient:
        raise RuntimeError('Candidate email is missing for no-match notification.')
    privacy_url = get_eures_privacy_url('fr')
    subject = "[EURES beta] Aucune mise en relation immédiate pour le moment"
    body_text = (
        "Bonjour,\n\n"
        "Nous vous confirmons la bonne réception de votre questionnaire EURES beta.\n\n"
        "A ce stade, aucun matching n'a pu être réalisé immédiatement selon vos critères.\n"
        "Votre profil reste pris en compte et vous serez prévenu dès qu'une mise en relation pertinente pourra être opérée.\n\n"
        f"Informations sur vos données : {privacy_url}\n\n"
        "Cordialement,\n"
        f"{get_eures_mail_signature_name()}\n"
        f"{get_eures_mail_signature_role()}\n"
        "EURES beta\n"
    )
    body_html = f"""
<!doctype html>
<html lang="fr">
  <body style="margin:0;padding:0;background:#f4efe6;font-family:Georgia,'Times New Roman',serif;color:#1f1f1f;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4efe6;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;background:#fffdf9;border:1px solid #e7dcc7;border-radius:18px;overflow:hidden;">
            <tr>
              <td style="padding:28px 32px;background:linear-gradient(135deg,#0f2742 0%,#004494 100%);color:#ffffff;">
                <div style="font-size:13px;letter-spacing:1.6px;text-transform:uppercase;opacity:0.82;">EURES beta</div>
                <h1 style="margin:10px 0 0;font-size:30px;line-height:1.2;font-weight:700;">Suivi de votre candidature</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 32px;">
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">Bonjour,</p>
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">Nous vous confirmons la bonne réception de votre questionnaire EURES beta.</p>
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">À ce stade, aucun matching n'a pu être réalisé immédiatement selon vos critères.</p>
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">Votre profil reste pris en compte et vous serez prévenu dès qu'une mise en relation pertinente pourra être opérée.</p>
                <p style="margin:18px 0 0;font-size:13px;line-height:1.7;color:#6b6256;">
                  Informations sur le traitement de vos données :
                  <a href="{escape(privacy_url)}" style="color:#004494;">consulter la notice de confidentialité</a>.
                </p>
                <p style="margin:22px 0 0;font-size:15px;line-height:1.7;">
                  Cordialement,<br><br>{escape(get_eures_mail_signature_name())}<br>{escape(get_eures_mail_signature_role())}<br>EURES beta
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
    return recipient, subject, body_text, body_html


def build_brevo_employer_no_match_email(row: dict) -> tuple[str, str, str, str]:
    payload = row.get('payload', {}) if isinstance(row.get('payload'), dict) else {}
    recipient = _resolve_employer_recipient(payload)
    if not recipient:
        raise RuntimeError('Employer email is missing for no-match notification.')
    privacy_url = get_eures_privacy_url('fr')
    poste = str(payload.get('poste') or 'votre besoin').strip()
    subject = f"[EURES beta] Suivi de votre besoin de recrutement - {poste}"
    body_text = (
        "Bonjour,\n\n"
        "Nous vous confirmons la bonne réception de votre questionnaire EURES beta.\n\n"
        "A ce stade, aucun matching n'a pu être généré immédiatement pour votre besoin.\n"
        "Nous allons poursuivre la recherche de profils pertinents dans la base EURES et reviendrons vers vous dès qu'une candidature adaptée pourra être proposée.\n\n"
        f"Informations sur vos données : {privacy_url}\n\n"
        "Cordialement,\n"
        f"{get_eures_mail_signature_name()}\n"
        f"{get_eures_mail_signature_role()}\n"
        "EURES beta\n"
    )
    body_html = f"""
<!doctype html>
<html lang="fr">
  <body style="margin:0;padding:0;background:#f4efe6;font-family:Georgia,'Times New Roman',serif;color:#1f1f1f;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f4efe6;padding:24px 12px;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:680px;background:#fffdf9;border:1px solid #e7dcc7;border-radius:18px;overflow:hidden;">
            <tr>
              <td style="padding:28px 32px;background:linear-gradient(135deg,#103a2b 0%,#1f5a45 100%);color:#ffffff;">
                <div style="font-size:13px;letter-spacing:1.6px;text-transform:uppercase;opacity:0.82;">EURES beta</div>
                <h1 style="margin:10px 0 0;font-size:30px;line-height:1.2;font-weight:700;">Suivi de votre besoin</h1>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 32px;">
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">Bonjour,</p>
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">Nous vous confirmons la bonne réception de votre questionnaire EURES beta.</p>
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">À ce stade, aucun matching n'a pu être généré immédiatement pour votre besoin.</p>
                <p style="margin:0 0 18px;font-size:16px;line-height:1.7;">Nous allons poursuivre la recherche de profils pertinents dans la base EURES et reviendrons vers vous dès qu'une candidature adaptée pourra être proposée.</p>
                <p style="margin:18px 0 0;font-size:13px;line-height:1.7;color:#6b6256;">
                  Informations sur le traitement de vos données :
                  <a href="{escape(privacy_url)}" style="color:#103a2b;">consulter la notice de confidentialité</a>.
                </p>
                <p style="margin:22px 0 0;font-size:15px;line-height:1.7;">
                  Cordialement,<br><br>{escape(get_eures_mail_signature_name())}<br>{escape(get_eures_mail_signature_role())}<br>EURES beta
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
""".strip()
    return recipient, subject, body_text, body_html


def list_eures_admin_matchings(status: str = 'all', include_candidate_cv: bool = False) -> list[dict]:
    """Return matchings joined with candidate/employer info for the admin UI."""
    config = get_eures_matching_config()
    candidate_config = get_form_config('eures-beta', 'candidate')
    employer_config = get_form_config('eures-beta', 'employer')
    if not config or not candidate_config or not employer_config:
        raise RuntimeError('EURES beta Grist configuration is incomplete.')

    headers = _eures_admin_headers(config)
    candidate_headers = _eures_admin_headers(candidate_config)
    employer_headers = _eures_admin_headers(employer_config)

    matchings = fetch_table_records(config['doc_id'], EURES_MATCHINGS_TABLE, headers)
    candidats = fetch_table_records(candidate_config['doc_id'], EURES_CANDIDATS_TABLE, candidate_headers)
    besoins = fetch_table_records(employer_config['doc_id'], EURES_BESOINS_TABLE, employer_headers)

    candidats_by_id = {
        str((rec.get('fields') or {}).get('id_tally') or (rec.get('fields') or {}).get('uuid') or ''): rec.get('fields', {})
        for rec in candidats
        if isinstance(rec, dict) and _is_eures_response_active((rec.get('fields') or {}))
    }
    besoins_by_id = {
        str((rec.get('fields') or {}).get('id_tally') or (rec.get('fields') or {}).get('uuid') or ''): rec.get('fields', {})
        for rec in besoins
        if isinstance(rec, dict) and _is_eures_response_active((rec.get('fields') or {}))
    }

    rows = []
    for rec in matchings:
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        if not fields:
            continue
        scoring_status = str(fields.get('statut') or '').strip().lower()
        admin_status = _eures_admin_status(fields)
        if scoring_status not in {'a_valider', 'auto_envoyable'} and admin_status == 'pending':
            continue
        if status in {'pending', 'accepted', 'refused'} and admin_status != status:
            continue

        besoin_id = str(fields.get('besoin_id') or '')
        candidat_id = str(fields.get('candidat_id') or '')
        candidat = candidats_by_id.get(candidat_id, {})
        besoin = besoins_by_id.get(besoin_id, {})
        if not candidat or not besoin:
            continue
        candidat_job_titles = ' | '.join(
            str(candidat.get(field_name) or '').strip()
            for field_name in EURES_CANDIDAT_SECTOR_JOB_TITLE_FIELDS.values()
            if str(candidat.get(field_name) or '').strip()
        )
        employeur_job_titles = ' | '.join(
            str(besoin.get(field_name) or '').strip()
            for field_name in EURES_EMPLOYEUR_SECTOR_JOB_TITLE_FIELDS.values()
            if str(besoin.get(field_name) or '').strip()
        )

        rows.append({
            'record_id': rec.get('id'),
            'besoin_id': besoin_id,
            'candidat_id': candidat_id,
            'score': _safe_int(fields.get('score')),
            'scoring_status': scoring_status,
            'admin_status': admin_status,
            'workflow_status': _matching_workflow_status(fields),
            'score_metier': _safe_int(fields.get('score_metier')),
            'score_competences': _safe_int(fields.get('score_competences')),
            'score_langues': _safe_int(fields.get('score_langues')),
            'score_mobilite': _safe_int(fields.get('score_mobilite')),
            'score_disponibilite': _safe_int(fields.get('score_disponibilite')),
            'score_salaire': _safe_int(fields.get('score_salaire')),
            'raisons': _split_matching_text(fields.get('raisons')),
            'points_faibles': _split_matching_text(fields.get('points_faibles')),
            'date_calcul': fields.get('date_calcul', ''),
            'admin_decision_at': fields.get('admin_decision_at', ''),
            'admin_decision_by': fields.get('admin_decision_by', ''),
            'admin_decision_note': fields.get('admin_decision_note', ''),
            'employer_email_comment': fields.get('employer_email_comment', ''),
            'candidate_email_comment': fields.get('candidate_email_comment', ''),
            'manual_matching_source': fields.get('manual_matching_source', ''),
            'manual_matching_created_at': fields.get('manual_matching_created_at', ''),
            'manual_matching_created_by': fields.get('manual_matching_created_by', ''),
            'manual_matching_note': fields.get('manual_matching_note', ''),
            'workflow_status_updated_at': fields.get('workflow_status_updated_at', ''),
            'workflow_status_updated_by': fields.get('workflow_status_updated_by', ''),
            'sent_to_employer_at': fields.get('sent_to_employer_at', ''),
            'sent_to_employer_by': fields.get('sent_to_employer_by', ''),
            'employer_response': fields.get('employer_response', ''),
            'employer_response_at': fields.get('employer_response_at', ''),
            'mise_en_relation_at': fields.get('mise_en_relation_at', ''),
            'mise_en_relation_by': fields.get('mise_en_relation_by', ''),
            'embauche_confirmee_at': fields.get('embauche_confirmee_at', ''),
            'embauche_confirmee_by': fields.get('embauche_confirmee_by', ''),
            'candidat': {
                'nom': candidat.get('nom', ''),
                'email': candidat.get('email', ''),
                'telephone': candidat.get('telephone', ''),
                'ville': candidat.get('ville', ''),
                'pays': candidat.get('pays', ''),
                'metier': candidat.get('metier', ''),
                'intitules_poste': candidat_job_titles,
                'langues': candidat.get('langues', ''),
                'mobilite': candidat.get('mobilite', ''),
                'disponibilite': candidat.get('disponibilite', ''),
                'competences': candidat.get('competences', ''),
                'cv_file_name': candidat.get('cv_file_name', ''),
                'cv_file_base64': candidat.get('cv_file_base64', '') if include_candidate_cv else '',
            },
            'employeur': {
                'employeur': besoin.get('employeur', ''),
                'contact': besoin.get('contact', ''),
                'email': _resolve_employer_recipient(besoin),
                'pays': besoin.get('pays', ''),
                'poste': besoin.get('poste', ''),
                'intitules_poste': employeur_job_titles,
                'langues_requises': besoin.get('langues_requises', ''),
                'date_debut': besoin.get('date_debut', ''),
                'competences_clefs': besoin.get('competences_clefs', ''),
                'contraintes_travail': besoin.get('contraintes_travail', ''),
            },
        })

    rows.sort(key=lambda row: (row['admin_status'] != 'pending', -row['score'], -(int(row['record_id'] or 0))))
    return rows


def _parse_iso_datetime(value) -> datetime | None:
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        if raw.endswith('Z'):
            return datetime.fromisoformat(raw.replace('Z', '+00:00'))
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def _same_utc_day(value, target_day: datetime | None = None) -> bool:
    dt = _parse_iso_datetime(value)
    if not dt:
        return False
    target = target_day or datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).date() == target.astimezone(timezone.utc).date()


def _mean_hours(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def _compute_eures_delay_hours(start_value, end_value) -> float | None:
    start_dt = _parse_iso_datetime(start_value)
    end_dt = _parse_iso_datetime(end_value)
    if not start_dt or not end_dt:
        return None
    delta = (end_dt - start_dt).total_seconds() / 3600
    if delta < 0:
        return None
    return delta


def build_eures_admin_tasks(status: str = 'pending') -> list[dict]:
    """Return one unified admin task list for the cockpit."""
    rows = []
    invitations = list_eures_invitations()

    for row in list_eures_admin_matchings(status='all'):
        task_status = 'pending'
        if row.get('admin_status') == 'accepted':
            task_status = 'done'
        elif row.get('admin_status') == 'refused':
            task_status = 'dismissed'
        if status != 'all' and task_status != status:
            continue
        rows.append({
            'task_type': 'matching_review',
            'status': task_status,
            'priority': 'high' if row.get('scoring_status') == 'auto_envoyable' else 'normal',
            'created_at': row.get('date_calcul', ''),
            'updated_at': row.get('admin_decision_at') or row.get('workflow_status_updated_at') or row.get('date_calcul', ''),
            'record_id': row.get('record_id'),
            'title': f"{row.get('employeur', {}).get('poste') or 'Poste non renseigné'} · {row.get('candidat', {}).get('nom') or 'Candidat'}",
            'subtitle': f"{row.get('employeur', {}).get('employeur') or 'Entreprise non renseignée'} · score {row.get('score', 0)}",
            'summary': 'Validation manuelle du matching proposée.',
            'matching': row,
        })

    for row in list_eures_admin_no_match_notifications(status='all'):
        task_status = 'pending'
        if row.get('notification_status') == 'sent':
            task_status = 'done'
        elif row.get('notification_status') == 'dismissed':
            task_status = 'dismissed'
        if status != 'all' and task_status != status:
            continue
        rows.append({
            'task_type': 'no_match_followup',
            'status': task_status,
            'priority': 'normal',
            'created_at': row.get('created_at', ''),
            'updated_at': row.get('sent_at') or row.get('dismissed_at') or row.get('created_at', ''),
            'record_id': row.get('record_id'),
            'role': row.get('role'),
            'title': row.get('title') or ('Candidat' if row.get('role') == 'candidate' else 'Employeur'),
            'subtitle': row.get('subtitle') or row.get('recipient_email') or '',
            'summary': 'Aucun matching immédiat: notification manuelle à valider.',
            'no_match': row,
        })

    for row in list_eures_admin_new_job_requests(status='all'):
        task_status = 'pending'
        if row.get('request_status') == 'processed':
            task_status = 'done'
        elif row.get('request_status') == 'dismissed':
            task_status = 'dismissed'
        if status != 'all' and task_status != status:
            continue
        rows.append({
            'task_type': 'new_job_request',
            'status': task_status,
            'priority': 'normal',
            'created_at': row.get('created_at', ''),
            'updated_at': row.get('processed_at') or row.get('created_at', ''),
            'record_id': row.get('record_id'),
            'title': row.get('employeur') or 'Entreprise non renseignée',
            'subtitle': row.get('poste') or 'Poste non renseigné',
            'summary': row.get('requested_jobs') or 'Demande de nouveaux métiers',
            'new_job': row,
        })

    for row in list_eures_admin_new_employer_alerts(status='all'):
        task_status = 'pending'
        if row.get('alert_status') == 'reviewed':
            task_status = 'done'
        elif row.get('alert_status') == 'dismissed':
            task_status = 'dismissed'
        if status != 'all' and task_status != status:
            continue
        rows.append({
            'task_type': 'new_employer_alert',
            'status': task_status,
            'priority': 'high',
            'created_at': row.get('created_at', ''),
            'updated_at': row.get('processed_at') or row.get('created_at', ''),
            'record_id': row.get('record_id'),
            'title': row.get('employeur') or 'Nouvel employeur',
            'subtitle': row.get('poste') or 'Besoin employeur',
            'summary': 'Besoin déposé par un employeur recommandé: vigilance manuelle demandée.',
            'new_employer': row,
        })

    for row in invitations:
        followup_status = _normalize_eures_duplicate_followup_status(row.get('duplicate_followup_status', ''))
        if not followup_status:
            continue
        task_status = 'pending'
        if followup_status == 'reminded':
            task_status = 'done'
        elif followup_status == 'ignored':
            task_status = 'dismissed'
        if status != 'all' and task_status != status:
            continue
        target_type = str(row.get('duplicate_followup_type') or '').strip().lower()
        target_status = str(row.get('duplicate_followup_target_status') or '').strip().lower()
        can_remind = target_type == 'existing_invitation' and target_status == 'invitation_envoyee'
        task_title = (
            row.get('company_name')
            or ' '.join(part for part in [row.get('first_name'), row.get('last_name')] if str(part or '').strip())
            or row.get('email')
            or 'Invitation en doublon'
        )
        rows.append({
            'task_type': 'duplicate_invitation_followup',
            'status': task_status,
            'priority': 'normal',
            'created_at': row.get('duplicate_followup_created_at') or row.get('invitation_status_updated_at') or '',
            'updated_at': row.get('duplicate_followup_processed_at') or row.get('duplicate_followup_created_at') or '',
            'record_id': row.get('record_id'),
            'title': task_title,
            'subtitle': row.get('email') or '',
            'summary': row.get('duplicate_followup_message') or 'Adresse déjà connue: relance ou clôture à confirmer.',
            'duplicate_followup': {
                **row,
                'can_remind': can_remind,
            },
        })

    priority_rank = {'high': 0, 'normal': 1, 'low': 2}
    status_rank = {'pending': 0, 'done': 1, 'dismissed': 2}
    rows.sort(
        key=lambda row: (
            status_rank.get(str(row.get('status') or ''), 9),
            priority_rank.get(str(row.get('priority') or ''), 9),
            str(row.get('created_at') or ''),
            int(row.get('record_id') or 0),
        ),
        reverse=False,
    )
    return rows


def build_eures_cockpit_summary() -> dict:
    """Build a compact cockpit payload for the EURES beta admin home."""
    matchings_all = list_eures_admin_matchings(status='all')
    tasks_pending = build_eures_admin_tasks(status='pending')
    no_match_all = list_eures_admin_no_match_notifications(status='all')
    new_jobs_all = list_eures_admin_new_job_requests(status='all')
    new_employers_all = list_eures_admin_new_employer_alerts(status='all')
    invitations = list_eures_invitations()

    candidate_config = _get_eures_role_table_config('candidate')
    employer_config = _get_eures_role_table_config('employer')
    candidate_headers = _eures_admin_headers(candidate_config) if candidate_config else {}
    employer_headers = _eures_admin_headers(employer_config) if employer_config else {}
    candidats = fetch_table_records(candidate_config['doc_id'], candidate_config['table_id'], candidate_headers) if candidate_config else []
    besoins = fetch_table_records(employer_config['doc_id'], employer_config['table_id'], employer_headers) if employer_config else []

    today = datetime.now(timezone.utc)
    delays_matching_to_validation = []
    delays_validation_to_send = []
    delays_send_to_response = []
    delays_response_to_relation = []
    recent_activity = []

    for row in matchings_all:
        d1 = _compute_eures_delay_hours(row.get('date_calcul'), row.get('admin_decision_at'))
        if d1 is not None:
            delays_matching_to_validation.append(d1)
        d2 = _compute_eures_delay_hours(row.get('admin_decision_at'), row.get('sent_to_employer_at'))
        if d2 is not None:
            delays_validation_to_send.append(d2)
        d3 = _compute_eures_delay_hours(row.get('sent_to_employer_at'), row.get('employer_response_at'))
        if d3 is not None:
            delays_send_to_response.append(d3)
        d4 = _compute_eures_delay_hours(row.get('employer_response_at'), row.get('mise_en_relation_at'))
        if d4 is not None:
            delays_response_to_relation.append(d4)

        if row.get('admin_decision_at'):
            recent_activity.append({
                'at': row.get('admin_decision_at'),
                'type': 'matching_decision',
                'label': f"Matching {('accepté' if row.get('admin_status') == 'accepted' else 'refusé')} · {row.get('employeur', {}).get('employeur') or 'Entreprise'}",
            })
        if row.get('employer_response_at'):
            recent_activity.append({
                'at': row.get('employer_response_at'),
                'type': 'employer_response',
                'label': f"Retour employeur · {row.get('employeur', {}).get('employeur') or 'Entreprise'}",
            })

    for row in no_match_all:
        recent_activity.append({
            'at': row.get('sent_at') or row.get('created_at'),
            'type': 'no_match',
            'label': f"Sans matching · {row.get('title') or 'Entrée'}",
        })

    for row in new_jobs_all:
        recent_activity.append({
            'at': row.get('processed_at') or row.get('created_at'),
            'type': 'new_job_request',
            'label': f"Nouveau métier demandé · {row.get('employeur') or 'Entreprise'}",
        })

    for row in new_employers_all:
        recent_activity.append({
            'at': row.get('processed_at') or row.get('created_at'),
            'type': 'new_employer_alert',
            'label': f"Nouvel employeur recommandé · {row.get('employeur') or 'Entreprise'}",
        })

    accepted_count = sum(1 for row in matchings_all if row.get('admin_status') == 'accepted')
    sent_count = sum(1 for row in matchings_all if row.get('workflow_status') in {'envoye_employeur', 'accepte_employeur', 'refuse_employeur', 'mise_en_relation_faite', 'embauche_confirmee'})
    manual_sent_count = sum(
        1 for row in matchings_all
        if str(row.get('manual_matching_source') or '').strip().lower() == 'admin_manual'
        and row.get('workflow_status') in {'envoye_employeur', 'accepte_employeur', 'refuse_employeur', 'mise_en_relation_faite', 'embauche_confirmee'}
    )
    relation_count = sum(1 for row in matchings_all if row.get('workflow_status') in {'mise_en_relation_faite', 'embauche_confirmee'})
    hire_count = sum(1 for row in matchings_all if row.get('workflow_status') == 'embauche_confirmee')
    matchings_today = sum(1 for row in matchings_all if _same_utc_day(row.get('date_calcul'), today))
    manual_sent_today = sum(
        1 for row in matchings_all
        if str(row.get('manual_matching_source') or '').strip().lower() == 'admin_manual'
        and _same_utc_day(row.get('sent_to_employer_at'), today)
    )
    invitation_emails_today = sum(1 for row in invitations if _same_utc_day(row.get('sent_at'), today))
    candidate_invitations_sent = sum(
        1 for row in invitations
        if str(row.get('role') or '').strip().lower() == 'candidate'
        and str(row.get('invitation_status') or '').strip().lower() == 'invitation_envoyee'
    )
    no_match_today = sum(1 for row in no_match_all if _same_utc_day(row.get('created_at'), today))
    new_jobs_today = sum(1 for row in new_jobs_all if _same_utc_day(row.get('created_at'), today))

    recent_activity.sort(key=lambda row: str(row.get('at') or ''), reverse=True)
    recent_activity = [row for row in recent_activity if row.get('at')][:12]

    return {
        'priorities': {
            'matching_review': sum(1 for row in tasks_pending if row.get('task_type') == 'matching_review'),
            'no_match_followup': sum(1 for row in tasks_pending if row.get('task_type') == 'no_match_followup'),
            'new_job_request': sum(1 for row in tasks_pending if row.get('task_type') == 'new_job_request'),
            'new_employer_alert': sum(1 for row in tasks_pending if row.get('task_type') == 'new_employer_alert'),
            'duplicate_invitation_followup': sum(1 for row in tasks_pending if row.get('task_type') == 'duplicate_invitation_followup'),
            'invitation_errors': sum(1 for row in invitations if str(row.get('invitation_status') or '') == 'erreur_envoi'),
        },
        'today_flow': {
            'matchings_calcules': matchings_today,
            'matchings_manuels_envoyes': manual_sent_today,
            'emails_envoyes': invitation_emails_today,
            'sans_matching_crees': no_match_today,
            'nouveaux_metiers_recus': new_jobs_today,
        },
        'funnel': {
            'besoins_recus': len(besoins),
            'candidats_contactes': candidate_invitations_sent,
            'candidats_recus': len(candidats),
            'matchings_exploitables': len(matchings_all),
            'matchings_valides': accepted_count,
            'matchings_manuels_envoyes': manual_sent_count,
            'envoyes_employeurs': sent_count,
            'mises_en_relation': relation_count,
            'embauches_confirmees': hire_count,
        },
        'delays': {
            'matching_to_validation_hours': _mean_hours(delays_matching_to_validation),
            'validation_to_send_hours': _mean_hours(delays_validation_to_send),
            'send_to_response_hours': _mean_hours(delays_send_to_response),
            'response_to_relation_hours': _mean_hours(delays_response_to_relation),
        },
        'recent_activity': recent_activity,
    }


def normalize_finess(value) -> str:
    """Normalize FINESS value for duplicate checks."""
    raw = str(value or '').strip()
    digits = ''.join(ch for ch in raw if ch.isdigit())
    if digits and digits == raw:
        return digits.zfill(9) if len(digits) == 8 else digits
    return raw.upper()

def normalize_email(value) -> str:
    """Normalize email value for lookup."""
    return str(value or '').strip().lower()


def extract_finess_values(fields: dict) -> set:
    """Extract FINESS values from standard and JSON fields."""
    values = set()
    if not isinstance(fields, dict):
        return values

    main = normalize_finess(fields.get('finess_main'))
    if main:
        values.add(main)

    raw_json = fields.get('finess_json')
    parsed = []
    if isinstance(raw_json, str) and raw_json.strip():
        try:
            parsed = json.loads(raw_json)
        except Exception:
            parsed = []
    elif isinstance(raw_json, list):
        parsed = raw_json

    if isinstance(parsed, list):
        for item in parsed:
            v = normalize_finess(item)
            if v:
                values.add(v)

    return values


def find_duplicate_finess(config: dict, current_uuid: str, finess_values: set, headers: dict):
    """Find FINESS values already used by another record in the same table."""
    if not finess_values:
        return set()

    records = fetch_all_records(config, headers)
    duplicates = set()
    cur = normalize_finess(current_uuid)

    for rec in records:
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        rec_uuid = normalize_finess(fields.get('uuid'))
        if cur and rec_uuid == cur:
            continue
        rec_finess = extract_finess_values(fields)
        duplicates.update(finess_values.intersection(rec_finess))

    return duplicates


@app.route('/api/forms/<form_id>/record', methods=['GET'])
def get_record(form_id: str):
    """Fetch a record by UUID or table-specific identifier."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id == 'eures-beta':
        return jsonify({
            'error': 'Public record lookup is disabled for this form.',
        }), 403
    config = get_form_config(form_id, request.args.get('flow_role'))
    if not config:
        return jsonify({'error': f'Unknown form: {form_id}'}), 404

    uuid = request.args.get('uuid')
    if not uuid:
        return jsonify({'error': 'UUID parameter required'}), 400

    # Build Grist API URL with filter
    filter_param = f'{{"uuid":["{uuid}"]}}'
    url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}/records"

    headers = {'Accept': 'application/json'}
    # API key optional for read if doc is public
    if config['api_key']:
        headers['Authorization'] = f"Bearer {config['api_key']}"

    try:
        allowed_columns = get_table_columns(config, headers)
        record_key = resolve_record_key(allowed_columns)
        if not record_key:
            return jsonify({'error': 'Target table has no supported record key (uuid or id_tally).'}), 500
        resp = requests.get(
            url,
            params={'filter': json.dumps({record_key: [uuid]})},
            headers=headers,
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/write-token', methods=['GET'])
def issue_public_write_token(form_id: str):
    """Issue a short-lived public write token for EURES beta public forms."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': 'Write token endpoint is not enabled for this form.'}), 404
    role = _normalize_eures_invitation_role(request.args.get('role') or '')
    if role not in {'candidate', 'employer'}:
        return jsonify({'error': 'Invalid role'}), 400
    try:
        token = _issue_eures_public_write_token(role)
    except Exception as e:
        return jsonify({'error': f'Unable to issue write token: {e}'}), 500
    return jsonify({
        'ok': True,
        'role': role,
        'token': token,
        'expires_in_seconds': get_eures_public_write_ttl_seconds(),
    }), 200


@app.route('/api/forms/<form_id>/access', methods=['GET'])
def get_form_access(form_id: str):
    """Expose public access state to the frontend."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    settings = get_form_access_settings(form_id)
    return jsonify({
        'ok': True,
        'form_id': form_id,
        'read_only': settings['read_only'],
        'message': settings['message'],
    }), 200


@app.route('/api/forms/<form_id>/employer-referrals', methods=['POST'])
def create_eures_employer_referral(form_id: str):
    """Create and send one employer invitation from an existing employer link."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': 'Referral endpoint is not enabled for this form.'}), 404

    data = request.get_json() or {}
    invite_token = str(data.get('invite_token') or '').strip()
    write_token = str(data.get('write_token') or '').strip()
    is_valid, message = _validate_eures_public_write_token('employer', write_token)
    if not is_valid:
        return jsonify({'error': message}), 403
    allowed, retry_after = _check_eures_public_write_rate_limit('employer')
    if not allowed:
        return jsonify({'error': f'Trop de tentatives. Réessayez dans {retry_after} secondes.'}), 429

    sponsor_invitation, sponsor_error = get_eures_active_employer_invitation(invite_token)
    if not sponsor_invitation:
        return jsonify({'error': sponsor_error}), 403

    sponsor_fields = sponsor_invitation.get('fields', {}) if isinstance(sponsor_invitation.get('fields'), dict) else {}
    sponsor_company = str(sponsor_fields.get('company_name') or '').strip()
    sponsor_email = normalize_email(sponsor_fields.get('email', ''))

    invite_scope = str(data.get('invite_scope') or '').strip().lower()
    if invite_scope not in {'same_company', 'new_company'}:
        return jsonify({'error': "invite_scope doit valoir 'same_company' ou 'new_company'."}), 400

    recipient_email = normalize_email(data.get('email', ''))
    if not recipient_email:
        return jsonify({'error': 'Email destinataire manquant.'}), 400

    company_name = str(data.get('company_name') or '').strip()
    if invite_scope == 'same_company' and not company_name:
        company_name = sponsor_company
    if invite_scope == 'new_company' and not company_name:
        return jsonify({'error': "Le nom de l'entreprise est requis pour inviter une autre entreprise."}), 400

    row = {
        'role': 'employer',
        'email': recipient_email,
        'first_name': str(data.get('first_name') or '').strip(),
        'last_name': str(data.get('last_name') or '').strip(),
        'company_name': company_name,
        'language': str(data.get('language') or sponsor_fields.get('language') or 'fr').strip().lower(),
        'source': 'employer_referral',
        'external_ref': str(data.get('external_ref') or '').strip(),
        'notes': str(data.get('notes') or '').strip(),
        'invitation_status': 'invitation_a_envoyer',
        'sponsor_invitation_record_id': str(sponsor_invitation.get('id') or ''),
        'sponsor_email': sponsor_email,
        'sponsor_company_name': sponsor_company,
        'invited_by_type': 'employer_self_service',
        'invite_scope': invite_scope,
    }

    try:
        upsert_eures_invitation_rows([row], actor='public_employer_referral')
        config = get_eures_invitations_config()
        if not config:
            return jsonify({'error': 'EURES invitations configuration is incomplete.'}), 500
        headers = _eures_admin_headers(config)
        invitation = find_eures_invitation_by_role_email('employer', recipient_email, headers=headers)
        if not invitation:
            return jsonify({'error': "Invitation créée mais introuvable pour l'envoi."}), 500
        record_id = int(invitation.get('id') or 0)
        fields = invitation.get('fields', {}) if isinstance(invitation.get('fields'), dict) else {}
        current_status = str(fields.get('invitation_status') or '').strip().lower()
        if current_status == 'desactivee':
            return jsonify({'error': 'Cette invitation a été désactivée.'}), 400
        send_conflict = check_eures_invitation_send_conflict(
            'employer',
            recipient_email,
            current_record_id=record_id,
            invitation_headers=headers,
        )
        if send_conflict:
            followup_note = (
                f"Doublon détecté pour {recipient_email}. "
                f"Action admin attendue sur l'invitation {record_id}."
            )
            mark_eures_duplicate_followup_pending(
                record_id,
                {**send_conflict, 'note': followup_note},
                actor='public_employer_referral',
                headers=headers,
            )
            return jsonify({
                'error': send_conflict['message'],
                'conflict_type': send_conflict['type'],
                'conflict_record_id': send_conflict['record_id'],
                'conflict_status': send_conflict['status'],
                'followup_created': True,
            }), 409

        recipient, subject, text_body, html_body, new_invite_token, invite_link = build_brevo_invitation_email(fields)
        brevo_result = send_brevo_transactional_email(recipient, subject, text_body, html_body)
        update_fields = {
            'invite_token': new_invite_token,
            'invite_link': invite_link,
            'invitation_status_updated_at': _now_iso_utc(),
            'invitation_status_updated_by': 'public_employer_referral',
            'sent_at': _now_iso_utc(),
            'sent_by': 'public_employer_referral',
            'brevo_message_id': str((brevo_result or {}).get('messageId') or ''),
            'sponsor_invitation_record_id': str(sponsor_invitation.get('id') or ''),
            'sponsor_email': sponsor_email,
            'sponsor_company_name': sponsor_company,
            'invited_by_type': 'employer_self_service',
            'invite_scope': invite_scope,
            'company_name': company_name,
        }
        if not str(fields.get('answered_at') or '').strip():
            update_fields['invitation_status'] = 'invitation_envoyee'
        update_eures_invitation_record_by_id(record_id, update_fields, headers=headers)
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'email': recipient_email,
            'invite_scope': invite_scope,
            'invite_link': invite_link,
            'message_id': str((brevo_result or {}).get('messageId') or ''),
        }), 200
    except Exception as e:
        app.logger.exception('EURES employer referral invite failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/record', methods=['POST'])
def save_record(form_id: str):
    """Create or update a record."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    access_settings = get_form_access_settings(form_id)
    if access_settings['read_only']:
        return jsonify({
            'error': access_settings['message'],
            'read_only': True,
        }), 403
    data = request.get_json()
    if not data or 'fields' not in data:
        return jsonify({'error': 'Invalid request body'}), 400

    fields = data['fields']
    if not isinstance(fields, dict):
        return jsonify({'error': 'Invalid fields payload'}), 400
    if form_id == 'eures-beta':
        role = str(fields.get('flow_role') or '')
        write_token = str(fields.get('write_token') or request.headers.get('X-Eures-Write-Token') or '').strip()
        is_valid, message = _validate_eures_public_write_token(role, write_token)
        if not is_valid:
            return jsonify({'error': message}), 403
        allowed, retry_after = _check_eures_public_write_rate_limit(role)
        if not allowed:
            return jsonify({
                'error': f'Trop de tentatives pour ce formulaire. Réessayez dans {retry_after} secondes.',
            }), 429
        fields = {k: v for k, v in fields.items() if k != 'write_token'}
    config = get_form_config(form_id, fields.get('flow_role'))
    if not config:
        return jsonify({'error': f'Unknown form: {form_id}'}), 404

    if not config['api_key']:
        return jsonify({'error': 'API key not configured for this form'}), 500
    uuid = fields.get('uuid') or fields.get('id_tally')
    if not uuid:
        return jsonify({'error': 'UUID or id_tally required in fields'}), 400
    try:
        if form_id == 'eures-beta' and str(fields.get('flow_role') or '').strip().lower() == 'candidate':
            fields = normalize_eures_candidate_cv_fields(fields)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    base_url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}"
    headers = {
        'Authorization': f"Bearer {config['api_key']}",
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }

    # Keep only fields that exist in target table (prod/local may differ).
    try:
        if form_id == 'eures-beta':
            ensure_table_columns(config, set(str(key) for key in fields.keys()) | EURES_RESPONSE_ADMIN_FIELDS, headers)
        allowed_columns = get_table_columns(config, headers)
        filtered_fields = {k: v for k, v in fields.items() if str(k) in allowed_columns}
        record_key = resolve_record_key(allowed_columns)
    except Exception as e:
        return jsonify({'error': f'Failed to fetch Grist table columns: {e}'}), 500

    if not record_key:
        return jsonify({'error': "Table is missing a supported unique key column ('uuid' or 'id_tally')"}), 500

    if record_key not in filtered_fields:
        filtered_fields[record_key] = uuid

    # Check if record exists
    try:
        existing_record, check_resp = fetch_record_by_field(base_url, record_key, filtered_fields[record_key], headers)
        if check_resp.status_code != 200:
            return jsonify(_parse_response_json_safe(check_resp)), check_resp.status_code
        record_id = existing_record.get('id') if isinstance(existing_record, dict) else None
    except Exception as e:
        return jsonify({'error': f'Failed to check existing record: {e}'}), 500

    # Enforce uniqueness of FINESS across records (excluding current UUID)
    try:
        incoming_finess = extract_finess_values(filtered_fields)
        duplicates = find_duplicate_finess(config, uuid, incoming_finess, headers)
        if duplicates:
            duplicates_sorted = sorted(duplicates)
            return jsonify({
                'error': 'Un ou plusieurs numéros FINESS sont déjà utilisés par un autre questionnaire.',
                'duplicates': duplicates_sorted,
            }), 409
    except Exception as e:
        return jsonify({'error': f'Failed to validate FINESS uniqueness: {e}'}), 500

    # Create or update, then re-read the UUID so callers never get a false success.
    try:
        now_iso = _now_iso_utc()
        if form_id == 'eures-beta':
            if existing_record:
                existing_fields = existing_record.get('fields', {}) if isinstance(existing_record.get('fields'), dict) else {}
                filtered_fields['response_status'] = _normalize_eures_response_status(existing_fields.get('response_status', '')) or 'active'
                filtered_fields['response_status_updated_at'] = str(existing_fields.get('response_status_updated_at') or '').strip() or now_iso
                filtered_fields['response_status_updated_by'] = str(existing_fields.get('response_status_updated_by') or '').strip() or 'system_questionnaire_submission'
                filtered_fields['response_received_at'] = _eures_response_received_at(existing_fields) or now_iso
                if filtered_fields['response_status'] == 'disabled':
                    filtered_fields['response_disabled_at'] = str(existing_fields.get('response_disabled_at') or '').strip()
                    filtered_fields['response_disabled_by'] = str(existing_fields.get('response_disabled_by') or '').strip()
                    filtered_fields['response_disabled_reason'] = str(existing_fields.get('response_disabled_reason') or '').strip()
            else:
                filtered_fields['response_status'] = 'active'
                filtered_fields['response_status_updated_at'] = now_iso
                filtered_fields['response_status_updated_by'] = 'system_questionnaire_submission'
                filtered_fields['response_received_at'] = now_iso
        action = 'updated' if record_id else 'created'
        if record_id:
            # Update existing
            payload = {'records': [{'id': record_id, 'fields': filtered_fields}]}
            resp = write_grist_records('PATCH', f"{base_url}/records", payload, headers)
        else:
            # Create new
            payload = {'records': [{'fields': filtered_fields}]}
            resp = write_grist_records('POST', f"{base_url}/records", payload, headers)

        redirect_error = _grist_write_redirect_response(resp)
        if redirect_error:
            return redirect_error

        if resp.status_code != 200:
            return jsonify(_parse_response_json_safe(resp)), resp.status_code

        saved_record, verify_resp = fetch_record_by_field(base_url, record_key, filtered_fields[record_key], headers)
        if verify_resp.status_code != 200:
            return jsonify({
                'error': f'Grist write returned success, but verification failed with HTTP {verify_resp.status_code}.',
            }), 502
        if not isinstance(saved_record, dict):
            return jsonify({
                'error': 'Grist write returned success, but the questionnaire was not found after saving.',
            }), 502

        saved_fields = saved_record.get('fields', {}) if isinstance(saved_record.get('fields'), dict) else {}
        if str(saved_fields.get(record_key) or '') != str(filtered_fields[record_key]):
            return jsonify({
                'error': f'Grist write returned success, but the saved questionnaire {record_key} did not match.',
            }), 502

        matching_result = None
        invitation_linking = None
        no_match_notification = None
        new_job_request = None
        new_employer_alert = None
        if form_id == 'eures-beta':
            if action == 'created':
                matching_result = run_eures_matching_for_saved_record(
                    form_id=form_id,
                    role=str(fields.get('flow_role') or ''),
                    saved_record=saved_record,
                    config=config,
                    headers=headers,
                )
            else:
                matching_result = {
                    'processed': False,
                    'reason': 'existing_record_update',
                    'role': str(fields.get('flow_role') or ''),
                }
            if (
                action == 'created'
                and isinstance(matching_result, dict)
                and matching_result.get('processed')
                and matching_result.get('no_immediate_match')
            ):
                queue_eures_no_match_notification(str(fields.get('flow_role') or ''), int(saved_record.get('id') or 0))
                no_match_notification = {
                    'queued': True,
                    'status': 'pending',
                }
            if (
                action == 'created'
                and str(fields.get('flow_role') or '') == 'employer'
                and str(saved_fields.get('autres_metiers_souhaites') or '').strip()
            ):
                queue_eures_new_job_request(int(saved_record.get('id') or 0))
                new_job_request = {
                    'queued': True,
                    'status': 'pending',
                }
            invitation_linking = link_eures_invitation_after_save(
                role=str(fields.get('flow_role') or ''),
                request_fields=fields,
                saved_record=saved_record,
                matching_result=matching_result,
            )
            if (
                action == 'created'
                and str(fields.get('flow_role') or '') == 'employer'
                and isinstance(invitation_linking, dict)
                and invitation_linking.get('linked')
                and str(invitation_linking.get('invite_scope') or '') == 'new_company'
            ):
                queue_eures_new_employer_alert(int(saved_record.get('id') or 0), invitation_linking)
                new_employer_alert = {
                    'queued': True,
                    'status': 'pending',
                }

        return jsonify({
            'ok': True,
            'action': action,
            'uuid': uuid,
            'record_key': record_key,
            'record_id': saved_record.get('id'),
            'matching': matching_result,
            'no_match_notification': no_match_notification,
            'new_job_request': new_job_request,
            'new_employer_alert': new_employer_alert,
            'invitation_linking': invitation_linking,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/export-readable-xlsx', methods=['POST'])
def export_readable_xlsx(form_id: str):
    """Generate a human-readable Excel export from a form payload without changing Grist storage."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid request body'}), 400
    try:
        xlsx = build_readable_xlsx(data)
    except Exception as e:
        return jsonify({'error': f'Failed to build readable Excel export: {e}'}), 500

    uuid = str(data.get('uuid') or (data.get('fields') or {}).get('uuid') or 'saisie').strip() or 'saisie'
    filename = f'fagerh_saisie_lisible_{uuid}.xlsx'
    return send_file(
        xlsx,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename,
    )


@app.route('/api/forms/<form_id>/check-finess', methods=['POST'])
def check_finess(form_id: str):
    """Check whether FINESS values already exist in another questionnaire."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id == 'eures-beta':
        return jsonify({
            'error': 'Public FINESS lookup is disabled for this form.',
        }), 403
    config = get_form_config(form_id)
    if not config:
        return jsonify({'error': f'Unknown form: {form_id}'}), 404

    data = request.get_json() or {}
    uuid = normalize_finess(data.get('uuid'))
    raw_finess = data.get('finess') or []

    if not isinstance(raw_finess, list):
        return jsonify({'error': 'Invalid request body: finess must be a list'}), 400

    finess_values = {normalize_finess(v) for v in raw_finess if normalize_finess(v)}
    headers = {'Accept': 'application/json'}
    if config['api_key']:
        headers['Authorization'] = f"Bearer {config['api_key']}"

    try:
        duplicates = sorted(find_duplicate_finess(config, uuid, finess_values, headers))
        return jsonify({
            'ok': True,
            'duplicates': duplicates,
            'has_duplicates': len(duplicates) > 0,
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/recover-by-email', methods=['POST'])
def recover_by_email(form_id: str):
    """Recover a questionnaire UUID from validation email (+ optional FINESS)."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id == 'eures-beta':
        return jsonify({
            'error': 'Public questionnaire recovery is disabled for this form.',
        }), 403
    config = get_form_config(form_id)
    if not config:
        return jsonify({'error': f'Unknown form: {form_id}'}), 404

    data = request.get_json() or {}
    email = normalize_email(data.get('email'))
    finess = normalize_finess(data.get('finess'))
    if not email:
        return jsonify({'error': 'Email required'}), 400
    if finess and not finess.isdigit():
        return jsonify({'error': 'FINESS invalide'}), 400

    url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}/records"
    headers = {'Accept': 'application/json'}
    if config['api_key']:
        headers['Authorization'] = f"Bearer {config['api_key']}"

    try:
        # 1) Fast path: exact filter on the email column.
        filter_param = json.dumps({"validateur_email": [email]})
        resp = requests.get(url, params={'filter': filter_param, 'limit': 5000}, headers=headers)
        if resp.status_code != 200:
            return jsonify(resp.json()), resp.status_code
        payload = resp.json()
        records = payload.get('records', [])

        matches = []
        for rec in records:
            fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
            if not fields.get('uuid'):
                continue
            if finess:
                rec_finess = extract_finess_values(fields)
                if finess not in rec_finess:
                    continue
            matches.append(rec)

        # 2) Fallback: scan and compare case-insensitively (older rows / casing differences).
        if not matches:
            scan_resp = requests.get(url, params={'limit': 5000}, headers=headers)
            if scan_resp.status_code != 200:
                return jsonify(scan_resp.json()), scan_resp.status_code
            scan_payload = scan_resp.json()
            for rec in scan_payload.get('records', []):
                fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
                if normalize_email(fields.get('validateur_email')) != email:
                    continue
                if not fields.get('uuid'):
                    continue
                if finess:
                    rec_finess = extract_finess_values(fields)
                    if finess not in rec_finess:
                        continue
                matches.append(rec)

        if not matches:
            if finess:
                return jsonify({'error': 'Aucun questionnaire trouvé pour ce couple email + FINESS.'}), 404
            return jsonify({'error': 'Aucun questionnaire trouvé pour cet email.'}), 404

        chosen = max(matches, key=lambda r: int(r.get('id', 0) or 0))
        chosen_fields = chosen.get('fields', {}) if isinstance(chosen, dict) else {}
        return jsonify({
            'ok': True,
            'uuid': chosen_fields.get('uuid'),
            'count': len(matches),
            'match_on': 'email+finess' if finess else 'email',
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/overview', methods=['GET'])
@admin_required
def admin_overview(form_id: str):
    """Admin dashboard data: counts + questionnaire list."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    config = get_form_config(form_id)
    if not config:
        return jsonify({'error': f'Unknown form: {form_id}'}), 404

    headers = {'Accept': 'application/json'}
    if config['api_key']:
        headers['Authorization'] = f"Bearer {config['api_key']}"

    search = str(request.args.get('search', '') or '').strip().lower()
    status = str(request.args.get('status', 'all') or 'all').strip().lower()

    try:
        records = fetch_all_records(config, headers)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    rows = []
    for rec in records:
        fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
        if not fields:
            continue
        row = {
            'record_id': rec.get('id'),
            'uuid': fields.get('uuid', ''),
            'es_nom': fields.get('es_nom', ''),
            'departement': fields.get('es_departement', ''),
            'finess_main': fields.get('finess_main', ''),
            'validateur_nom': fields.get('validateur_nom', ''),
            'validateur_prenom': fields.get('validateur_prenom', ''),
            'validateur_email': fields.get('validateur_email', ''),
            'saisie_terminee': _as_bool(fields.get('saisie_terminee')),
        }
        row['quick_progress'] = compute_quick_step_progress(fields)
        rows.append(row)

    total = len(rows)
    termines = sum(1 for r in rows if r['saisie_terminee'])
    en_cours = total - termines

    # Newest first by record id.
    rows.sort(key=lambda r: int(r['record_id'] or 0), reverse=True)

    if status in {'en_cours', 'termines'}:
        want_done = status == 'termines'
        rows = [r for r in rows if r['saisie_terminee'] is want_done]

    if search:
        def _matches(r):
            haystack = ' '.join([
                str(r.get('es_nom', '')),
                str(r.get('departement', '')),
                str(r.get('finess_main', '')),
                str(r.get('validateur_nom', '')),
                str(r.get('validateur_prenom', '')),
                str(r.get('validateur_email', '')),
                str(r.get('uuid', '')),
            ]).lower()
            return search in haystack
        rows = [r for r in rows if _matches(r)]

    return jsonify({
        'ok': True,
        'form_id': form_id,
        'stats': {
            'total_questionnaires': total,
            'en_cours': en_cours,
            'termines': termines,
        },
        'rows': rows,
    }), 200


@app.route('/api/forms/<form_id>/admin/invitations', methods=['GET'])
@admin_required
def admin_eures_invitations(form_id: str):
    """Admin API: list invitations for EURES beta."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown invitation admin form: {form_id}'}), 404

    status = str(request.args.get('status', 'all') or 'all').strip().lower()
    role = _normalize_eures_invitation_role(request.args.get('role', '')) if request.args.get('role') else ''
    search = str(request.args.get('search', '') or '').strip().lower()

    try:
        rows = list_eures_invitations()
        if status != 'all':
            rows = [row for row in rows if str(row.get('invitation_status') or '') == status]
        if role:
            rows = [row for row in rows if str(row.get('role') or '') == role]
        if search:
            rows = [
                row for row in rows
                if search in ' '.join([
                    str(row.get('email') or ''),
                    str(row.get('first_name') or ''),
                    str(row.get('last_name') or ''),
                    str(row.get('company_name') or ''),
                    str(row.get('external_ref') or ''),
                ]).lower()
            ]
        stats = Counter(row.get('invitation_status') or 'invitation_a_envoyer' for row in rows)
        reminder_due = sum(1 for row in rows if row.get('needs_reminder'))
        duplicate_followup_pending = sum(
            1 for row in rows
            if _normalize_eures_duplicate_followup_status(row.get('duplicate_followup_status', '')) == 'pending'
        )
        ready_to_send = sum(
            1 for row in rows
            if str(row.get('invitation_status') or '') == 'invitation_a_envoyer'
            and _normalize_eures_duplicate_followup_status(row.get('duplicate_followup_status', '')) != 'pending'
        )
        return jsonify({
            'ok': True,
            'form_id': form_id,
            'stats': {
                'total': len(rows),
                'invitation_a_envoyer': ready_to_send,
                'invitation_envoyee': stats.get('invitation_envoyee', 0),
                'questionnaire_recu': stats.get('questionnaire_recu', 0),
                'rapprochee': stats.get('rapprochee', 0),
                'erreur_envoi': stats.get('erreur_envoi', 0),
                'reminder_due': reminder_due,
                'duplicate_followup_pending': duplicate_followup_pending,
            },
            'rows': rows,
        }), 200
    except Exception as e:
        app.logger.exception('EURES invitations list failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/invitations/import', methods=['POST'])
@admin_required
def admin_eures_invitations_import(form_id: str):
    """Admin API: import invitation rows from JSON or CSV payload."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown invitation import form: {form_id}'}), 404

    data = request.get_json() or {}
    rows = _parse_eures_invitation_rows(data)
    if not rows:
        return jsonify({'error': 'No invitation rows provided'}), 400

    actor = get_admin_actor(form_id)
    try:
        result = upsert_eures_invitation_rows(rows, actor=actor)
        return jsonify(result), 200
    except Exception as e:
        app.logger.exception('EURES invitations import failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/invitations/<int:record_id>', methods=['PATCH'])
@admin_required
def admin_eures_invitation_update(form_id: str, record_id: int):
    """Admin API: patch one invitation row."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown invitation update form: {form_id}'}), 404

    data = request.get_json() or {}
    update_fields = {}
    role = data.get('role')
    if role is not None:
        normalized_role = _normalize_eures_invitation_role(role)
        if normalized_role not in EURES_INVITATION_ALLOWED_ROLES:
            return jsonify({'error': 'Invalid invitation role'}), 400
        update_fields['role'] = normalized_role

    email = data.get('email')
    if email is not None:
        normalized_email = normalize_email(email)
        if not normalized_email:
            return jsonify({'error': 'Invalid invitation email'}), 400
        update_fields['email'] = normalized_email

    status = data.get('invitation_status')
    if status is not None:
        normalized_status = _normalize_eures_invitation_status(status)
        if normalized_status not in EURES_INVITATION_ALLOWED_STATUSES:
            return jsonify({'error': 'Invalid invitation status'}), 400
        actor = get_admin_actor(form_id)
        update_fields['invitation_status'] = normalized_status
        update_fields['invitation_status_updated_at'] = _now_iso_utc()
        update_fields['invitation_status_updated_by'] = actor

    for field_name in {
        'first_name',
        'last_name',
        'company_name',
        'language',
        'source',
        'external_ref',
        'target_job_keys',
        'notes',
        'answered_at',
        'linked_form_role',
        'linked_record_id',
        'linked_record_key',
        'matching_status',
    }:
        if field_name in data:
            if field_name == 'target_job_keys':
                update_fields[field_name] = _serialize_eures_invitation_target_job_keys(data.get(field_name))
            else:
                update_fields[field_name] = str(data.get(field_name) or '').strip()

    if not update_fields:
        return jsonify({'error': 'No supported invitation fields provided'}), 400

    config = get_eures_invitations_config()
    if not config:
        return jsonify({'error': 'EURES invitations configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    try:
        ensure_table_columns(config, set(update_fields.keys()) & EURES_INVITATION_FIELDS, headers)
        allowed_columns = get_table_columns(config, headers)
        filtered_fields = {k: v for k, v in update_fields.items() if k in allowed_columns}
        base_url = f"{GRIST_BASE_URL}/api/docs/{config['doc_id']}/tables/{config['table_id']}/records"
        resp = write_grist_records('PATCH', base_url, {'records': [{'id': record_id, 'fields': filtered_fields}]}, headers)
        if resp.status_code != 200:
            raise RuntimeError(f'Failed to update invitation: HTTP {resp.status_code} - {resp.text}')
        updated = fetch_record_by_id(config['doc_id'], config['table_id'], record_id, headers)
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'fields': updated.get('fields', {}) if isinstance(updated, dict) else {},
        }), 200
    except Exception as e:
        app.logger.exception('EURES invitation update failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/invitations/<int:record_id>', methods=['DELETE'])
@admin_required
def admin_eures_invitation_delete(form_id: str, record_id: int):
    """Admin API: delete one invitation row in error state."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown invitation delete form: {form_id}'}), 404

    config = get_eures_invitations_config()
    if not config:
        return jsonify({'error': 'EURES invitations configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    try:
        existing = fetch_record_by_id(config['doc_id'], config['table_id'], record_id, headers)
        if not existing:
            return jsonify({'error': 'Invitation not found'}), 404
        fields = existing.get('fields', {}) if isinstance(existing.get('fields'), dict) else {}
        current_status = str(fields.get('invitation_status') or '').strip().lower()
        if current_status != 'erreur_envoi':
            return jsonify({'error': "Seules les invitations en erreur d'envoi peuvent être supprimées."}), 400

        delete_eures_invitation_record_by_id(record_id, headers=headers)
        app.logger.info(
            'EURES invitation deleted',
            extra={'form_id': form_id, 'record_id': record_id, 'status': current_status},
        )
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'deleted': True,
        }), 200
    except Exception as e:
        app.logger.exception('EURES invitation delete failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/invitations/<int:record_id>/duplicate-followup', methods=['POST'])
@admin_required
def admin_eures_invitation_duplicate_followup(form_id: str, record_id: int):
    """Admin API: accept or ignore one duplicate invitation follow-up."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown duplicate follow-up admin form: {form_id}'}), 404

    data = request.get_json() or {}
    action = str(data.get('action') or '').strip().lower()
    note = str(data.get('note') or '').strip()
    if action not in {'remind', 'ignore'}:
        return jsonify({'error': "action doit valoir 'remind' ou 'ignore'."}), 400

    config = get_eures_invitations_config()
    if not config:
        return jsonify({'error': 'EURES invitations configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    actor = get_admin_actor(form_id)
    try:
        current = fetch_record_by_id(config['doc_id'], config['table_id'], record_id, headers)
        if not current:
            return jsonify({'error': 'Invitation introuvable'}), 404
        fields = current.get('fields', {}) if isinstance(current.get('fields'), dict) else {}
        followup_status = _normalize_eures_duplicate_followup_status(fields.get('duplicate_followup_status', ''))
        if followup_status != 'pending':
            return jsonify({'error': 'Cette proposition de relance a déjà été traitée.'}), 400

        target_type = str(fields.get('duplicate_followup_type') or '').strip().lower()
        target_record_id = int(fields.get('duplicate_followup_target_record_id') or 0)
        result = {'action': action}
        if action == 'remind':
            if target_type != 'existing_invitation' or not target_record_id:
                return jsonify({'error': 'Aucune invitation existante ne peut être relancée pour cette adresse.'}), 400
            result['reminder'] = send_eures_invitation_reminder_by_record_id(target_record_id, actor, headers=headers)
            clear_eures_duplicate_followup(record_id, actor, status='reminded', note=note, headers=headers)
        else:
            clear_eures_duplicate_followup(record_id, actor, status='ignored', note=note, headers=headers)

        updated = fetch_record_by_id(config['doc_id'], config['table_id'], record_id, headers)
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'result': result,
            'fields': updated.get('fields', {}) if isinstance(updated, dict) else {},
        }), 200
    except Exception as e:
        app.logger.exception('EURES duplicate follow-up update failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/invitations/send', methods=['POST'])
@admin_required
def admin_eures_invitations_send(form_id: str):
    """Admin API: send pending invitations through Brevo."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown invitation send form: {form_id}'}), 404

    data = request.get_json() or {}
    requested_ids = data.get('record_ids') or []
    force_resend = bool(data.get('force_resend'))
    if requested_ids and not isinstance(requested_ids, list):
        return jsonify({'error': 'record_ids must be a list'}), 400

    config = get_eures_invitations_config()
    if not config:
        return jsonify({'error': 'EURES invitations configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    actor = get_admin_actor(form_id)
    try:
        records = fetch_table_records(config['doc_id'], config['table_id'], headers)
        if requested_ids:
            requested_ids_set = {int(value) for value in requested_ids}
            target_records = [rec for rec in records if int(rec.get('id') or 0) in requested_ids_set]
        else:
            target_records = []
            for rec in records:
                fields = rec.get('fields', {}) if isinstance(rec, dict) else {}
                if str(fields.get('invitation_status') or '').strip().lower() == 'invitation_a_envoyer':
                    target_records.append(rec)

        sent = []
        skipped = []
        errors = []
        for rec in target_records:
            record_id = int(rec.get('id') or 0)
            fields = rec.get('fields', {}) if isinstance(rec.get('fields'), dict) else {}
            current_status = str(fields.get('invitation_status') or '').strip().lower()
            sendable_statuses = EURES_INVITATION_SENDABLE_STATUSES
            if force_resend and requested_ids:
                sendable_statuses = EURES_INVITATION_ALLOWED_STATUSES - {'desactivee'}
            if current_status not in sendable_statuses:
                skipped.append({
                    'record_id': record_id,
                    'email': fields.get('email', ''),
                    'reason': f'status_not_sendable:{current_status or "unknown"}',
                })
                continue
            send_conflict = check_eures_invitation_send_conflict(
                fields.get('role', ''),
                fields.get('email', ''),
                current_record_id=record_id,
                invitation_headers=headers,
            )
            if send_conflict:
                followup_note = (
                    f"Doublon détecté pour {fields.get('email', '')}. "
                    f"Action admin attendue sur l'invitation {record_id}."
                )
                mark_eures_duplicate_followup_pending(
                    record_id,
                    {**send_conflict, 'note': followup_note},
                    actor=actor,
                    headers=headers,
                )
                skipped.append({
                    'record_id': record_id,
                    'email': fields.get('email', ''),
                    'reason': send_conflict['type'],
                    'message': send_conflict['message'],
                    'conflict_record_id': send_conflict['record_id'],
                    'conflict_status': send_conflict['status'],
                    'followup_created': True,
                })
                continue
            try:
                recipient, subject, text_body, html_body, invite_token, invite_link = build_brevo_invitation_email(fields)
                brevo_result = send_brevo_transactional_email(recipient, subject, text_body, html_body)
                update_eures_invitation_record_by_id(record_id, {
                    'invite_token': invite_token,
                    'invite_link': invite_link,
                    'invitation_status': 'invitation_envoyee',
                    'invitation_status_updated_at': _now_iso_utc(),
                    'invitation_status_updated_by': actor,
                    'sent_at': _now_iso_utc(),
                    'sent_by': actor,
                    'brevo_message_id': str((brevo_result or {}).get('messageId') or ''),
                }, headers=headers)
                sent.append({
                    'record_id': record_id,
                    'email': recipient,
                    'brevo_message_id': str((brevo_result or {}).get('messageId') or ''),
                    'force_resend': force_resend,
                })
            except Exception as e:
                error_message = str(e)
                errors.append({
                    'record_id': record_id,
                    'email': fields.get('email', ''),
                    'error': error_message,
                })
                try:
                    update_eures_invitation_record_by_id(record_id, {
                        'invitation_status': 'erreur_envoi',
                        'invitation_status_updated_at': _now_iso_utc(),
                        'invitation_status_updated_by': actor,
                        'notes': error_message[:500],
                    }, headers=headers)
                except Exception:
                    app.logger.exception('EURES invitation error status update failed')

        return jsonify({
            'ok': True,
            'requested': len(target_records),
            'force_resend': force_resend,
            'sent': sent,
            'skipped': skipped,
            'errors': errors,
        }), 200
    except Exception as e:
        app.logger.exception('EURES invitations send failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/invitations/remind', methods=['POST'])
@admin_required
def admin_eures_invitations_remind(form_id: str):
    """Admin API: send reminder emails for already sent invitations."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown invitation reminder form: {form_id}'}), 404

    data = request.get_json() or {}
    requested_ids = data.get('record_ids') or []
    if requested_ids and not isinstance(requested_ids, list):
        return jsonify({'error': 'record_ids must be a list'}), 400

    config = get_eures_invitations_config()
    if not config:
        return jsonify({'error': 'EURES invitations configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    actor = get_admin_actor(form_id)
    try:
        ensure_table_columns(config, EURES_INVITATION_FIELDS, headers)
        records = fetch_table_records(config['doc_id'], config['table_id'], headers)
        requested_ids_set = {int(value) for value in requested_ids} if requested_ids else set()
        target_records = []
        for rec in records:
            record_id = int(rec.get('id') or 0)
            fields = rec.get('fields', {}) if isinstance(rec.get('fields'), dict) else {}
            if requested_ids_set and record_id not in requested_ids_set:
                continue
            if not requested_ids_set and not _eures_invitation_needs_reminder(fields):
                continue
            target_records.append(rec)

        reminded = []
        skipped = []
        errors = []
        for rec in target_records:
            record_id = int(rec.get('id') or 0)
            fields = rec.get('fields', {}) if isinstance(rec.get('fields'), dict) else {}
            current_status = str(fields.get('invitation_status') or '').strip().lower()
            if current_status != 'invitation_envoyee':
                skipped.append({
                    'record_id': record_id,
                    'email': fields.get('email', ''),
                    'reason': f'status_not_remindable:{current_status or "unknown"}',
                })
                continue
            if str(fields.get('answered_at') or '').strip():
                skipped.append({
                    'record_id': record_id,
                    'email': fields.get('email', ''),
                    'reason': 'already_answered',
                })
                continue
            try:
                reminded.append(send_eures_invitation_reminder_by_record_id(record_id, actor, headers=headers))
            except Exception as e:
                errors.append({
                    'record_id': record_id,
                    'email': fields.get('email', ''),
                    'error': str(e),
                })

        return jsonify({
            'ok': True,
            'requested': len(target_records),
            'reminded': reminded,
            'skipped': skipped,
            'errors': errors,
        }), 200
    except Exception as e:
        app.logger.exception('EURES invitations remind failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/cockpit', methods=['GET'])
@admin_required
def admin_eures_cockpit(form_id: str):
    """Admin API: compact cockpit summary for EURES beta."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown cockpit admin form: {form_id}'}), 404

    try:
        return jsonify({
            'ok': True,
            'form_id': form_id,
            'cockpit': build_eures_cockpit_summary(),
        }), 200
    except Exception as e:
        app.logger.exception('EURES cockpit summary failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/tasks', methods=['GET'])
@admin_required
def admin_eures_tasks(form_id: str):
    """Admin API: unified pending work queue for EURES beta."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown tasks admin form: {form_id}'}), 404

    status = str(request.args.get('status', 'pending') or 'pending').strip().lower()
    if status not in {'all', 'pending', 'done', 'dismissed'}:
        return jsonify({'error': 'Invalid status filter'}), 400

    try:
        rows = build_eures_admin_tasks(status=status)
        stats = Counter(str(row.get('status') or 'pending') for row in rows)
        return jsonify({
            'ok': True,
            'form_id': form_id,
            'stats': {
                'total': len(rows),
                'pending': stats.get('pending', 0),
                'done': stats.get('done', 0),
                'dismissed': stats.get('dismissed', 0),
            },
            'rows': rows,
        }), 200
    except Exception as e:
        app.logger.exception('EURES tasks list failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/questionnaires/<role>', methods=['GET'])
@admin_required
def admin_eures_questionnaire_responses(form_id: str, role: str):
    """Admin API: list raw candidate or employer questionnaire responses."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown questionnaire admin form: {form_id}'}), 404

    normalized_role = _normalize_eures_invitation_role(role)
    if normalized_role not in {'candidate', 'employer'}:
        return jsonify({'error': 'Invalid questionnaire role'}), 400

    try:
        rows = list_eures_admin_questionnaire_responses(normalized_role)
        stats = Counter('active' if row.get('is_active') else 'disabled' for row in rows)
        return jsonify({
            'ok': True,
            'form_id': form_id,
            'role': normalized_role,
            'stats': {
                'total': len(rows),
                'active': stats.get('active', 0),
                'disabled': stats.get('disabled', 0),
            },
            'rows': rows,
        }), 200
    except Exception as e:
        app.logger.exception('EURES questionnaire response list failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/questionnaires/<role>/<int:record_id>/cv', methods=['GET'])
@admin_required
def admin_eures_questionnaire_response_cv(form_id: str, role: str, record_id: int):
    """Admin API: download one stored candidate CV."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown questionnaire admin form: {form_id}'}), 404

    normalized_role = _normalize_eures_invitation_role(role)
    if normalized_role != 'candidate':
        return jsonify({'error': 'CV disponible uniquement pour les candidats.'}), 400

    config = _get_eures_role_table_config(normalized_role)
    if not config:
        return jsonify({'error': 'EURES role configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    try:
        record = fetch_record_by_id(config['doc_id'], config['table_id'], record_id, headers)
        if not record:
            return jsonify({'error': 'Réponse introuvable'}), 404
        fields = record.get('fields', {}) if isinstance(record.get('fields'), dict) else {}
        cv_base64 = str(fields.get('cv_file_base64') or '').strip()
        cv_name = str(fields.get('cv_file_name') or '').strip() or 'cv-candidat'
        cv_mime = str(fields.get('cv_file_mime') or '').strip() or 'application/octet-stream'
        if not cv_base64:
            return jsonify({'error': 'Aucun CV disponible pour cette réponse.'}), 404
        try:
            payload = base64.b64decode(cv_base64, validate=True)
        except Exception as exc:
            raise RuntimeError('Le CV stocké est invalide.') from exc
        return send_file(
            BytesIO(payload),
            mimetype=cv_mime,
            as_attachment=True,
            download_name=cv_name,
        )
    except Exception as e:
        app.logger.exception('EURES questionnaire CV download failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/questionnaires/<role>/<int:record_id>/status', methods=['POST'])
@admin_required
def admin_eures_questionnaire_response_status(form_id: str, role: str, record_id: int):
    """Admin API: activate or disable one candidate/employer response."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown questionnaire admin form: {form_id}'}), 404

    normalized_role = _normalize_eures_invitation_role(role)
    if normalized_role not in {'candidate', 'employer'}:
        return jsonify({'error': 'Invalid questionnaire role'}), 400

    data = request.get_json() or {}
    status = _normalize_eures_response_status(data.get('status') or '')
    reason = str(data.get('reason') or '').strip()
    if status not in {'active', 'disabled'}:
        return jsonify({'error': "status doit valoir 'active' ou 'disabled'."}), 400

    config = _get_eures_role_table_config(normalized_role)
    if not config:
        return jsonify({'error': 'EURES role configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    actor = get_admin_actor(form_id)
    try:
        record = fetch_record_by_id(config['doc_id'], config['table_id'], record_id, headers)
        if not record:
            return jsonify({'error': 'Réponse introuvable'}), 404
        update_fields = {
            'response_status': status,
            'response_status_updated_at': _now_iso_utc(),
            'response_status_updated_by': actor,
            'response_disabled_reason': reason if status == 'disabled' else '',
            'response_disabled_at': _now_iso_utc() if status == 'disabled' else '',
            'response_disabled_by': actor if status == 'disabled' else '',
        }
        update_table_record_by_id(config, record_id, update_fields, headers, EURES_RESPONSE_ADMIN_FIELDS)
        app.logger.info(
            'EURES questionnaire response status updated',
            extra={'form_id': form_id, 'role': normalized_role, 'record_id': record_id, 'status': status},
        )
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'role': normalized_role,
            'status': status,
        }), 200
    except Exception as e:
        app.logger.exception('EURES questionnaire response status update failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/questionnaires/<role>/<int:record_id>', methods=['DELETE'])
@admin_required
def admin_eures_questionnaire_response_delete(form_id: str, role: str, record_id: int):
    """Admin API: delete one candidate/employer response and related matchings."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown questionnaire admin form: {form_id}'}), 404

    normalized_role = _normalize_eures_invitation_role(role)
    if normalized_role not in {'candidate', 'employer'}:
        return jsonify({'error': 'Invalid questionnaire role'}), 400

    config = _get_eures_role_table_config(normalized_role)
    if not config:
        return jsonify({'error': 'EURES role configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    try:
        record = fetch_record_by_id(config['doc_id'], config['table_id'], record_id, headers)
        if not record:
            return jsonify({'error': 'Réponse introuvable'}), 404
        fields = record.get('fields', {}) if isinstance(record.get('fields'), dict) else {}
        response_key = str(fields.get('id_tally') or fields.get('uuid') or '').strip()
        deleted_matchings = delete_matching_records_for_response(normalized_role, response_key)
        delete_table_record_by_id(config, record_id, headers)
        app.logger.info(
            'EURES questionnaire response deleted',
            extra={'form_id': form_id, 'role': normalized_role, 'record_id': record_id, 'deleted_matchings': deleted_matchings},
        )
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'role': normalized_role,
            'deleted': True,
            'deleted_matchings': deleted_matchings,
        }), 200
    except Exception as e:
        app.logger.exception('EURES questionnaire response delete failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/no-match', methods=['GET'])
@admin_required
def admin_eures_no_match(form_id: str):
    """Admin API: list candidate/employer rows with no immediate matching."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown no-match admin form: {form_id}'}), 404

    status = str(request.args.get('status', 'pending') or 'pending').strip().lower()
    if status != 'all' and status not in EURES_NO_MATCH_ALLOWED_STATUSES:
        return jsonify({'error': 'Invalid status filter'}), 400

    try:
        rows = list_eures_admin_no_match_notifications(status=status)
        stats = Counter(row['notification_status'] for row in rows)
        return jsonify({
            'ok': True,
            'form_id': form_id,
            'stats': {
                'total': len(rows),
                'pending': stats.get('pending', 0),
                'sent': stats.get('sent', 0),
                'dismissed': stats.get('dismissed', 0),
            },
            'rows': rows,
        }), 200
    except Exception as e:
        app.logger.exception('EURES no-match list failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/no-match/<role>/<int:record_id>/send', methods=['POST'])
@admin_required
def admin_eures_no_match_send(form_id: str, role: str, record_id: int):
    """Admin API: send one no-match follow-up email."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown no-match admin form: {form_id}'}), 404

    normalized_role = _normalize_eures_invitation_role(role)
    if normalized_role not in {'candidate', 'employer'}:
        return jsonify({'error': 'Invalid role'}), 400

    data = request.get_json() or {}
    note = str(data.get('note') or '').strip()
    config = _get_eures_role_table_config(normalized_role)
    if not config:
        return jsonify({'error': 'EURES role configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    actor = get_admin_actor(form_id)
    try:
        ensure_brevo_ready(check_api=True)
        record = fetch_record_by_id(config['doc_id'], config['table_id'], record_id, headers)
        row = _build_eures_no_match_row(normalized_role, record or {})
        if not row:
            return jsonify({'error': 'No-match entry not found'}), 404

        if normalized_role == 'candidate':
            recipient, subject, text_body, html_body = build_brevo_candidate_no_match_email(row)
        else:
            recipient, subject, text_body, html_body = build_brevo_employer_no_match_email(row)
        brevo_result = send_brevo_transactional_email(recipient, subject, text_body, html_body)

        update_table_record_by_id(
            config,
            record_id,
            {
                'no_match_notification_status': 'sent',
                'no_match_notification_sent_at': _now_iso_utc(),
                'no_match_notification_sent_by': actor,
                'no_match_notification_note': note,
            },
            headers,
            EURES_NO_MATCH_NOTIFICATION_FIELDS,
        )
        app.logger.info(
            'EURES no-match notification sent',
            extra={'form_id': form_id, 'role': normalized_role, 'record_id': record_id, 'to_email': recipient},
        )
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'role': normalized_role,
            'notification_status': 'sent',
            'email': recipient,
            'email_result': brevo_result,
        }), 200
    except Exception as e:
        app.logger.exception('EURES no-match notification send failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/no-match/<role>/<int:record_id>/dismiss', methods=['POST'])
@admin_required
def admin_eures_no_match_dismiss(form_id: str, role: str, record_id: int):
    """Admin API: dismiss one no-match follow-up without sending email."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown no-match admin form: {form_id}'}), 404

    normalized_role = _normalize_eures_invitation_role(role)
    if normalized_role not in {'candidate', 'employer'}:
        return jsonify({'error': 'Invalid role'}), 400

    data = request.get_json() or {}
    note = str(data.get('note') or '').strip()
    config = _get_eures_role_table_config(normalized_role)
    if not config:
        return jsonify({'error': 'EURES role configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    actor = get_admin_actor(form_id)
    try:
        update_table_record_by_id(
            config,
            record_id,
            {
                'no_match_notification_status': 'dismissed',
                'no_match_notification_dismissed_at': _now_iso_utc(),
                'no_match_notification_dismissed_by': actor,
                'no_match_notification_note': note,
            },
            headers,
            EURES_NO_MATCH_NOTIFICATION_FIELDS,
        )
        app.logger.info(
            'EURES no-match notification dismissed',
            extra={'form_id': form_id, 'role': normalized_role, 'record_id': record_id},
        )
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'role': normalized_role,
            'notification_status': 'dismissed',
        }), 200
    except Exception as e:
        app.logger.exception('EURES no-match notification dismiss failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/new-job-requests', methods=['GET'])
@admin_required
def admin_eures_new_job_requests(form_id: str):
    """Admin API: list employer requests for additional job families."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown new-job admin form: {form_id}'}), 404

    status = str(request.args.get('status', 'pending') or 'pending').strip().lower()
    if status != 'all' and status not in EURES_NEW_JOB_REQUEST_ALLOWED_STATUSES:
        return jsonify({'error': 'Invalid status filter'}), 400

    try:
        rows = list_eures_admin_new_job_requests(status=status)
        stats = Counter(row['request_status'] for row in rows)
        return jsonify({
            'ok': True,
            'form_id': form_id,
            'stats': {
                'total': len(rows),
                'pending': stats.get('pending', 0),
                'processed': stats.get('processed', 0),
                'dismissed': stats.get('dismissed', 0),
            },
            'rows': rows,
        }), 200
    except Exception as e:
        app.logger.exception('EURES new job requests list failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/new-job-requests/<int:record_id>/status', methods=['POST'])
@admin_required
def admin_eures_new_job_request_status(form_id: str, record_id: int):
    """Admin API: mark one employer new-job request as processed or dismissed."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown new-job admin form: {form_id}'}), 404

    data = request.get_json() or {}
    status = _normalize_eures_new_job_request_status(data.get('status') or '')
    note = str(data.get('note') or '').strip()
    if status not in {'processed', 'dismissed'}:
        return jsonify({'error': 'Status must be processed or dismissed'}), 400

    config = _get_eures_role_table_config('employer')
    if not config:
        return jsonify({'error': 'EURES employer configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    actor = get_admin_actor(form_id)
    try:
        update_table_record_by_id(
            config,
            record_id,
            {
                'new_job_request_status': status,
                'new_job_request_processed_at': _now_iso_utc(),
                'new_job_request_processed_by': actor,
                'new_job_request_note': note,
            },
            headers,
            EURES_NEW_JOB_REQUEST_FIELDS,
        )
        app.logger.info(
            'EURES new job request status updated',
            extra={'form_id': form_id, 'record_id': record_id, 'status': status},
        )
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'status': status,
        }), 200
    except Exception as e:
        app.logger.exception('EURES new job request status update failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/new-employer-alerts/<int:record_id>/status', methods=['POST'])
@admin_required
def admin_eures_new_employer_alert_status(form_id: str, record_id: int):
    """Admin API: mark one newly referred employer alert as reviewed or dismissed."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown new-employer admin form: {form_id}'}), 404

    data = request.get_json() or {}
    status = _normalize_eures_new_employer_alert_status(data.get('status') or '')
    note = str(data.get('note') or '').strip()
    if status not in {'reviewed', 'dismissed'}:
        return jsonify({'error': 'Status must be reviewed or dismissed'}), 400

    config = _get_eures_role_table_config('employer')
    if not config:
        return jsonify({'error': 'EURES employer configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    actor = get_admin_actor(form_id)
    try:
        update_table_record_by_id(
            config,
            record_id,
            {
                'new_employer_alert_status': status,
                'new_employer_alert_processed_at': _now_iso_utc(),
                'new_employer_alert_processed_by': actor,
                'new_employer_alert_note': note,
            },
            headers,
            EURES_NEW_EMPLOYER_ALERT_FIELDS,
        )
        app.logger.info(
            'EURES new employer alert status updated',
            extra={'form_id': form_id, 'record_id': record_id, 'status': status},
        )
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'status': status,
        }), 200
    except Exception as e:
        app.logger.exception('EURES new employer alert status update failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/matchings', methods=['GET'])
@admin_required
def admin_eures_matchings(form_id: str):
    """Admin API: list matchings for EURES beta review."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown admin matching form: {form_id}'}), 404

    status = str(request.args.get('status', 'all') or 'all').strip().lower()
    if status not in {'all', 'pending', 'accepted', 'refused'}:
        return jsonify({'error': 'Invalid status filter'}), 400

    try:
        rows = list_eures_admin_matchings(status=status)
        stats = Counter(row['admin_status'] for row in rows)
        return jsonify({
            'ok': True,
            'form_id': form_id,
            'stats': {
                'total': len(rows),
                'pending': stats.get('pending', 0),
                'accepted': stats.get('accepted', 0),
                'refused': stats.get('refused', 0),
            },
            'rows': rows,
        }), 200
    except Exception as e:
        app.logger.exception('EURES admin matchings list failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/matchings/manual', methods=['POST'])
@admin_required
def admin_eures_manual_matching(form_id: str):
    """Admin API: create or refresh one matching manually from selected records."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown admin matching form: {form_id}'}), 404

    data = request.get_json() or {}
    candidat_record_id = int(data.get('candidate_record_id') or 0)
    employeur_record_id = int(data.get('employer_record_id') or 0)
    employer_email_comment = str(data.get('employer_email_comment') or '').strip()
    candidate_email_comment = str(data.get('candidate_email_comment') or '').strip()
    send_directly = bool(data.get('send_directly'))
    if not candidat_record_id or not employeur_record_id:
        return jsonify({'error': 'Candidate and employer selections are required'}), 400

    matching_config = get_eures_matching_config()
    candidate_config = get_form_config('eures-beta', 'candidate')
    employer_config = get_form_config('eures-beta', 'employer')
    if not matching_config or not candidate_config or not employer_config:
        return jsonify({'error': 'EURES beta matching configuration is incomplete.'}), 500

    headers = _eures_admin_headers(matching_config)
    candidate_headers = _eures_admin_headers(candidate_config)
    employer_headers = _eures_admin_headers(employer_config)
    actor = get_admin_actor(form_id)

    try:
        if send_directly:
            ensure_brevo_ready(check_api=True)
        candidat_record = fetch_record_by_id(candidate_config['doc_id'], EURES_CANDIDATS_TABLE, candidat_record_id, candidate_headers)
        employeur_record = fetch_record_by_id(employer_config['doc_id'], EURES_BESOINS_TABLE, employeur_record_id, employer_headers)
        if not candidat_record:
            return jsonify({'error': 'Candidate record not found'}), 404
        if not employeur_record:
            return jsonify({'error': 'Employer record not found'}), 404

        candidat_fields = candidat_record.get('fields', {}) if isinstance(candidat_record.get('fields'), dict) else {}
        employeur_fields = employeur_record.get('fields', {}) if isinstance(employeur_record.get('fields'), dict) else {}
        if not _is_eures_response_active(candidat_fields):
            return jsonify({'error': 'Le candidat sélectionné est désactivé et ne peut pas être utilisé pour un matching.'}), 400
        if not _is_eures_response_active(employeur_fields):
            return jsonify({'error': "Le besoin employeur sélectionné est désactivé et ne peut pas être utilisé pour un matching."}), 400
        candidat_id = str(candidat_fields.get('id_tally') or candidat_fields.get('uuid') or '').strip()
        besoin_id = str(employeur_fields.get('id_tally') or employeur_fields.get('uuid') or '').strip()
        if not candidat_id or not besoin_id:
            return jsonify({'error': 'Matching keys are missing on the selected records'}), 400

        matching = compute_eures_matching(employeur_fields, candidat_fields)
        payload = {
            'besoin_id': besoin_id,
            'candidat_id': candidat_id,
            'manual_matching_source': 'admin_manual',
            'manual_matching_created_at': _now_iso_utc(),
            'manual_matching_created_by': actor,
            'manual_matching_note': '',
            'employer_email_comment': employer_email_comment,
            'candidate_email_comment': candidate_email_comment,
            **matching,
        }
        upsert_matching_record(matching_config['doc_id'], payload, headers)
        existing = fetch_matching_record(matching_config['doc_id'], besoin_id, candidat_id, headers)
        record_id = int((existing or {}).get('id') or 0)
        brevo_result = None
        candidate_brevo_result = None

        if send_directly:
            decision_fields = {
                'admin_status': 'accepted',
                'admin_decision_at': _now_iso_utc(),
                'admin_decision_by': actor,
                'admin_decision_note': '',
                'employer_email_comment': employer_email_comment,
                'candidate_email_comment': candidate_email_comment,
                **_matching_workflow_update_fields('valide_admin', actor),
            }
            update_matching_record_by_id(matching_config['doc_id'], record_id, decision_fields, headers)
            matching_rows = list_eures_admin_matchings(status='all', include_candidate_cv=True)
            matching_row = next((row for row in matching_rows if int(row.get('record_id') or 0) == record_id), None)
            if not matching_row:
                raise RuntimeError('Manual matching could not be reloaded for direct email delivery.')
            cv_attachment = get_candidate_cv_attachment(matching_row.get('candidat', {}))
            to_email, subject, text_body, html_body = build_brevo_matching_email(matching_row)
            brevo_result = send_brevo_transactional_email(
                to_email,
                subject,
                text_body,
                html_body,
                attachments=[cv_attachment] if cv_attachment else None,
            )
            candidate_to_email, candidate_subject, candidate_text_body, candidate_html_body = build_brevo_candidate_matching_notification_email(matching_row)
            candidate_brevo_result = send_brevo_transactional_email(
                candidate_to_email,
                candidate_subject,
                candidate_text_body,
                candidate_html_body,
            )
            update_matching_record_by_id(
                matching_config['doc_id'],
                record_id,
                _matching_workflow_update_fields('envoye_employeur', actor),
                headers,
            )

        app.logger.info(
            'EURES manual matching created',
            extra={
                'form_id': form_id,
                'record_id': record_id,
                'besoin_id': besoin_id,
                'candidat_id': candidat_id,
                'created_by': actor,
                'send_directly': send_directly,
            },
        )
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'besoin_id': besoin_id,
            'candidat_id': candidat_id,
            'score': matching.get('score', 0),
            'statut': matching.get('statut', ''),
            'sent_directly': send_directly,
            'email_result': brevo_result,
            'candidate_email_result': candidate_brevo_result,
        }), 200
    except Exception as e:
        app.logger.exception('EURES manual matching failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/brevo-health', methods=['GET'])
@admin_required
def admin_eures_brevo_health(form_id: str):
    """Admin API: return the current Brevo configuration and API reachability state."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown admin form: {form_id}'}), 404

    check_api = str(request.args.get('check') or '').strip().lower() in {'1', 'true', 'yes', 'on'}
    health = get_brevo_health(check_api=check_api)
    status_code = 200 if health['configured'] and (not check_api or health['api_ok'] is True) else 503
    return jsonify({
        'ok': status_code == 200,
        'brevo': health,
    }), status_code


@app.route('/api/forms/<form_id>/admin/matchings/<int:record_id>/decision', methods=['POST'])
@admin_required
def admin_eures_matching_decision(form_id: str, record_id: int):
    """Admin API: accept or refuse one matching."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown admin matching form: {form_id}'}), 404

    data = request.get_json() or {}
    decision = str(data.get('decision') or '').strip().lower()
    note = str(data.get('note') or '').strip()
    employer_email_comment = str(data.get('employer_email_comment') or '').strip()
    candidate_email_comment = str(data.get('candidate_email_comment') or '').strip()
    if decision not in {'accepted', 'refused'}:
        return jsonify({'error': 'Decision must be accepted or refused'}), 400

    config = get_eures_matching_config()
    if not config:
        return jsonify({'error': 'EURES beta matching configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    try:
        existing = fetch_record_by_id(config['doc_id'], EURES_MATCHINGS_TABLE, record_id, headers)
        if not existing:
            return jsonify({'error': 'Matching not found'}), 404
        existing_fields = existing.get('fields', {}) if isinstance(existing.get('fields'), dict) else {}

        if decision == 'accepted':
            ensure_brevo_ready(check_api=True)

        decided_by = get_admin_actor(form_id)
        decision_fields = {
            'admin_status': decision,
            'admin_decision_at': _now_iso_utc(),
            'admin_decision_by': decided_by,
            'admin_decision_note': note,
            'employer_email_comment': employer_email_comment,
            'candidate_email_comment': candidate_email_comment,
        }
        if decision == 'accepted':
            decision_fields.update(_matching_workflow_update_fields('valide_admin', decided_by))
        else:
            decision_fields.update(_matching_workflow_update_fields('refuse_admin', decided_by))
        update_matching_record_by_id(config['doc_id'], record_id, decision_fields, headers)

        app.logger.info(
            'EURES matching decision saved',
            extra={
                'form_id': form_id,
                'record_id': record_id,
                'decision': decision,
                'decided_by': decided_by,
            },
        )

        updated = fetch_record_by_id(config['doc_id'], EURES_MATCHINGS_TABLE, record_id, headers)
        updated_fields = updated.get('fields', {}) if isinstance(updated, dict) else {}
        brevo_result = None
        candidate_brevo_result = None
        if decision == 'accepted':
            matching_rows = list_eures_admin_matchings(status='all', include_candidate_cv=True)
            matching_row = next((row for row in matching_rows if int(row.get('record_id') or 0) == record_id), None)
            if not matching_row:
                raise RuntimeError('Accepted matching could not be reloaded for email delivery.')
            cv_attachment = get_candidate_cv_attachment(matching_row.get('candidat', {}))
            to_email, subject, text_body, html_body = build_brevo_matching_email(matching_row)
            brevo_result = send_brevo_transactional_email(
                to_email,
                subject,
                text_body,
                html_body,
                attachments=[cv_attachment] if cv_attachment else None,
            )
            candidate_to_email, candidate_subject, candidate_text_body, candidate_html_body = build_brevo_candidate_matching_notification_email(matching_row)
            candidate_brevo_result = send_brevo_transactional_email(
                candidate_to_email,
                candidate_subject,
                candidate_text_body,
                candidate_html_body,
            )
            update_matching_record_by_id(
                config['doc_id'],
                record_id,
                _matching_workflow_update_fields('envoye_employeur', decided_by),
                headers,
            )
            app.logger.info(
                'EURES accepted matching email sent',
                extra={
                    'form_id': form_id,
                    'record_id': record_id,
                    'to_email': to_email,
                },
            )
            app.logger.info(
                'EURES accepted matching candidate notification sent',
                extra={
                    'form_id': form_id,
                    'record_id': record_id,
                    'to_email': candidate_to_email,
                },
            )
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'admin_status': updated_fields.get('admin_status', decision),
            'admin_decision_at': updated_fields.get('admin_decision_at', decision_fields['admin_decision_at']),
            'admin_decision_by': updated_fields.get('admin_decision_by', decided_by),
            'admin_decision_note': updated_fields.get('admin_decision_note', note),
            'employer_email_comment': updated_fields.get('employer_email_comment', employer_email_comment),
            'candidate_email_comment': updated_fields.get('candidate_email_comment', candidate_email_comment),
            'email_sent': decision == 'accepted',
            'email_result': brevo_result,
            'candidate_email_result': candidate_brevo_result,
        }), 200
    except Exception as e:
        app.logger.exception('EURES matching decision update failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/matchings/<int:record_id>/candidate-email', methods=['POST'])
@admin_required
def admin_eures_matching_candidate_email(form_id: str, record_id: int):
    """Admin API: resend only the candidate notification email for one matching."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown admin matching form: {form_id}'}), 404

    config = get_eures_matching_config()
    if not config:
        return jsonify({'error': 'EURES beta matching configuration is incomplete.'}), 500

    try:
        ensure_brevo_ready(check_api=True)
        matching_rows = list_eures_admin_matchings(status='all', include_candidate_cv=True)
        matching_row = next((row for row in matching_rows if int(row.get('record_id') or 0) == record_id), None)
        if not matching_row:
            return jsonify({'error': 'Matching not found'}), 404

        candidate_to_email, candidate_subject, candidate_text_body, candidate_html_body = (
            build_brevo_candidate_matching_notification_email(matching_row)
        )
        candidate_brevo_result = send_brevo_transactional_email(
            candidate_to_email,
            candidate_subject,
            candidate_text_body,
            candidate_html_body,
        )

        app.logger.info(
            'EURES matching candidate notification resent',
            extra={
                'form_id': form_id,
                'record_id': record_id,
                'to_email': candidate_to_email,
            },
        )
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'candidate_email_sent': True,
            'candidate_email': candidate_to_email,
            'candidate_email_result': candidate_brevo_result,
        }), 200
    except Exception as e:
        app.logger.exception('EURES matching candidate notification resend failed')
        return jsonify({'error': str(e)}), 500


@app.route('/api/forms/<form_id>/admin/matchings/<int:record_id>/workflow', methods=['POST'])
@admin_required
def admin_eures_matching_workflow(form_id: str, record_id: int):
    """Admin API: advance one matching in the business workflow."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown admin matching form: {form_id}'}), 404

    data = request.get_json() or {}
    target_status = str(data.get('workflow_status') or '').strip().lower()
    note = str(data.get('note') or '').strip()
    allowed_targets = {'mise_en_relation_faite', 'embauche_confirmee', 'envoye_employeur'}
    if target_status not in allowed_targets:
        return jsonify({'error': 'Unsupported workflow status'}), 400

    config = get_eures_matching_config()
    if not config:
        return jsonify({'error': 'EURES beta matching configuration is incomplete.'}), 500

    headers = _eures_admin_headers(config)
    try:
        existing = fetch_record_by_id(config['doc_id'], EURES_MATCHINGS_TABLE, record_id, headers)
        if not existing:
            return jsonify({'error': 'Matching not found'}), 404
        existing_fields = existing.get('fields', {}) if isinstance(existing.get('fields'), dict) else {}
        current_status = _matching_workflow_status(existing_fields)
        if not _eures_workflow_transition_allowed(current_status, target_status):
            return jsonify({
                'error': f'Transition impossible: {current_status} -> {target_status}',
            }), 400

        actor = get_admin_actor(form_id)
        update_fields = _matching_workflow_update_fields(target_status, actor)
        if note:
            previous_note = str(existing_fields.get('admin_decision_note') or '').strip()
            update_fields['admin_decision_note'] = f'{previous_note}\n{note}'.strip() if previous_note else note
        update_matching_record_by_id(config['doc_id'], record_id, update_fields, headers)
        updated = fetch_record_by_id(config['doc_id'], EURES_MATCHINGS_TABLE, record_id, headers)
        updated_fields = updated.get('fields', {}) if isinstance(updated, dict) else {}
        return jsonify({
            'ok': True,
            'record_id': record_id,
            'workflow_status': _matching_workflow_status(updated_fields),
            'workflow_label': _matching_workflow_label(_matching_workflow_status(updated_fields)),
            'workflow_status_updated_at': updated_fields.get('workflow_status_updated_at', ''),
            'workflow_status_updated_by': updated_fields.get('workflow_status_updated_by', actor),
        }), 200
    except Exception as e:
        app.logger.exception('EURES matching workflow update failed')
        return jsonify({'error': str(e)}), 500


@app.route('/eures-beta/matching-feedback', methods=['GET'])
def eures_matching_feedback():
    """Record employer feedback from email CTA links."""
    if should_proxy_eures_public_request('eures-beta'):
        return proxy_eures_public_request(request.path)
    token = str(request.args.get('token') or '').strip()
    if not token:
        return Response('Lien invalide : token manquant.', status=400, mimetype='text/plain')

    try:
        payload = get_eures_email_action_serializer().loads(token)
    except BadSignature:
        return Response('Lien invalide ou expiré.', status=400, mimetype='text/plain')
    except Exception as e:
        app.logger.exception('EURES feedback token decode failed')
        return Response(f'Erreur de lecture du lien : {e}', status=500, mimetype='text/plain')

    record_id = int(payload.get('record_id') or 0)
    response_code = str(payload.get('response') or '').strip().lower()
    if not record_id or response_code not in {'contact', 'not_contact'}:
        return Response('Lien invalide : données incomplètes.', status=400, mimetype='text/plain')

    config = get_eures_matching_config()
    if not config:
        return Response('Configuration EURES incomplète.', status=500, mimetype='text/plain')

    headers = _eures_admin_headers(config)
    response_label = 'je vais le contacter' if response_code == 'contact' else 'je ne vais pas le contacter'
    update_fields = _matching_workflow_update_fields(
        'accepte_employeur' if response_code == 'contact' else 'refuse_employeur',
        'employer_email_link',
    )

    try:
        update_matching_record_by_id(config['doc_id'], record_id, update_fields, headers)
        app.logger.info(
            'EURES employer response recorded',
            extra={
                'record_id': record_id,
                'response': response_code,
            },
        )
    except Exception as e:
        app.logger.exception('EURES employer response update failed')
        return Response(f'Erreur lors de l’enregistrement de votre réponse : {e}', status=500, mimetype='text/plain')

    html = f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>EURES beta - Réponse enregistrée</title>
  </head>
  <body style="margin:0;background:#f4efe6;font-family:Georgia,'Times New Roman',serif;color:#1f1f1f;">
    <div style="max-width:720px;margin:32px auto;padding:0 16px;">
      <div style="background:#fffdf9;border:1px solid #e7dcc7;border-radius:18px;overflow:hidden;">
        <div style="padding:28px 32px;background:linear-gradient(135deg,#103a2b 0%,#1f5a45 100%);color:#fff;">
          <div style="font-size:13px;letter-spacing:1.4px;text-transform:uppercase;opacity:0.82;">EURES beta</div>
          <h1 style="margin:10px 0 0;font-size:30px;line-height:1.2;">Réponse enregistrée</h1>
        </div>
        <div style="padding:28px 32px;">
          <p style="margin:0 0 16px;font-size:17px;line-height:1.7;">
            Merci. Votre réponse a bien été enregistrée :
            <strong>{escape(response_label)}</strong>.
          </p>
          <p style="margin:0;font-size:15px;line-height:1.7;">
            Si besoin, vous pouvez aussi répondre directement à l’email reçu.
          </p>
        </div>
      </div>
    </div>
  </body>
</html>"""
    return Response(html, status=200, mimetype='text/html')


@app.route('/api/forms/<form_id>/public-stats', methods=['GET'])
def public_stats(form_id: str):
    """Public aggregated stats page data."""
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    if form_id != 'eures-beta':
        return jsonify({'error': f'Unknown public stats form: {form_id}'}), 404

    try:
        return jsonify(build_eures_public_stats()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    deep = str(request.args.get('deep') or '').strip().lower() in {'1', 'true', 'yes', 'on'}
    payload = {'status': 'ok'}
    if deep:
        brevo = get_brevo_health(check_api=True)
        payload['brevo'] = brevo
        if not brevo['configured'] or brevo['api_ok'] is not True:
            payload['status'] = 'degraded'
            return jsonify(payload), 503
    return jsonify(payload)


@app.route('/')
def index():
    return redirect(f"/forms/{get_default_home_form_id()}/")


# Static file serving for forms and frontend
@app.route('/forms/<form_id>/')
@app.route('/forms/<form_id>')
def serve_form(form_id: str):
    """Serve form HTML."""
    if not is_form_enabled(form_id):
        return jsonify({'error': 'File not found'}), 404
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    return send_from_directory(FORMS_DIR / form_id, 'index.html')


@app.route('/forms/fagerh/questions-pdf')
def serve_fagerh_questions_pdf():
    """Serve the reference PDF containing FAGERH questions."""
    return send_from_directory(
        DOCS_DIR,
        'fagerh_questions_completes.pdf',
        as_attachment=True,
        download_name='fagerh_questions_fagerh.pdf',
    )


@app.route('/forms/<form_id>/<path:filename>')
def serve_form_file(form_id: str, filename: str):
    """Serve extra files from a form folder (e.g. UI prototypes)."""
    if not is_form_enabled(form_id):
        return jsonify({'error': 'File not found'}), 404
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    resolved = _resolve_form_path(form_id, filename)
    if not resolved:
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(FORMS_DIR / form_id, resolved)


@app.route('/admin/<form_id>/login', methods=['GET', 'POST'])
def admin_login(form_id: str):
    """Magic-link login entrypoint for admin surfaces."""
    if not is_form_enabled(form_id):
        return jsonify({'error': 'File not found'}), 404
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    mode = get_admin_auth_mode(form_id)
    if mode not in {'magic_link', 'hybrid'}:
        return Response('Admin magic-link login is not enabled for this form.', status=404, mimetype='text/plain')

    if _current_admin_session(form_id):
        return redirect(url_for('serve_admin', form_id=form_id))

    if request.method == 'GET':
        return _render_admin_login_page(form_id)

    payload = request.get_json(silent=True) if request.is_json else {}
    email = normalize_email((payload or {}).get('email') or request.form.get('email'))
    allowed_emails = get_admin_allowed_emails(form_id)
    generic_message = "Si cette adresse est autorisee, un lien de connexion vient d'etre envoye."
    rate_limit_seconds = get_admin_magic_link_rate_limit_seconds(form_id)

    if not email:
        if request.is_json:
            return jsonify({'error': 'Email required'}), 400
        return _render_admin_login_page(form_id, error='Veuillez saisir une adresse email valide.')

    app.logger.info(
        'Admin magic link requested',
        extra={
            'form_id': form_id,
            'email': email,
            'client_ip': request.headers.get('X-Forwarded-For', request.remote_addr or ''),
        },
    )

    if email in allowed_emails:
        throttle_key = (form_id, email)
        now = time.time()
        last_sent = _ADMIN_MAGIC_LINK_REQUESTS.get(throttle_key, 0.0)
        if rate_limit_seconds and now - last_sent < rate_limit_seconds:
            app.logger.warning(
                'Admin magic link throttled',
                extra={'form_id': form_id, 'email': email},
            )
        else:
            token = get_admin_magic_link_serializer(form_id).dumps({
                'form_id': form_id,
                'email': email,
                'jti': secrets.token_urlsafe(16),
            })
            login_link = url_for('admin_magic_link_consume', form_id=form_id, token=token, _external=True)
            recipient, subject, text_body, html_body = build_admin_magic_link_email(form_id, email, login_link)
            send_brevo_transactional_email(recipient, subject, text_body, html_body)
            _ADMIN_MAGIC_LINK_REQUESTS[throttle_key] = now
            app.logger.info(
                'Admin magic link sent',
                extra={'form_id': form_id, 'email': email},
            )
    else:
        app.logger.warning(
            'Admin magic link rejected by allowlist',
            extra={'form_id': form_id, 'email': email},
        )

    if request.is_json:
        return jsonify({'ok': True, 'message': generic_message}), 200
    return _render_admin_login_page(form_id, message=generic_message)


@app.route('/admin/<form_id>/magic-login', methods=['GET'])
@app.route('/admin/<form_id>/magic', methods=['GET'])
def admin_magic_link_consume(form_id: str):
    """Validate one signed admin login link and open a session."""
    if not is_form_enabled(form_id):
        return jsonify({'error': 'File not found'}), 404
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    mode = get_admin_auth_mode(form_id)
    if mode not in {'magic_link', 'hybrid'}:
        return Response('Admin magic-link login is not enabled for this form.', status=404, mimetype='text/plain')

    token = str(request.args.get('token') or '').strip()
    if not token:
        return Response('Lien invalide : token manquant.', status=400, mimetype='text/plain')

    try:
        payload = get_admin_magic_link_serializer(form_id).loads(
            token,
            max_age=get_admin_magic_link_ttl_seconds(form_id),
        )
    except SignatureExpired:
        return Response('Lien invalide ou expire.', status=400, mimetype='text/plain')
    except BadSignature:
        return Response('Lien invalide ou expire.', status=400, mimetype='text/plain')
    except Exception as e:
        app.logger.exception('Admin magic link decode failed')
        return Response(f'Erreur de lecture du lien : {e}', status=500, mimetype='text/plain')

    email = normalize_email(payload.get('email'))
    token_form_id = str(payload.get('form_id') or '').strip()
    jti = str(payload.get('jti') or '').strip()
    if token_form_id != form_id or email not in get_admin_allowed_emails(form_id) or not jti:
        app.logger.warning(
            'Admin magic link rejected after decode',
            extra={'form_id': form_id, 'email': email},
        )
        return Response('Lien invalide : acces non autorise.', status=403, mimetype='text/plain')
    if not _consume_admin_magic_link_jti(jti, get_admin_magic_link_ttl_seconds(form_id)):
        app.logger.warning(
            'Admin magic link replay blocked',
            extra={'form_id': form_id, 'email': email},
        )
        return Response('Lien deja utilise.', status=400, mimetype='text/plain')

    _set_admin_session(form_id, email)
    app.logger.info(
        'Admin magic link session opened',
        extra={'form_id': form_id, 'email': email},
    )
    return redirect(url_for('serve_admin', form_id=form_id))


@app.route('/admin/<form_id>/logout', methods=['GET', 'POST'])
def admin_logout(form_id: str):
    """Close one admin session."""
    if not is_form_enabled(form_id):
        return jsonify({'error': 'File not found'}), 404
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    identity = _current_admin_session(form_id)
    _clear_admin_session(form_id)
    if identity:
        app.logger.info(
            'Admin session closed',
            extra={'form_id': form_id, 'email': identity.get('email', '')},
        )
    return redirect(url_for('admin_login', form_id=form_id))


@app.route('/admin/<form_id>/')
@app.route('/admin/<form_id>')
@admin_required
def serve_admin(form_id: str):
    """Serve admin dashboard HTML for a form."""
    if not is_form_enabled(form_id):
        return jsonify({'error': 'File not found'}), 404
    proxied = maybe_proxy_eures_request(form_id)
    if proxied:
        return proxied
    return send_from_directory(FORMS_DIR / form_id, 'admin.html')


@app.route('/assets/<path:filename>')
def serve_assets(filename: str):
    """Serve static assets (JS, CSS)."""
    return send_from_directory(ASSETS_DIR, filename)

if fagerh_suivi_app is not None:
    app.wsgi_app = DispatcherMiddleware(
        app.wsgi_app,
        {
            '/forms/fagerh/saisie-quotidienne': fagerh_suivi_app,
        },
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005, debug=False)
