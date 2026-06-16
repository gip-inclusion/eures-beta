const FORM_ID = "eures-beta";
const BASE_PATH = `/forms/${FORM_ID}`;
const LANGS = ["fr", "en", "de"];
const DEFAULT_LANG = "fr";

const copy = {
  fr: {
    common: {
      brandTitle: "EURES beta",
      brandSubtitle: "Mobilité, matching et accompagnement transfrontalier",
      navHome: "Accueil",
      navCandidate: "Candidat",
      navEmployer: "Employeur",
      navStats: "Statistiques",
      langLabel: "Langue",
      footer: "Prototype de démarrage pour tester l’inscription, le matching et l’envoi structuré vers GRIST.",
      ctaStartCandidate: "Commencer côté candidat",
      ctaStartEmployer: "Commencer côté employeur",
      ctaBackHome: "Retour à l’accueil",
      ctaQuestionnaire: "Démarrer le questionnaire",
      ctaSeeCandidate: "Voir le parcours candidat",
      ctaSeeEmployer: "Voir le parcours employeur",
      matchingTitle: "Comment le matching va fonctionner",
      matchingBullets: [
        "Chaque réponse est envoyée dans GRIST avec un rôle, une langue et un identifiant de reprise.",
        "Un score de compatibilité peut être calculé entre secteurs, mobilité, langues, disponibilités et conditions proposées.",
        "Si le score est élevé, la mise en relation peut être automatisée. Sinon, un contrôle humain peut valider ou corriger."
      ],
      futureTitle: "Ce qui vient ensuite",
      futureBullets: [
        "Tableau de bord candidat pour suivre ses opportunités et son statut.",
        "Tableau de bord employeur pour suivre les profils proposés et les retours.",
        "Historique de matching, validations humaines et traçabilité des décisions."
      ],
      consent: "J’accepte que mes réponses soient utilisées par les équipes et partenaires EURES dans le cadre du matching et de l’accompagnement à la mobilité professionnelle.",
      submit: "Enregistrer mes réponses",
      saving: "Enregistrement en cours...",
      saved: "Réponses enregistrées.",
      saveErrorPrefix: "Échec de l’enregistrement",
      uuidPrefix: "Identifiant de reprise",
      questionnaireNote: "Le questionnaire est volontairement resserré pour cette première version. Il reprend la logique des Tally de référence sans les recopier entièrement."
    },
    home: {
      eyebrow: "Tester un service concret dans la Grande Région",
      title: "Connecter les travailleurs mobiles et les offres qui restent hors radar.",
      lede: "EURES beta vise un problème simple : le marché du travail est transfrontalier, mais la recherche d’emploi et le recrutement restent encore très nationaux. Le service veut capter les intentions, structurer les besoins et envoyer les bonnes opportunités plus vite.",
      storyTitle: "Le point de départ",
      storyText: "Des personnes ayant déjà travaillé au Luxembourg, en Allemagne ou dans un autre pays voisin cherchent souvent d’abord dans leur pays de résidence. En face, des employeurs ont des besoins réels mais peinent à toucher ces profils mobiles.",
      stats: [
        ["280 000", "travailleurs frontaliers circulent chaque jour dans la Grande Région."],
        ["40–50 k", "personnes avec expérience transfrontalière pourraient rechercher un emploi."],
        ["15 000+", "postes resteraient vacants dans le même bassin économique."]
      ],
      tracksTitle: "Deux portes d’entrée, un même moteur",
      candidateTitle: "Parcours candidat",
      candidateText: "Comprendre le projet de mobilité, les secteurs visés, les langues, les disponibilités et les éléments concrets qui facilitent une mise en relation rapide.",
      employerTitle: "Parcours employeur",
      employerText: "Qualifier les besoins de recrutement, les langues, les contraintes de poste, les aides à l’installation et les critères déterminants côté entreprise.",
      principlesTitle: "Principes produit",
      principles: [
        ["Simple dès le départ", "Un premier parcours léger, multilingue, exploitable tout de suite."],
        ["Data utile", "Des réponses structurées pour alimenter GRIST et préparer le scoring de matching."],
        ["Validation humaine", "Quand le score est insuffisant ou ambigu, un opérateur EURES reprend la main."]
      ]
    },
    candidateLanding: {
      kicker: "Parcours candidat",
      title: "Un questionnaire simple pour explorer des opportunités de mobilité en Europe.",
      lede: "Cette démarche s’adresse aux personnes qui peuvent envisager une mobilité professionnelle européenne, soit en transfrontalier, soit en expatriation. En clair : travailler dans un pays voisin tout en vivant chez soi, ou partir vivre et travailler dans un autre pays européen.",
      messageTitle: "Pourquoi remplir ce questionnaire ?",
      messageIntro: "Ce questionnaire nous aide à comprendre plus vite si votre profil peut correspondre à des opportunités liées à la mobilité européenne.",
      messageBody: [
        "Aujourd’hui, le test est mené surtout avec des entreprises basées au Luxembourg, dans un cadre de mobilité transfrontalière ou de mobilité vers un autre pays européen.",
        "Nous parlons ici d’une phase de test très concrète : on essaie, on regarde ce qui marche, puis on améliore.",
        "Autrement dit, le service n’est pas encore finalisé, mais il sert déjà à faire remonter de vraies opportunités pour des personnes prêtes à bouger en Europe."
      ],
      messageHighlight: "Vous répondez une fois, et cela nous permet de mieux voir si certaines offres en mobilité européenne peuvent vous convenir maintenant ou bientôt.",
      messageOutcome: "Le service va ensuite s’ouvrir à d’autres employeurs en Allemagne, en Belgique et en France, ainsi qu’à davantage de métiers.",
      signatureTitle: "En ce moment, les premiers tests concernent surtout :",
      signatureName: "le Luxembourg",
      signatureRole: "et plusieurs secteurs qui recrutent",
      bulletsTitle: "Métiers actuellement testés avec des employeurs luxembourgeois",
      bullets: [
        "La vente et le commerce",
        "Le nettoyage et l’entretien",
        "L’hôtellerie et la restauration",
        "L’agriculture et les récoltes",
        "Les missions polyvalentes et les emplois accessibles rapidement"
      ],
      sideTitle: "Qui sommes-nous ?",
      sideText: "EURES est le réseau européen de coopération pour l’emploi. Il facilite les recrutements et les opportunités professionnelles en Europe, en particulier sur les parcours transfrontaliers où les candidatures et les offres se croisent difficilement.",
      disclaimerTitle: "Ce qui va se passer ensuite",
      disclaimerText: "Si votre profil correspond à des besoins en cours, il pourra être regardé pour une mise en relation. Et au fil du temps, d’autres entreprises, d’autres pays et d’autres métiers viendront enrichir le service.",
      tags: ["EURES", "France Travail", "Union européenne", "Luxembourg", "Vente & commerce"],
      logos: {
        eures: {
          src: "https://eures.europa.eu/sites/default/files/site-logo-overrides/EURES%20Gradient%20logo%20SVG%20stretched.svg",
          alt: "Logo EURES"
        },
        franceTravail: {
          src: "https://cdn.francetravail.fr/studio/logos/marque/favicon/favicon.svg",
          alt: "Logo France Travail"
        },
        europeanUnion: {
          src: "https://european-union.europa.eu/themes/contrib/oe_theme/dist/eu/images/logo/condensed-version/positive/logo-eu--en.svg",
          alt: "Logo Union européenne"
        }
      }
    },
    employerLanding: {
      kicker: "Parcours employeur",
      title: "Un questionnaire simple pour faire remonter vos besoins de recrutement en mobilité européenne.",
      lede: "Cette démarche s’adresse aux employeurs qui peuvent recruter au-delà de leur marché local, en transfrontalier ou avec des candidats venant d’un autre pays européen. L’objectif est simple : comprendre votre besoin plus clairement pour identifier plus vite des profils pouvant correspondre.",
      messageTitle: "Pourquoi remplir ce questionnaire ?",
      messageIntro: "Ce questionnaire nous aide à comprendre votre besoin de recrutement, le contexte du poste et les conditions proposées.",
      messageBody: [
        "Aujourd’hui, l’expérimentation est menée d’abord avec des entreprises basées au Luxembourg, sur des recrutements concrets et parfois difficiles à couvrir.",
        "Nous sommes dans une phase de test très pratique : nous regardons ce qui aide vraiment à faire émerger des profils pertinents, puis nous améliorons le service.",
        "En clair, vous décrivez votre besoin une fois, et cela nous permet de mieux repérer les candidatures qui peuvent être compatibles."
      ],
      messageHighlight: "Le but n’est pas de vous faire perdre du temps avec un formulaire de plus. Le but est de mieux qualifier votre besoin pour faciliter ensuite les mises en relation.",
      messageOutcome: "Le service s’ouvrira progressivement à d’autres employeurs en Allemagne, en Belgique et en France, ainsi qu’à d’autres métiers.",
      signatureTitle: "En ce moment, les premiers tests concernent surtout :",
      signatureName: "des employeurs luxembourgeois",
      signatureRole: "et plusieurs secteurs qui recrutent",
      bulletsTitle: "Ce que l’on va qualifier",
      bullets: [
        "La vente et le commerce",
        "Le nettoyage et l’entretien",
        "L’hôtellerie et la restauration",
        "L’agriculture et les récoltes",
        "Les missions polyvalentes et les emplois accessibles rapidement"
      ],
      sideTitle: "Ce que cela change pour vous",
      sideText: "Vous précisez le type de recrutement, les langues utiles, les contraintes du poste, le niveau attendu et les aides éventuelles à l’arrivée. Cela nous permet de comparer plus sérieusement les besoins côté employeur et les attentes côté candidat.",
      disclaimerTitle: "Ce qui se passe ensuite",
      disclaimerText: "Si des profils paraissent compatibles avec votre recherche, votre besoin peut être repris pour une mise en relation. Et si le besoin n’est pas encore assez clair, le questionnaire nous aide déjà à mieux préparer les prochains recrutements.",
      tags: ["EURES", "France Travail", "Union européenne", "Luxembourg", "Recrutement"]
    },
    candidateQuestionnaire: {
      eyebrow: "Questionnaire candidat",
      title: "Premier signal de matching candidat",
      lede: "Nous captons ici les informations utiles pour vous proposer ensuite des mises en relation ciblées.",
      sections: {
        mobility: "Projet de mobilité",
        profile: "Projet professionnel",
        contact: "Pour vous recontacter"
      },
      fields: {
        residenceCountry: "Pays de résidence",
        targetCountries: "Pays visés",
        mobilityType: "Type de mobilité",
        availability: "Disponibilité de démarrage",
        sectors: "Secteurs recherchés",
        experienceLevel: "Niveau d’expérience",
        languages: "Langues de travail",
        fullName: "Nom complet",
        email: "Adresse e-mail",
        phone: "Téléphone",
        city: "Ville actuelle",
        notes: "Éléments utiles complémentaires"
      },
      options: {
        targetCountries: ["Luxembourg", "France", "Allemagne", "Belgique"],
        mobilityType: ["Transfrontalière", "Expatriation", "Les deux"],
        availability: ["Immédiatement", "Sous 1 mois", "Sous 3 mois", "Plus tard"],
        sectors: ["Vente et commerce", "Nettoyage et entretien", "Hôtellerie-restauration", "Agriculture et récolte", "Missions polyvalentes"],
        experienceLevel: ["Plus de 2 ans", "Entre 6 mois et 2 ans", "Moins de 6 mois", "Débutant mais motivé"],
        languages: ["Français", "Anglais", "Allemand", "Luxembourgeois"]
      },
      helper: "Vous pourrez enrichir ce parcours ensuite avec le CV, les documents administratifs et les critères détaillés par métier."
    },
    employerQuestionnaire: {
      eyebrow: "Questionnaire employeur",
      title: "Premier signal de matching employeur",
      lede: "Nous captons ici les informations utiles pour filtrer et proposer des profils compatibles avec votre besoin.",
      sections: {
        need: "Besoin de recrutement",
        conditions: "Conditions proposées",
        contact: "Pour vous recontacter"
      },
      fields: {
        companyName: "Nom de l’entreprise",
        workLocation: "Lieu de travail",
        sector: "Secteur principal",
        recruitCount: "Nombre de recrutements",
        startDate: "Date ou délai souhaité",
        languagesRequired: "Langues impératives",
        contractDuration: "Durée de contrat",
        weeklyHours: "Volume hebdomadaire",
        installationSupport: "Aides à l’installation",
        criticalCriteria: "Critères indispensables",
        contactName: "Nom du contact",
        email: "Adresse e-mail",
        phone: "Téléphone",
        notes: "Précisions sur le poste"
      },
      options: {
        sector: ["Vente et commerce", "Nettoyage et entretien", "Hôtellerie-restauration", "Agriculture et récolte", "Missions polyvalentes"],
        recruitCount: ["1", "2 à 5", "6 à 10", "10+"],
        languagesRequired: ["Français", "Anglais", "Allemand", "Luxembourgeois"],
        contractDuration: ["Saisonnier", "CDD", "CDI", "À préciser"],
        weeklyHours: ["Temps plein", "Temps partiel", "Variable"],
        installationSupport: ["Aucune aide", "Aide administrative", "Aide logement", "Aide transport"],
        criticalCriteria: ["Disponibilité rapide", "Expérience métier", "Langue orale", "Autonomie", "Mobilité"]
      },
      helper: "Vous pourrez enrichir ensuite le scoring avec les exigences fines par métier et les validations humaines."
    },
    statPage: {
      eyebrow: "Données publiques agrégées",
      title: "Statistiques publiques EURES beta",
      lede: "Cette page présente des indicateurs agrégés et non nominatifs sur l’activité du projet EURES beta.",
      updatedPrefix: "Dernière mise à jour",
      methodology: "Les chiffres affichés proviennent des tables Grist du projet. Les données personnelles, identifiants et contenus libres ne sont jamais affichés.",
      manualNote: "Les indicateurs de contact, de transmission et d’embauche peuvent être complétés manuellement dans la table mensuelle de pilotage.",
      manualMissing: "La table mensuelle de pilotage n’est pas encore configurée. Les indicateurs saisis à la main restent donc à zéro.",
      keyFiguresTitle: "Chiffres clés",
      monthlyTitle: "Suivi mensuel",
      monthlyLead: "Les volumes automatiques sont calculés à partir des dates d’enregistrement. Les suivis métier peuvent être complétés mois par mois.",
      breakdownsTitle: "Répartitions",
      totals: {
        candidats: "Candidatures reçues",
        besoins_employeurs: "Besoins employeurs reçus",
        matchings: "Matchings calculés",
        candidats_contactes: "Candidats contactés",
        candidatures_transmises_employeur: "Candidatures transmises",
        embauches: "Embauches"
      },
      monthlyColumns: {
        mois: "Mois",
        candidats: "Candidatures",
        besoins_employeurs: "Besoins employeurs",
        matchings: "Matchings",
        candidats_contactes: "Candidats contactés",
        candidatures_transmises_employeur: "Candidatures transmises",
        embauches: "Embauches"
      },
      breakdownLabels: {
        candidats_par_pays: "Candidatures par pays visé",
        besoins_par_pays: "Besoins employeurs par pays",
        secteurs: "Secteurs",
        mobilite_candidats: "Mobilité des candidats",
        matchings_par_statut: "Statuts de matching"
      },
      emptyBreakdown: "Aucune donnée exploitable pour le moment.",
      loading: "Chargement des statistiques...",
      error: "Impossible de charger les statistiques pour le moment."
    }
  },
  en: {
    common: {
      brandTitle: "EURES beta",
      brandSubtitle: "Cross-border mobility, matching and follow-up",
      navHome: "Home",
      navCandidate: "Candidate",
      navEmployer: "Employer",
      navStats: "Stats",
      langLabel: "Language",
      footer: "Starter prototype to test sign-up, matching and structured delivery into GRIST.",
      ctaStartCandidate: "Start as candidate",
      ctaStartEmployer: "Start as employer",
      ctaBackHome: "Back to home",
      ctaQuestionnaire: "Start questionnaire",
      ctaSeeCandidate: "See candidate flow",
      ctaSeeEmployer: "See employer flow",
      matchingTitle: "How matching will work",
      matchingBullets: [
        "Each answer is sent to GRIST with a role, a language and a reusable identifier.",
        "A compatibility score can be computed across sectors, mobility, languages, availability and job conditions.",
        "High scores can trigger automated matching. Lower scores can be reviewed by a human operator."
      ],
      futureTitle: "What comes next",
      futureBullets: [
        "Candidate dashboard to track opportunities and status.",
        "Employer dashboard to track suggested profiles and responses.",
        "Matching history, human validation and decision traceability."
      ],
      consent: "I agree that my answers may be used by EURES teams and partners for matching and mobility support.",
      submit: "Save my answers",
      saving: "Saving...",
      saved: "Answers saved.",
      saveErrorPrefix: "Save failed",
      uuidPrefix: "Resume identifier",
      questionnaireNote: "This questionnaire is intentionally compact for the first version. It follows the logic of the reference Tally forms without copying them in full."
    },
    home: {
      eyebrow: "Test a practical service in the Greater Region",
      title: "Connect mobile workers with job opportunities that stay off their radar.",
      lede: "EURES beta addresses a simple issue: the labour market is cross-border, while job search and hiring remain largely national. The service aims to capture intent, structure needs and send the right opportunities faster.",
      storyTitle: "Starting point",
      storyText: "People who already worked in Luxembourg, Germany or a neighbouring country often look first in their country of residence. At the same time, employers have real hiring needs but struggle to reach these mobile profiles.",
      stats: [
        ["280,000", "cross-border workers commute daily within the Greater Region."],
        ["40–50k", "people with cross-border experience may be looking for work."],
        ["15,000+", "vacancies remain open in the same labour basin."]
      ],
      tracksTitle: "Two entry points, one matching engine",
      candidateTitle: "Candidate flow",
      candidateText: "Capture mobility plans, target sectors, languages, availability and concrete signals that make matching faster.",
      employerTitle: "Employer flow",
      employerText: "Capture hiring demand, languages, work constraints, relocation support and the employer’s strongest criteria.",
      principlesTitle: "Product principles",
      principles: [
        ["Simple first", "A lightweight multilingual first flow that can be used immediately."],
        ["Useful data", "Structured answers that feed GRIST and prepare matching scoring."],
        ["Human validation", "If the score is weak or ambiguous, an EURES operator can review the match."]
      ]
    },
    candidateLanding: {
      kicker: "Candidate flow",
      title: "A simple questionnaire to explore mobility opportunities in Europe.",
      lede: "This approach is for people who may consider European professional mobility, either as cross-border commuting or relocation. In simple terms: working in a neighbouring country while staying at home, or moving to live and work in another European country.",
      messageTitle: "Why fill in this questionnaire?",
      messageIntro: "This questionnaire helps us quickly understand whether your profile may match opportunities linked to European mobility.",
      messageBody: [
        "At the moment, the test mainly involves companies based in Luxembourg, within a cross-border or broader European mobility framework.",
        "This is a practical test phase: we try something real, we see what works, and then we improve it.",
        "In other words, the service is not final yet, but it is already used to identify real opportunities for people ready to move within Europe."
      ],
      messageHighlight: "You answer once, and it helps us see whether some current or upcoming European mobility opportunities may fit you.",
      messageOutcome: "The service will then expand to other employers in Germany, Belgium and France, as well as more job families.",
      signatureTitle: "At the moment, the first tests mainly cover:",
      signatureName: "Luxembourg",
      signatureRole: "and several hiring sectors",
      bulletsTitle: "Jobs currently tested with employers in Luxembourg",
      bullets: [
        "Retail and sales",
        "Cleaning and maintenance",
        "Hospitality and food service",
        "Agriculture and harvesting",
        "Flexible jobs and roles accessible quickly"
      ],
      sideTitle: "Who are we?",
      sideText: "EURES is the European employment cooperation network. It supports recruitment and professional opportunities across Europe, especially for cross-border mobility where candidates and vacancies often miss each other.",
      disclaimerTitle: "What happens next",
      disclaimerText: "If your profile matches ongoing needs, it may be reviewed for a possible introduction. Over time, more companies, more countries and more job families will be added.",
      tags: ["EURES", "France Travail", "European Union", "Luxembourg", "Retail & sales"],
      logos: {
        eures: {
          src: "https://eures.europa.eu/sites/default/files/site-logo-overrides/EURES%20Gradient%20logo%20SVG%20stretched.svg",
          alt: "EURES logo"
        },
        franceTravail: {
          src: "https://cdn.francetravail.fr/studio/logos/marque/favicon/favicon.svg",
          alt: "France Travail logo"
        },
        europeanUnion: {
          src: "https://european-union.europa.eu/themes/contrib/oe_theme/dist/eu/images/logo/condensed-version/positive/logo-eu--en.svg",
          alt: "European Union logo"
        }
      }
    },
    employerLanding: {
      kicker: "Employer flow",
      title: "A simple questionnaire to surface your hiring needs in European mobility.",
      lede: "This approach is for employers who can recruit beyond their local market, either cross-border or with candidates coming from another European country. The goal is simple: understand your need more clearly so we can identify matching profiles faster.",
      messageTitle: "Why fill in this questionnaire?",
      messageIntro: "This questionnaire helps us understand your hiring need, the role context and the conditions you offer.",
      messageBody: [
        "At the moment, the experiment is first being carried out with companies based in Luxembourg, on concrete recruitments that can sometimes be difficult to fill.",
        "We are in a very practical testing phase: we look at what really helps suitable profiles emerge, then we improve the service.",
        "In simple terms, you describe your need once, and this helps us spot applications that may be compatible more effectively."
      ],
      messageHighlight: "The point is not to waste your time with one more form. The point is to qualify your need better so future introductions are easier.",
      messageOutcome: "The service will gradually open up to other employers in Germany, Belgium and France, as well as to more occupations.",
      signatureTitle: "At the moment, the first tests mainly concern:",
      signatureName: "Luxembourg-based employers",
      signatureRole: "and several sectors that are hiring",
      bulletsTitle: "What we will qualify",
      bullets: [
        "Sales and retail",
        "Cleaning and maintenance",
        "Hospitality and food service",
        "Agriculture and harvesting",
        "Versatile jobs and roles accessible quickly"
      ],
      sideTitle: "What this changes for you",
      sideText: "You clarify the type of recruitment, the useful languages, the job constraints, the expected level and any arrival support. This allows us to compare employer needs and candidate expectations more seriously.",
      disclaimerTitle: "What happens next",
      disclaimerText: "If some profiles appear compatible with your search, your need can be taken up for an introduction. And if the need is not yet clear enough, the questionnaire already helps us prepare the next recruitments better.",
      tags: ["EURES", "France Travail", "European Union", "Luxembourg", "Recruitment"]
    },
    candidateQuestionnaire: {
      eyebrow: "Candidate questionnaire",
      title: "First candidate matching signal",
      lede: "We capture the minimum useful information to propose relevant introductions later.",
      sections: {
        mobility: "Mobility plan",
        profile: "Professional profile",
        contact: "Contact details"
      },
      fields: {
        residenceCountry: "Country of residence",
        targetCountries: "Target countries",
        mobilityType: "Mobility type",
        availability: "Availability",
        sectors: "Target sectors",
        experienceLevel: "Experience level",
        languages: "Working languages",
        fullName: "Full name",
        email: "Email",
        phone: "Phone",
        city: "Current city",
        notes: "Additional context"
      },
      options: {
        targetCountries: ["Luxembourg", "France", "Germany", "Belgium"],
        mobilityType: ["Cross-border", "Relocation", "Both"],
        availability: ["Immediately", "Within 1 month", "Within 3 months", "Later"],
        sectors: ["Retail and sales", "Cleaning and maintenance", "Hospitality", "Agriculture and harvest", "Flexible entry jobs"],
        experienceLevel: ["More than 2 years", "6 months to 2 years", "Less than 6 months", "Beginner but motivated"],
        languages: ["French", "English", "German", "Luxembourgish"]
      },
      helper: "You can extend this later with CV upload, admin documents and detailed criteria by sector."
    },
    employerQuestionnaire: {
      eyebrow: "Employer questionnaire",
      title: "First employer matching signal",
      lede: "We capture the minimum useful information to filter and suggest compatible profiles.",
      sections: {
        need: "Hiring need",
        conditions: "Conditions offered",
        contact: "Contact details"
      },
      fields: {
        companyName: "Company name",
        workLocation: "Work location",
        sector: "Main sector",
        recruitCount: "Hiring volume",
        startDate: "Start date or timing",
        languagesRequired: "Required languages",
        contractDuration: "Contract duration",
        weeklyHours: "Weekly workload",
        installationSupport: "Relocation support",
        criticalCriteria: "Critical criteria",
        contactName: "Contact name",
        email: "Email",
        phone: "Phone",
        notes: "Role details"
      },
      options: {
        sector: ["Retail and sales", "Cleaning and maintenance", "Hospitality", "Agriculture and harvest", "Flexible entry jobs"],
        recruitCount: ["1", "2 to 5", "6 to 10", "10+"],
        languagesRequired: ["French", "English", "German", "Luxembourgish"],
        contractDuration: ["Seasonal", "Fixed-term", "Permanent", "To be defined"],
        weeklyHours: ["Full-time", "Part-time", "Variable"],
        installationSupport: ["No support", "Administrative support", "Housing support", "Transport support"],
        criticalCriteria: ["Fast availability", "Sector experience", "Spoken language", "Autonomy", "Mobility"]
      },
      helper: "You can extend the scoring later with detailed requirements per sector and human validation."
    },
    statPage: {
      eyebrow: "Public aggregated data",
      title: "EURES beta public stats",
      lede: "This page shows aggregated, non-identifying indicators about EURES beta activity.",
      updatedPrefix: "Last updated",
      methodology: "Figures come from the project's Grist tables. Personal data, identifiers and free text are never displayed.",
      manualNote: "Contact, transmission and hiring indicators can be completed manually in the monthly steering table.",
      manualMissing: "The monthly steering table is not configured yet. Manually entered indicators therefore remain at zero.",
      keyFiguresTitle: "Key figures",
      monthlyTitle: "Monthly tracking",
      monthlyLead: "Automatic volumes are calculated from submission dates. Operational follow-up can then be completed month by month.",
      breakdownsTitle: "Breakdowns",
      totals: {
        candidats: "Candidate submissions",
        besoins_employeurs: "Employer needs",
        matchings: "Computed matchings",
        candidats_contactes: "Candidates contacted",
        candidatures_transmises_employeur: "Applications transmitted",
        embauches: "Hires"
      },
      monthlyColumns: {
        mois: "Month",
        candidats: "Candidates",
        besoins_employeurs: "Employer needs",
        matchings: "Matchings",
        candidats_contactes: "Candidates contacted",
        candidatures_transmises_employeur: "Applications transmitted",
        embauches: "Hires"
      },
      breakdownLabels: {
        candidats_par_pays: "Candidates by target country",
        besoins_par_pays: "Employer needs by country",
        secteurs: "Sectors",
        mobilite_candidats: "Candidate mobility",
        matchings_par_statut: "Matching statuses"
      },
      emptyBreakdown: "No usable data yet.",
      loading: "Loading statistics...",
      error: "Unable to load statistics right now."
    }
  },
  de: {
    common: {
      brandTitle: "EURES beta",
      brandSubtitle: "Grenzüberschreitende Mobilität, Matching und Begleitung",
      navHome: "Start",
      navCandidate: "Kandidaten",
      navEmployer: "Arbeitgeber",
      navStats: "Statistik",
      langLabel: "Sprache",
      footer: "Startprototyp zum Testen von Erfassung, Matching und strukturierter Übergabe an GRIST.",
      ctaStartCandidate: "Als Kandidat starten",
      ctaStartEmployer: "Als Arbeitgeber starten",
      ctaBackHome: "Zur Startseite",
      ctaQuestionnaire: "Fragebogen starten",
      ctaSeeCandidate: "Kandidatenweg ansehen",
      ctaSeeEmployer: "Arbeitgeberweg ansehen",
      matchingTitle: "So soll das Matching funktionieren",
      matchingBullets: [
        "Jede Antwort wird mit Rolle, Sprache und Wiederaufnahme-ID in GRIST gespeichert.",
        "Ein Kompatibilitätsscore kann aus Branche, Mobilität, Sprachen, Verfügbarkeit und Arbeitsbedingungen berechnet werden.",
        "Hohe Scores können automatisch gematcht werden. Niedrige Scores gehen in eine menschliche Prüfung."
      ],
      futureTitle: "Nächste Ausbaustufen",
      futureBullets: [
        "Kandidaten-Dashboard für Chancen und Status.",
        "Arbeitgeber-Dashboard für vorgeschlagene Profile und Rückmeldungen.",
        "Matching-Historie, menschliche Freigaben und nachvollziehbare Entscheidungen."
      ],
      consent: "Ich stimme zu, dass meine Antworten von EURES-Teams und Partnern für Matching und Mobilitätsbegleitung verwendet werden.",
      submit: "Meine Antworten speichern",
      saving: "Speicherung läuft...",
      saved: "Antworten gespeichert.",
      saveErrorPrefix: "Speichern fehlgeschlagen",
      uuidPrefix: "Wiederaufnahme-ID",
      questionnaireNote: "Dieser Fragebogen ist für die erste Version bewusst kompakt. Er orientiert sich an den vorhandenen Tally-Formularen, ohne sie vollständig zu kopieren."
    },
    home: {
      eyebrow: "Einen konkreten Dienst in der Großregion testen",
      title: "Mobile Arbeitskräfte mit Stellen verbinden, die heute unter dem Radar bleiben.",
      lede: "EURES beta adressiert ein einfaches Problem: Der Arbeitsmarkt ist grenzüberschreitend, Stellensuche und Rekrutierung bleiben aber weitgehend national. Der Dienst soll Absichten erfassen, Bedarfe strukturieren und passende Chancen schneller zuspielen.",
      storyTitle: "Ausgangspunkt",
      storyText: "Menschen, die bereits in Luxemburg, Deutschland oder einem Nachbarland gearbeitet haben, suchen oft zuerst im Wohnland. Gleichzeitig haben Arbeitgeber echte Bedarfe, erreichen diese mobilen Profile aber nur schwer.",
      stats: [
        ["280.000", "Grenzpendler bewegen sich täglich in der Großregion."],
        ["40–50 Tsd.", "Menschen mit grenzüberschreitender Erfahrung könnten Arbeit suchen."],
        ["15.000+", "offene Stellen bleiben im selben Arbeitsraum unbesetzt."]
      ],
      tracksTitle: "Zwei Einstiege, ein Matching-Motor",
      candidateTitle: "Kandidatenweg",
      candidateText: "Mobilitätspläne, Zielbranchen, Sprachen, Verfügbarkeit und konkrete Matching-Signale erfassen.",
      employerTitle: "Arbeitgeberweg",
      employerText: "Personalbedarf, Sprachen, Rahmenbedingungen, Unterstützung bei Ankunft und starke Kriterien erfassen.",
      principlesTitle: "Produktprinzipien",
      principles: [
        ["Einfach starten", "Ein leichtgewichtiger mehrsprachiger Erstfluss, sofort nutzbar."],
        ["Nützliche Daten", "Strukturierte Antworten für GRIST und den späteren Matching-Score."],
        ["Menschliche Prüfung", "Bei schwachem oder unklarem Score prüft ein EURES-Mitarbeiter."]
      ]
    },
    candidateLanding: {
      kicker: "Kandidatenweg",
      title: "Ein kurzer Fragebogen, um berufliche Mobilitätschancen in Europa zu erkunden.",
      lede: "Dieses Angebot richtet sich an Menschen, die berufliche Mobilität in Europa in Betracht ziehen, entweder grenzüberschreitend oder durch einen Umzug. Einfach gesagt: in einem Nachbarland arbeiten und zu Hause wohnen bleiben, oder in ein anderes europäisches Land ziehen und dort arbeiten.",
      messageTitle: "Warum diesen Fragebogen ausfüllen?",
      messageIntro: "Der Fragebogen hilft uns, schneller zu erkennen, ob Ihr Profil zu Chancen im Rahmen europäischer Mobilität passen könnte.",
      messageBody: [
        "Im Moment wird vor allem mit Unternehmen in Luxemburg getestet, in einem grenzüberschreitenden oder breiteren europäischen Mobilitätsrahmen.",
        "Das ist eine ganz praktische Testphase: Wir probieren etwas Reales aus, schauen, was funktioniert, und verbessern es danach.",
        "Mit anderen Worten: Der Dienst ist noch nicht fertig, wird aber bereits genutzt, um echte Chancen für Menschen sichtbar zu machen, die sich in Europa beruflich bewegen möchten."
      ],
      messageHighlight: "Sie antworten einmal, und das hilft uns zu sehen, ob aktuelle oder kommende Chancen der europäischen Mobilität zu Ihnen passen könnten.",
      messageOutcome: "Der Dienst soll danach auf weitere Arbeitgeber in Deutschland, Belgien und Frankreich sowie auf weitere Berufe ausgeweitet werden.",
      signatureTitle: "Die ersten Tests betreffen im Moment vor allem:",
      signatureName: "Luxemburg",
      signatureRole: "und mehrere Branchen mit Personalbedarf",
      bulletsTitle: "Berufe, die aktuell mit Arbeitgebern in Luxemburg getestet werden",
      bullets: [
        "Verkauf und Handel",
        "Reinigung und Instandhaltung",
        "Hotellerie und Gastronomie",
        "Landwirtschaft und Ernte",
        "Vielseitige Tätigkeiten und Jobs mit schnellem Einstieg"
      ],
      sideTitle: "Wer sind wir?",
      sideText: "EURES ist das europäische Kooperationsnetzwerk für Beschäftigung. Es erleichtert Rekrutierung und berufliche Chancen in Europa, insbesondere in grenzüberschreitenden Arbeitsmärkten.",
      disclaimerTitle: "Wie es danach weitergeht",
      disclaimerText: "Wenn Ihr Profil zu laufenden Bedarfen passt, kann es für eine mögliche Vermittlung berücksichtigt werden. Mit der Zeit kommen weitere Unternehmen, weitere Länder und weitere Berufe hinzu.",
      tags: ["EURES", "France Travail", "Europäische Union", "Luxemburg", "Verkauf & Handel"],
      logos: {
        eures: {
          src: "https://eures.europa.eu/sites/default/files/site-logo-overrides/EURES%20Gradient%20logo%20SVG%20stretched.svg",
          alt: "EURES-Logo"
        },
        franceTravail: {
          src: "https://cdn.francetravail.fr/studio/logos/marque/favicon/favicon.svg",
          alt: "France-Travail-Logo"
        },
        europeanUnion: {
          src: "https://european-union.europa.eu/themes/contrib/oe_theme/dist/eu/images/logo/condensed-version/positive/logo-eu--en.svg",
          alt: "Logo der Europäischen Union"
        }
      }
    },
    employerLanding: {
      kicker: "Arbeitgeberweg",
      title: "Ein einfacher Fragebogen, um Ihren Personalbedarf in der europäischen Mobilität sichtbar zu machen.",
      lede: "Dieses Angebot richtet sich an Arbeitgeber, die über ihren lokalen Markt hinaus rekrutieren können, grenzüberschreitend oder mit Kandidaten aus einem anderen europäischen Land. Das Ziel ist einfach: Ihren Bedarf klarer verstehen, um schneller passende Profile zu erkennen.",
      messageTitle: "Warum diesen Fragebogen ausfüllen?",
      messageIntro: "Dieser Fragebogen hilft uns, Ihren Personalbedarf, den Kontext der Stelle und die angebotenen Bedingungen besser zu verstehen.",
      messageBody: [
        "Zurzeit wird die Erprobung zunächst mit Unternehmen in Luxemburg durchgeführt, bei konkreten Einstellungen, die manchmal schwer zu besetzen sind.",
        "Wir befinden uns in einer sehr praktischen Testphase: Wir schauen, was wirklich hilft, passende Profile sichtbar zu machen, und verbessern den Dienst danach.",
        "Einfach gesagt: Sie beschreiben Ihren Bedarf einmal, und das hilft uns, kompatible Bewerbungen besser zu erkennen."
      ],
      messageHighlight: "Es geht nicht darum, Ihnen ein weiteres Formular aufzubürden. Es geht darum, Ihren Bedarf besser zu qualifizieren, damit spätere Vermittlungen einfacher werden.",
      messageOutcome: "Der Dienst wird schrittweise auch für andere Arbeitgeber in Deutschland, Belgien und Frankreich sowie für weitere Berufe geöffnet.",
      signatureTitle: "Die ersten Tests betreffen im Moment vor allem:",
      signatureName: "Arbeitgeber in Luxemburg",
      signatureRole: "und mehrere Branchen mit Personalbedarf",
      bulletsTitle: "Was wir qualifizieren",
      bullets: [
        "Verkauf und Handel",
        "Reinigung und Instandhaltung",
        "Hotellerie und Gastronomie",
        "Landwirtschaft und Ernte",
        "Vielseitige Tätigkeiten und Jobs mit schnellem Einstieg"
      ],
      sideTitle: "Was das für Sie verändert",
      sideText: "Sie präzisieren die Art der Rekrutierung, die nützlichen Sprachen, die Rahmenbedingungen der Stelle, das erwartete Niveau und mögliche Unterstützung bei der Ankunft. So können wir Arbeitgeberbedarfe und Kandidatenerwartungen fundierter vergleichen.",
      disclaimerTitle: "Wie es danach weitergeht",
      disclaimerText: "Wenn einige Profile mit Ihrer Suche vereinbar erscheinen, kann Ihr Bedarf für eine Vermittlung aufgegriffen werden. Und wenn der Bedarf noch nicht klar genug ist, hilft uns der Fragebogen bereits dabei, die nächsten Einstellungen besser vorzubereiten.",
      tags: ["EURES", "France Travail", "Europäische Union", "Luxemburg", "Rekrutierung"]
    },
    candidateQuestionnaire: {
      eyebrow: "Kandidatenfragebogen",
      title: "Erstes Matching-Signal für Kandidaten",
      lede: "Wir erfassen hier die minimal nötigen Informationen für spätere passende Vorschläge.",
      sections: {
        mobility: "Mobilitätsprojekt",
        profile: "Berufliches Profil",
        contact: "Kontaktdaten"
      },
      fields: {
        residenceCountry: "Wohnland",
        targetCountries: "Zielländer",
        mobilityType: "Mobilitätsart",
        availability: "Verfügbarkeit",
        sectors: "Zielbranchen",
        experienceLevel: "Erfahrungsniveau",
        languages: "Arbeitssprachen",
        fullName: "Vollständiger Name",
        email: "E-Mail",
        phone: "Telefon",
        city: "Aktueller Wohnort",
        notes: "Zusätzliche Hinweise"
      },
      options: {
        targetCountries: ["Luxemburg", "Frankreich", "Deutschland", "Belgien"],
        mobilityType: ["Grenzüberschreitend", "Umzug", "Beides"],
        availability: ["Sofort", "Innerhalb 1 Monats", "Innerhalb 3 Monaten", "Später"],
        sectors: ["Verkauf und Handel", "Reinigung und Instandhaltung", "Hotellerie und Gastronomie", "Landwirtschaft und Ernte", "Flexible Einstiegsjobs"],
        experienceLevel: ["Mehr als 2 Jahre", "6 Monate bis 2 Jahre", "Weniger als 6 Monate", "Anfänger, aber motiviert"],
        languages: ["Französisch", "Englisch", "Deutsch", "Luxemburgisch"]
      },
      helper: "Später kann der Ablauf um CV-Upload, Verwaltungsdokumente und branchenspezifische Details erweitert werden."
    },
    employerQuestionnaire: {
      eyebrow: "Arbeitgeberfragebogen",
      title: "Erstes Matching-Signal für Arbeitgeber",
      lede: "Wir erfassen hier die minimal nötigen Informationen, um kompatible Profile vorzuschlagen.",
      sections: {
        need: "Personalbedarf",
        conditions: "Rahmenbedingungen",
        contact: "Kontaktdaten"
      },
      fields: {
        companyName: "Unternehmensname",
        workLocation: "Arbeitsort",
        sector: "Hauptbranche",
        recruitCount: "Anzahl Einstellungen",
        startDate: "Startdatum oder Zeitraum",
        languagesRequired: "Erforderliche Sprachen",
        contractDuration: "Vertragsdauer",
        weeklyHours: "Wochenstunden",
        installationSupport: "Unterstützung bei Ankunft",
        criticalCriteria: "Wichtige Kriterien",
        contactName: "Kontaktperson",
        email: "E-Mail",
        phone: "Telefon",
        notes: "Details zur Stelle"
      },
      options: {
        sector: ["Verkauf und Handel", "Reinigung und Instandhaltung", "Hotellerie und Gastronomie", "Landwirtschaft und Ernte", "Flexible Einstiegsjobs"],
        recruitCount: ["1", "2 bis 5", "6 bis 10", "10+"],
        languagesRequired: ["Französisch", "Englisch", "Deutsch", "Luxemburgisch"],
        contractDuration: ["Saisonal", "Befristet", "Unbefristet", "Noch offen"],
        weeklyHours: ["Vollzeit", "Teilzeit", "Variabel"],
        installationSupport: ["Keine Unterstützung", "Administrative Hilfe", "Wohnungshilfe", "Transporthilfe"],
        criticalCriteria: ["Schnelle Verfügbarkeit", "Branchenerfahrung", "Gesprochene Sprache", "Selbstständigkeit", "Mobilität"]
      },
      helper: "Später kann das Scoring um feinere Kriterien je Branche und menschliche Validierung ergänzt werden."
    },
    statPage: {
      eyebrow: "Öffentliche aggregierte Daten",
      title: "Öffentliche EURES-beta-Statistiken",
      lede: "Diese Seite zeigt aggregierte und nicht personenbezogene Kennzahlen zur Aktivität von EURES beta.",
      updatedPrefix: "Letzte Aktualisierung",
      methodology: "Die Zahlen stammen aus den Grist-Tabellen des Projekts. Personendaten, Kennungen und freie Texte werden nie angezeigt.",
      manualNote: "Kontakt-, Übermittlungs- und Einstellungsindikatoren können in der monatlichen Steuerungstabelle manuell ergänzt werden.",
      manualMissing: "Die monatliche Steuerungstabelle ist noch nicht konfiguriert. Manuell gepflegte Kennzahlen bleiben daher auf null.",
      keyFiguresTitle: "Kennzahlen",
      monthlyTitle: "Monatliche Entwicklung",
      monthlyLead: "Automatische Volumen werden aus den Einreichungsdaten berechnet. Die operative Nachverfolgung kann dann monatlich ergänzt werden.",
      breakdownsTitle: "Verteilungen",
      totals: {
        candidats: "Kandidaten-Eingänge",
        besoins_employeurs: "Arbeitgeberbedarfe",
        matchings: "Berechnete Matchings",
        candidats_contactes: "Kontaktierte Kandidaten",
        candidatures_transmises_employeur: "Übermittelte Bewerbungen",
        embauches: "Einstellungen"
      },
      monthlyColumns: {
        mois: "Monat",
        candidats: "Kandidaten",
        besoins_employeurs: "Arbeitgeberbedarfe",
        matchings: "Matchings",
        candidats_contactes: "Kontaktierte Kandidaten",
        candidatures_transmises_employeur: "Übermittelte Bewerbungen",
        embauches: "Einstellungen"
      },
      breakdownLabels: {
        candidats_par_pays: "Kandidaten nach Zielland",
        besoins_par_pays: "Arbeitgeberbedarfe nach Land",
        secteurs: "Sektoren",
        mobilite_candidats: "Mobilität der Kandidaten",
        matchings_par_statut: "Matching-Status"
      },
      emptyBreakdown: "Noch keine auswertbaren Daten.",
      loading: "Statistiken werden geladen...",
      error: "Die Statistiken können derzeit nicht geladen werden."
    }
  }
};

