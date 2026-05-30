/**
 * Plain-language aliases for medical disease and symptom names.
 * Used everywhere a clinical term would confuse a community user.
 */

export const DISEASE_COMMON_NAMES = {
  // Complex / Latin disease names
  'Helicobacteriosis PepticUlcer': 'Stomach Ulcer',
  'Onchocerciasis':                'River Blindness',
  'Filariasis':                    'Elephantiasis',
  'Cystitis UTI':                  'Bladder / Urinary Infection',
  'HIV AIDS':                      'HIV/AIDS',
  'Benign Prostatic Hyperplasia':  'Enlarged Prostate',
  'Septicemia':                    'Blood Poisoning',
  'Herpes Zoster':                 'Shingles',
  'Leptospirosis':                 "Weil's Disease",
  'Brucellosis':                   'Undulant Fever',
  'Iron Deficiency Anemia':        'Low Blood / Anaemia',
  'Pelvic Inflammatory Disease':   'Pelvic Infection (PID)',
  'Sickle Cell Crisis':            'Sickle Cell Disease Crisis',
  'Whooping Cough':                'Pertussis',
  'Diabetes Mellitus':             'Diabetes / High Blood Sugar',
  'Hypertension':                  'High Blood Pressure',
  'Dengue Fever':                  'Breakbone Fever',
  'Conjunctivitis':                'Pink Eye',
  'Appendicitis':                  'Inflamed Appendix',
  'Typhus':                        'Rickettsial Fever',
  'Gastroenteritis':               'Stomach Bug / Food Poisoning',
  'Anaphylaxis':                   'Severe Allergic Reaction',
  'Diphtheria':                    'Throat Membrane Infection',
  'Rubella':                       'German Measles',
  'Mumps':                         'Swollen Jaw Glands',
  'Tonsillitis':                   'Inflamed Tonsils',
  'Sinusitis':                     'Sinus Infection',
  'Ringworm':                      'Fungal Ring Rash',
  'Dysentery':                     'Bloody Diarrhoea',
  'Skin Abscess':                  'Skin Boil',
  'Skin Fungal Infection':         'Fungal Skin Rash',
  'Ear Infection':                 'Middle Ear Infection',
  'Kidney Stones':                 'Kidney Gravel',
  'Meningitis':                    'Brain Lining Infection',
  'Typhoid Fever':                 'Enteric Fever',
  'Yellow Fever':                  'Yellow Jack',
  'Epilepsy':                      'Seizure Disorder',
  'Migraine':                      'Severe One-Sided Headache',
  // STIs
  'Gonorrhea':                     'The Clap / Gonorrhoea',
  'Syphilis':                      'The Pox / Syphilis',
  'Chlamydia':                     'Silent STI / Chlamydia',
  'Genital Herpes':                'HSV-2 / Herpes',
  'Trichomoniasis':                'Trich / Parasitic STI',
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
