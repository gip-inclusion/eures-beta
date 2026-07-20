"""Editorial templates for EURES beta candidate invitation emails.

This module stores email copy separately from the invitation sending logic.
"""

from __future__ import annotations

from copy import deepcopy


SUPPORTED_LANGUAGES = ("fr", "en", "de")

CANDIDATE_TARGET_JOB_OPTIONS = [
    {
        "key": "vente",
        "labels": {
            "fr": "Vente et commerce",
            "en": "Sales and retail",
            "de": "Verkauf und Handel",
        },
    },
    {
        "key": "nettoyage",
        "labels": {
            "fr": "Nettoyage et entretien",
            "en": "Cleaning and maintenance",
            "de": "Reinigung und Instandhaltung",
        },
    },
    {
        "key": "hotellerie",
        "labels": {
            "fr": "Hôtellerie et restauration",
            "en": "Hospitality and catering",
            "de": "Hotellerie und Gastronomie",
        },
    },
    {
        "key": "agriculture",
        "labels": {
            "fr": "Agriculture et récolte",
            "en": "Agriculture and harvesting",
            "de": "Landwirtschaft und Ernte",
        },
    },
    {
        "key": "polyvalent",
        "labels": {
            "fr": "Missions polyvalentes",
            "en": "Versatile entry-level jobs",
            "de": "Vielseitige Tätigkeiten",
        },
    },
    {
        "key": "industrie_production",
        "labels": {
            "fr": "Production industrielle (assemblage, fabrication, conditionnement, contrôle qualité)",
            "en": "Industrial production (assembly, manufacturing, packaging, quality control)",
            "de": "Industrielle Produktion (Montage, Fertigung, Verpackung, Qualitätskontrolle)",
        },
    },
]

_OPTION_KEYS = {item["key"] for item in CANDIDATE_TARGET_JOB_OPTIONS}