const candidateTallyMeta = {
  formId: "449blX",
  mobilityTypes: ["Transfrontalière", "Expatriation"],
  countryColumns: ["J'y habite", "Je veux y travailler", "J'y ai déjà travaillé"],
  countryRows: [
    { field: "tally_q01_f01", label: "Allemagne" },
    { field: "tally_q01_f02", label: "France" },
    { field: "tally_q01_f03", label: "Luxembourg" },
    { field: "tally_q01_f04", label: "Un autre pays de l'UE" },
    { field: "tally_q01_f05", label: "Un autre pays hors UE" }
  ],
  scheduleColumns: ["Matin", "Après-midi", "Soir", "Nuit"],
  scheduleRows: [
    { field: "tally_q07_f01", label: "Lundi" },
    { field: "tally_q07_f02", label: "Mardi" },
    { field: "tally_q07_f03", label: "Mercredi" },
    { field: "tally_q07_f04", label: "Jeudi" },
    { field: "tally_q07_f05", label: "Vendredi" },
    { field: "tally_q07_f06", label: "Samedi" },
    { field: "tally_q07_f07", label: "Dimanche" }
  ],
  documentsColumns: ["Je l'ai", "Je suis en train de le préparer", "Je ne sais pas encore"],
  documentsRows: [
    { field: "tally_q10_f01", label: "Carte d'identité ou passeport (en cours de validité)" },
    { field: "tally_q10_f02", label: "CV à jour" },
    { field: "tally_q10_f03", label: "Vos diplômes ou qualifications professionnelles" },
    { field: "tally_q10_f04", label: "Compte bancaire / IBAN" },
    { field: "tally_q10_f05", label: "Attestation d'affiliation à la sécurité sociale" }
  ],
  languageColumns: [
    "Langue maternelle",
    "Je peux échanger à l'oral",
    "Je peux travailler avec cette langue",
    "J'utilise un outil de traduction si nécessaire",
    "Je ne la pratique pas"
  ],
  languageRows: [
    { field: "tally_q18_f01", label: "Allemand" },
    { field: "tally_q18_f02", label: "Anglais" },
    { field: "tally_q18_f03", label: "Français" },
    { field: "tally_q18_f04", label: "Luxembourgeois" }
  ],
  rankingOptions: [
    "Trouver un logement",
    "Trouver un emploi",
    "Comprendre les démarches administratives/fiscales",
    "Préparer votre budget et vos finances",
    "Améliorer votre niveau de langue",
    "Obtenir de l'aide à l'arrivée (installation, démarches)",
    "Construire un réseau, vous intégrer socialement"
  ],
  sectors: [
    "Vente et commerce (ex : prêt-à-porter, chaussures, commerce spécialisé)",
    "Nettoyage et entretien (ex : bureaux, espaces collectifs)",
    "Hôtellerie et restauration (ex : plonge, service, aide de cuisine)",
    "Agriculture et récolte (ex : récolte de fruits, travaux saisonniers)",
    "Missions polyvalentes et emplois accessibles rapidement"
  ]
};

