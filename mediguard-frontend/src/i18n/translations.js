/**
 * MediGuard UI translations — English (en) and French (fr)
 * Usage: t('key') from useLanguage() hook
 */
const translations = {
  en: {
    // ── Navigation ──────────────────────────────────────────────────────────
    nav_home:              'Home',
    nav_symptom_checker:   'Symptom Checker',
    nav_disease_library:   'Disease Library',
    nav_chat_ai:           'MediGuard AI',
    nav_facilities:        'Facilities',
    nav_trends:            'Trends Dashboard',
    nav_support:           'Support',
    nav_login:             'Login',
    nav_register:          'Register',
    nav_profile:           'Profile',
    nav_history:           'History',
    nav_logout:            'Logout',
    nav_dark_mode:         'Dark Mode',
    nav_light_mode:        'Light Mode',

    // ── Homepage ─────────────────────────────────────────────────────────────
    hero_title:            'Smart Diagnosis - Fast Care - Safe Health',
    hero_subtitle:         'AI-powered early disease detection for Bamenda, combining symptom prediction, curated medical-reference chat, disease education, and local trend monitoring.',
    hero_get_started:      'Get Started',
    hero_try_ai:           'Try MediGuard AI',
    hero_learn_more:       'Learn More',

    // ── Symptom Checker ───────────────────────────────────────────────────────
    sc_title:              'Symptom Checker',
    sc_subtitle:           'Move through the symptom zones, collect the clues that match how you feel, then launch the diagnosis scan.',
    sc_describe_hint:      'Describe symptoms in your own words',
    sc_describe_sub:       '(handles typos & local names)',
    sc_upload_photo:       'Upload a photo of your symptom',
    sc_upload_sub:         '(rash, skin lesion, eye, swelling…)',
    sc_tap_upload:         'Tap to upload photo',
    sc_search:             'Search all symptoms…',
    sc_back:               'Back',
    sc_next_zone:          'Next Zone',
    sc_skip:               'Skip',
    sc_launch:             'Launch Scan',
    sc_launch_full:        'Launch Diagnosis Scan',
    sc_scanning:           'Scanning…',
    sc_analyse:            'Analyse Image',
    sc_analysing:          'Analysing…',
    sc_add:                'Add',
    sc_personal_info:      'Personal Information (Optional — improves accuracy)',
    sc_gender:             'Gender',
    sc_male:               'male',
    sc_female:             'female',
    sc_other:              'other',
    sc_age:                'Age',
    sc_pregnant:           'Currently pregnant',
    sc_weeks:              'Weeks',
    sc_duration:           'Symptom Duration',
    sc_severity:           'Overall Severity',
    sc_fatigue_label:      'Symptoms may relate to fatigue, poor sleep, stress, or heavy activity',
    sc_awaiting:           'Awaiting input',
    sc_signal:             'Signal acquired',
    sc_good_signal:        'Good signal',
    sc_deep_scan:          'Deep scan ready',

    // ── Chat AI ───────────────────────────────────────────────────────────────
    chat_placeholder:      'Type your message here...',
    chat_image_placeholder:'Describe the symptom (optional)…',
    chat_welcome:          'Hello! I am your MediGuard AI health assistant. You can ask a health question, or describe symptoms like "fever and chills and headache" for a symptom check.',
    chat_clear:            'Clear',
    chat_new_chat:         'New Chat',
    chat_no_chats:         'No chats yet',
    chat_online:           'Online & Ready',
    chat_guest:            'Guest Mode',
    chat_info:             'MediGuard AI is for informational purposes only and does not replace professional medical advice.',
    chat_location_hint:    'Location detected — hospital directions will be personalised',
    chat_image_ready:      'Image ready — add a description or send directly',

    // ── Nearby Facilities ─────────────────────────────────────────────────────
    fac_title:             'Nearby Health Facilities – Bamenda',
    fac_subtitle:          'trusted facilities with maps, contacts, and directions',
    fac_use_location:      'Use my location',
    fac_locating:          'Locating…',
    fac_location_ready:    'Location ready',
    fac_directions:        'Directions',
    fac_open_maps:         'Google Maps',
    fac_services:          'Services Available',
    fac_location_preview:  'Location Preview',
    fac_emergency:         '24/7 Emergency',
    fac_get_directions:    'Get Directions',
    fac_location_active:   'Directions will start from your current location',

    // ── Location Banner ───────────────────────────────────────────────────────
    loc_banner_title:      'Enable location for nearby hospitals',
    loc_banner_body:       'Allow MediGuard to use your location so we can show directions to the nearest health facility from where you are.',
    loc_allow:             'Allow Location',
    loc_dismiss:           'Not now',
    loc_granted:           'Location enabled — hospital directions are now personalised.',

    // ── Prediction Results ────────────────────────────────────────────────────
    results_title:         'Diagnosis Assessment',
    results_also_known:    'Also known as:',
    results_top_match:     'Top Match',
    results_save:          'Save Diagnosis',
    results_login_save:    'Login to Save',
    results_download:      'Download PDF',
    results_new:           'New Diagnosis',
    results_discuss_ai:    'Discuss with AI',
    results_full_info:     'Full Disease Info',
    results_disclaimer:    'Medical Disclaimer',
    results_urgent:        'Seek Care Immediately',
    results_see_soon:      'See Doctor Soon',
    results_routine:       'Routine Care',

    // ── Disease Library ───────────────────────────────────────────────────────
    lib_title:             'Disease Library',
    lib_subtitle:          'Explore symptoms, causes, prevention, and treatment summaries.',
    lib_search:            'Search by name, symptom, or description...',
    lib_common_in_bamenda: 'Common in Bamenda',

    // ── General UI ───────────────────────────────────────────────────────────
    btn_learn_more:        'Learn More',
    btn_view_all:          'View all',
    btn_send:              'Send',
    btn_save:              'Save',
    btn_cancel:            'Cancel',
    btn_close:             'Close',
    disclaimer_not_diagnosis: 'This is NOT a medical diagnosis.',
    disclaimer_consult:    'Always consult a qualified healthcare professional.',

    // ── Auth ──────────────────────────────────────────────────────────────────
    auth_email:            'Email',
    auth_password:         'Password',
    auth_full_name:        'Full Name',
    auth_login_title:      'Welcome Back',
    auth_register_title:   'Create Account',
    auth_no_account:       "Don't have an account?",
    auth_have_account:     'Already have an account?',
    auth_forgot:           'Forgot password?',

    // ── Seasonal Alert Banner ─────────────────────────────────────────────────
    seasonal_alert_title:  'Health Alert — Bamenda',
    seasonal_high_risk:    'High risk this month',
    seasonal_dismiss:      'Dismiss alert',
    seasonal_tip:          'Mention related symptoms early for faster guidance.',

    // ── Voice Input ───────────────────────────────────────────────────────────
    voice_speak_now:       'Listening… speak your symptoms now',
    voice_btn_title:       'Speak your symptoms (voice input)',
    voice_btn_stop:        'Stop listening',

    // ── Child Mode (Symptom Checker & Chat) ──────────────────────────────────
    child_mode_label:      'I am checking for a child (my pikin)',
    child_mode_sub:        'Activates child health mode — paediatric dosing, EPI vaccination schedule, child danger signs.',
    child_mode_active:     'Child mode active — all guidance uses paediatric context',
    child_mode_toggle:     'Toggle child mode',

    // ── Symptom Checker extras ─────────────────────────────────────────────────
    sc_describe_sub_lang:  '(Pidgin, English, Français)',
    sc_voice_placeholder_child: '"My pikin dey hot and vomit"',
    sc_voice_placeholder:  '"my head dey pain me / fever and body ache"',
  },

  fr: {
    // ── Navigation ──────────────────────────────────────────────────────────
    nav_home:              'Accueil',
    nav_symptom_checker:   'Vérificateur de Symptômes',
    nav_disease_library:   'Bibliothèque des Maladies',
    nav_chat_ai:           'MediGuard IA',
    nav_facilities:        'Établissements',
    nav_trends:            'Tableau de Bord',
    nav_support:           'Support',
    nav_login:             'Connexion',
    nav_register:          'S\'inscrire',
    nav_profile:           'Profil',
    nav_history:           'Historique',
    nav_logout:            'Déconnexion',
    nav_dark_mode:         'Mode Sombre',
    nav_light_mode:        'Mode Clair',

    // ── Homepage ─────────────────────────────────────────────────────────────
    hero_title:            'Diagnostic Intelligent – Soins Rapides – Santé Sûre',
    hero_subtitle:         'Détection précoce des maladies par IA pour Bamenda — prédiction de symptômes, chat médical, éducation sanitaire et surveillance des tendances locales.',
    hero_get_started:      'Commencer',
    hero_try_ai:           'Essayer MediGuard IA',
    hero_learn_more:       'En Savoir Plus',

    // ── Symptom Checker ───────────────────────────────────────────────────────
    sc_title:              'Vérificateur de Symptômes',
    sc_subtitle:           'Parcourez les zones de symptômes, cochez ce que vous ressentez, puis lancez le diagnostic.',
    sc_describe_hint:      'Décrivez vos symptômes avec vos propres mots',
    sc_describe_sub:       '(tolère les fautes de frappe)',
    sc_upload_photo:       'Téléverser une photo du symptôme',
    sc_upload_sub:         '(éruption, lésion cutanée, œil, gonflement…)',
    sc_tap_upload:         'Appuyer pour téléverser',
    sc_search:             'Rechercher des symptômes…',
    sc_back:               'Retour',
    sc_next_zone:          'Zone Suivante',
    sc_skip:               'Passer',
    sc_launch:             'Lancer le Scan',
    sc_launch_full:        'Lancer le Diagnostic',
    sc_scanning:           'Analyse…',
    sc_analyse:            'Analyser l\'Image',
    sc_analysing:          'Analyse…',
    sc_add:                'Ajouter',
    sc_personal_info:      'Informations Personnelles (Optionnel — améliore la précision)',
    sc_gender:             'Sexe',
    sc_male:               'masculin',
    sc_female:             'féminin',
    sc_other:              'autre',
    sc_age:                'Âge',
    sc_pregnant:           'Actuellement enceinte',
    sc_weeks:              'Semaines',
    sc_duration:           'Durée des Symptômes',
    sc_severity:           'Gravité Générale',
    sc_fatigue_label:      'Les symptômes peuvent être liés à la fatigue, au manque de sommeil, au stress ou à une activité intense',
    sc_awaiting:           'En attente de saisie',
    sc_signal:             'Signal reçu',
    sc_good_signal:        'Bon signal',
    sc_deep_scan:          'Scan approfondi prêt',

    // ── Chat AI ───────────────────────────────────────────────────────────────
    chat_placeholder:      'Tapez votre message ici...',
    chat_image_placeholder:'Décrivez le symptôme (optionnel)…',
    chat_welcome:          'Bonjour ! Je suis votre assistant santé MediGuard IA. Posez une question de santé ou décrivez vos symptômes comme « fièvre et frissons et maux de tête » pour une vérification.',
    chat_clear:            'Effacer',
    chat_new_chat:         'Nouvelle conversation',
    chat_no_chats:         'Aucune conversation',
    chat_online:           'En ligne et prêt',
    chat_guest:            'Mode invité',
    chat_info:             'MediGuard IA est uniquement à titre informatif et ne remplace pas un avis médical professionnel.',
    chat_location_hint:    'Localisation détectée — les directions vers les hôpitaux seront personnalisées',
    chat_image_ready:      'Image prête — ajoutez une description ou envoyez directement',

    // ── Nearby Facilities ─────────────────────────────────────────────────────
    fac_title:             'Établissements de Santé Proches – Bamenda',
    fac_subtitle:          'établissements vérifiés avec cartes, contacts et directions',
    fac_use_location:      'Utiliser ma position',
    fac_locating:          'Localisation…',
    fac_location_ready:    'Position prête',
    fac_directions:        'Itinéraire',
    fac_open_maps:         'Google Maps',
    fac_services:          'Services Disponibles',
    fac_location_preview:  'Aperçu de l\'Emplacement',
    fac_emergency:         'Urgences 24h/24',
    fac_get_directions:    'Obtenir l\'Itinéraire',
    fac_location_active:   'L\'itinéraire partira de votre position actuelle',

    // ── Location Banner ───────────────────────────────────────────────────────
    loc_banner_title:      'Activer la localisation pour les hôpitaux proches',
    loc_banner_body:       'Autorisez MediGuard à utiliser votre position pour afficher les directions vers l\'établissement de santé le plus proche.',
    loc_allow:             'Autoriser la Localisation',
    loc_dismiss:           'Pas maintenant',
    loc_granted:           'Localisation activée — les directions vers les hôpitaux sont maintenant personnalisées.',

    // ── Prediction Results ────────────────────────────────────────────────────
    results_title:         'Évaluation du Diagnostic',
    results_also_known:    'Aussi connu sous :',
    results_top_match:     'Meilleure Correspondance',
    results_save:          'Enregistrer le Diagnostic',
    results_login_save:    'Connexion pour Enregistrer',
    results_download:      'Télécharger PDF',
    results_new:           'Nouveau Diagnostic',
    results_discuss_ai:    'Discuter avec l\'IA',
    results_full_info:     'Infos Complètes',
    results_disclaimer:    'Avertissement Médical',
    results_urgent:        'Consulter Immédiatement',
    results_see_soon:      'Consulter Bientôt',
    results_routine:       'Soins de Routine',

    // ── Disease Library ───────────────────────────────────────────────────────
    lib_title:             'Bibliothèque des Maladies',
    lib_subtitle:          'Explorez les symptômes, causes, prévention et traitements.',
    lib_search:            'Rechercher par nom, symptôme ou description...',
    lib_common_in_bamenda: 'Courant à Bamenda',

    // ── General UI ───────────────────────────────────────────────────────────
    btn_learn_more:        'En Savoir Plus',
    btn_view_all:          'Voir tout',
    btn_send:              'Envoyer',
    btn_save:              'Enregistrer',
    btn_cancel:            'Annuler',
    btn_close:             'Fermer',
    disclaimer_not_diagnosis: 'CECI N\'EST PAS un diagnostic médical.',
    disclaimer_consult:    'Consultez toujours un professionnel de santé qualifié.',

    // ── Auth ──────────────────────────────────────────────────────────────────
    auth_email:            'Adresse e-mail',
    auth_password:         'Mot de passe',
    auth_full_name:        'Nom Complet',
    auth_login_title:      'Bienvenue',
    auth_register_title:   'Créer un Compte',
    auth_no_account:       'Pas encore de compte ?',
    auth_have_account:     'Vous avez déjà un compte ?',
    auth_forgot:           'Mot de passe oublié ?',

    // ── Seasonal Alert Banner ─────────────────────────────────────────────────
    seasonal_alert_title:  'Alerte Santé — Bamenda',
    seasonal_high_risk:    'Risque élevé ce mois-ci',
    seasonal_dismiss:      'Fermer l\'alerte',
    seasonal_tip:          'Mentionnez les symptômes liés tôt pour une orientation plus rapide.',

    // ── Voice Input ───────────────────────────────────────────────────────────
    voice_speak_now:       'Écoute… décrivez vos symptômes maintenant',
    voice_btn_title:       'Parler vos symptômes (saisie vocale)',
    voice_btn_stop:        'Arrêter l\'écoute',

    // ── Child Mode ────────────────────────────────────────────────────────────
    child_mode_label:      'Je consulte pour un enfant',
    child_mode_sub:        'Active le mode pédiatrique — dosage enfant, calendrier EPI, signes de danger.',
    child_mode_active:     'Mode enfant actif — tous les conseils utilisent le contexte pédiatrique',
    child_mode_toggle:     'Activer/désactiver le mode enfant',

    // ── Symptom Checker extras ─────────────────────────────────────────────────
    sc_describe_sub_lang:  '(Pidgin, English, Français)',
    sc_voice_placeholder_child: '"Mon enfant a de la fièvre et vomit"',
    sc_voice_placeholder:  '"j\'ai mal à la tête / fièvre et courbatures"',
  },
};

export default translations;