CANDIDATE_INVITATION_EMAIL_TEMPLATES = {
    "generic": {
        "initial": {
            "fr": {
                "subject": "Des entreprises recrutent actuellement — votre profil nous intéresse",
                "preheader": "Répondez en 2 à 3 minutes pour voir si votre profil peut être proposé à des employeurs partenaires.",
                "eyebrow": "",
                "title": "Des employeurs recrutent actuellement",
                "hook": "Votre profil pourrait correspondre à des besoins déjà exprimés par des entreprises partenaires.",
                "body": [
                    "Nous vous invitons à répondre à un court questionnaire afin de mieux comprendre votre disponibilité, votre mobilité et le type d’opportunités qui vous correspondent.",
                    "Ce questionnaire constitue la première étape pour pouvoir vous proposer à des employeurs partenaires lorsqu’un besoin correspond à votre profil.",
                ],
                "cta_label": "Voir si mon profil correspond",
                "cta_note": "Le questionnaire prend 2 à 3 minutes et vous permet d’être positionné sur des opportunités correspondant à votre profil.",
                "info_title": "À retenir",
                "info_items": [
                    "Première étape avant proposition à des employeurs partenaires",
                    "Analyse réalisée dans le cadre d’EURES beta par France Travail et EURES",
                ],
                "legal_intro": "Vous recevez ce message dans le cadre de l’expérimentation EURES beta portée par France Travail et EURES.",
                "footer_network": "EURES est le réseau européen de coopération pour l’emploi, qui facilite les recrutements et les opportunités professionnelles en Europe.",
            },
            "en": {
                "subject": "Companies are currently recruiting in your field – your profile may be relevant",
                "preheader": "Answer in 2 to 3 minutes to see whether your profile could be shared with partner employers.",
                "eyebrow": "Current opportunities",
                "title": "Employers are currently recruiting in your field",
                "hook": "Your profile may match needs already expressed by partner employers.",
                "body": [
                    "We invite you to complete a short questionnaire so we can better understand your availability, your mobility plans and the opportunities that may suit you.",
                    "This questionnaire is the first step that allows us to share your profile with partner employers when a need matches your situation.",
                ],
                "cta_label": "See if my profile matches",
                "cta_note": "The questionnaire takes 2 to 3 minutes and helps position you on opportunities that match your profile.",
                "info_title": "Key points",
                "info_items": [
                    "Quick answer: 2 to 3 minutes",
                    "First step before being shared with partner employers",
                    "Reviewed within EURES beta by France Travail and EURES",
                ],
                "legal_intro": "You are receiving this message as part of the EURES beta experiment led by France Travail and EURES.",
                "footer_network": "EURES is the European cooperation network for employment, helping with recruitment and professional opportunities across Europe.",
            },
            "de": {
                "subject": "Unternehmen rekrutieren aktuell in Ihrem Bereich – Ihr Profil könnte passen",
                "preheader": "Antworten Sie in 2 bis 3 Minuten, um zu sehen, ob Ihr Profil an Partnerarbeitgeber weitergeleitet werden kann.",
                "eyebrow": "Aktuelle Chancen",
                "title": "Arbeitgeber rekrutieren aktuell in Ihrem Tätigkeitsbereich",
                "hook": "Ihr Profil könnte zu bereits gemeldeten Bedarfen von Partnerarbeitgebern passen.",
                "body": [
                    "Wir laden Sie ein, einen kurzen Fragebogen auszufüllen, damit wir Ihre Verfügbarkeit, Ihr Mobilitätsprojekt und passende berufliche Möglichkeiten besser verstehen können.",
                    "Dieser Fragebogen ist der erste Schritt, damit Ihr Profil an Partnerarbeitgeber weitergeleitet werden kann, wenn ein Bedarf zu Ihrer Situation passt.",
                ],
                "cta_label": "Prüfen, ob mein Profil passt",
                "cta_note": "Der Fragebogen dauert 2 bis 3 Minuten und hilft, Sie auf passende Möglichkeiten zu positionieren.",
                "info_title": "Wichtig zu wissen",
                "info_items": [
                    "Schnelle Antwort: 2 bis 3 Minuten",
                    "Erster Schritt vor einer Weiterleitung an Partnerarbeitgeber",
                    "Prüfung im Rahmen von EURES beta durch France Travail und EURES",
                ],
                "legal_intro": "Sie erhalten diese Nachricht im Rahmen des Experiments EURES beta von France Travail und EURES.",
                "footer_network": "EURES ist das europäische Kooperationsnetzwerk für Beschäftigung und unterstützt Rekrutierung sowie berufliche Chancen in Europa.",
            },
        },
        "reminder": {
            "fr": {
                "subject": "Des entreprises recrutent toujours – vérifiez si votre profil correspond",
                "preheader": "Le questionnaire prend 2 à 3 minutes et reste la première étape pour être proposé à des employeurs partenaires.",
                "eyebrow": "",
                "title": "Des employeurs recrutent actuellement",
                "hook": "Votre profil pourrait toujours correspondre à des besoins en cours.",
                "body": [
                    "Si vous êtes toujours disponible ou intéressé par des opportunités, vous pouvez encore compléter le questionnaire ci-dessous.",
                    "Il nous permet de vérifier rapidement si votre profil peut être proposé à des employeurs partenaires.",
                ],
                "cta_label": "Voir si mon profil correspond",
                "cta_note": "Le questionnaire prend 2 à 3 minutes.",
                "info_title": "Pourquoi répondre",
                "info_items": [
                    "Des recrutements sont en cours",
                    "Réponse rapide en 2 à 3 minutes",
                    "Première étape avant proposition à des employeurs partenaires",
                ],
                "legal_intro": "Ce rappel vous est adressé dans le cadre de l’expérimentation EURES beta portée par France Travail et EURES.",
                "footer_network": "EURES est le réseau européen de coopération pour l’emploi, qui facilite les recrutements et les opportunités professionnelles en Europe.",
            },
            "en": {
                "subject": "Companies are still recruiting – check whether your profile matches",
                "preheader": "The questionnaire still takes 2 to 3 minutes and remains the first step before being shared with partner employers.",
                "eyebrow": "Reminder",
                "title": "Employers are still recruiting in your field",
                "hook": "Your profile may still match ongoing recruitment needs.",
                "body": [
                    "If you are still available or interested in opportunities, you can still complete the questionnaire below.",
                    "It allows us to quickly check whether your profile can be shared with partner employers.",
                ],
                "cta_label": "See if my profile matches",
                "cta_note": "The questionnaire takes 2 to 3 minutes.",
                "info_title": "Why answer",
                "info_items": [
                    "Recruitment is ongoing",
                    "Quick answer in 2 to 3 minutes",
                    "First step before being shared with partner employers",
                ],
                "legal_intro": "This reminder is sent as part of the EURES beta experiment led by France Travail and EURES.",
                "footer_network": "EURES is the European cooperation network for employment, helping with recruitment and professional opportunities across Europe.",
            },
            "de": {
                "subject": "Unternehmen rekrutieren weiterhin – prüfen Sie, ob Ihr Profil passt",
                "preheader": "Der Fragebogen dauert weiterhin 2 bis 3 Minuten und bleibt der erste Schritt vor einer Weiterleitung an Partnerarbeitgeber.",
                "eyebrow": "Erinnerung",
                "title": "Arbeitgeber rekrutieren weiterhin in Ihrem Bereich",
                "hook": "Ihr Profil könnte weiterhin zu laufenden Bedarfen passen.",
                "body": [
                    "Wenn Sie weiterhin verfügbar oder interessiert sind, können Sie den Fragebogen unten noch ausfüllen.",
                    "So können wir schnell prüfen, ob Ihr Profil an Partnerarbeitgeber weitergeleitet werden kann.",
                ],
                "cta_label": "Prüfen, ob mein Profil passt",
                "cta_note": "Der Fragebogen dauert 2 bis 3 Minuten.",
                "info_title": "Warum antworten",
                "info_items": [
                    "Rekrutierungen laufen noch",
                    "Schnelle Antwort in 2 bis 3 Minuten",
                    "Erster Schritt vor einer Weiterleitung an Partnerarbeitgeber",
                ],
                "legal_intro": "Diese Erinnerung wird im Rahmen des Experiments EURES beta von France Travail und EURES versendet.",
                "footer_network": "EURES ist das europäische Kooperationsnetzwerk für Beschäftigung und unterstützt Rekrutierung sowie berufliche Chancen in Europa.",
            },
        },
    },
    "industrie_production": {
        "initial": {
            "fr": {
                "subject": "Des entreprises recrutent actuellement en production industrielle – votre profil nous intéresse",
                "preheader": "Répondez en 2 à 3 minutes pour voir si votre profil peut correspondre à des postes en production industrielle.",
                "title": "Vous recherchez un poste en production industrielle ?",
                "hook": "Des entreprises partenaires recrutent actuellement sur ce métier et votre profil pourrait correspondre à leurs besoins.",
                "body": [
                    "En répondant au questionnaire, vous nous aidez à vérifier rapidement vos disponibilités, votre mobilité et les conditions de travail qui vous conviennent.",
                    "C’est la première étape pour pouvoir vous proposer à des employeurs partenaires qui recrutent actuellement en production industrielle.",
                ],
                "cta_note": "Le questionnaire prend 2 à 3 minutes et nous permet de vérifier rapidement si votre profil peut être positionné sur ces recrutements.",
            },
            "en": {
                "subject": "Companies are currently recruiting production operators – your profile may be relevant",
                "preheader": "Answer in 2 to 3 minutes to see whether your profile may fit production operator roles in industry.",
                "title": "Are you looking for a production operator role in industry?",
                "hook": "Partner companies are currently recruiting for this role and your profile may fit their needs.",
                "body": [
                    "By answering the questionnaire, you help us quickly check your availability, your mobility plans and the working conditions that suit you.",
                    "This is the first step that allows us to share your profile with partner employers currently looking for production operators.",
                ],
                "cta_note": "The questionnaire takes 2 to 3 minutes and helps us quickly assess whether your profile can be positioned on these recruitments.",
            },
            "de": {
                "subject": "Unternehmen rekrutieren aktuell Produktionsmitarbeitende – Ihr Profil könnte passen",
                "preheader": "Antworten Sie in 2 bis 3 Minuten, um zu sehen, ob Ihr Profil zu Produktionsstellen in der Industrie passen könnte.",
                "title": "Suchen Sie eine Stelle in der industriellen Produktion?",
                "hook": "Partnerunternehmen rekrutieren aktuell für dieses Tätigkeitsfeld und Ihr Profil könnte zu ihrem Bedarf passen.",
                "body": [
                    "Mit Ihrer Antwort auf den Fragebogen helfen Sie uns, Ihre Verfügbarkeit, Ihr Mobilitätsprojekt und passende Arbeitsbedingungen schnell einzuordnen.",
                    "Das ist der erste Schritt, damit Ihr Profil an Partnerarbeitgeber weitergeleitet werden kann, die aktuell Produktionsmitarbeitende suchen.",
                ],
                "cta_note": "Der Fragebogen dauert 2 bis 3 Minuten und hilft uns, Ihr Profil schnell auf diese Rekrutierungen zu positionieren.",
            },
        },
        "reminder": {
            "fr": {
                "subject": "Des postes en production industrielle sont toujours ouverts – vérifiez si votre profil correspond",
                "preheader": "Le questionnaire prend 2 à 3 minutes et permet toujours de vous positionner sur des recrutements en production industrielle.",
                "title": "Des postes en production industrielle sont toujours ouverts",
                "hook": "Des employeurs partenaires recherchent toujours ce profil.",
                "body": [
                    "Si vous êtes toujours intéressé, vous pouvez encore compléter le questionnaire ci-dessous afin que nous vérifiions rapidement si votre profil correspond.",
                    "C’est la première étape pour pouvoir vous proposer à des employeurs partenaires sur ce métier.",
                ],
                "cta_note": "Le questionnaire prend 2 à 3 minutes.",
            },
            "en": {
                "subject": "Production operator roles are still open – check whether your profile matches",
                "preheader": "The questionnaire still takes 2 to 3 minutes and can still position you on ongoing production recruitments.",
                "title": "Production operator roles are still open",
                "hook": "Partner employers are still recruiting for this profile.",
                "body": [
                    "If you are still interested, you can still complete the questionnaire below so that we can quickly check whether your profile matches.",
                    "This is the first step before we can share your profile with partner employers for this role.",
                ],
                "cta_note": "The questionnaire takes 2 to 3 minutes.",
            },
            "de": {
                "subject": "Produktionsstellen sind weiterhin offen – prüfen Sie, ob Ihr Profil passt",
                "preheader": "Der Fragebogen dauert weiterhin 2 bis 3 Minuten und kann Sie noch auf laufende Rekrutierungen in der Industrie positionieren.",
                "title": "Produktionsstellen sind weiterhin offen",
                "hook": "Partnerarbeitgeber suchen weiterhin nach diesem Profil.",
                "body": [
                    "Wenn Sie weiterhin interessiert sind, können Sie den Fragebogen unten noch ausfüllen, damit wir schnell prüfen können, ob Ihr Profil passt.",
                    "Das ist der erste Schritt, bevor Ihr Profil an Partnerarbeitgeber für dieses Tätigkeitsfeld weitergeleitet werden kann.",
                ],
                "cta_note": "Der Fragebogen dauert 2 bis 3 Minuten.",
            },
        },
    },
}