const candidateTallyCopy = {
  fr: {
    eyebrow: "Questionnaire candidat EURES",
    heroTitle: "Mobilité européenne, transfrontalière ou expatriation",
    heroLede: "Ce questionnaire nous aide à mieux comprendre votre projet de mobilité en Europe, que vous envisagiez de travailler dans un pays voisin ou de partir vivre et travailler dans un autre pays européen.",
    heroHighlight: "Quelques minutes suffisent. Vos réponses nous permettent de voir plus rapidement si des opportunités peuvent correspondre à votre situation, à vos disponibilités et à vos préférences.",
    overviewTitle: "Concernant votre projet de mobilité",
    overviewMatrixTitle: "Sélectionner ci-dessous votre pays de résidence, le(s) pays où vous souhaitez travailler et ceux où vous avez déjà travaillé",
    mobilityTypeTitle: "Quel type de mobilité envisagez vous ?",
    mobilityTypeHint: "Vous pouvez choisir une seule option ou les deux.",
    crossBorderTitle: "Votre projet de mobilité transfrontalière",
    expatriationTitle: "Votre projet d'expatriation",
    professionalTitle: "Votre projet professionnel",
    contactTitle: "Pour pouvoir vous recontacter",
    rankingTitle: "Classez du plus important au moins important pour vous ces propositions ?",
    rankingHint: "Attribuez un rang unique à chaque proposition : 1 pour le plus important, 7 pour le moins important.",
    sidebarWhyTitle: "Pourquoi ce questionnaire ?",
    sidebarWhyText: "Il sert à repérer plus facilement les personnes qui peuvent être intéressées par une opportunité de mobilité européenne, en fonction du pays visé, du métier, des langues, de la disponibilité et des conditions pratiques.",
    sidebarAfterTitle: "Et après ?",
    sidebarAfterText: "Si votre profil semble correspondre à un besoin en cours, il pourra être étudié pour une mise en relation. Si ce n’est pas encore le bon moment, vos réponses nous aident aussi à mieux préparer les prochaines opportunités.",
    sidebarResumeTitle: "Reprendre plus tard",
    sidebarResumeText: "Un identifiant est conservé pour retrouver votre progression si besoin.",
    salaryExpectationIntro: "Indiquez ici votre attente salariale pour ce métier, en euros, en précisant s'il s'agit d'un montant brut ou net.",
    fileNote: "Le nom du fichier sera enregistré. Le fichier lui-même n’est pas encore stocké côté plateforme.",
    consentText: "J’accepte que mes réponses soient utilisées par les équipes et partenaires EURES dans le cadre de l’accompagnement à la mobilité professionnelle et des mises en relation proposées. Vos données seront utilisées uniquement dans le cadre de votre accompagnement et conformément à la réglementation européenne sur la protection des données (RGPD).",
    rankingError: "Chaque priorité d'expatriation doit avoir un rang unique de 1 à 7.",
    errors: {
      maxFour: "Vous avez déjà choisi 4 éléments pour cette section."
    },
    mobilityTypeOptions: ["Transfrontalière", "Expatriation"],
    countryColumns: ["J'y habite", "Je veux y travailler", "J'y ai déjà travaillé"],
    countryRows: ["Allemagne", "France", "Luxembourg", "Un autre pays de l'UE", "Un autre pays hors UE"],
    scheduleColumns: ["Matin", "Après-midi", "Soir", "Nuit"],
    scheduleRows: ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"],
    documentsColumns: ["Je l'ai", "Je suis en train de le préparer", "Je ne sais pas encore"],
    documentsRows: [
      "Carte d'identité ou passeport (en cours de validité)",
      "CV à jour",
      "Vos diplômes ou qualifications professionnelles",
      "Compte bancaire / IBAN",
      "Attestation d'affiliation à la sécurité sociale"
    ],
    languageColumns: [
      "Langue maternelle",
      "Je peux échanger à l'oral",
      "Je peux travailler avec cette langue",
      "J'utilise un outil de traduction si nécessaire",
      "Je ne la pratique pas"
    ],
    languageRows: ["Allemand", "Anglais", "Français", "Luxembourgeois"],
    rankingOptions: [
      "Trouver un logement",
      "Trouver un emploi",
      "Comprendre les démarches administratives/fiscales",
      "Préparer votre budget et vos finances",
      "Améliorer votre niveau de langue",
      "Obtenir de l'aide à l'arrivée (installation, démarches)",
      "Construire un réseau, vous intégrer socialement"
    ],
    sectors: [
      "Vente et commerce (ex : prêt-à-porter, chaussures, commerce spécialisé)",
      "Nettoyage et entretien (ex : bureaux, espaces collectifs)",
      "Hôtellerie et restauration (ex : plonge, service, aide de cuisine)",
      "Agriculture et récolte (ex : récolte de fruits, travaux saisonniers)",
      "Missions polyvalentes et emplois accessibles rapidement"
    ],
    questions: {
      q03: "Avez-vous déjà travaillé sous statut \"frontalier\" ?",
      q04: "Quel temps de trajet maximum accepteriez vous de faire (aller simple) ?",
      q05: "Comment vous vous déplaceriez au quotidien ?",
      q06: "Quelles sont vos disponibilités horaires ?",
      q07: "Sélectionner vos disponibilités",
      q08: "Quels types de contrats accepteriez vous ?",
      q09: "À partir de quand seriez-vous disponible pour commencer un emploi ?",
      q10: "Où en êtes-vous dans la préparation de ces documents ?",
      q10Hint: "Il n’est pas nécessaire d’avoir déjà tous les documents.",
      q11: "Avez-vous déjà un numéro ou une affiliation à la sécurité sociale luxembourgeoise ?",
      q12: "Avez-vous déjà un numéro ou une affiliation à la sécurité sociale allemande ?",
      q13: "Avez-vous déjà un numéro ou une affiliation à la sécurité sociale française ?",
      q14: "Avez-vous déjà vécu et travaillé dans pays étranger ?",
      q15: "Quand souhaitez-vous partir ?",
      q16: "Concernant les conditions de votre départ, vous partirez :",
      q18: "Vos compétences linguistiques",
      q19: "Dans quels secteurs souhaitez-vous travailler ?",
      sectorHint: "Vous pouvez sélectionner jusqu'à 4 propositions.",
      q21: "Avez-vous une expérience professionnelle dans le secteur de la vente et du commerce ?",
      q23: "Avez-vous une expérience professionnelle dans le secteur du nettoyage ?",
      q24: "Disposez-vous d’un extrait de casier judiciaire (bulletin n°3) datant de moins de 3 mois ?",
      q26: "Avez-vous une expérience professionnelle dans le secteur de l'hôtellerie et de la restauration?",
      q28: "Avez-vous une expérience professionnelle dans le secteur de l'agriculture et de la récolte?",
      q30: "Avez-vous une expérience professionnelle ?",
      salaryType: "Sous quelle forme pensez-vous à votre salaire ?",
      salaryMin: "Quel est le minimum que vous souhaiteriez pour ce métier, en euros bruts ou nets ?",
      firstName: "Prénom",
      lastName: "Nom",
      email: "Adresse e-mail",
      phone: "Téléphone",
      city: "Ville de résidence actuelle",
      cv: "Souhaitez-vous transmettre votre CV ?"
    },
    options: {
      yesNo: ["Oui", "Non"],
      yesNoUnknown: ["Oui", "Non", "Je ne sais pas"],
      commute: ["30 min", "1h", "1h30", "2h", "Plus de 2h"],
      transport: ["Voiture", "Train", "Bus", "Covoiturage", "Je ne sais pas encore"],
      schedule: ["Je suis disponible sur des horaires variés", "J’ai des contraintes ou préférences horaires"],
      contracts: ["CDI", "CDD", "Intérim", "Saisonnier", "Temps plein", "Temps partiel"],
      startDate: ["Dès que possible", "Dans les prochains jours", "Dans les prochaines semaines", "Dans 1 à 3 mois", "Je ne sais pas encore"],
      departWhen: ["Dès que possible", "D'ici 3 mois", "Entre 3 et 6 mois", "Dans  plus de 6 mois", "Je ne sais pas"],
      departWith: ["Uniquement vous", "En couple", "En famille"],
      experience: ["Oui, plus de 2 ans", "Oui, entre 6 mois et 2 ans", "Oui, moins de 6 mois", "Non, mais je suis intéressé(e) par le secteur"],
      backgroundCheck: ["Oui", "Non", "Je peux en faire la demande rapidement", "Je ne sais pas"]
    },
    salaryUnits: ["Par heure", "Par mois", "Par an"],
    salaryFields: {
      type: "Sous quelle forme pensez-vous à votre salaire ?",
      min: "Quel est le minimum que vous souhaiteriez pour ce métier, en euros bruts ou nets ?"
    },
    sectorTitles: {
      vente: "Vente et commerce",
      nettoyage: "Nettoyage et entretien",
      hotel: "Hôtellerie et restauration",
      agri: "Agriculture et récolte",
      polyvalent: "Missions polyvalentes et emplois accessibles rapidement"
    },
    sectorLegends: {
      vente: "Vente et commerce — parmi les propositions suivantes, lesquelles vous correspondent le mieux ?",
      nettoyage: "Nettoyage et entretien — parmi les propositions suivantes, lesquelles vous correspondent le mieux ?",
      hotel: "Hôtellerie et restauration — parmi les propositions suivantes, lesquelles vous correspondent le mieux ?",
      agri: "Agriculture et récolte — parmi les propositions suivantes, lesquelles vous correspondent le mieux ?",
      polyvalent: "Missions polyvalentes et emplois accessibles rapidement — parmi les propositions suivantes, lesquelles vous correspondent le mieux ?"
    },
    sectorChoices: {
      vente: [
        "Accueillir et orienter les clients",
        "Conseiller un produit ou un service",
        "Comprendre rapidement une demande",
        "Réaliser un encaissement",
        "Garder son calme en période d’affluence",
        "Travailler en équipe",
        "Être ponctuel",
        "S’adapter à différentes tâches",
        "Résister au stress",
        "Aider un collègue si nécessaire",
        "Fidéliser la clientèle",
        "Maintenir un espace de vente propre et organisé"
      ],
      nettoyage: [
        "Travailler de manière autonome",
        "Appliquer des consignes",
        "Organiser son travail",
        "Maintenir un espace propre et organisé",
        "S'adapter à une situation imprévue",
        "Prendre soin du matériel utilisé",
        "Être efficace dans ses tâches",
        "Travailler en équipe",
        "Aider un collègue si nécessaire",
        "Être ponctuel",
        "Respecter des règles d’hygiène et de sécurité",
        "Effectuer des tâches répétitives"
      ],
      hotel: [
        "Accueillir et orienter les clients",
        "Travailler en équipe",
        "Garder son calme pendant les périodes d’affluence",
        "Appliquer des consignes",
        "Être ponctuel",
        "S’adapter à différentes tâches",
        "Mémoriser des commandes ou des informations",
        "Aider un collègue si nécessaire",
        "Résister au stress",
        "Maintenir un espace propre et organisé",
        "Conseiller un client ou répondre à une demande"
      ],
      agri: [
        "Être ponctuel",
        "Travailler en équipe",
        "Appliquer des consignes",
        "Prendre soin du matériel utilisé",
        "Aider un collègue si nécessaire",
        "Garder son calme en période d’activité intense",
        "Réaliser des tâches physiques",
        "Travailler en extérieur et selon les conditions météo",
        "S’adapter à différentes tâches",
        "Effectuer des tâches répétitives"
      ],
      polyvalent: [
        "S’adapter rapidement à une nouvelle tâche",
        "Travailler en équipe",
        "Respecter les consignes",
        "Respecter les horaires de travail",
        "Réaliser un travail physique",
        "Travailler à un rythme soutenu",
        "Travailler dans différents environnements",
        "Accepter des horaires variables",
        "Aider un collègue si nécessaire",
        "Être disponible rapidement"
      ]
    }
  },
  en: {
    eyebrow: "EURES candidate questionnaire",
    heroTitle: "European mobility, cross-border commuting or relocation",
    heroLede: "This questionnaire helps us better understand your mobility plans in Europe, whether you are considering working in a neighbouring country or moving to live and work in another European country.",
    heroHighlight: "It only takes a few minutes. Your answers help us identify more quickly whether opportunities may match your situation, availability and preferences.",
    overviewTitle: "About your mobility plans",
    overviewMatrixTitle: "Select below your country of residence, the country or countries where you would like to work, and those where you have already worked",
    mobilityTypeTitle: "What type of mobility are you considering?",
    mobilityTypeHint: "You can choose one option or both.",
    crossBorderTitle: "Your cross-border mobility plans",
    expatriationTitle: "Your relocation plans",
    professionalTitle: "Your professional plans",
    contactTitle: "So that we can contact you again",
    rankingTitle: "Rank these items from most important to least important for you",
    rankingHint: "Give a unique rank to each item: 1 for the most important, 7 for the least important.",
    sidebarWhyTitle: "Why this questionnaire?",
    sidebarWhyText: "It helps us identify more easily people who may be interested in a European mobility opportunity, based on the target country, job sector, languages, availability and practical conditions.",
    sidebarAfterTitle: "What happens next?",
    sidebarAfterText: "If your profile seems to match an active need, it may be reviewed for a possible introduction. If the timing is not right yet, your answers still help us prepare upcoming opportunities better.",
    sidebarResumeTitle: "Continue later",
    sidebarResumeText: "An identifier is kept so your progress can be found again if needed.",
    salaryExpectationIntro: "Indicate your salary expectation for this role here, in euros, and specify whether it is gross or net.",
    fileNote: "The file name will be recorded. The file itself is not yet stored on the platform.",
    consentText: "I agree that my answers may be used by EURES teams and partners for professional mobility support and the proposed introductions. Your data will only be used for your support and in accordance with European data protection rules (GDPR).",
    rankingError: "Each relocation priority must have a unique rank from 1 to 7.",
    errors: {
      maxFour: "You have already selected 4 items for this section."
    },
    mobilityTypeOptions: ["Cross-border commuting", "Relocation"],
    countryColumns: ["I live there", "I want to work there", "I have already worked there"],
    countryRows: ["Germany", "France", "Luxembourg", "Another EU country", "Another non-EU country"],
    scheduleColumns: ["Morning", "Afternoon", "Evening", "Night"],
    scheduleRows: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    documentsColumns: ["I already have it", "I am preparing it", "I do not know yet"],
    documentsRows: [
      "Identity card or passport (valid)",
      "Up-to-date CV",
      "Your diplomas or professional qualifications",
      "Bank account / IBAN",
      "Social security affiliation certificate"
    ],
    languageColumns: [
      "Native language",
      "I can speak it",
      "I can work in this language",
      "I use a translation tool if needed",
      "I do not use it"
    ],
    languageRows: ["German", "English", "French", "Luxembourgish"],
    rankingOptions: [
      "Finding accommodation",
      "Finding a job",
      "Understanding administrative and tax procedures",
      "Planning your budget and finances",
      "Improving your language level",
      "Getting help on arrival (settling in, procedures)",
      "Building a network and integrating socially"
    ],
    sectors: [
      "Sales and retail (for example ready-to-wear, shoes, specialist retail)",
      "Cleaning and maintenance (for example offices, shared spaces)",
      "Hospitality and food service (for example dishwashing, service, kitchen support)",
      "Agriculture and harvesting (for example fruit picking, seasonal work)",
      "Versatile jobs and roles accessible quickly"
    ],
    questions: {
      q03: "Have you already worked with cross-border commuter status?",
      q04: "What maximum travel time would you accept (one way)?",
      q05: "How would you travel on a daily basis?",
      q06: "What are your schedule availabilities?",
      q07: "Select your availabilities",
      q08: "Which types of contract would you accept?",
      q09: "When would you be available to start a job?",
      q10: "Where do you stand in preparing these documents?",
      q10Hint: "It is not necessary to already have all of them.",
      q11: "Do you already have a Luxembourg social security number or affiliation?",
      q12: "Do you already have a German social security number or affiliation?",
      q13: "Do you already have a French social security number or affiliation?",
      q14: "Have you already lived and worked in a foreign country?",
      q15: "When would you like to leave?",
      q16: "Regarding your departure, you would leave:",
      q18: "Your language skills",
      q19: "In which sectors would you like to work?",
      sectorHint: "You can select up to 4 options.",
      q21: "Do you have work experience in sales and retail?",
      q23: "Do you have work experience in cleaning?",
      q24: "Do you have a criminal record extract issued within the last 3 months?",
      q26: "Do you have work experience in hospitality and food service?",
      q28: "Do you have work experience in agriculture and harvesting?",
      q30: "Do you have work experience?",
      salaryType: "How do you think about your salary?",
      salaryMin: "What is the minimum you would like for this role, in gross or net euros?",
      firstName: "First name",
      lastName: "Last name",
      email: "Email address",
      phone: "Phone",
      city: "Current city of residence",
      cv: "Would you like to provide your CV?"
    },
    options: {
      yesNo: ["Yes", "No"],
      yesNoUnknown: ["Yes", "No", "I don't know"],
      commute: ["30 min", "1h", "1h30", "2h", "More than 2h"],
      transport: ["Car", "Train", "Bus", "Carpooling", "I don't know yet"],
      schedule: ["I am available on varied schedules", "I have schedule constraints or preferences"],
      contracts: ["Permanent contract", "Fixed-term contract", "Temporary agency work", "Seasonal", "Full-time", "Part-time"],
      startDate: ["As soon as possible", "In the next few days", "In the next few weeks", "In 1 to 3 months", "I don't know yet"],
      departWhen: ["As soon as possible", "Within 3 months", "Between 3 and 6 months", "In more than 6 months", "I don't know"],
      departWith: ["Only you", "As a couple", "As a family"],
      experience: ["Yes, more than 2 years", "Yes, between 6 months and 2 years", "Yes, less than 6 months", "No, but I am interested in this sector"],
      backgroundCheck: ["Yes", "No", "I can request it quickly", "I don't know"]
    },
    salaryUnits: ["Per hour", "Per month", "Per year"],
    salaryFields: {
      type: "How do you think about your salary?",
      min: "What is the minimum you would like for this role, in gross or net euros?"
    },
    sectorTitles: {
      vente: "Sales and retail",
      nettoyage: "Cleaning and maintenance",
      hotel: "Hospitality and food service",
      agri: "Agriculture and harvesting",
      polyvalent: "Versatile jobs and roles accessible quickly"
    },
    sectorLegends: {
      vente: "Sales and retail: which of the following statements describe you best?",
      nettoyage: "Cleaning and maintenance: which of the following statements describe you best?",
      hotel: "Hospitality and food service: which of the following statements describe you best?",
      agri: "Agriculture and harvesting: which of the following statements describe you best?",
      polyvalent: "Versatile jobs and roles accessible quickly: which of the following statements describe you best?"
    },
    sectorChoices: {
      vente: ["Welcoming and guiding customers", "Advising on a product or service", "Understanding a request quickly", "Handling payment", "Staying calm during busy periods", "Working as part of a team", "Being punctual", "Adapting to different tasks", "Handling stress", "Helping a colleague when needed", "Building customer loyalty", "Keeping the sales area clean and organised"],
      nettoyage: ["Working independently", "Following instructions", "Organising your work", "Keeping an area clean and organised", "Adapting to an unexpected situation", "Taking care of the equipment used", "Being efficient in your tasks", "Working as part of a team", "Helping a colleague when needed", "Being punctual", "Following hygiene and safety rules", "Carrying out repetitive tasks"],
      hotel: ["Welcoming and guiding customers", "Working as part of a team", "Staying calm during busy periods", "Following instructions", "Being punctual", "Adapting to different tasks", "Remembering orders or information", "Helping a colleague when needed", "Handling stress", "Keeping an area clean and organised", "Advising a customer or answering a request"],
      agri: ["Being punctual", "Working as part of a team", "Following instructions", "Taking care of the equipment used", "Helping a colleague when needed", "Staying calm during intense periods of activity", "Doing physical tasks", "Working outdoors and depending on weather conditions", "Adapting to different tasks", "Carrying out repetitive tasks"],
      polyvalent: ["Adapting quickly to a new task", "Working as part of a team", "Following instructions", "Respecting working hours", "Doing physical work", "Working at a sustained pace", "Working in different environments", "Accepting variable schedules", "Helping a colleague when needed", "Being available quickly"]
    }
  },
  de: {
    eyebrow: "EURES-Kandidatenfragebogen",
    heroTitle: "Europäische Mobilität, Grenzpendeln oder Umzug",
    heroLede: "Dieser Fragebogen hilft uns, Ihre Mobilitätspläne in Europa besser zu verstehen, egal ob Sie in einem Nachbarland arbeiten möchten oder in ein anderes europäisches Land ziehen wollen, um dort zu leben und zu arbeiten.",
    heroHighlight: "Das dauert nur wenige Minuten. Ihre Antworten helfen uns, schneller zu erkennen, ob Chancen zu Ihrer Situation, Ihrer Verfügbarkeit und Ihren Präferenzen passen könnten.",
    overviewTitle: "Zu Ihrem Mobilitätsprojekt",
    overviewMatrixTitle: "Wählen Sie unten Ihr Wohnland, die Länder, in denen Sie arbeiten möchten, und die Länder, in denen Sie bereits gearbeitet haben",
    mobilityTypeTitle: "Welche Art von Mobilität ziehen Sie in Betracht?",
    mobilityTypeHint: "Sie können eine oder beide Optionen wählen.",
    crossBorderTitle: "Ihr grenzüberschreitendes Mobilitätsprojekt",
    expatriationTitle: "Ihr Umzugsprojekt",
    professionalTitle: "Ihr berufliches Projekt",
    contactTitle: "Damit wir Sie wieder kontaktieren können",
    rankingTitle: "Ordnen Sie diese Punkte von am wichtigsten bis am wenigsten wichtig für Sie",
    rankingHint: "Geben Sie jedem Punkt einen eindeutigen Rang: 1 für am wichtigsten, 7 für am wenigsten wichtig.",
    sidebarWhyTitle: "Warum dieser Fragebogen?",
    sidebarWhyText: "Er hilft uns, leichter Personen zu erkennen, die an einer europäischen Mobilitätschance interessiert sein könnten, je nach Zielland, Berufsfeld, Sprachen, Verfügbarkeit und praktischen Bedingungen.",
    sidebarAfterTitle: "Wie geht es danach weiter?",
    sidebarAfterText: "Wenn Ihr Profil zu einem aktuellen Bedarf zu passen scheint, kann es für eine mögliche Vermittlung geprüft werden. Wenn der Zeitpunkt noch nicht passt, helfen uns Ihre Antworten trotzdem dabei, kommende Chancen besser vorzubereiten.",
    sidebarResumeTitle: "Später fortsetzen",
    sidebarResumeText: "Eine Kennung wird gespeichert, damit Ihr Fortschritt bei Bedarf wiedergefunden werden kann.",
    salaryExpectationIntro: "Geben Sie hier Ihre Gehaltserwartung für diesen Beruf in Euro an und präzisieren Sie, ob es sich um einen Brutto- oder Nettobetrag handelt.",
    fileNote: "Der Dateiname wird gespeichert. Die Datei selbst wird derzeit noch nicht auf der Plattform gespeichert.",
    consentText: "Ich stimme zu, dass meine Antworten von EURES-Teams und Partnern für die Begleitung der beruflichen Mobilität und die vorgeschlagenen Vermittlungen verwendet werden dürfen. Ihre Daten werden nur im Rahmen Ihrer Begleitung und gemäß den europäischen Datenschutzvorschriften (DSGVO) verwendet.",
    rankingError: "Jede Umzugspriorität muss einen eindeutigen Rang von 1 bis 7 haben.",
    errors: {
      maxFour: "Sie haben für diesen Abschnitt bereits 4 Elemente ausgewählt."
    },
    mobilityTypeOptions: ["Grenzpendeln", "Umzug"],
    countryColumns: ["Ich wohne dort", "Ich möchte dort arbeiten", "Ich habe dort bereits gearbeitet"],
    countryRows: ["Deutschland", "Frankreich", "Luxemburg", "Ein anderes EU-Land", "Ein anderes Nicht-EU-Land"],
    scheduleColumns: ["Morgen", "Nachmittag", "Abend", "Nacht"],
    scheduleRows: ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"],
    documentsColumns: ["Ich habe es bereits", "Ich bereite es gerade vor", "Ich weiß es noch nicht"],
    documentsRows: [
      "Personalausweis oder Reisepass (gültig)",
      "Aktueller Lebenslauf",
      "Ihre Diplome oder beruflichen Qualifikationen",
      "Bankkonto / IBAN",
      "Bescheinigung über die Sozialversicherungszugehörigkeit"
    ],
    languageColumns: [
      "Muttersprache",
      "Ich kann mich mündlich verständigen",
      "Ich kann in dieser Sprache arbeiten",
      "Ich nutze bei Bedarf ein Übersetzungstool",
      "Ich nutze sie nicht"
    ],
    languageRows: ["Deutsch", "Englisch", "Französisch", "Luxemburgisch"],
    rankingOptions: [
      "Eine Unterkunft finden",
      "Eine Arbeit finden",
      "Verwaltungs- und Steuerverfahren verstehen",
      "Ihr Budget und Ihre Finanzen planen",
      "Ihr Sprachniveau verbessern",
      "Hilfe bei der Ankunft erhalten (Einrichtung, Verfahren)",
      "Ein Netzwerk aufbauen und sich sozial integrieren"
    ],
    sectors: [
      "Verkauf und Handel (z. B. Bekleidung, Schuhe, Fachhandel)",
      "Reinigung und Instandhaltung (z. B. Büros, Gemeinschaftsflächen)",
      "Hotellerie und Gastronomie (z. B. Spülküche, Service, Küchenhilfe)",
      "Landwirtschaft und Ernte (z. B. Obsternte, Saisonarbeit)",
      "Vielseitige Tätigkeiten und Jobs mit schnellem Einstieg"
    ],
    questions: {
      q03: "Haben Sie bereits mit Grenzgängerstatus gearbeitet?",
      q04: "Welche maximale Fahrzeit würden Sie akzeptieren (einfache Strecke)?",
      q05: "Wie würden Sie sich täglich fortbewegen?",
      q06: "Wie sind Ihre zeitlichen Verfügbarkeiten?",
      q07: "Wählen Sie Ihre Verfügbarkeiten",
      q08: "Welche Vertragsarten würden Sie akzeptieren?",
      q09: "Ab wann wären Sie verfügbar, um eine Arbeit zu beginnen?",
      q10: "Wie weit sind Sie bei der Vorbereitung dieser Unterlagen?",
      q10Hint: "Es ist nicht nötig, bereits alle Unterlagen zu haben.",
      q11: "Haben Sie bereits eine luxemburgische Sozialversicherungsnummer oder Zugehörigkeit?",
      q12: "Haben Sie bereits eine deutsche Sozialversicherungsnummer oder Zugehörigkeit?",
      q13: "Haben Sie bereits eine französische Sozialversicherungsnummer oder Zugehörigkeit?",
      q14: "Haben Sie bereits in einem anderen Land gelebt und gearbeitet?",
      q15: "Wann möchten Sie aufbrechen?",
      q16: "Unter welchen Bedingungen würden Sie aufbrechen:",
      q18: "Ihre Sprachkenntnisse",
      q19: "In welchen Bereichen möchten Sie arbeiten?",
      sectorHint: "Sie können bis zu 4 Antworten auswählen.",
      q21: "Haben Sie Berufserfahrung im Verkauf und Handel?",
      q23: "Haben Sie Berufserfahrung in der Reinigung?",
      q24: "Verfügen Sie über einen Strafregisterauszug, der nicht älter als 3 Monate ist?",
      q26: "Haben Sie Berufserfahrung in Hotellerie und Gastronomie?",
      q28: "Haben Sie Berufserfahrung in Landwirtschaft und Ernte?",
      q30: "Haben Sie Berufserfahrung?",
      salaryType: "In welcher Form denken Sie an Ihr Gehalt?",
      salaryMin: "Was ist das Minimum, das Sie für diesen Beruf in Euro brutto oder netto erwarten würden?",
      firstName: "Vorname",
      lastName: "Nachname",
      email: "E-Mail-Adresse",
      phone: "Telefon",
      city: "Aktueller Wohnort",
      cv: "Möchten Sie Ihren Lebenslauf übermitteln?"
    },
    options: {
      yesNo: ["Ja", "Nein"],
      yesNoUnknown: ["Ja", "Nein", "Ich weiß es nicht"],
      commute: ["30 Min.", "1 Std.", "1 Std. 30", "2 Std.", "Mehr als 2 Std."],
      transport: ["Auto", "Zug", "Bus", "Fahrgemeinschaft", "Ich weiß es noch nicht"],
      schedule: ["Ich bin zu unterschiedlichen Zeiten verfügbar", "Ich habe zeitliche Einschränkungen oder Präferenzen"],
      contracts: ["Unbefristeter Vertrag", "Befristeter Vertrag", "Zeitarbeit", "Saisonarbeit", "Vollzeit", "Teilzeit"],
      startDate: ["So schnell wie möglich", "In den nächsten Tagen", "In den nächsten Wochen", "In 1 bis 3 Monaten", "Ich weiß es noch nicht"],
      departWhen: ["So schnell wie möglich", "Innerhalb von 3 Monaten", "Zwischen 3 und 6 Monaten", "In mehr als 6 Monaten", "Ich weiß es nicht"],
      departWith: ["Nur Sie", "Als Paar", "Als Familie"],
      experience: ["Ja, mehr als 2 Jahre", "Ja, zwischen 6 Monaten und 2 Jahren", "Ja, weniger als 6 Monate", "Nein, aber ich interessiere mich für diesen Bereich"],
      backgroundCheck: ["Ja", "Nein", "Ich kann ihn schnell beantragen", "Ich weiß es nicht"]
    },
    salaryUnits: ["Pro Stunde", "Pro Monat", "Pro Jahr"],
    salaryFields: {
      type: "In welcher Form denken Sie an Ihr Gehalt?",
      min: "Was ist das Minimum, das Sie für diesen Beruf in Euro brutto oder netto erwarten würden?"
    },
    sectorTitles: {
      vente: "Verkauf und Handel",
      nettoyage: "Reinigung und Instandhaltung",
      hotel: "Hotellerie und Gastronomie",
      agri: "Landwirtschaft und Ernte",
      polyvalent: "Vielseitige Tätigkeiten und Jobs mit schnellem Einstieg"
    },
    sectorLegends: {
      vente: "Verkauf und Handel: Welche der folgenden Aussagen passen am besten zu Ihnen?",
      nettoyage: "Reinigung und Instandhaltung: Welche der folgenden Aussagen passen am besten zu Ihnen?",
      hotel: "Hotellerie und Gastronomie: Welche der folgenden Aussagen passen am besten zu Ihnen?",
      agri: "Landwirtschaft und Ernte: Welche der folgenden Aussagen passen am besten zu Ihnen?",
      polyvalent: "Vielseitige Tätigkeiten und Jobs mit schnellem Einstieg: Welche der folgenden Aussagen passen am besten zu Ihnen?"
    },
    sectorChoices: {
      vente: ["Kunden empfangen und orientieren", "Zu einem Produkt oder einer Dienstleistung beraten", "Eine Anfrage schnell verstehen", "Eine Zahlung durchführen", "In Stoßzeiten ruhig bleiben", "Im Team arbeiten", "Pünktlich sein", "Sich an verschiedene Aufgaben anpassen", "Stress standhalten", "Bei Bedarf einem Kollegen helfen", "Kundschaft binden", "Einen Verkaufsbereich sauber und organisiert halten"],
      nettoyage: ["Selbstständig arbeiten", "Anweisungen befolgen", "Die eigene Arbeit organisieren", "Einen Bereich sauber und organisiert halten", "Sich an eine unvorhergesehene Situation anpassen", "Sorgfältig mit dem verwendeten Material umgehen", "In den Aufgaben effizient sein", "Im Team arbeiten", "Bei Bedarf einem Kollegen helfen", "Pünktlich sein", "Hygiene- und Sicherheitsregeln einhalten", "Wiederholende Aufgaben ausführen"],
      hotel: ["Kunden empfangen und orientieren", "Im Team arbeiten", "Während starker Auslastung ruhig bleiben", "Anweisungen befolgen", "Pünktlich sein", "Sich an verschiedene Aufgaben anpassen", "Bestellungen oder Informationen behalten", "Bei Bedarf einem Kollegen helfen", "Stress standhalten", "Einen Bereich sauber und organisiert halten", "Einen Kunden beraten oder auf eine Anfrage antworten"],
      agri: ["Pünktlich sein", "Im Team arbeiten", "Anweisungen befolgen", "Sorgfältig mit dem verwendeten Material umgehen", "Bei Bedarf einem Kollegen helfen", "In intensiven Arbeitsphasen ruhig bleiben", "Körperliche Aufgaben ausführen", "Im Freien und je nach Wetterbedingungen arbeiten", "Sich an verschiedene Aufgaben anpassen", "Wiederholende Aufgaben ausführen"],
      polyvalent: ["Sich schnell an eine neue Aufgabe anpassen", "Im Team arbeiten", "Anweisungen befolgen", "Arbeitszeiten einhalten", "Körperliche Arbeit ausführen", "In hohem Tempo arbeiten", "In unterschiedlichen Umgebungen arbeiten", "Variable Arbeitszeiten akzeptieren", "Bei Bedarf einem Kollegen helfen", "Schnell verfügbar sein"]
    }
  }
};

