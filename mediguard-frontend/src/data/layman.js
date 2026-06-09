/**
 * Plain-language aliases for medical disease and symptom names.
 * Uses Bamenda / Cameroonian Pidgin English (CPE) local names where available,
 * so community users in Bamenda, NW Cameroon recognise the condition instantly.
 */

export const DISEASE_COMMON_NAMES = {
  // ── Infectious / Parasitic / Vector-Borne ─────────────────────────────────
  'Malaria':                       'Malaris / Fever',
  'Typhoid Fever':                 'Typhoy',
  'Cholera':                       'Bad running stomach',
  'Dysentery':                     'Running stomach / Purging',
  'Gastroenteritis':               'Running stomach / Belly bug',
  'Intestinal Worms':              'Worm for belly',
  'Scabies':                       'Craw-craw / Scratch-scratch',
  'Skin Fungal Infection':         'Ringworm / Kanda disease',
  'Ringworm':                      'Kanda disease / Ringworm',
  'Herpes Zoster':                 'Fire for skin',
  'Chickenpox':                    'Smallpox (Waterchicken)',
  'Measles':                       'Red skin / Measles',
  'Gonorrhea':                     'Fly-motto / Urinary tracking',
  'Syphilis':                      'Bad disease / The pox',
  'HIV AIDS':                      'Thin-thin sickness / Four letters',
  'Filariasis':                    'Big-foot / Elephantiasis',
  'Onchocerciasis':                'River blindness / Oncho',
  'African Trypanosomiasis':       'Sleeping sickness',
  'Schistosomiasis':               'Blood for urine / Bilharzia',
  'Leptospirosis':                 'Rat fever',
  'Brucellosis':                   'Animal fever / Undulant fever',
  'Typhus':                        'Hard fever with rash',
  'Mpox':                          'New smallpox / Monkeypox',
  'Buruli Ulcer':                  'Big flesh wound',
  'Rabies':                        'Mad dog sickness',
  'Dengue Fever':                  'Bone-breaking fever',

  // ── Respiratory / ENT ─────────────────────────────────────────────────────
  'Common Cold':                   'Cold-head / Catarrh',
  'Asthma':                        'Cough wey e dey choke person',
  'Pneumonia':                     'Cold for chest / Chest pain',
  'Sinusitis':                     'Block-nose',
  'Ear Infection':                 'Ear dey pain / Water for ear',
  'Conjunctivitis':                'Apollo',
  'Tonsillitis':                   'Throat pain / Throat swelling',
  'Whooping Cough':                'Cough wey no stop',
  'Diphtheria':                    'Throat block sickness',
  'Tuberculosis':                  'Bad cough / Cough wey e dey split blood',

  // ── Gastrointestinal / Abdominal ──────────────────────────────────────────
  'Helicobacteriosis PepticUlcer': 'Belly bite / Ulcer',
  'Appendicitis':                  'Side-pain',
  'Hemorrhoids (Piles)':           'Piles / Koko for anus',
  'Kidney Stones':                 'Stone for kidney',

  // ── Musculoskeletal / Neurological ────────────────────────────────────────
  'Stroke':                        'Paralysis / One-side die',
  'Epilepsy':                      'Falling sickness',
  'Migraine':                      'Split-head',
  'Arthritis':                     'Rheumatism / Joint pain',
  'Tetanus':                       'Jaw lock / Lockjaw',
  'Meningitis':                    'Stiff neck fever',

  // ── Non-Communicable / Chronic ────────────────────────────────────────────
  'Diabetes Mellitus':             'Sugar disease',
  'Hypertension':                  'High BP / Blood pressure',
  'Iron Deficiency Anemia':        'Lack of blood / No blood',
  'Hepatitis A':                   'Yellow eye (A)',
  'Hepatitis B':                   'Yellow eye (B)',
  'Yellow Fever':                  'Yellow eye fever',
  'Heart Failure':                 'Heart failure sickness',
  'Hypothyroidism':                'Cold body / Slow thyroid sickness',
  'Septicemia':                    'Bad blood / Blood poisoning',

  // ── Skin / Dermatological ─────────────────────────────────────────────────
  'Eczema':                        'White skin / Eczema',
  'Acne':                          'Face pimples',
  'Skin Abscess':                  'Boil / Koko for skin',
  'Cellulitis':                    'Red skin fire / Skin swelling',

  // ── Pediatric / Reproductive ──────────────────────────────────────────────
  'Mumps':                         'Koko for jaw / Jaw swelling sickness',
  'Rubella':                       'German measles / Small measles',
  'Pelvic Inflammatory Disease':   'Womb pain / Inside pain',
  'Benign Prostatic Hyperplasia':  'Old man pee problem / Prostate',
  'Sickle Cell Crisis':            'Sickle cell crisis',
  'Malnutrition':                  'Big-belly sickness / Lack of food',

  // ── Urinary ───────────────────────────────────────────────────────────────
  'Cystitis UTI':                  'Pee pain / Bladder pain',

  // ── STIs ──────────────────────────────────────────────────────────────────
  'Chlamydia':                     'Silent disease / Chlamydia',
  'Genital Herpes':                'Fire for private part',
  'Trichomoniasis':                'Discharge sickness',

  // ── Allergic / Emergency ──────────────────────────────────────────────────
  'Anaphylaxis':                   'Body react / Serious allergy',

  // ── Fungal / Oral ─────────────────────────────────────────────────────────
  'Candidiasis':                   'White tongue / Mouth thrush',

  // ── Viral ─────────────────────────────────────────────────────────────────
  'COVID-19':                      'Corona sickness / Covid',

  // ── Endocrine (local) ─────────────────────────────────────────────────────
  'Goiter':                        'Throat-swell / Koko for neck',

  // ── Musculoskeletal / Neurological (local) ────────────────────────────────
  'Sciatica':                      'Waist pain',
  'Vertigo':                       'Giddy-giddy / Eye dey turn',

  // ── Gastrointestinal (local) ──────────────────────────────────────────────
  'Gastric Reflux GERD':           'Fire for chest / Heartburn',
  'Severe Constipation':           'Hard-shitt / Belly lock',
  'Inguinal Hernia':               'Belle-burst / Hernia',

  // ── Parasitic / Worm infections (local) ───────────────────────────────────
  'Hookworm':                      'Ground worm',
  'Pinworm Infection':             'Sweet belly',

  // ── Reproductive (local) ───────────────────────────────────────────────────
  'Uterine Fibroids':              'Belle-koko',

  // ── Pediatric (local) ──────────────────────────────────────────────────────
  'Infant Colic':                  'Gripe',
};