def normalize_email_template_language(language: str) -> str:
    normalized = str(language or "fr").strip().lower()
    return normalized if normalized in SUPPORTED_LANGUAGES else "fr"


def normalize_target_job_key(value: str) -> str:
    key = str(value or "").strip().lower()
    return key if key in _OPTION_KEYS else ""


def get_candidate_target_job_options(language: str = "fr") -> list[dict]:
    lang = normalize_email_template_language(language)
    return [
        {"key": item["key"], "label": item["labels"].get(lang) or item["labels"]["fr"]}
        for item in CANDIDATE_TARGET_JOB_OPTIONS
    ]


def get_candidate_target_job_label(target_job_key: str, language: str = "fr") -> str:
    key = normalize_target_job_key(target_job_key)
    if not key:
        return ""
    for item in CANDIDATE_TARGET_JOB_OPTIONS:
        if item["key"] == key:
            lang = normalize_email_template_language(language)
            return item["labels"].get(lang) or item["labels"]["fr"]
    return ""


def get_candidate_invitation_template(
    language: str = "fr",
    *,
    target_job_key: str = "",
    kind: str = "initial",
) -> dict:
    """Return one candidate invitation template with generic fallback."""
    lang = normalize_email_template_language(language)
    normalized_kind = "reminder" if str(kind).strip().lower() == "reminder" else "initial"
    base = deepcopy(CANDIDATE_INVITATION_EMAIL_TEMPLATES["generic"][normalized_kind][lang])
    job_key = normalize_target_job_key(target_job_key)
    if not job_key:
        return base
    job_label = get_candidate_target_job_label(job_key, lang)
    specific_bundle = CANDIDATE_INVITATION_EMAIL_TEMPLATES.get(job_key, {}).get(normalized_kind, {})
    specific = specific_bundle.get(lang) or {}
    if not specific:
        if job_label:
            if lang == "en":
                if normalized_kind == "reminder":
                    base["subject"] = f"Companies are still recruiting in {job_label} – check whether your profile matches"
                    base["title"] = f"Employers are still recruiting in {job_label}"
                    base["hook"] = f"Your profile may still match ongoing recruitment needs in {job_label.lower()}."
                else:
                    base["subject"] = f"Companies are currently recruiting in {job_label} — your profile may be relevant"
                    base["title"] = f"Employers are currently recruiting in {job_label}"
                    base["hook"] = f"Your profile may match needs already expressed by partner employers in {job_label.lower()}."
            elif lang == "de":
                if normalized_kind == "reminder":
                    base["subject"] = f"Unternehmen rekrutieren weiterhin in {job_label} – prüfen Sie, ob Ihr Profil passt"
                    base["title"] = f"Arbeitgeber rekrutieren weiterhin in {job_label}"
                    base["hook"] = f"Ihr Profil könnte weiterhin zu laufenden Bedarfen in {job_label} passen."
                else:
                    base["subject"] = f"Unternehmen rekrutieren aktuell in {job_label} — Ihr Profil könnte passen"
                    base["title"] = f"Arbeitgeber rekrutieren aktuell in {job_label}"
                    base["hook"] = f"Ihr Profil könnte zu bereits gemeldeten Bedarfen von Partnerarbeitgebern in {job_label} passen."
            else:
                if normalized_kind == "reminder":
                    base["subject"] = f"Des entreprises recrutent toujours en {job_label} – vérifiez si votre profil correspond"
                    base["title"] = f"Des employeurs recrutent actuellement en {job_label}"
                    base["hook"] = f"Votre profil pourrait toujours correspondre à des besoins en {job_label.lower()}."
                else:
                    base["subject"] = f"Des entreprises recrutent actuellement en {job_label} — votre profil nous intéresse"
                    base["title"] = f"Des employeurs recrutent actuellement en {job_label}"
                    base["hook"] = f"Votre profil pourrait correspondre à des besoins déjà exprimés par des entreprises partenaires en {job_label.lower()}."
        return base
    merged = deepcopy(base)
    merged.update(specific)
    return merged