function localizeOptions(values, labels) {
  return values.map((value, index) => ({ value, label: labels[index] || value }));
}

function localizeRows(rows, labels) {
  return rows.map((row, index) => ({ ...row, label: labels[index] || row.label }));
}

function getCandidateTallyContent(lang) {
  const content = candidateTallyCopy[lang] || candidateTallyCopy.fr;
  return {
    ...content,
    mobilityTypeOptions: localizeOptions(candidateTallyMeta.mobilityTypes, content.mobilityTypeOptions),
    countryColumns: localizeOptions(candidateTallyMeta.countryColumns, content.countryColumns),
    countryRows: localizeRows(candidateTallyMeta.countryRows, content.countryRows),
    scheduleColumns: localizeOptions(candidateTallyMeta.scheduleColumns, content.scheduleColumns),
    scheduleRows: localizeRows(candidateTallyMeta.scheduleRows, content.scheduleRows),
    documentsColumns: localizeOptions(candidateTallyMeta.documentsColumns, content.documentsColumns),
    documentsRows: localizeRows(candidateTallyMeta.documentsRows, content.documentsRows),
    languageColumns: localizeOptions(candidateTallyMeta.languageColumns, content.languageColumns),
    languageRows: localizeRows(candidateTallyMeta.languageRows, content.languageRows),
    sectorsOptions: localizeOptions(candidateTallyMeta.sectors, content.sectors),
    rankingDisplayOptions: content.rankingOptions
  };
}

const employerTallyMeta = {
  formId: "ZjZA7A",
  sectors: [
    "Vente et commerce",
    "Nettoyage et entretien",
    "Hôtellerie et restauration",
    "Agriculture et récolte",
    "Missions polyvalentes et emplois accessibles rapidement"
  ],
  languageColumns: ["Pas nécessaire", "Communication simple", "Communication professionelle", "Très important au quotidien"],
  languageRows: [
    { field: "tally_q02_f01", label: "Allemand" },
    { field: "tally_q02_f02", label: "Anglais" },
    { field: "tally_q02_f03", label: "Français" },
    { field: "tally_q02_f04", label: "Luxembourgeois" }
  ],
  sectorPriorityGroups: {
    tally_q10: [
      "Être à l’aise avec les clients",
      "Pouvoir communiquer simplement avec les clients",
      "Travailler pendant les périodes d’affluence",
      "Réaliser des opérations d'encaissements",
      "Travailler en équipe",
      "S’adapter à différentes tâches",
      "Maintenir un espace de vente propre et organisé",
      "Respecter les horaires de travail"
    ],
    tally_q11: [
      "Respecter les procédures, consignes et les règles d’hygiène",
      "Maintenir un niveau de qualité constant",
      "Respecter les horaires de travail",
      "Travailler de manière autonome",
      "Travailler en équipe",
      "Travailler à un rythme soutenu",
      "S’adapter à différents lieux ou environnements de travail",
      "Réaliser des tâches répétitives",
      "Pouvoir se déplacer facilement sur les lieux d’intervention"
    ],
    tally_q12: [
      "Accueillir et orienter les clients",
      "Pouvoir communiquer simplement avec les clients",
      "Travailler pendant les périodes d’affluence",
      "Garder son calme en période d’activité intense",
      "Travailler en équipe",
      "Respecter les horaires de travail",
      "Travailler en soirée, le week-end ou les jours fériés",
      "Mémoriser des commandes ou des informations",
      "S’adapter à différentes tâches",
      "Maintenir un espace d'accueil ou de service propre et organisé"
    ],
    tally_q13: [
      "Respecter les horaires et les périodes de récolte",
      "Travailler en extérieur et selon les conditions météo",
      "Réaliser un travail physique",
      "Travailler à un rythme soutenu",
      "Respecter les consignes de travail et de sécurité",
      "Utiliser correctement le matériel ou les outils",
      "Travailler en équipe",
      "S’adapter à différents types de travaux",
      "Pouvoir se déplacer facilement sur les lieux de travail",
      "Maintenir une qualité de travail régulière"
    ],
    tally_q14: [
      "S’adapter rapidement à différentes tâches",
      "Respecter les consignes et les horaires",
      "Réaliser un travail physique",
      "Travailler à un rythme soutenu",
      "Travailler dans différents environnements",
      "Intégrer rapidement une équipe",
      "Travailler en équipe",
      "Accepter des horaires variables",
      "Être disponible rapidement",
      "Pouvoir commencer rapidement une mission"
    ]
  }
};