/**
 * Plain equivalents for medical / technical symptom names.
 */
export const SYMPTOM_PLAIN_NAMES = {
  'Profuse watery diarrhea':         'Rice-water diarrhoea',
  'Bloody or mucus-filled diarrhea': 'Bloody / slimy stools',
  'Tenesmus':                        'Straining to pass stool',
  'Koplik spots':                    'White spots inside mouth',
  'Burrow tracks':                   'Skin tunnels from mites',
  'Ring-shaped rash':                'Round ring-shaped rash',
  'Pain behind eyes':                'Eye socket pain',
  'Sensitivity to light':            'Light hurts eyes (photophobia)',
  'Sensitivity to sound':            'Loud sounds cause pain',
  'Slow-healing sores':              "Wounds that won't heal",
  'Pus or discharge':                'Fluid / pus from wound or eye',
  'Hoarse voice':                    'Rough / scratchy voice',
  'Reduced urination':               'Trouble passing urine',
  'Ankle swelling':                  'Swollen ankles',
  'Skin peeling':                    'Skin flaking off',
  'Pain during intercourse':         'Pain during sex',
  'Difficulty swallowing':           'Hard to swallow',
  'Visible worms in stool':          'Worms seen in stool',
  'Anal itching':                    'Bottom / rear itching',
  'White patches in mouth':          'White sores in mouth',
  'Nasal congestion':                'Blocked nose',
  'Night sweats':                    'Heavy sweating at night',
  'Poor coordination':               'Losing balance / falling',
  'Heat intolerance':                "Can't stand heat",
  'Cold intolerance':                "Can't stand cold",
  'Fast heartbeat':                  'Racing / pounding heart',
  'Low blood pressure':              'Blood pressure too low',
  'Rapid dehydration':               'Quick / severe fluid loss',
  'Mild bleeding':                   'Minor bleeding / easy bruising',
  'Rose spots':                      'Faint pink skin spots',
  'Coughing up blood':               'Blood in cough / sputum',
  // STI-specific symptoms
  'Genital sores':                   'Sores / blisters on genitals',
  'Genital discharge':               'Unusual genital discharge / pus',
  'Morning sickness':                'Pregnancy nausea / vomiting',
  'Reduced fetal movement':          'Baby moving less than usual',
  'Leaking fluid':                   'Fluid leaking from vagina',
  'Face swelling':                   'Swollen face',
  'Hand swelling':                   'Swollen hands',
  'Vision changes':                  'Seeing spots / blurred vision',
};

/**
 * Returns the common name if one exists, or null.
 * @param {string} name - official disease name
 */
export function getCommonName(name) {
  return DISEASE_COMMON_NAMES[name] || null;
}

/**
 * Returns a display label: "Official Name" or "Official Name (Common Name)".
 * @param {string} name
 */
export function diseaseLabel(name) {
  const common = DISEASE_COMMON_NAMES[name];
  return common ? `${name} (${common})` : name;
}

/**
 * Returns the plain-language symptom name, or the original if no alias.
 * @param {string} symptom
 */
export function symptomLabel(symptom) {
  return SYMPTOM_PLAIN_NAMES[symptom] || symptom;
}