const employerTallyCopy = {
  fr: {
    eyebrow: "Questionnaire employeur EURES",
    heroTitle: "Décrire un besoin de recrutement ouvert à la mobilité européenne",
    heroLede: "Ce questionnaire nous aide à mieux comprendre votre besoin de recrutement, les profils recherchés, les langues utiles et les conditions de travail proposées.",
    heroHighlight: "L’objectif est de rendre votre besoin plus clair et plus comparable, pour faciliter ensuite l’identification de profils compatibles.",
    sidebarWhyTitle: "Pourquoi ce questionnaire ?",
    sidebarWhyText: "Il sert à rendre le besoin de recrutement plus lisible : secteur, volume, langues, contraintes de travail, profils acceptés et éventuelles aides à l’installation.",
    sidebarAfterTitle: "Et après ?",
    sidebarAfterText: "Si des profils semblent correspondre, votre besoin peut être repris pour une mise en relation. Sinon, les réponses servent déjà à mieux structurer les prochains recrutements.",
    sidebarResumeTitle: "Reprendre plus tard",
    sidebarResumeText: "Un identifiant est conservé pour retrouver votre progression si besoin.",
    salaryOfferIntro: "Indiquez ici le salaire proposé pour ce métier, en euros, en précisant s'il s'agit d'un montant brut ou net.",
    introNote: "Ce formulaire prend 2 à 3 minutes et s’adresse aux employeurs ayant des besoins de recrutement ouverts à la mobilité européenne et aux recrutements hors frontières.",
    introNote2: "Nous travaillons actuellement sur quelques métiers prioritaires, afin de tester le service sur des cas concrets.",
    sections: {
      need: "Votre besoin de recrutement",
      conditions: "Profils, aides et conditions de travail",
      contact: "Pour pouvoir vous recontacter"
    },
    questions: {
      q01: "Dans quel secteur recrutez-vous actuellement ?",
      q02: "Quelles langues sont impératives pour ce recrutement ?",
      q02Hint: "Indiquez le niveau de communication attendu pour chaque langue.",
      q03: "Combien de personnes souhaitez-vous recruter ?",
      q04: "À partir de quand avez-vous besoin de ces recrutements ?",
      q05: "Quelle durée de contrat proposez-vous ?",
      q06: "Quel volume de travail hebdomadaire proposez-vous ?",
      q07: "Quels profils êtes-vous prêts à recruter ?",
      q08: "Pouvez-vous aider les personnes recrutées dans leur arrivée ou leur installation ?",
      q09: "Parmi les éléments suivants, lesquels sont indispensables pour vous ?",
      q10: "Pour ce recrutement en vente et commerce, quels éléments vous semblent les plus importants ?",
      q11: "Pour ce recrutement en nettoyage et entretien, quels éléments vous semblent les plus importants ?",
      q12: "Pour ce recrutement en hôtellerie et restauration, quels éléments vous semblent les plus importants ?",
      q13: "Pour ce recrutement en agriculture et récolte, quels éléments vous semblent les plus importants ?",
      q14: "Pour ce recrutement en missions polyvalentes et emplois accessibles rapidement, quels éléments vous semblent les plus importants ?",
      q14Hint: "Vous pouvez sélectionner jusqu'à 4 propositions.",
      q15: "Quelles conditions de travail les personnes recrutées doivent-elles connaître ?",
      q16: "Prénom",
      q17: "Nom de l'entreprise",
      q18: "Adresse e-mail",
      q19: "Téléphone",
      q20: "Lieux de travail",
      salaryType: "Sous quelle forme exprimez-vous le salaire proposé ?",
      salaryMin: "Montant minimum proposé, en euros bruts ou nets",
      salaryMax: "Montant maximum proposé, en euros bruts ou nets",
      q21Title: "Protection des données",
      q21Text: "Les informations transmises permettront à l’équipe EURES beta de mieux comprendre votre besoin de recrutement et les conditions proposées afin d’identifier des profils susceptibles de correspondre.",
      q21Text2: "Si des profils compatibles avec votre recherche sont identifiés, vous pourrez être recontacté prochainement.",
      q21Text3: "Pensez à répondre aux appels masqués ou inconnus et à vérifier régulièrement vos courriers indésirables (spams).",
      consent: "J’accepte que les informations transmises soient utilisées par les équipes et partenaires EURES dans le cadre des mises en relation et des échanges liés au recrutement. Les données transmises seront utilisées uniquement dans le cadre des échanges liés au recrutement et conformément à la réglementation européenne sur la protection des données (RGPD)."
    },
    options: {
      sectors: employerTallyMeta.sectors,
      q03: ["1 personne", "2 à 5 personnes", "Plus de 5 personnes", "Je ne sais pas encore"],
      q04: ["Dès que possible", "Dans les prochains jours", "Dans les prochaines semaines", "Pour une période saisonnière", "Je ne sais pas encore"],
      q05: ["Moins d'un mois", "1 à 3 mois", "3 à 6 mois", "Plus de 6 mois", "Contrat sans date de fin prévue", "Je ne sais pas encore"],
      q06: ["Moins de 20 heures par semaine", "20 à 34 heures par semaine", "35 heures ou plus par semaine", "Le volume peut varier selon l'activité", "Je ne sais pas encore"],
      q07: ["Des travailleurs frontaliers", "Des personnes venant d’un autre pays de l’Union européenne", "Des personnes débutantes dans le métier", "Des personnes ayant besoin de temps pour s’installer", "Des personnes ne parlant pas encore parfaitement la langue", "Je ne sais pas encore"],
      q08: ["Oui, pour le logement", "Oui, pour les démarches administratives", "Oui, pour les transports ou déplacement", "Non", "Je ne sais pas encore"],
      q09: ["Une expérience dans le métier", "Une disponibilité rapide", "Le permis de conduire", "Une expérience de travail dans le pays", "Aucun de ces éléments n'est indispensable", "La motivation pour le poste", "Je ne sais pas encore"],
      q15: ["Travail tôt le matin ou en horaire décalés", "Travail en soirée ou la nuit", "Travail le week-end ou les jours fériés", "Horaires variables", "Travail physique", "Travail debout prolongé", "Travail en extérieur", "Déplacement fréquents", "Travail en équipe", "Aucune condition particulière", "Je ne sais pas encore"]
    },
    salaryUnits: ["Par heure", "Par mois", "Par an"],
    salaryFields: {
      type: "Sous quelle forme exprimez-vous le salaire proposé ?",
      min: "Montant minimum proposé, en euros bruts ou nets",
      max: "Montant maximum proposé, en euros bruts ou nets"
    },
    sectorTitles: {
      tally_q10: "Vente et commerce",
      tally_q11: "Nettoyage et entretien",
      tally_q12: "Hôtellerie et restauration",
      tally_q13: "Agriculture et récolte",
      tally_q14: "Missions polyvalentes et emplois accessibles rapidement"
    },
    errors: {
      chooseAtLeastOne: "Sélectionnez au moins une réponse pour :",
      chooseBetween: "Sélectionnez entre 1 et 4 réponses pour :",
      maxFour: "Vous avez déjà choisi 4 éléments pour cette section."
    }
  },
  en: {
    eyebrow: "EURES employer questionnaire",
    heroTitle: "Describe a hiring need open to European mobility",
    heroLede: "This questionnaire helps us better understand your hiring need, the profiles you are looking for, the useful languages and the working conditions you offer.",
    heroHighlight: "The aim is to make your need clearer and more comparable, so that compatible profiles can be identified more easily afterwards.",
    sidebarWhyTitle: "Why this questionnaire?",
    sidebarWhyText: "It makes the hiring need easier to read: sector, volume, languages, working constraints, accepted profiles and possible relocation support.",
    sidebarAfterTitle: "What happens next?",
    sidebarAfterText: "If some profiles seem compatible, your need can be used for an introduction. Otherwise, the answers already help us structure future recruitments better.",
    sidebarResumeTitle: "Continue later",
    sidebarResumeText: "An identifier is kept so your progress can be found again if needed.",
    salaryOfferIntro: "Indicate the salary offered for this role here, in euros, and specify whether it is gross or net.",
    introNote: "This form takes 2 to 3 minutes and is intended for employers with hiring needs open to European mobility and cross-border recruitment.",
    introNote2: "We are currently working on a few priority occupations in order to test the service on concrete cases.",
    sections: {
      need: "Your hiring need",
      conditions: "Profiles, support and working conditions",
      contact: "So that we can contact you again"
    },
    questions: {
      q01: "In which sector are you currently recruiting?",
      q02: "Which languages are essential for this recruitment?",
      q02Hint: "Indicate the expected level of communication for each language.",
      q03: "How many people would you like to recruit?",
      q04: "From when do you need these recruitments?",
      q05: "What contract duration do you offer?",
      q06: "What weekly working volume do you offer?",
      q07: "Which profiles are you ready to recruit?",
      q08: "Can you help recruited people with their arrival or settlement?",
      q09: "Which of the following elements are essential for you?",
      q10: "For this sales and retail recruitment, which elements seem most important to you?",
      q11: "For this cleaning and maintenance recruitment, which elements seem most important to you?",
      q12: "For this hospitality and food service recruitment, which elements seem most important to you?",
      q13: "For this agriculture and harvesting recruitment, which elements seem most important to you?",
      q14: "For this versatile jobs and quick-access roles recruitment, which elements seem most important to you?",
      q14Hint: "You can select up to 4 options.",
      q15: "Which working conditions should recruited people be aware of?",
      q16: "First name",
      q17: "Company name",
      q18: "Email address",
      q19: "Phone",
      q20: "Work locations",
      salaryType: "How do you express the salary offered?",
      salaryMin: "Minimum amount offered, in gross or net euros",
      salaryMax: "Maximum amount offered, in gross or net euros",
      q21Title: "Data protection",
      q21Text: "The information provided will allow the EURES beta team to better understand your hiring need and the conditions offered in order to identify profiles that may match.",
      q21Text2: "If profiles compatible with your search are identified, you may be contacted again soon.",
      q21Text3: "Please remember to answer hidden or unknown calls and to check your junk mail regularly.",
      consent: "I agree that the information provided may be used by EURES teams and partners for introductions and exchanges related to recruitment. The data provided will only be used within the framework of recruitment exchanges and in accordance with European data protection rules (GDPR)."
    },
    options: {
      sectors: ["Sales and retail", "Cleaning and maintenance", "Hospitality and food service", "Agriculture and harvesting", "Versatile jobs and roles accessible quickly"],
      q02Columns: ["Not necessary", "Simple communication", "Professional communication", "Very important on a daily basis"],
      q02Rows: ["German", "English", "French", "Luxembourgish"],
      q03: ["1 person", "2 to 5 people", "More than 5 people", "I do not know yet"],
      q04: ["As soon as possible", "In the next few days", "In the next few weeks", "For a seasonal period", "I do not know yet"],
      q05: ["Less than one month", "1 to 3 months", "3 to 6 months", "More than 6 months", "Contract with no planned end date", "I do not know yet"],
      q06: ["Less than 20 hours per week", "20 to 34 hours per week", "35 hours or more per week", "The workload may vary depending on activity", "I do not know yet"],
      q07: ["Cross-border workers", "People coming from another European Union country", "People who are beginners in the profession", "People who need time to settle in", "People who do not yet speak the language perfectly", "I do not know yet"],
      q08: ["Yes, for housing", "Yes, for administrative procedures", "Yes, for transport or travel", "No", "I do not know yet"],
      q09: ["Experience in the profession", "Quick availability", "Driving licence", "Work experience in the country", "None of these elements is essential", "Motivation for the role", "I do not know yet"],
      q15: ["Early morning work or staggered hours", "Evening or night work", "Weekend or public holiday work", "Variable hours", "Physical work", "Prolonged standing work", "Outdoor work", "Frequent travel", "Teamwork", "No particular condition", "I do not know yet"]
    },
    salaryUnits: ["Per hour", "Per month", "Per year"],
    salaryFields: {
      type: "How do you express the salary offered?",
      min: "Minimum amount offered, in gross or net euros",
      max: "Maximum amount offered, in gross or net euros"
    },
    sectorTitles: {
      tally_q10: "Sales and retail",
      tally_q11: "Cleaning and maintenance",
      tally_q12: "Hospitality and food service",
      tally_q13: "Agriculture and harvesting",
      tally_q14: "Versatile jobs and roles accessible quickly"
    },
    sectorChoices: {
      tally_q10: ["Being comfortable with customers", "Being able to communicate simply with customers", "Working during busy periods", "Handling payment operations", "Working as part of a team", "Adapting to different tasks", "Keeping a sales area clean and organised", "Respecting working hours"],
      tally_q11: ["Following procedures, instructions and hygiene rules", "Maintaining a consistent level of quality", "Respecting working hours", "Working independently", "Working as part of a team", "Working at a sustained pace", "Adapting to different workplaces or environments", "Carrying out repetitive tasks", "Being able to travel easily to intervention sites"],
      tally_q12: ["Welcoming and guiding customers", "Being able to communicate simply with customers", "Working during busy periods", "Staying calm during intense periods of activity", "Working as part of a team", "Respecting working hours", "Working in the evening, on weekends or on public holidays", "Remembering orders or information", "Adapting to different tasks", "Keeping a reception or service area clean and organised"],
      tally_q13: ["Respecting schedules and harvesting periods", "Working outdoors and depending on weather conditions", "Doing physical work", "Working at a sustained pace", "Following work and safety instructions", "Using equipment or tools correctly", "Working as part of a team", "Adapting to different types of tasks", "Being able to travel easily to work sites", "Maintaining a consistent quality of work"],
      tally_q14: ["Adapting quickly to different tasks", "Respecting instructions and schedules", "Doing physical work", "Working at a sustained pace", "Working in different environments", "Joining a team quickly", "Working as part of a team", "Accepting variable schedules", "Being available quickly", "Being able to start an assignment quickly"]
    },
    errors: {
      chooseAtLeastOne: "Select at least one answer for:",
      chooseBetween: "Select between 1 and 4 answers for:",
      maxFour: "You have already selected 4 items for this section."
    }
  },
  de: {
    eyebrow: "EURES-Arbeitgeberfragebogen",
    heroTitle: "Einen Personalbedarf beschreiben, der für europäische Mobilität offen ist",
    heroLede: "Dieser Fragebogen hilft uns, Ihren Personalbedarf, die gesuchten Profile, die nützlichen Sprachen und die angebotenen Arbeitsbedingungen besser zu verstehen.",
    heroHighlight: "Ziel ist es, Ihren Bedarf klarer und besser vergleichbar zu machen, damit anschließend passende Profile leichter erkannt werden können.",
    sidebarWhyTitle: "Warum dieser Fragebogen?",
    sidebarWhyText: "Er macht den Personalbedarf besser lesbar: Bereich, Volumen, Sprachen, Arbeitsbedingungen, akzeptierte Profile und mögliche Unterstützung bei der Installation.",
    sidebarAfterTitle: "Wie geht es danach weiter?",
    sidebarAfterText: "Wenn einige Profile kompatibel erscheinen, kann Ihr Bedarf für eine Vermittlung genutzt werden. Andernfalls helfen die Antworten bereits dabei, künftige Einstellungen besser zu strukturieren.",
    sidebarResumeTitle: "Später fortsetzen",
    sidebarResumeText: "Eine Kennung wird gespeichert, damit Ihr Fortschritt bei Bedarf wiedergefunden werden kann.",
    salaryOfferIntro: "Geben Sie hier das für diesen Beruf angebotene Gehalt in Euro an und präzisieren Sie, ob es sich um einen Brutto- oder Nettobetrag handelt.",
    introNote: "Dieses Formular dauert 2 bis 3 Minuten und richtet sich an Arbeitgeber mit Personalbedarf, der für europäische Mobilität und grenzüberschreitende Rekrutierung offen ist.",
    introNote2: "Wir arbeiten derzeit an einigen prioritären Berufen, um den Dienst an konkreten Fällen zu testen.",
    sections: {
      need: "Ihr Personalbedarf",
      conditions: "Profile, Unterstützung und Arbeitsbedingungen",
      contact: "Damit wir Sie wieder kontaktieren können"
    },
    questions: {
      q01: "In welchem Bereich rekrutieren Sie derzeit?",
      q02: "Welche Sprachen sind für diese Rekrutierung zwingend erforderlich?",
      q02Hint: "Geben Sie das erwartete Kommunikationsniveau für jede Sprache an.",
      q03: "Wie viele Personen möchten Sie einstellen?",
      q04: "Ab wann benötigen Sie diese Einstellungen?",
      q05: "Welche Vertragsdauer bieten Sie an?",
      q06: "Welches wöchentliche Arbeitsvolumen bieten Sie an?",
      q07: "Welche Profile sind Sie bereit einzustellen?",
      q08: "Können Sie den eingestellten Personen bei ihrer Ankunft oder Installation helfen?",
      q09: "Welche der folgenden Elemente sind für Sie unverzichtbar?",
      q10: "Welche Elemente erscheinen Ihnen bei dieser Einstellung im Verkauf und Handel am wichtigsten?",
      q11: "Welche Elemente erscheinen Ihnen bei dieser Einstellung in Reinigung und Instandhaltung am wichtigsten?",
      q12: "Welche Elemente erscheinen Ihnen bei dieser Einstellung in Hotellerie und Gastronomie am wichtigsten?",
      q13: "Welche Elemente erscheinen Ihnen bei dieser Einstellung in Landwirtschaft und Ernte am wichtigsten?",
      q14: "Welche Elemente erscheinen Ihnen bei dieser Einstellung für vielseitige Tätigkeiten und schnell zugängliche Jobs am wichtigsten?",
      q14Hint: "Sie können bis zu 4 Antworten auswählen.",
      q15: "Welche Arbeitsbedingungen sollten die eingestellten Personen kennen?",
      q16: "Vorname",
      q17: "Unternehmensname",
      q18: "E-Mail-Adresse",
      q19: "Telefon",
      q20: "Arbeitsorte",
      salaryType: "In welcher Form geben Sie das angebotene Gehalt an?",
      salaryMin: "Angebotener Mindestbetrag in Euro brutto oder netto",
      salaryMax: "Angebotener Höchstbetrag in Euro brutto oder netto",
      q21Title: "Datenschutz",
      q21Text: "Die übermittelten Informationen ermöglichen es dem EURES-beta-Team, Ihren Personalbedarf und die angebotenen Bedingungen besser zu verstehen, um Profile zu identifizieren, die passen könnten.",
      q21Text2: "Wenn mit Ihrer Suche kompatible Profile identifiziert werden, können Sie in Kürze erneut kontaktiert werden.",
      q21Text3: "Bitte denken Sie daran, anonyme oder unbekannte Anrufe anzunehmen und regelmäßig Ihren Spam-Ordner zu prüfen.",
      consent: "Ich stimme zu, dass die übermittelten Informationen von EURES-Teams und Partnern im Rahmen von Vermittlungen und austauschbezogenen Rekrutierungen verwendet werden dürfen. Die übermittelten Daten werden nur im Rahmen des recruitmentbezogenen Austauschs und gemäß den europäischen Datenschutzvorschriften (DSGVO) verwendet."
    },
    options: {
      sectors: ["Verkauf und Handel", "Reinigung und Instandhaltung", "Hotellerie und Gastronomie", "Landwirtschaft und Ernte", "Vielseitige Tätigkeiten und Jobs mit schnellem Einstieg"],
      q02Columns: ["Nicht erforderlich", "Einfache Kommunikation", "Berufliche Kommunikation", "Im Alltag sehr wichtig"],
      q02Rows: ["Deutsch", "Englisch", "Französisch", "Luxemburgisch"],
      q03: ["1 Person", "2 bis 5 Personen", "Mehr als 5 Personen", "Ich weiß es noch nicht"],
      q04: ["So schnell wie möglich", "In den nächsten Tagen", "In den nächsten Wochen", "Für einen saisonalen Zeitraum", "Ich weiß es noch nicht"],
      q05: ["Weniger als ein Monat", "1 bis 3 Monate", "3 bis 6 Monate", "Mehr als 6 Monate", "Vertrag ohne geplantes Enddatum", "Ich weiß es noch nicht"],
      q06: ["Weniger als 20 Stunden pro Woche", "20 bis 34 Stunden pro Woche", "35 Stunden oder mehr pro Woche", "Das Arbeitsvolumen kann je nach Aktivität variieren", "Ich weiß es noch nicht"],
      q07: ["Grenzgänger", "Personen aus einem anderen Land der Europäischen Union", "Berufseinsteiger", "Personen, die Zeit für die Installation brauchen", "Personen, die die Sprache noch nicht perfekt sprechen", "Ich weiß es noch nicht"],
      q08: ["Ja, beim Wohnen", "Ja, bei administrativen Verfahren", "Ja, bei Transport oder Fahrten", "Nein", "Ich weiß es noch nicht"],
      q09: ["Berufserfahrung", "Schnelle Verfügbarkeit", "Führerschein", "Arbeitserfahrung im Land", "Keines dieser Elemente ist unverzichtbar", "Motivation für die Stelle", "Ich weiß es noch nicht"],
      q15: ["Arbeit früh am Morgen oder zu versetzten Zeiten", "Arbeit am Abend oder in der Nacht", "Arbeit am Wochenende oder an Feiertagen", "Variable Arbeitszeiten", "Körperliche Arbeit", "Längeres Stehen", "Arbeit im Freien", "Häufige Fahrten", "Teamarbeit", "Keine besonderen Bedingungen", "Ich weiß es noch nicht"]
    },
    salaryUnits: ["Pro Stunde", "Pro Monat", "Pro Jahr"],
    salaryFields: {
      type: "In welcher Form geben Sie das angebotene Gehalt an?",
      min: "Angebotener Mindestbetrag in Euro brutto oder netto",
      max: "Angebotener Höchstbetrag in Euro brutto oder netto"
    },
    sectorTitles: {
      tally_q10: "Verkauf und Handel",
      tally_q11: "Reinigung und Instandhaltung",
      tally_q12: "Hotellerie und Gastronomie",
      tally_q13: "Landwirtschaft und Ernte",
      tally_q14: "Vielseitige Tätigkeiten und Jobs mit schnellem Einstieg"
    },
    sectorChoices: {
      tally_q10: ["Sich im Umgang mit Kunden wohlfühlen", "Einfach mit Kunden kommunizieren können", "Während Stoßzeiten arbeiten", "Kassenvorgänge durchführen", "Im Team arbeiten", "Sich an verschiedene Aufgaben anpassen", "Einen Verkaufsbereich sauber und organisiert halten", "Arbeitszeiten einhalten"],
      tally_q11: ["Verfahren, Anweisungen und Hygieneregeln einhalten", "Ein gleichbleibendes Qualitätsniveau halten", "Arbeitszeiten einhalten", "Selbstständig arbeiten", "Im Team arbeiten", "In hohem Tempo arbeiten", "Sich an verschiedene Arbeitsorte oder Umgebungen anpassen", "Wiederholende Aufgaben ausführen", "Einsatzorte leicht erreichen können"],
      tally_q12: ["Kunden empfangen und orientieren", "Einfach mit Kunden kommunizieren können", "Während Stoßzeiten arbeiten", "In intensiven Phasen ruhig bleiben", "Im Team arbeiten", "Arbeitszeiten einhalten", "Abends, am Wochenende oder an Feiertagen arbeiten", "Bestellungen oder Informationen behalten", "Sich an verschiedene Aufgaben anpassen", "Einen Empfangs- oder Servicebereich sauber und organisiert halten"],
      tally_q13: ["Zeitpläne und Erntezeiten einhalten", "Im Freien und je nach Wetter arbeiten", "Körperliche Arbeit leisten", "In hohem Tempo arbeiten", "Arbeits- und Sicherheitsanweisungen einhalten", "Material oder Werkzeuge korrekt verwenden", "Im Team arbeiten", "Sich an unterschiedliche Arten von Aufgaben anpassen", "Arbeitsorte leicht erreichen können", "Eine gleichbleibende Arbeitsqualität aufrechterhalten"],
      tally_q14: ["Sich schnell an verschiedene Aufgaben anpassen", "Anweisungen und Zeitpläne einhalten", "Körperliche Arbeit leisten", "In hohem Tempo arbeiten", "In unterschiedlichen Umgebungen arbeiten", "Sich schnell in ein Team integrieren", "Im Team arbeiten", "Variable Arbeitszeiten akzeptieren", "Schnell verfügbar sein", "Schnell eine Aufgabe beginnen können"]
    },
    errors: {
      chooseAtLeastOne: "Wählen Sie mindestens eine Antwort für:",
      chooseBetween: "Wählen Sie zwischen 1 und 4 Antworten für:",
      maxFour: "Sie haben für diesen Abschnitt bereits 4 Elemente ausgewählt."
    }
  }
};

function getEmployerTallyContent(lang) {
  const content = employerTallyCopy[lang] || employerTallyCopy.fr;
  const frContent = employerTallyCopy.fr;
  return {
    ...content,
    sectorsOptions: localizeOptions(employerTallyMeta.sectors, content.options.sectors || frContent.options.sectors || employerTallyMeta.sectors),
    languageColumns: localizeOptions(
      employerTallyMeta.languageColumns,
      content.options.q02Columns || frContent.options.q02Columns || employerTallyMeta.languageColumns
    ),
    languageRows: localizeRows(
      employerTallyMeta.languageRows,
      content.options.q02Rows || frContent.options.q02Rows || employerTallyMeta.languageRows.map((row) => row.label)
    ),
    optionGroups: {
      q03: localizeOptions(frContent.options.q03, content.options.q03 || frContent.options.q03),
      q04: localizeOptions(frContent.options.q04, content.options.q04 || frContent.options.q04),
      q05: localizeOptions(frContent.options.q05, content.options.q05 || frContent.options.q05),
      q06: localizeOptions(frContent.options.q06, content.options.q06 || frContent.options.q06),
      q07: localizeOptions(frContent.options.q07, content.options.q07 || frContent.options.q07),
      q08: localizeOptions(frContent.options.q08, content.options.q08 || frContent.options.q08),
      q09: localizeOptions(frContent.options.q09, content.options.q09 || frContent.options.q09),
      q15: localizeOptions(frContent.options.q15, content.options.q15 || frContent.options.q15)
    },
    sectorPriorityOptions: Object.fromEntries(
      Object.entries(employerTallyMeta.sectorPriorityGroups).map(([key, value]) => [
        key,
        localizeOptions(value, (content.sectorChoices && content.sectorChoices[key]) || value)
      ])
    )
  };
}

function currentLang() {
  const params = new URLSearchParams(window.location.search);
  const lang = params.get("lang");
  return LANGS.includes(lang) ? lang : DEFAULT_LANG;
}

function setDocumentLang(lang) {
  document.documentElement.lang = lang;
}

function pageUrl(page, lang) {
  const map = {
    home: `${BASE_PATH}/`,
    "candidate-landing": `${BASE_PATH}/candidate`,
    "employer-landing": `${BASE_PATH}/employer`,
    stat: `${BASE_PATH}/stat`,
    "candidate-questionnaire": `${BASE_PATH}/questionnaire-candidate`,
    "employer-questionnaire": `${BASE_PATH}/questionnaire-employer`
  };
  return `${map[page]}?lang=${lang}`;
}

function nav(page, lang, t) {
  return `
    <header class="site-header">
      <div class="shell">
        <a class="brand" href="${pageUrl("home", lang)}">
          <span class="brand-copy">
            <strong>${t.common.brandTitle}</strong>
            <span>${t.common.brandSubtitle}</span>
          </span>
        </a>
        <nav class="nav" aria-label="Primary">
          <div class="nav-links">
            <a class="nav-pill" href="${pageUrl("home", lang)}">${t.common.navHome}</a>
            <a class="nav-pill" href="${pageUrl("candidate-landing", lang)}">${t.common.navCandidate}</a>
            <a class="nav-pill" href="${pageUrl("employer-landing", lang)}">${t.common.navEmployer}</a>
            <a class="nav-pill" href="${pageUrl("stat", lang)}">${t.common.navStats}</a>
          </div>
          <div class="lang-switch" aria-label="${t.common.langLabel}">
            ${LANGS.map((choice) => `
              <a class="lang-link${choice === lang ? " is-active" : ""}" href="${pageUrl(page, choice)}">${choice.toUpperCase()}</a>
            `).join("")}
          </div>
        </nav>
      </div>
    </header>
  `;
}

function footer(t) {
  return `<footer class="footer"><div class="shell">${t.common.footer}</div></footer>`;
}

function list(items) {
  return `<ul>${items.map((item) => `<li>${item}</li>`).join("")}</ul>`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatTimestamp(value, lang) {
  if (!value) return "n/a";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return escapeHtml(value);
  return new Intl.DateTimeFormat(lang, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  }).format(date);
}

function formatMonth(value, lang) {
  if (!value || !/^\d{4}-\d{2}$/.test(value)) return escapeHtml(value || "");
  const date = new Date(`${value}-01T00:00:00Z`);
  return new Intl.DateTimeFormat(lang, {
    year: "numeric",
    month: "long"
  }).format(date);
}

function renderBreakdownList(rows, emptyLabel) {
  if (!Array.isArray(rows) || rows.length === 0) {
    return `<p>${emptyLabel}</p>`;
  }
  const max = Math.max(...rows.map((row) => Number(row.count || 0)), 1);
  return `
    <div class="breakdown-list">
      ${rows.map((row) => {
        const count = Number(row.count || 0);
        const width = Math.max(8, Math.round((count / max) * 100));
        return `
          <div class="breakdown-row">
            <div class="breakdown-head">
              <span>${escapeHtml(row.label)}</span>
              <strong>${count}</strong>
            </div>
            <div class="breakdown-bar"><span style="width:${width}%"></span></div>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function statTemplate(lang, t, data) {
  const totals = data?.totals || {};
  const monthly = Array.isArray(data?.monthly) ? data.monthly : [];
  const breakdowns = data?.breakdowns || {};
  const manualConfigured = Boolean(data?.manual_stats_table?.configured);
  const totalCards = Object.entries(t.statPage.totals).map(([key, label]) => `
    <article class="stat-card kpi-card">
      <p>${label}</p>
      <strong>${Number(totals[key] || 0).toLocaleString(lang)}</strong>
    </article>
  `).join("");

  const breakdownPanels = Object.entries(t.statPage.breakdownLabels).map(([key, label]) => `
    <article class="panel breakdown-panel">
      <h2>${label}</h2>
      ${renderBreakdownList(breakdowns[key], t.statPage.emptyBreakdown)}
    </article>
  `).join("");

  return `
    ${nav("stat", lang, t)}
    <main>
      <section class="hero">
        <div class="shell hero-grid">
          <article class="hero-card hero">
            <div class="eyebrow">${t.statPage.eyebrow}</div>
            <h1>${t.statPage.title}</h1>
            <p class="lede">${t.statPage.lede}</p>
            <div class="stat-meta">
              <div><strong>${t.statPage.updatedPrefix}:</strong> ${formatTimestamp(data?.generated_at, lang)}</div>
              <div>${t.statPage.methodology}</div>
              <div>${manualConfigured ? t.statPage.manualNote : t.statPage.manualMissing}</div>
            </div>
          </article>
          <aside class="story-card">
            <h2>${t.statPage.keyFiguresTitle}</h2>
            <p>${t.statPage.monthlyLead}</p>
          </aside>
        </div>
      </section>

      <section class="section">
        <div class="shell">
          <div class="panel"><h2>${t.statPage.keyFiguresTitle}</h2></div>
          <div class="stats-grid" style="margin-top: 1rem;">
            ${totalCards}
          </div>
        </div>
      </section>

      <section class="section">
        <div class="shell">
          <div class="panel">
            <h2>${t.statPage.monthlyTitle}</h2>
            <p>${t.statPage.monthlyLead}</p>
          </div>
          <div class="table-wrap">
            <table class="stats-table">
              <thead>
                <tr>
                  ${Object.values(t.statPage.monthlyColumns).map((label) => `<th>${label}</th>`).join("")}
                </tr>
              </thead>
              <tbody>
                ${monthly.map((row) => `
                  <tr>
                    <th>${formatMonth(row.mois, lang)}</th>
                    <td>${Number(row.candidats || 0).toLocaleString(lang)}</td>
                    <td>${Number(row.besoins_employeurs || 0).toLocaleString(lang)}</td>
                    <td>${Number(row.matchings || 0).toLocaleString(lang)}</td>
                    <td>${Number(row.candidats_contactes || 0).toLocaleString(lang)}</td>
                    <td>${Number(row.candidatures_transmises_employeur || 0).toLocaleString(lang)}</td>
                    <td>${Number(row.embauches || 0).toLocaleString(lang)}</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="shell">
          <div class="panel"><h2>${t.statPage.breakdownsTitle}</h2></div>
          <div class="dashboard-grid" style="margin-top: 1rem;">
            ${breakdownPanels}
          </div>
        </div>
      </section>
    </main>
    ${footer(t)}
  `;
}

async function loadPublicStats() {
  const response = await fetch(`/api/forms/${FORM_ID}/public-stats`, {
    headers: { Accept: "application/json" }
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json();
}

function homeTemplate(lang, t) {
  return `
    ${nav("home", lang, t)}
    <main>
      <section class="hero">
        <div class="shell hero-grid">
          <article class="hero-card hero">
            <div class="eyebrow">${t.home.eyebrow}</div>
            <h1>${t.home.title}</h1>
            <p class="lede">${t.home.lede}</p>
            <div class="hero-actions">
              <a class="primary-action" href="${pageUrl("candidate-landing", lang)}">${t.common.ctaStartCandidate}</a>
              <a class="secondary-action" href="${pageUrl("employer-landing", lang)}">${t.common.ctaStartEmployer}</a>
            </div>
          </article>
          <aside class="story-card">
            <h2>${t.home.storyTitle}</h2>
            <p>${t.home.storyText}</p>
          </aside>
        </div>
      </section>

      <section class="section">
        <div class="shell stats-grid">
          ${t.home.stats.map(([value, text]) => `
            <article class="stat-card">
              <strong>${value}</strong>
              <p>${text}</p>
            </article>
          `).join("")}
        </div>
      </section>

      <section class="section">
        <div class="shell">
          <div class="panel"><h2>${t.home.tracksTitle}</h2></div>
          <div class="tracks-grid" style="margin-top: 1rem;">
            <article class="surface-card">
              <h2>${t.home.candidateTitle}</h2>
              <p>${t.home.candidateText}</p>
              <div class="hero-actions">
                <a class="primary-action" href="${pageUrl("candidate-landing", lang)}">${t.common.ctaSeeCandidate}</a>
              </div>
            </article>
            <article class="surface-card">
              <h2>${t.home.employerTitle}</h2>
              <p>${t.home.employerText}</p>
              <div class="hero-actions">
                <a class="primary-action" href="${pageUrl("employer-landing", lang)}">${t.common.ctaSeeEmployer}</a>
              </div>
            </article>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="shell principles-grid">
          ${t.home.principles.map(([title, text]) => `
            <article class="surface-card">
              <h2>${title}</h2>
              <p>${text}</p>
            </article>
          `).join("")}
        </div>
      </section>

      <section class="section">
        <div class="shell dashboard-grid">
          <article class="panel">
            <h2>${t.common.matchingTitle}</h2>
            ${list(t.common.matchingBullets)}
          </article>
          <article class="panel">
            <h2>${t.common.futureTitle}</h2>
            ${list(t.common.futureBullets)}
          </article>
        </div>
      </section>
    </main>
    ${footer(t)}
  `;
}

function landingTemplate(page, lang, t, data) {
  const questionnairePage = page === "candidate-landing" ? "candidate-questionnaire" : "employer-questionnaire";
  if (page === "candidate-landing") {
    return `
      ${nav(page, lang, t)}
      <main class="section candidate-landing-page">
        <div class="shell candidate-landing-layout">
          <article class="candidate-letter">
            <div class="candidate-logos" aria-label="Partners">
              <img src="${data.logos.eures.src}" alt="${data.logos.eures.alt}" class="logo-eures">
              <div class="candidate-badge">
                <img src="${data.logos.franceTravail.src}" alt="${data.logos.franceTravail.alt}" class="logo-france-travail">
                <span>France Travail</span>
              </div>
              <img src="${data.logos.europeanUnion.src}" alt="${data.logos.europeanUnion.alt}" class="logo-eu">
            </div>

            <div class="candidate-letter-head">
              <div class="kicker">${data.kicker}</div>
              <h1>${data.title}</h1>
              <p class="lede">${data.lede}</p>
            </div>

            <section class="candidate-message">
              <h2>${data.messageTitle}</h2>
              <p><strong>${data.messageIntro}</strong></p>
              ${data.messageBody.map((paragraph) => `<p>${paragraph}</p>`).join("")}
              <div class="candidate-highlight">${data.messageHighlight}</div>
              <div class="landing-actions">
                <a class="primary-action" href="${pageUrl(questionnairePage, lang)}">${t.common.ctaQuestionnaire}</a>
              </div>
              <p>${data.messageOutcome}</p>
              <p><strong>${data.signatureTitle}</strong><br>${data.signatureName}<br>${data.signatureRole}</p>
            </section>

            <section class="candidate-about">
              <h2>${data.sideTitle}</h2>
              <p>${data.sideText}</p>
            </section>
          </article>

          <aside class="candidate-sidebar">
            <article class="surface-card candidate-info-card">
              <h2>${data.bulletsTitle}</h2>
              ${list(data.bullets)}
              <div class="tag-row">
                ${data.tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}
              </div>
            </article>

            <article class="surface-card candidate-info-card">
              <h2>${data.disclaimerTitle}</h2>
              <p>${data.disclaimerText}</p>
            </article>

            <article class="panel candidate-info-card">
              <h2>${t.common.matchingTitle}</h2>
              ${list(t.common.matchingBullets)}
            </article>
          </aside>
        </div>
      </main>
      ${footer(t)}
    `;
  }

  return `
    ${nav(page, lang, t)}
    <main class="section">
      <div class="shell landing-grid">
        <article class="hero-card landing-card">
          <div class="kicker">${data.kicker}</div>
          <h1>${data.title}</h1>
          <p class="lede">${data.lede}</p>
          <div class="tag-row">
            ${data.tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}
          </div>
          <div class="landing-actions">
            <a class="primary-action" href="${pageUrl(questionnairePage, lang)}">${t.common.ctaQuestionnaire}</a>
            <a class="secondary-action" href="${pageUrl("home", lang)}">${t.common.ctaBackHome}</a>
          </div>
        </article>
        <div class="landing-side">
          <article class="surface-card">
            <h2>${data.bulletsTitle}</h2>
            ${list(data.bullets)}
          </article>
          <article class="surface-card">
            <h2>${data.sideTitle}</h2>
            <p>${data.sideText}</p>
          </article>
        </div>
      </div>

      <div class="shell dashboard-grid" style="margin-top: 1rem;">
        <article class="panel">
          <h2>${t.common.matchingTitle}</h2>
          ${list(t.common.matchingBullets)}
        </article>
        <article class="panel">
          <h2>${t.common.futureTitle}</h2>
          ${list(t.common.futureBullets)}
        </article>
      </div>
    </main>
    ${footer(t)}
  `;
}

function choicePills(name, options) {
  return `
    <div class="choice-grid">
      ${options.map((option) => {
        const item = typeof option === "string" ? { value: option, label: option } : option;
        return `
        <label class="checkbox-pill">
          <input type="checkbox" name="${name}" value="${item.value}">
          <span>${item.label}</span>
        </label>
      `;
      }).join("")}
    </div>
  `;
}

function radioPills(name, options) {
  return `
    <div class="choice-grid">
      ${options.map((option) => {
        const item = typeof option === "string" ? { value: option, label: option } : option;
        return `
        <label class="checkbox-pill">
          <input type="radio" name="${name}" value="${item.value}" required>
          <span>${item.label}</span>
        </label>
      `;
      }).join("")}
    </div>
  `;
}

function matrixQuestion(title, rows, columns, hint = "", inputType = "checkbox") {
  return `
    <div class="field">
      <span>${title}</span>
      ${hint ? `<p class="mini-note">${hint}</p>` : ""}
      <div class="matrix-wrap">
        <table class="matrix-table">
          <thead>
            <tr>
              <th></th>
              ${columns.map((column) => {
                const item = typeof column === "string" ? { value: column, label: column } : column;
                return `<th>${item.label}</th>`;
              }).join("")}
            </tr>
          </thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                <th>${row.label}</th>
                ${columns.map((column) => {
                  const item = typeof column === "string" ? { value: column, label: column } : column;
                  return `
                  <td>
                    <input type="${inputType}" name="${row.field}" value="${item.value}">
                  </td>
                `;
                }).join("")}
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function rankingQuestion(content) {
  return `
    <div class="field">
      <span>${content.rankingTitle}</span>
      <p class="mini-note">${content.rankingHint}</p>
      <div class="ranking-grid">
        ${content.rankingDisplayOptions.map((option, index) => `
          <label class="field rank-field">
            <span>${option}</span>
            <select name="rank__tally_q17__${index}" required>
              <option value=""></option>
              ${content.rankingDisplayOptions.map((_, rankIndex) => `
                <option value="${rankIndex + 1}">${rankIndex + 1}</option>
              `).join("")}
            </select>
          </label>
        `).join("")}
      </div>
    </div>
  `;
}

function salaryExpectationFields(baseName, content) {
  return `
    <div class="section-intro">
      <p class="mini-note">${content.salaryExpectationIntro}</p>
    </div>
    <div class="form-grid">
      <div class="field">
        <span>${content.salaryFields.type}</span>
        ${radioPills(`${baseName}_salary_type`, content.salaryUnits)}
      </div>
      <label class="field">
        <span>${content.salaryFields.min}</span>
        <input type="number" name="${baseName}_salary_min" min="0" step="0.01">
      </label>
    </div>
  `;
}

function salaryOfferFields(baseName, content) {
  return `
    <div class="section-intro">
      <p class="mini-note">${content.salaryOfferIntro}</p>
    </div>
    <div class="form-grid">
      <div class="field">
        <span>${content.salaryFields.type}</span>
        ${radioPills(`${baseName}_salary_type`, content.salaryUnits)}
      </div>
      <label class="field">
        <span>${content.salaryFields.min}</span>
        <input type="number" name="${baseName}_salary_min" min="0" step="0.01">
      </label>
      <label class="field">
        <span>${content.salaryFields.max}</span>
        <input type="number" name="${baseName}_salary_max" min="0" step="0.01">
      </label>
    </div>
  `;
}

function candidateTallyQuestionnaireTemplate(lang, t) {
  const logos = t.candidateLanding.logos;
  const content = getCandidateTallyContent(lang);
  return `
    ${nav("candidate-questionnaire", lang, t)}
    <main class="questionnaire-shell">
      <div class="shell questionnaire-grid">
        <section class="questionnaire-card candidate-letter questionnaire-letter">
          <div class="questionnaire-hero">
            <div class="candidate-logos">
              <img class="logo-eures" src="${logos.eures.src}" alt="${logos.eures.alt}">
              <div class="candidate-badge">
                <img class="logo-france-travail" src="${logos.franceTravail.src}" alt="${logos.franceTravail.alt}">
                <span>France Travail</span>
              </div>
              <img class="logo-eu" src="${logos.europeanUnion.src}" alt="${logos.europeanUnion.alt}">
            </div>
            <div class="eyebrow">${content.eyebrow}</div>
            <h1>${content.heroTitle}</h1>
            <p class="lede">${content.heroLede}</p>
            <div class="candidate-highlight">${content.heroHighlight}</div>
          </div>

          <form class="questionnaire-form" id="candidate-tally-form" data-role="candidate">
            <section class="form-section">
              <h3>${content.overviewTitle}</h3>
              ${matrixQuestion(
                content.overviewMatrixTitle,
                content.countryRows,
                content.countryColumns
              )}

              <div class="field">
                <span>${content.mobilityTypeTitle}</span>
                <p class="mini-note">${content.mobilityTypeHint}</p>
                ${choicePills("tally_q02", content.mobilityTypeOptions)}
              </div>
            </section>

            <section class="form-section" data-condition="transfrontaliere">
              <h3>${content.crossBorderTitle}</h3>
              <div class="field">
                <span>${content.questions.q03}</span>
                ${radioPills("tally_q03", localizeOptions(["Oui", "Non"], content.options.yesNo))}
              </div>
              <div class="field">
                <span>${content.questions.q04}</span>
                ${radioPills("tally_q04", localizeOptions(["30 min", "1h", "1h30", "2h", "Plus de 2h"], content.options.commute))}
              </div>
              <fieldset class="fieldset">
                <legend>${content.questions.q05}</legend>
                ${choicePills("tally_q05", localizeOptions(["Voiture", "Train", "Bus", "Covoiturage", "Je ne sais pas encore"], content.options.transport))}
              </fieldset>
              <div class="field">
                <span>${content.questions.q06}</span>
                ${radioPills("tally_q06", localizeOptions(["Je suis disponible sur des horaires variés", "J’ai des contraintes ou préférences horaires"], content.options.schedule))}
              </div>
              <div data-condition="horaire-precis">
                ${matrixQuestion(content.questions.q07, content.scheduleRows, content.scheduleColumns)}
              </div>
              <fieldset class="fieldset">
                <legend>${content.questions.q08}</legend>
                ${choicePills("tally_q08", localizeOptions(["CDI", "CDD", "Intérim", "Saisonnier", "Temps plein", "Temps partiel"], content.options.contracts))}
              </fieldset>
              <div class="field">
                <span>${content.questions.q09}</span>
                ${radioPills("tally_q09", localizeOptions(["Dès que possible", "Dans les prochains jours", "Dans les prochaines semaines", "Dans 1 à 3 mois", "Je ne sais pas encore"], content.options.startDate))}
              </div>
              ${matrixQuestion(
                content.questions.q10,
                content.documentsRows,
                content.documentsColumns,
                content.questions.q10Hint,
                "radio"
              )}
              <div class="field" data-condition="show-lu-social">
                <span>${content.questions.q11}</span>
                ${radioPills("tally_q11", localizeOptions(["Oui", "Non", "Je ne sais pas"], content.options.yesNoUnknown))}
              </div>
              <div class="field" data-condition="show-de-social">
                <span>${content.questions.q12}</span>
                ${radioPills("raw_tally_q12", localizeOptions(["Oui", "Non", "Je ne sais pas"], content.options.yesNoUnknown))}
              </div>
              <div class="field" data-condition="show-fr-social">
                <span>${content.questions.q13}</span>
                ${radioPills("raw_tally_q13", localizeOptions(["Oui", "Non", "Je ne sais pas"], content.options.yesNoUnknown))}
              </div>
            </section>

            <section class="form-section" data-condition="expatriation">
              <h3>${content.expatriationTitle}</h3>
              <div class="field">
                <span>${content.questions.q14}</span>
                ${radioPills("tally_q14", localizeOptions(["Oui", "Non"], content.options.yesNo))}
              </div>
              <div class="field">
                <span>${content.questions.q15}</span>
                ${radioPills("tally_q15", localizeOptions(["Dès que possible", "D'ici 3 mois", "Entre 3 et 6 mois", "Dans  plus de 6 mois", "Je ne sais pas"], content.options.departWhen))}
              </div>
              <div class="field">
                <span>${content.questions.q16}</span>
                ${radioPills("tally_q16", localizeOptions(["Uniquement vous", "En couple", "En famille"], content.options.departWith))}
              </div>
              ${rankingQuestion(content)}
            </section>

            <section class="form-section">
              <h3>${content.professionalTitle}</h3>
              ${matrixQuestion(content.questions.q18, content.languageRows, content.languageColumns, "", "radio")}
              <fieldset class="fieldset">
                <legend>${content.questions.q19}</legend>
                ${choicePills("tally_q19", content.sectorsOptions)}
              </fieldset>
            </section>

            <section class="form-section" data-condition="sector-vente">
              <h3>${content.sectorTitles.vente}</h3>
              <fieldset class="fieldset">
                <legend>${content.sectorLegends.vente} <span class="mini-note">${content.questions.sectorHint}</span></legend>
                ${choicePills("tally_q20", localizeOptions(candidateTallyCopy.fr.sectorChoices.vente, content.sectorChoices.vente))}
              </fieldset>
              <div class="field">
                <span>${content.questions.q21}</span>
                ${radioPills("tally_q21", localizeOptions(["Oui, plus de 2 ans", "Oui, entre 6 mois et 2 ans", "Oui, moins de 6 mois", "Non, mais je suis intéressé(e) par le secteur"], content.options.experience))}
              </div>
              ${salaryExpectationFields("tally_q20", content)}
            </section>

            <section class="form-section" data-condition="sector-nettoyage">
              <h3>${content.sectorTitles.nettoyage}</h3>
              <fieldset class="fieldset">
                <legend>${content.sectorLegends.nettoyage} <span class="mini-note">${content.questions.sectorHint}</span></legend>
                ${choicePills("tally_q22", localizeOptions(candidateTallyCopy.fr.sectorChoices.nettoyage, content.sectorChoices.nettoyage))}
              </fieldset>
              <div class="field">
                <span>${content.questions.q23}</span>
                ${radioPills("tally_q23", localizeOptions(["Oui, plus de 2 ans", "Oui, entre 6 mois et 2 ans", "Oui, moins de 6 mois", "Non, mais je suis intéressé(e) par le secteur"], content.options.experience))}
              </div>
              <div class="field">
                <span>${content.questions.q24}</span>
                ${radioPills("tally_q24", localizeOptions(["Oui", "Non", "Je peux en faire la demande rapidement", "Je ne sais pas"], content.options.backgroundCheck))}
              </div>
              ${salaryExpectationFields("tally_q22", content)}
            </section>

            <section class="form-section" data-condition="sector-hotel">
              <h3>${content.sectorTitles.hotel}</h3>
              <fieldset class="fieldset">
                <legend>${content.sectorLegends.hotel} <span class="mini-note">${content.questions.sectorHint}</span></legend>
                ${choicePills("tally_q25", localizeOptions(candidateTallyCopy.fr.sectorChoices.hotel, content.sectorChoices.hotel))}
              </fieldset>
              <div class="field">
                <span>${content.questions.q26}</span>
                ${radioPills("tally_q26", localizeOptions(["Oui, plus de 2 ans", "Oui, entre 6 mois et 2 ans", "Oui, moins de 6 mois", "Non, mais je suis intéressé(e) par le secteur"], content.options.experience))}
              </div>
              ${salaryExpectationFields("tally_q25", content)}
            </section>

            <section class="form-section" data-condition="sector-agri">
              <h3>${content.sectorTitles.agri}</h3>
              <fieldset class="fieldset">
                <legend>${content.sectorLegends.agri} <span class="mini-note">${content.questions.sectorHint}</span></legend>
                ${choicePills("tally_q27", localizeOptions(candidateTallyCopy.fr.sectorChoices.agri, content.sectorChoices.agri))}
              </fieldset>
              <div class="field">
                <span>${content.questions.q28}</span>
                ${radioPills("tally_q28", localizeOptions(["Oui, plus de 2 ans", "Oui, entre 6 mois et 2 ans", "Oui, moins de 6 mois", "Non, mais je suis intéressé(e) par le secteur"], content.options.experience))}
              </div>
              ${salaryExpectationFields("tally_q27", content)}
            </section>

            <section class="form-section" data-condition="sector-polyvalent">
              <h3>${content.sectorTitles.polyvalent}</h3>
              <fieldset class="fieldset">
                <legend>${content.sectorLegends.polyvalent} <span class="mini-note">${content.questions.sectorHint}</span></legend>
                ${choicePills("tally_q29", localizeOptions(candidateTallyCopy.fr.sectorChoices.polyvalent, content.sectorChoices.polyvalent))}
              </fieldset>
              <div class="field">
                <span>${content.questions.q30}</span>
                ${radioPills("tally_q30", localizeOptions(["Oui, plus de 2 ans", "Oui, entre 6 mois et 2 ans", "Oui, moins de 6 mois", "Non, mais je suis intéressé(e) par le secteur"], content.options.experience))}
              </div>
              ${salaryExpectationFields("tally_q29", content)}
            </section>

            <section class="form-section">
              <h3>${content.contactTitle}</h3>
              <div class="form-grid">
                <label class="field">
                  <span>${content.questions.firstName}</span>
                  <input type="text" name="tally_q31" required>
                </label>
                <label class="field">
                  <span>${content.questions.lastName}</span>
                  <input type="text" name="tally_q32" required>
                </label>
                <label class="field">
                  <span>${content.questions.email}</span>
                  <input type="email" name="tally_q33" required>
                </label>
                <label class="field">
                  <span>${content.questions.phone}</span>
                  <input type="tel" name="tally_q34">
                </label>
              </div>
              <label class="field">
                <span>${content.questions.city}</span>
                <input type="text" name="tally_q35" required>
              </label>
              <label class="field">
                <span>${content.questions.cv}</span>
                <input type="file" name="file__tally_q36" accept=".pdf,.doc,.docx,.odt">
                <p class="mini-note">${content.fileNote}</p>
              </label>
            </section>

            <section class="form-section">
              <label class="checkbox-pill consent-pill">
                <input type="checkbox" name="tally_q37" value="yes" required>
                <span>${content.consentText}</span>
              </label>
            </section>

            <div class="questionnaire-actions">
              <button class="primary-action" type="submit" id="save-btn">${t.common.submit}</button>
              <a class="ghost-action" href="${pageUrl("candidate-landing", lang)}">${t.common.ctaBackHome}</a>
            </div>
            <div class="status" id="status" aria-live="polite"></div>
          </form>
        </section>

        <aside class="candidate-sidebar">
          <section class="questionnaire-card candidate-info-card">
            <h2>${content.sidebarWhyTitle}</h2>
            <p>${content.sidebarWhyText}</p>
          </section>
          <section class="questionnaire-card candidate-info-card">
            <h2>${content.sidebarAfterTitle}</h2>
            <p>${content.sidebarAfterText}</p>
          </section>
          <section class="questionnaire-card candidate-info-card">
            <h2>${content.sidebarResumeTitle}</h2>
            <p class="mini-note">${content.sidebarResumeText}</p>
            <div class="uuid-box" id="uuid-box"></div>
          </section>
        </aside>
      </div>
    </main>
    ${footer(t)}
  `;
}

function employerLandingTemplate(lang, t) {
  const data = t.employerLanding;
  const logos = t.candidateLanding.logos;
  return `
    ${nav("employer-landing", lang, t)}
    <main class="section candidate-landing-page">
      <div class="shell candidate-landing-layout">
        <article class="candidate-letter">
          <div class="candidate-logos" aria-label="Partners">
            <img src="${logos.eures.src}" alt="${logos.eures.alt}" class="logo-eures">
            <div class="candidate-badge">
              <img src="${logos.franceTravail.src}" alt="${logos.franceTravail.alt}" class="logo-france-travail">
              <span>France Travail</span>
            </div>
            <img src="${logos.europeanUnion.src}" alt="${logos.europeanUnion.alt}" class="logo-eu">
          </div>

          <div class="candidate-letter-head">
            <div class="kicker">${data.kicker}</div>
            <h1>${data.title}</h1>
            <p class="lede">${data.lede}</p>
          </div>

          <section class="candidate-message">
            <h2>${data.messageTitle || data.bulletsTitle}</h2>
            <p><strong>${data.messageIntro || data.sideText}</strong></p>
            ${(data.messageBody || []).map((paragraph) => `<p>${paragraph}</p>`).join("")}
            ${data.messageHighlight ? `<div class="candidate-highlight">${data.messageHighlight}</div>` : ""}
            <div class="landing-actions">
              <a class="primary-action" href="${pageUrl("employer-questionnaire", lang)}">${t.common.ctaQuestionnaire}</a>
            </div>
            ${data.messageOutcome ? `<p>${data.messageOutcome}</p>` : ""}
            ${data.signatureTitle ? `<p><strong>${data.signatureTitle}</strong><br>${data.signatureName}<br>${data.signatureRole}</p>` : ""}
          </section>

          <section class="candidate-about">
            <h2>${data.sideTitle}</h2>
            <p>${data.sideText}</p>
          </section>
        </article>

        <aside class="candidate-sidebar">
          <article class="surface-card candidate-info-card">
            <h2>${data.bulletsTitle}</h2>
            ${list(data.bullets)}
            <div class="tag-row">
              ${data.tags.map((tag) => `<span class="tag">${tag}</span>`).join("")}
            </div>
          </article>

          <article class="surface-card candidate-info-card">
            <h2>${data.disclaimerTitle || t.common.futureTitle}</h2>
            <p>${data.disclaimerText || data.sideText}</p>
          </article>

          <article class="panel candidate-info-card">
            <h2>${t.common.matchingTitle}</h2>
            ${list(t.common.matchingBullets)}
          </article>
        </aside>
      </div>
    </main>
    ${footer(t)}
  `;
}

function employerTallyQuestionnaireTemplate(lang, t) {
  const logos = t.candidateLanding.logos;
  const content = getEmployerTallyContent(lang);
  return `
    ${nav("employer-questionnaire", lang, t)}
    <main class="questionnaire-shell">
      <div class="shell questionnaire-grid">
        <section class="questionnaire-card candidate-letter questionnaire-letter">
          <div class="questionnaire-hero">
            <div class="candidate-logos">
              <img class="logo-eures" src="${logos.eures.src}" alt="${logos.eures.alt}">
              <div class="candidate-badge">
                <img class="logo-france-travail" src="${logos.franceTravail.src}" alt="${logos.franceTravail.alt}">
                <span>France Travail</span>
              </div>
              <img class="logo-eu" src="${logos.europeanUnion.src}" alt="${logos.europeanUnion.alt}">
            </div>
            <div class="eyebrow">${content.eyebrow}</div>
            <h1>${content.heroTitle}</h1>
            <p class="lede">${content.heroLede}</p>
            <div class="candidate-highlight">${content.heroHighlight}</div>
          </div>

          <form class="questionnaire-form" id="employer-tally-form" data-role="employer">
            <section class="form-section">
              <h3>${content.sections.need}</h3>
              <div class="section-intro">
                <p class="mini-note">${content.introNote}</p>
                <p class="mini-note">${content.introNote2}</p>
              </div>
              <fieldset class="fieldset">
                <legend>${content.questions.q01}</legend>
                ${choicePills("tally_q01", content.sectorsOptions)}
              </fieldset>
              ${matrixQuestion(content.questions.q02, content.languageRows, content.languageColumns, content.questions.q02Hint, "radio")}
              <div class="field">
                <span>${content.questions.q03}</span>
                ${radioPills("tally_q03", content.optionGroups.q03)}
              </div>
              <div class="field">
                <span>${content.questions.q04}</span>
                ${radioPills("tally_q04", content.optionGroups.q04)}
              </div>
              <label class="field">
                <span>${content.questions.q20}</span>
                <input type="text" name="tally_q20" required>
              </label>
              <fieldset class="fieldset">
                <legend>${content.questions.q05}</legend>
                ${choicePills("tally_q05", content.optionGroups.q05)}
              </fieldset>
              <fieldset class="fieldset">
                <legend>${content.questions.q06}</legend>
                ${choicePills("tally_q06", content.optionGroups.q06)}
              </fieldset>
            </section>

            <section class="form-section">
              <h3>${content.sections.conditions}</h3>
              <div class="section-intro">
                <p class="mini-note">Décrivez ici les profils que vous pouvez accueillir, les aides éventuelles à l’arrivée et les critères qui comptent vraiment pour vous.</p>
              </div>
              <fieldset class="fieldset">
                <legend>${content.questions.q07}</legend>
                ${choicePills("tally_q07", content.optionGroups.q07)}
              </fieldset>
              <fieldset class="fieldset">
                <legend>${content.questions.q08}</legend>
                ${choicePills("tally_q08", content.optionGroups.q08)}
              </fieldset>
              <fieldset class="fieldset">
                <legend>${content.questions.q09}</legend>
                ${choicePills("tally_q09", content.optionGroups.q09)}
              </fieldset>
            </section>

            ${["tally_q10", "tally_q11", "tally_q12", "tally_q13", "tally_q14"].map((name, index) => `
              <section class="form-section" data-condition="employer-sector-${index}">
                <h3>${content.sectorTitles[name]}</h3>
                <fieldset class="fieldset">
                  <legend>${index === 4 ? content.questions.q14 : content.questions[`q${10 + index}`]} <span class="mini-note">${content.questions.q14Hint}</span></legend>
                  ${choicePills(name, content.sectorPriorityOptions[name])}
                </fieldset>
                ${salaryOfferFields(name, content)}
              </section>
            `).join("")}

            <section class="form-section">
              <fieldset class="fieldset">
                <legend>${content.questions.q15}</legend>
                ${choicePills("tally_q15", content.optionGroups.q15)}
              </fieldset>
            </section>

            <section class="form-section">
              <h3>${content.sections.contact}</h3>
              <div class="section-intro">
                <p class="mini-note">Ces informations nous permettent de vous recontacter rapidement si des profils semblent compatibles avec votre besoin.</p>
              </div>
              <div class="form-grid">
                <label class="field">
                  <span>${content.questions.q16}</span>
                  <input type="text" name="tally_q16" required>
                </label>
                <label class="field">
                  <span>${content.questions.q17}</span>
                  <input type="text" name="tally_q17" required>
                </label>
                <label class="field">
                  <span>${content.questions.q18}</span>
                  <input type="email" name="tally_q18" required>
                </label>
                <label class="field">
                  <span>${content.questions.q19}</span>
                  <input type="tel" name="tally_q19" required>
                </label>
              </div>
            </section>

            <section class="form-section">
              <h3>${content.questions.q21Title}</h3>
              <p class="mini-note">${content.questions.q21Text}</p>
              <p class="mini-note">${content.questions.q21Text2}</p>
              <p class="mini-note"><strong>${content.questions.q21Text3}</strong></p>
              <label class="checkbox-pill consent-pill">
                <input type="checkbox" name="tally_q21" value="yes" required>
                <span>${content.questions.consent}</span>
              </label>
            </section>

            <div class="questionnaire-actions">
              <button class="primary-action" type="submit" id="save-btn">${t.common.submit}</button>
              <a class="ghost-action" href="${pageUrl("employer-landing", lang)}">${t.common.ctaBackHome}</a>
            </div>
            <div class="status" id="status" aria-live="polite"></div>
          </form>
        </section>

        <aside class="candidate-sidebar">
          <section class="questionnaire-card candidate-info-card">
            <h2>${content.sidebarWhyTitle}</h2>
            <p>${content.sidebarWhyText}</p>
          </section>
          <section class="questionnaire-card candidate-info-card">
            <h2>${content.sidebarAfterTitle}</h2>
            <p>${content.sidebarAfterText}</p>
          </section>
          <section class="questionnaire-card candidate-info-card">
            <h2>${content.sidebarResumeTitle}</h2>
            <p class="mini-note">${content.sidebarResumeText}</p>
            <div class="uuid-box" id="uuid-box"></div>
          </section>
        </aside>
      </div>
    </main>
    ${footer(t)}
  `;
}

function isCheckedValue(form, name, value) {
  return Array.from(form.querySelectorAll(`input[name="${name}"]`)).some((input) => input.checked && input.value === value);
}

function toggleConditionBlocks(form) {
  const transfrontaliere = isCheckedValue(form, "tally_q02", "Transfrontalière");
  const expatriation = isCheckedValue(form, "tally_q02", "Expatriation");
  const horairePrecis = (form.querySelector('input[name="tally_q06"]:checked') || {}).value === "J’ai des contraintes ou préférences horaires";

  const q01lu = Array.from(form.querySelectorAll('input[name="tally_q01_f03"]:checked')).map((input) => input.value);
  const q01de = Array.from(form.querySelectorAll('input[name="tally_q01_f01"]:checked')).map((input) => input.value);
  const q01fr = Array.from(form.querySelectorAll('input[name="tally_q01_f02"]:checked')).map((input) => input.value);
  const selectedSectors = Array.from(form.querySelectorAll('input[name="tally_q19"]:checked')).map((input) => input.value);

  const visibility = {
    transfrontaliere,
    expatriation,
    "horaire-precis": horairePrecis,
    "show-lu-social": q01lu.includes("Je veux y travailler") && !q01lu.includes("J'y habite"),
    "show-de-social": q01de.includes("Je veux y travailler") && !q01de.includes("J'y habite"),
    "show-fr-social": q01fr.includes("Je veux y travailler") && !q01fr.includes("J'y habite"),
    "sector-vente": selectedSectors.includes(candidateTallyMeta.sectors[0]),
    "sector-nettoyage": selectedSectors.includes(candidateTallyMeta.sectors[1]),
    "sector-hotel": selectedSectors.includes(candidateTallyMeta.sectors[2]),
    "sector-agri": selectedSectors.includes(candidateTallyMeta.sectors[3]),
    "sector-polyvalent": selectedSectors.includes(candidateTallyMeta.sectors[4])
  };

  function shouldShow(element) {
    let current = element;
    while (current && current !== form) {
      if (current.dataset && current.dataset.condition && !visibility[current.dataset.condition]) {
        return false;
      }
      current = current.parentElement;
    }
    return true;
  }

  form.querySelectorAll("[data-condition]").forEach((element) => {
    const shown = shouldShow(element);
    element.hidden = !shown;
    element.setAttribute("aria-hidden", shown ? "false" : "true");
    element.querySelectorAll("input, select, textarea, button").forEach((control) => {
      if (control.id === "save-btn" || control.type === "hidden") {
        return;
      }
      control.disabled = !shown;
    });
  });
}

function humanizeCandidateRawAnswers(fields, fileMeta, rankingSummary) {
  return {
    pays_mobilite: {
      allemagne: fields.tally_q01_f01 || [],
      france: fields.tally_q01_f02 || [],
      luxembourg: fields.tally_q01_f03 || [],
      autre_pays_ue: fields.tally_q01_f04 || [],
      autre_pays_hors_ue: fields.tally_q01_f05 || []
    },
    type_mobilite: fields.tally_q02 || [],
    frontalier: {
      deja_travaille: fields.tally_q03 || "",
      trajet_max: fields.tally_q04 || "",
      transport: fields.tally_q05 || [],
      disponibilites_horaires: fields.tally_q06 || "",
      grille_horaire: {
        lundi: fields.tally_q07_f01 || [],
        mardi: fields.tally_q07_f02 || [],
        mercredi: fields.tally_q07_f03 || [],
        jeudi: fields.tally_q07_f04 || [],
        vendredi: fields.tally_q07_f05 || [],
        samedi: fields.tally_q07_f06 || [],
        dimanche: fields.tally_q07_f07 || []
      },
      contrats: fields.tally_q08 || [],
      dispo_demarrage: fields.tally_q09 || "",
      documents: {
        identite: fields.tally_q10_f01 || [],
        cv: fields.tally_q10_f02 || [],
        diplomes: fields.tally_q10_f03 || [],
        iban: fields.tally_q10_f04 || [],
        securite_sociale: fields.tally_q10_f05 || []
      },
      secu_lux: fields.tally_q11 || "",
      secu_de: fields.raw_tally_q12 || "",
      secu_fr: fields.raw_tally_q13 || ""
    },
    expatriation: {
      deja_vécu_etranger: fields.tally_q14 || "",
      quand_partir: fields.tally_q15 || "",
      partir_avec: fields.tally_q16 || "",
      priorites: rankingSummary
    },
    langues: {
      allemand: fields.tally_q18_f01 || [],
      anglais: fields.tally_q18_f02 || [],
      francais: fields.tally_q18_f03 || [],
      luxembourgeois: fields.tally_q18_f04 || []
    },
    secteurs: fields.tally_q19 || [],
    vente: {
      qualites: fields.tally_q20 || [],
      experience: fields.tally_q21 || "",
      salaire: { type: fields.tally_q20_salary_type || "", minimum: fields.tally_q20_salary_min || "", note: fields.tally_q20_salary_note || "" }
    },
    nettoyage: {
      qualites: fields.tally_q22 || [],
      experience: fields.tally_q23 || "",
      casier: fields.tally_q24 || "",
      salaire: { type: fields.tally_q22_salary_type || "", minimum: fields.tally_q22_salary_min || "", note: fields.tally_q22_salary_note || "" }
    },
    hotel_restaurant: {
      qualites: fields.tally_q25 || [],
      experience: fields.tally_q26 || "",
      salaire: { type: fields.tally_q25_salary_type || "", minimum: fields.tally_q25_salary_min || "", note: fields.tally_q25_salary_note || "" }
    },
    agriculture: {
      qualites: fields.tally_q27 || [],
      experience: fields.tally_q28 || "",
      salaire: { type: fields.tally_q27_salary_type || "", minimum: fields.tally_q27_salary_min || "", note: fields.tally_q27_salary_note || "" }
    },
    missions_polyvalentes: {
      qualites: fields.tally_q29 || [],
      experience: fields.tally_q30 || "",
      salaire: { type: fields.tally_q29_salary_type || "", minimum: fields.tally_q29_salary_min || "", note: fields.tally_q29_salary_note || "" }
    },
    contact: {
      prenom: fields.tally_q31 || "",
      nom: fields.tally_q32 || "",
      email: fields.tally_q33 || "",
      telephone: fields.tally_q34 || "",
      ville: fields.tally_q35 || ""
    },
    cv: fileMeta,
    consentement_rgpd: fields.tally_q37 || ""
  };
}

function enforceCheckboxLimit(form, groupNames, max, setStatus, message, changedInput = null) {
  groupNames.forEach((name) => {
    const inputs = Array.from(form.querySelectorAll(`input[type="checkbox"][name="${name}"]`))
      .filter((input) => !input.disabled || input.checked);

    if (!inputs.length) {
      return;
    }

    const checkedCount = inputs.filter((input) => input.checked).length;
    if (changedInput && changedInput.name === name && changedInput.checked && checkedCount > max) {
      changedInput.checked = false;
      setStatus(message, "error");
      const container = changedInput.closest(".fieldset") || changedInput.closest(".form-section");
      if (container) {
        let note = container.querySelector(".limit-note");
        if (!note) {
          note = document.createElement("p");
          note.className = "limit-note";
          container.appendChild(note);
        }
        note.textContent = message;
      }
    }

    const finalCheckedCount = inputs.filter((input) => input.checked).length;
    const limitReached = finalCheckedCount >= max;
    const container = inputs[0].closest(".fieldset") || inputs[0].closest(".form-section");
    const note = container ? container.querySelector(".limit-note") : null;
    if (note && finalCheckedCount < max) {
      note.remove();
    }
    inputs.forEach((input) => {
      if (input.checked) {
        return;
      }
      input.disabled = limitReached;
    });
  });
}

function toggleEmployerConditionBlocks(form) {
  const selectedSectors = Array.from(form.querySelectorAll('input[name="tally_q01"]:checked')).map((input) => input.value);
  const visibility = {
    "employer-sector-0": selectedSectors.includes(employerTallyMeta.sectors[0]),
    "employer-sector-1": selectedSectors.includes(employerTallyMeta.sectors[1]),
    "employer-sector-2": selectedSectors.includes(employerTallyMeta.sectors[2]),
    "employer-sector-3": selectedSectors.includes(employerTallyMeta.sectors[3]),
    "employer-sector-4": selectedSectors.includes(employerTallyMeta.sectors[4])
  };

  form.querySelectorAll("[data-condition]").forEach((element) => {
    const shown = Boolean(visibility[element.dataset.condition]);
    element.hidden = !shown;
    element.setAttribute("aria-hidden", shown ? "false" : "true");
    element.querySelectorAll("input, select, textarea, button").forEach((control) => {
      if (control.id === "save-btn" || control.type === "hidden") {
        return;
      }
      control.disabled = !shown;
    });
  });
}

function humanizeEmployerRawAnswers(fields) {
  return {
    secteur: fields.tally_q01 || [],
    langues: {
      allemand: fields.tally_q02_f01 || [],
      anglais: fields.tally_q02_f02 || [],
      francais: fields.tally_q02_f03 || [],
      luxembourgeois: fields.tally_q02_f04 || []
    },
    volume_recrutement: fields.tally_q03 || "",
    date_besoin: fields.tally_q04 || "",
    duree_contrat: fields.tally_q05 || [],
    volume_hebdomadaire: fields.tally_q06 || [],
    profils_acceptes: fields.tally_q07 || [],
    aides_installation: fields.tally_q08 || [],
    indispensables: fields.tally_q09 || [],
    priorites_vente: {
      choix: fields.tally_q10 || [],
      salaire: { type: fields.tally_q10_salary_type || "", minimum: fields.tally_q10_salary_min || "", maximum: fields.tally_q10_salary_max || "", note: fields.tally_q10_salary_note || "" }
    },
    priorites_nettoyage: {
      choix: fields.tally_q11 || [],
      salaire: { type: fields.tally_q11_salary_type || "", minimum: fields.tally_q11_salary_min || "", maximum: fields.tally_q11_salary_max || "", note: fields.tally_q11_salary_note || "" }
    },
    priorites_hotel: {
      choix: fields.tally_q12 || [],
      salaire: { type: fields.tally_q12_salary_type || "", minimum: fields.tally_q12_salary_min || "", maximum: fields.tally_q12_salary_max || "", note: fields.tally_q12_salary_note || "" }
    },
    priorites_agriculture: {
      choix: fields.tally_q13 || [],
      salaire: { type: fields.tally_q13_salary_type || "", minimum: fields.tally_q13_salary_min || "", maximum: fields.tally_q13_salary_max || "", note: fields.tally_q13_salary_note || "" }
    },
    priorites_polyvalent: {
      choix: fields.tally_q14 || [],
      salaire: { type: fields.tally_q14_salary_type || "", minimum: fields.tally_q14_salary_min || "", maximum: fields.tally_q14_salary_max || "", note: fields.tally_q14_salary_note || "" }
    },
    conditions_travail: fields.tally_q15 || [],
    contact: {
      prenom: fields.tally_q16 || "",
      entreprise: fields.tally_q17 || "",
      email: fields.tally_q18 || "",
      telephone: fields.tally_q19 || "",
      lieux_travail: fields.tally_q20 || ""
    },
    consentement_rgpd: fields.tally_q21 || ""
  };
}

function attachEmployerTallyBehavior(lang, t) {
  const form = document.getElementById("employer-tally-form");
  if (!form) {
    return;
  }
  const content = getEmployerTallyContent(lang);
  const uuid = getUuid("employer");
  const statusEl = document.getElementById("status");
  const uuidBox = document.getElementById("uuid-box");
  const saveBtn = document.getElementById("save-btn");
  uuidBox.textContent = `${t.common.uuidPrefix}: ${uuid}`;

  function setStatus(message, state = "") {
    statusEl.textContent = message;
    statusEl.dataset.state = state;
  }

  const limitedGroups = ["tally_q10", "tally_q11", "tally_q12", "tally_q13", "tally_q14"];

  function collectValues() {
    const data = new FormData(form);
    const values = {};
    for (const [key, rawValue] of data.entries()) {
      const value = String(rawValue || "").trim();
      if (!value) {
        continue;
      }
      if (values[key]) {
        if (Array.isArray(values[key])) {
          values[key].push(value);
        } else {
          values[key] = [values[key], value];
        }
      } else {
        values[key] = value;
      }
    }
    return values;
  }

  function validateCheckboxGroup(name, label, min = 1, max = Infinity) {
    const visibleInputs = Array.from(form.querySelectorAll(`input[name="${name}"]`)).filter((input) => !input.disabled);
    if (!visibleInputs.length) {
      return true;
    }
    const checkedCount = visibleInputs.filter((input) => input.checked).length;
    if (checkedCount < min) {
      setStatus(`${content.errors.chooseAtLeastOne} ${label}`, "error");
      return false;
    }
    if (checkedCount > max) {
      setStatus(`${content.errors.chooseBetween} ${label}`, "error");
      return false;
    }
    return true;
  }

  form.addEventListener("change", () => toggleEmployerConditionBlocks(form));
  form.addEventListener("input", () => toggleEmployerConditionBlocks(form));
  toggleEmployerConditionBlocks(form);
  enforceCheckboxLimit(form, limitedGroups, 4, setStatus, content.errors.maxFour);

  form.addEventListener("change", (event) => {
    toggleEmployerConditionBlocks(form);
    enforceCheckboxLimit(form, limitedGroups, 4, setStatus, content.errors.maxFour, event.target);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const validations = [
      ["tally_q01", content.questions.q01],
      ["tally_q05", content.questions.q05],
      ["tally_q06", content.questions.q06],
      ["tally_q07", content.questions.q07],
      ["tally_q08", content.questions.q08],
      ["tally_q09", content.questions.q09],
      ["tally_q10", content.questions.q10, 1, 4],
      ["tally_q11", content.questions.q11, 1, 4],
      ["tally_q12", content.questions.q12, 1, 4],
      ["tally_q13", content.questions.q13, 1, 4],
      ["tally_q14", content.questions.q14, 1, 4],
      ["tally_q15", content.questions.q15]
    ];
    for (const [name, label, min, max] of validations) {
      if (!validateCheckboxGroup(name, label, min, max)) {
        return;
      }
    }

    const normalized = collectValues();
    const rawAnswers = humanizeEmployerRawAnswers(normalized);
    const languageSummary = employerTallyMeta.languageRows
      .map((row) => `${row.label}: ${Array.isArray(normalized[row.field]) ? normalized[row.field].join(", ") : ""}`)
      .filter((line) => !line.endsWith(": "));
    const prioritySummary = [
      normalized.tally_q09 || [],
      normalized.tally_q10 || [],
      normalized.tally_q11 || [],
      normalized.tally_q12 || [],
      normalized.tally_q13 || [],
      normalized.tally_q14 || []
    ].flat();

    const fields = {
      id_tally: uuid,
      tally_form_id: employerTallyMeta.formId,
      tally_respondent_id: uuid,
      tally_submitted_at: new Date().toISOString(),
      tally_raw_json: JSON.stringify(rawAnswers),
      employeur: normalized.tally_q17 || "",
      contact: normalized.tally_q16 || "",
      pays: normalized.tally_q20 || "",
      poste: Array.isArray(normalized.tally_q01) ? normalized.tally_q01.join(" | ") : (normalized.tally_q01 || ""),
      competences_requises: prioritySummary.join(" | "),
      langues_requises: languageSummary.join(" | "),
      date_debut: normalized.tally_q04 || "",
      pays_normalise: normalized.tally_q20 || "",
      lieu_travail_normalise: normalized.tally_q20 || "",
      competences_clefs: Array.isArray(normalized.tally_q09) ? normalized.tally_q09.join(" | ") : (normalized.tally_q09 || ""),
      contraintes_travail: Array.isArray(normalized.tally_q15) ? normalized.tally_q15.join(" | ") : (normalized.tally_q15 || ""),
      profils_acceptes: Array.isArray(normalized.tally_q07) ? normalized.tally_q07.join(" | ") : (normalized.tally_q07 || ""),
      aides_installation: Array.isArray(normalized.tally_q08) ? normalized.tally_q08.join(" | ") : (normalized.tally_q08 || ""),
      flow_role: "employer",
      ui_language: lang,
      source_page: "employer-questionnaire",
      form_version: "2026-06-tally-employer-v1",
      ...Object.fromEntries(
        Object.entries(normalized).map(([key, value]) => [
          key,
          Array.isArray(value) ? value.join(" | ") : value
        ])
      )
    };

    saveBtn.disabled = true;
    setStatus(t.common.saving);

    try {
      const response = await fetch(`/api/forms/${FORM_ID}/record`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({ fields })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || `${t.common.saveErrorPrefix} (${response.status})`);
      }
      setStatus(t.common.saved, "success");
    } catch (error) {
      const message = error && error.message ? error.message : t.common.saveErrorPrefix;
      setStatus(`${t.common.saveErrorPrefix}: ${message}`, "error");
    } finally {
      saveBtn.disabled = false;
    }
  });
}

function attachCandidateTallyBehavior(lang, t) {
  const form = document.getElementById("candidate-tally-form");
  if (!form) {
    return;
  }
  const content = getCandidateTallyContent(lang);

  const uuid = getUuid("candidate");
  const statusEl = document.getElementById("status");
  const uuidBox = document.getElementById("uuid-box");
  const saveBtn = document.getElementById("save-btn");
  uuidBox.textContent = `${t.common.uuidPrefix}: ${uuid}`;

  function setStatus(message, state = "") {
    statusEl.textContent = message;
    statusEl.dataset.state = state;
  }

  const limitedGroups = ["tally_q20", "tally_q22", "tally_q25", "tally_q27", "tally_q29"];

  function collectValues() {
    const data = new FormData(form);
    const values = {};
    const files = {};

    for (const [key, rawValue] of data.entries()) {
      if (rawValue instanceof File) {
        if (!rawValue.name) {
          continue;
        }
        const meta = { name: rawValue.name, size: rawValue.size, type: rawValue.type || "" };
        files[key] = meta;
        values[key] = meta.name;
        continue;
      }

      const value = String(rawValue || "").trim();
      if (!value) {
        continue;
      }

      if (values[key]) {
        if (Array.isArray(values[key])) {
          values[key].push(value);
        } else {
          values[key] = [values[key], value];
        }
      } else {
        values[key] = value;
      }
    }

    return { values, files };
  }

  form.addEventListener("change", () => toggleConditionBlocks(form));
  form.addEventListener("input", () => toggleConditionBlocks(form));
  toggleConditionBlocks(form);
  enforceCheckboxLimit(form, limitedGroups, 4, setStatus, content.errors.maxFour);

  form.addEventListener("change", (event) => {
    toggleConditionBlocks(form);
    enforceCheckboxLimit(form, limitedGroups, 4, setStatus, content.errors.maxFour, event.target);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const { values, files } = collectValues();
    const activeRankingIndexes = candidateTallyMeta.rankingOptions
      .map((_, index) => index)
      .filter((index) => {
        const control = form.querySelector(`select[name="rank__tally_q17__${index}"]`);
        return control && !control.disabled;
      });

    let rankingSummary = [];
    if (activeRankingIndexes.length) {
      const rankSelections = activeRankingIndexes.map((index) => ({
        option: candidateTallyMeta.rankingOptions[index],
        rank: Number(values[`rank__tally_q17__${index}`] || 0)
      }));
      const seenRanks = rankSelections.map((item) => item.rank).filter(Boolean);
      const uniqueRanks = new Set(seenRanks);
      if (seenRanks.length !== activeRankingIndexes.length || uniqueRanks.size !== seenRanks.length) {
        setStatus(content.rankingError, "error");
        return;
      }

      rankingSummary = rankSelections
        .sort((a, b) => a.rank - b.rank)
        .map((item) => `${item.rank}. ${item.option}`);
    }

    const normalized = {};
    Object.entries(values).forEach(([key, value]) => {
      if (key.startsWith("rank__")) {
        return;
      }
      if (Array.isArray(value)) {
        normalized[key] = value;
      } else {
        normalized[key] = value;
      }
    });

    normalized.tally_q17 = rankingSummary.join(" > ");
    normalized.tally_q36 = files["file__tally_q36"] ? files["file__tally_q36"].name : "";

    const rawAnswers = humanizeCandidateRawAnswers(normalized, files["file__tally_q36"] || null, rankingSummary);

    const targetCountries = candidateTallyMeta.countryRows
      .filter((row) => Array.isArray(normalized[row.field]) && normalized[row.field].includes("Je veux y travailler"))
      .map((row) => row.label);

    const languageSummary = candidateTallyMeta.languageRows
      .map((row) => `${row.label}: ${Array.isArray(normalized[row.field]) ? normalized[row.field].join(", ") : ""}`)
      .filter((line) => !line.endsWith(": "));

    const skillsSummary = [
      normalized.tally_q20 || [],
      normalized.tally_q22 || [],
      normalized.tally_q25 || [],
      normalized.tally_q27 || [],
      normalized.tally_q29 || []
    ].flat();

    const fields = {
      uuid,
      id_tally: uuid,
      tally_form_id: candidateTallyMeta.formId,
      tally_respondent_id: uuid,
      tally_submitted_at: new Date().toISOString(),
      tally_raw_json: JSON.stringify(rawAnswers),
      nom: `${normalized.tally_q31 || ""} ${normalized.tally_q32 || ""}`.trim(),
      email: normalized.tally_q33 || "",
      pays: targetCountries.join(" | "),
      metier: Array.isArray(normalized.tally_q19) ? normalized.tally_q19.join(" | ") : (normalized.tally_q19 || ""),
      competences: skillsSummary.join(" | "),
      langues: languageSummary.join(" | "),
      mobilite: Array.isArray(normalized.tally_q02) ? normalized.tally_q02.join(" | ") : (normalized.tally_q02 || ""),
      disponibilite: [normalized.tally_q09 || "", ...(Array.isArray(normalized.tally_q08) ? normalized.tally_q08 : [])].filter(Boolean).join(" | "),
      form_version: "2026-06-tally-candidate-v1",
      source_page: "candidate-questionnaire",
      ui_language: lang,
      flow_role: "candidate",
      ...Object.fromEntries(
        Object.entries(normalized).map(([key, value]) => [
          key.replace(/^raw_/, ""),
          Array.isArray(value) ? value.join(" | ") : value
        ])
      )
    };

    saveBtn.disabled = true;
    setStatus(t.common.saving);

    try {
      const response = await fetch(`/api/forms/${FORM_ID}/record`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({ fields })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || `${t.common.saveErrorPrefix} (${response.status})`);
      }
      setStatus(t.common.saved, "success");
    } catch (error) {
      const message = error && error.message ? error.message : t.common.saveErrorPrefix;
      setStatus(`${t.common.saveErrorPrefix}: ${message}`, "error");
    } finally {
      saveBtn.disabled = false;
    }
  });
}

function questionnaireTemplate(page, lang, t, data) {
  const isCandidate = page === "candidate-questionnaire";
  return `
    ${nav(page, lang, t)}
    <main class="questionnaire-shell">
      <div class="shell questionnaire-grid">
        <section class="questionnaire-card">
          <div class="questionnaire-hero">
            <div class="eyebrow">${data.eyebrow}</div>
            <h1>${data.title}</h1>
            <p class="lede">${data.lede}</p>
          </div>
          <p class="mini-note">${t.common.questionnaireNote}</p>

          <form class="questionnaire-form" id="questionnaire-form" data-role="${isCandidate ? "candidate" : "employer"}">
            ${isCandidate ? `
              <section class="form-section">
                <h3>${data.sections.mobility}</h3>
                <div class="form-grid">
                  <label class="field">
                    <span>${data.fields.residenceCountry}</span>
                    <input type="text" name="candidate_residence_country" required>
                  </label>
                  <label class="field">
                    <span>${data.fields.mobilityType}</span>
                    <select name="candidate_mobility_type" required>
                      <option value=""></option>
                      ${data.options.mobilityType.map((option) => `<option value="${option}">${option}</option>`).join("")}
                    </select>
                  </label>
                </div>
                <fieldset class="fieldset">
                  <legend>${data.fields.targetCountries}</legend>
                  ${choicePills("candidate_target_countries", data.options.targetCountries)}
                </fieldset>
                <label class="field">
                  <span>${data.fields.availability}</span>
                  <select name="candidate_availability" required>
                    <option value=""></option>
                    ${data.options.availability.map((option) => `<option value="${option}">${option}</option>`).join("")}
                  </select>
                </label>
              </section>

              <section class="form-section">
                <h3>${data.sections.profile}</h3>
                <fieldset class="fieldset">
                  <legend>${data.fields.sectors}</legend>
                  ${choicePills("candidate_sectors", data.options.sectors)}
                </fieldset>
                <div class="form-grid">
                  <label class="field">
                    <span>${data.fields.experienceLevel}</span>
                    <select name="candidate_experience_level" required>
                      <option value=""></option>
                      ${data.options.experienceLevel.map((option) => `<option value="${option}">${option}</option>`).join("")}
                    </select>
                  </label>
                  <fieldset class="fieldset">
                    <legend>${data.fields.languages}</legend>
                    ${choicePills("candidate_languages", data.options.languages)}
                  </fieldset>
                </div>
              </section>

              <section class="form-section">
                <h3>${data.sections.contact}</h3>
                <div class="form-grid">
                  <label class="field">
                    <span>${data.fields.fullName}</span>
                    <input type="text" name="candidate_full_name" required>
                  </label>
                  <label class="field">
                    <span>${data.fields.email}</span>
                    <input type="email" name="email" required>
                  </label>
                  <label class="field">
                    <span>${data.fields.phone}</span>
                    <input type="tel" name="candidate_phone">
                  </label>
                  <label class="field">
                    <span>${data.fields.city}</span>
                    <input type="text" name="candidate_city" required>
                  </label>
                </div>
                <label class="field">
                  <span>${data.fields.notes}</span>
                  <textarea name="candidate_notes"></textarea>
                </label>
              </section>
            ` : `
              <section class="form-section">
                <h3>${data.sections.need}</h3>
                <div class="form-grid">
                  <label class="field">
                    <span>${data.fields.companyName}</span>
                    <input type="text" name="employer_company_name" required>
                  </label>
                  <label class="field">
                    <span>${data.fields.workLocation}</span>
                    <input type="text" name="employer_work_location" required>
                  </label>
                  <label class="field">
                    <span>${data.fields.sector}</span>
                    <select name="employer_sector" required>
                      <option value=""></option>
                      ${data.options.sector.map((option) => `<option value="${option}">${option}</option>`).join("")}
                    </select>
                  </label>
                  <label class="field">
                    <span>${data.fields.recruitCount}</span>
                    <select name="employer_recruit_count" required>
                      <option value=""></option>
                      ${data.options.recruitCount.map((option) => `<option value="${option}">${option}</option>`).join("")}
                    </select>
                  </label>
                </div>
                <label class="field">
                  <span>${data.fields.startDate}</span>
                  <input type="text" name="employer_start_date" required>
                </label>
              </section>

              <section class="form-section">
                <h3>${data.sections.conditions}</h3>
                <fieldset class="fieldset">
                  <legend>${data.fields.languagesRequired}</legend>
                  ${choicePills("employer_languages_required", data.options.languagesRequired)}
                </fieldset>
                <div class="form-grid">
                  <label class="field">
                    <span>${data.fields.contractDuration}</span>
                    <select name="employer_contract_duration" required>
                      <option value=""></option>
                      ${data.options.contractDuration.map((option) => `<option value="${option}">${option}</option>`).join("")}
                    </select>
                  </label>
                  <label class="field">
                    <span>${data.fields.weeklyHours}</span>
                    <select name="employer_weekly_hours" required>
                      <option value=""></option>
                      ${data.options.weeklyHours.map((option) => `<option value="${option}">${option}</option>`).join("")}
                    </select>
                  </label>
                </div>
                <fieldset class="fieldset">
                  <legend>${data.fields.installationSupport}</legend>
                  ${choicePills("employer_installation_support", data.options.installationSupport)}
                </fieldset>
                <fieldset class="fieldset">
                  <legend>${data.fields.criticalCriteria}</legend>
                  ${choicePills("employer_critical_criteria", data.options.criticalCriteria)}
                </fieldset>
              </section>

              <section class="form-section">
                <h3>${data.sections.contact}</h3>
                <div class="form-grid">
                  <label class="field">
                    <span>${data.fields.contactName}</span>
                    <input type="text" name="employer_contact_name" required>
                  </label>
                  <label class="field">
                    <span>${data.fields.email}</span>
                    <input type="email" name="email" required>
                  </label>
                  <label class="field">
                    <span>${data.fields.phone}</span>
                    <input type="tel" name="employer_phone">
                  </label>
                </div>
                <label class="field">
                  <span>${data.fields.notes}</span>
                  <textarea name="employer_notes"></textarea>
                </label>
              </section>
            `}

            <section class="form-section">
              <label class="checkbox-pill consent-pill">
                <input type="checkbox" name="consent_rgpd" value="yes" required>
                <span>${t.common.consent}</span>
              </label>
            </section>

            <div class="questionnaire-actions">
              <button class="primary-action" type="submit" id="save-btn">${t.common.submit}</button>
              <a class="ghost-action" href="${pageUrl(isCandidate ? "candidate-landing" : "employer-landing", lang)}">${t.common.ctaBackHome}</a>
            </div>
            <div class="status" id="status" aria-live="polite"></div>
          </form>
        </section>

        <aside class="questionnaire-card">
          <h2>${t.common.matchingTitle}</h2>
          ${list(t.common.matchingBullets)}
          <div class="uuid-box" id="uuid-box"></div>
          <div style="height: 1rem;"></div>
          <h2>${t.common.futureTitle}</h2>
          ${list(t.common.futureBullets)}
          <div style="height: 1rem;"></div>
          <p class="mini-note">${data.helper}</p>
        </aside>
      </div>
    </main>
    ${footer(t)}
  `;
}

function createUuid() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return window.crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (char) => {
    const random = Math.random() * 16 | 0;
    const value = char === "x" ? random : (random & 0x3 | 0x8);
    return value.toString(16);
  });
}

function storageKey(role) {
  return `grist-custom-forms:${FORM_ID}:${role}:uuid`;
}

function getUuid(role) {
  let uuid = localStorage.getItem(storageKey(role));
  if (!uuid) {
    uuid = createUuid();
    localStorage.setItem(storageKey(role), uuid);
  }
  return uuid;
}

function aggregateFormData(form) {
  const data = new FormData(form);
  const result = {};
  for (const [key, value] of data.entries()) {
    const clean = typeof value === "string" ? value.trim() : value;
    if (result[key]) {
      if (Array.isArray(result[key])) {
        result[key].push(clean);
      } else {
        result[key] = [result[key], clean];
      }
    } else {
      result[key] = clean;
    }
  }

  Object.keys(result).forEach((key) => {
    if (Array.isArray(result[key])) {
      result[key] = JSON.stringify(result[key]);
    }
  });

  return result;
}

function attachQuestionnaireBehavior(page, lang, t) {
  const form = document.getElementById("questionnaire-form");
  if (!form) {
    return;
  }

  const role = form.dataset.role;
  const uuid = getUuid(role);
  const statusEl = document.getElementById("status");
  const uuidBox = document.getElementById("uuid-box");
  const saveBtn = document.getElementById("save-btn");
  uuidBox.textContent = `${t.common.uuidPrefix}: ${uuid}`;

  function setStatus(message, state = "") {
    statusEl.textContent = message;
    statusEl.dataset.state = state;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const fields = aggregateFormData(form);
    fields.uuid = uuid;
    fields.flow_role = role;
    fields.ui_language = lang;
    fields.source_page = page;
    fields.submitted_at = new Date().toISOString();
    fields.form_version = "2026-06-home-landing-v1";

    saveBtn.disabled = true;
    setStatus(t.common.saving);

    try {
      const response = await fetch(`/api/forms/${FORM_ID}/record`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json"
        },
        body: JSON.stringify({ fields })
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || `${t.common.saveErrorPrefix} (${response.status})`);
      }
      setStatus(t.common.saved, "success");
    } catch (error) {
      const message = error && error.message ? error.message : t.common.saveErrorPrefix;
      setStatus(`${t.common.saveErrorPrefix}: ${message}`, "error");
    } finally {
      saveBtn.disabled = false;
    }
  });
}

function render() {
  const root = document.getElementById("app");
  const page = document.body.dataset.page;
  const lang = currentLang();
  const t = copy[lang];
  setDocumentLang(lang);

  if (page === "home") {
    root.innerHTML = homeTemplate(lang, t);
    return;
  }

  if (page === "stat") {
    root.innerHTML = `
      ${nav("stat", lang, t)}
      <main class="section">
        <div class="shell">
          <div class="panel"><p>${t.statPage.loading}</p></div>
        </div>
      </main>
      ${footer(t)}
    `;
    loadPublicStats()
      .then((data) => {
        root.innerHTML = statTemplate(lang, t, data);
      })
      .catch(() => {
        root.innerHTML = `
          ${nav("stat", lang, t)}
          <main class="section">
            <div class="shell">
              <div class="panel"><p>${t.statPage.error}</p></div>
            </div>
          </main>
          ${footer(t)}
        `;
      });
    return;
  }

  if (page === "candidate-landing") {
    root.innerHTML = landingTemplate(page, lang, t, t.candidateLanding);
    return;
  }

  if (page === "employer-landing") {
    root.innerHTML = employerLandingTemplate(lang, t);
    return;
  }

  if (page === "candidate-questionnaire") {
    root.innerHTML = candidateTallyQuestionnaireTemplate(lang, t);
    attachCandidateTallyBehavior(lang, t);
    return;
  }

  if (page === "employer-questionnaire") {
    root.innerHTML = employerTallyQuestionnaireTemplate(lang, t);
    attachEmployerTallyBehavior(lang, t);
  }
}

render();
