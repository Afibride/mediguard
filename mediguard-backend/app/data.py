import json
import re
from pathlib import Path


CORE_SYMPTOMS = {
    # ── Original 20 diseases ──────────────────────────────────────────────────
    "Malaria": ["Fever", "Chills", "Sweating", "Headache", "Nausea", "Vomiting", "Muscle aches", "Fatigue"],
    "Typhoid Fever": ["Prolonged fever", "Headache", "Weakness", "Abdominal pain", "Constipation", "Diarrhea", "Rose spots"],
    "Cholera": ["Profuse watery diarrhea", "Vomiting", "Muscle cramps", "Rapid dehydration", "Low blood pressure"],
    "Pneumonia": ["Cough", "Fever", "Chest pain", "Shortness of breath", "Fatigue", "Chills"],
    "Tuberculosis": ["Chronic cough", "Chest pain", "Coughing up blood", "Fatigue", "Night sweats", "Weight loss"],
    "Meningitis": ["Sudden high fever", "Stiff neck", "Severe headache", "Nausea", "Confusion", "Sensitivity to light"],
    "Dengue Fever": ["High fever", "Severe headache", "Pain behind eyes", "Joint pain", "Muscle aches", "Rash", "Mild bleeding"],
    "Dysentery": ["Bloody or mucus-filled diarrhea", "Abdominal pain", "Fever", "Tenesmus", "Dehydration"],
    "Gastroenteritis": ["Diarrhea", "Vomiting", "Abdominal pain", "Nausea", "Fever", "Weakness"],
    "Asthma": ["Wheezing", "Shortness of breath", "Chest tightness", "Cough"],
    "Chickenpox": ["Fever", "Itchy rash", "Blisters", "Fatigue", "Loss of appetite"],
    "Measles": ["High fever", "Cough", "Runny nose", "Red eyes", "Koplik spots", "Rash"],
    "Scabies": ["Severe itching", "Burrow tracks", "Rash", "Skin sores", "Night itching"],
    "Diabetes Mellitus": ["Increased thirst", "Frequent urination", "Fatigue", "Blurred vision", "Slow-healing sores"],
    "Hypertension": ["Headache", "Dizziness", "Blurred vision", "Chest pain", "Shortness of breath"],
    "Iron Deficiency Anemia": ["Fatigue", "Pale skin", "Dizziness", "Shortness of breath", "Fast heartbeat"],
    "Cystitis UTI": ["Frequent urination", "Painful urination", "Pelvic pain", "Blood in urine", "Lower abdominal pain"],
    "Helicobacteriosis PepticUlcer": ["Burning stomach pain", "Nausea", "Bloating", "Heartburn", "Loss of appetite"],
    "Common Cold": ["Runny nose", "Sore throat", "Cough", "Sneezing", "Mild fever", "Headache"],
    "Skin Fungal Infection": ["Itchy skin", "Ring-shaped rash", "Red scaly skin", "Skin peeling", "Skin lesions"],
    # ── New 30 diseases (21-50) ────────────────────────────────────────────────
    "Hepatitis A": ["Jaundice", "Fatigue", "Nausea", "Vomiting", "Abdominal pain", "Dark urine", "Loss of appetite", "Fever"],
    "Hepatitis B": ["Jaundice", "Dark urine", "Fatigue", "Yellow eyes", "Abdominal pain", "Joint pain", "Loss of appetite", "Nausea"],
    "Yellow Fever": ["High fever", "Jaundice", "Muscle aches", "Severe headache", "Nausea", "Vomiting", "Back pain", "Yellow eyes"],
    "Whooping Cough": ["Paroxysmal cough", "Runny nose", "Fever", "Sneezing", "Vomiting", "Fatigue", "Weakness"],
    "Mumps": ["Parotid swelling", "Jaw stiffness", "Fever", "Headache", "Muscle aches", "Fatigue", "Loss of appetite"],
    "Rubella": ["Mild fever", "Rash", "Swollen lymph nodes", "Red eyes", "Runny nose", "Joint pain", "Headache"],
    "Sinusitis": ["Headache", "Nasal congestion", "Facial pain", "Runny nose", "Cough", "Sore throat", "Fever"],
    "Tonsillitis": ["Sore throat", "Difficulty swallowing", "Swollen lymph nodes", "High fever", "Headache", "Fatigue", "Loss of appetite"],
    "Ear Infection": ["Ear pain", "Fever", "Hearing loss", "Headache", "Dizziness", "Fatigue", "Pus or discharge"],
    "Conjunctivitis": ["Red eyes", "Eye discharge", "Eye itching", "Eye pain", "Sensitivity to light", "Headache"],
    "Herpes Zoster": ["Blisters", "Rash", "Itchy rash", "Fever", "Fatigue", "Headache", "Sensitivity to light", "Skin sores"],
    "Appendicitis": ["Abdominal pain", "Fever", "Nausea", "Vomiting", "Loss of appetite", "Weakness", "Constipation"],
    "Kidney Stones": ["Back pain", "Blood in urine", "Painful urination", "Nausea", "Vomiting", "Frequent urination", "Lower abdominal pain"],
    "Sickle Cell Crisis": ["Joint pain", "Fatigue", "Pale skin", "Chest pain", "Shortness of breath", "Jaundice", "Swollen feet"],
    "Tetanus": ["Jaw stiffness", "Stiff neck", "Muscle cramps", "Fever", "Headache", "Difficulty swallowing", "Sweating"],
    "Diphtheria": ["Sore throat", "Hoarse voice", "Difficulty swallowing", "Fever", "Swollen lymph nodes", "Fatigue", "Runny nose"],
    "Ringworm": ["Ring-shaped rash", "Itchy skin", "Red scaly skin", "Skin peeling", "Skin lesions", "Hair loss"],
    "Leptospirosis": ["High fever", "Muscle aches", "Headache", "Red eyes", "Jaundice", "Vomiting", "Rash", "Dark urine"],
    "Typhus": ["Sudden high fever", "Severe headache", "Rash", "Muscle aches", "Fatigue", "Confusion", "Chills"],
    "Brucellosis": ["Fever", "Sweating", "Joint pain", "Muscle aches", "Fatigue", "Loss of appetite", "Back pain", "Night sweats"],
    "Septicemia": ["High fever", "Confusion", "Fast heartbeat", "Shortness of breath", "Low blood pressure", "Chills", "Sweating"],
    "Pelvic Inflammatory Disease": ["Pelvic pain", "Vaginal discharge", "Lower abdominal pain", "Fever", "Painful urination", "Pain during intercourse"],
    "Benign Prostatic Hyperplasia": ["Frequent urination", "Reduced urination", "Sleep disturbances", "Lower abdominal pain", "Weakness", "Back pain"],
    "Migraine": ["Severe headache", "Sensitivity to light", "Sensitivity to sound", "Nausea", "Vomiting", "Blurred vision", "Dizziness"],
    "Epilepsy": ["Seizures", "Confusion", "Confusion at night", "Muscle cramps", "Fatigue", "Weakness", "Poor coordination"],
    "Onchocerciasis": ["Severe itching", "Skin lesions", "Blurred vision", "Rash", "Skin peeling", "Swollen lymph nodes", "Weight loss"],
    "Filariasis": ["Swollen feet", "Ankle swelling", "Skin lesions", "Fever", "Skin sores", "Weakness", "Itchy skin"],
    "HIV AIDS": ["Fatigue", "Weight loss", "Night sweats", "Swollen lymph nodes", "Diarrhea", "Fever", "Rash", "Loss of appetite", "Cough", "Sore throat"],
    "Skin Abscess": ["Skin sores", "Pus or discharge", "Rash", "Fever", "Fatigue", "Swollen lymph nodes"],
    "Anaphylaxis": ["Rash", "Shortness of breath", "Fast heartbeat", "Dizziness", "Low blood pressure", "Nausea", "Face swelling", "Sweating"],
    # ── STIs ──────────────────────────────────────────────────────────────────
    "Gonorrhea": ["Genital discharge", "Painful urination", "Pelvic pain", "Vaginal discharge", "Vaginal itching", "Sore throat", "Swollen lymph nodes", "Fever"],
    "Syphilis": ["Genital sores", "Rash", "Swollen lymph nodes", "Fever", "Fatigue", "Headache", "Muscle aches", "Skin sores"],
    "Chlamydia": ["Genital discharge", "Painful urination", "Pelvic pain", "Vaginal discharge", "Pain during intercourse", "Vaginal itching", "Lower abdominal pain"],
    "Genital Herpes": ["Genital sores", "Blisters", "Painful urination", "Fever", "Fatigue", "Muscle aches", "Vaginal itching", "Skin sores"],
    "Trichomoniasis": ["Vaginal itching", "Genital discharge", "Painful urination", "Vaginal discharge", "Pelvic pain", "Rash", "Lower abdominal pain"],
    # ── Colorectal / Anorectal ────────────────────────────────────────────────
    "Hemorrhoids (Piles)": ["Rectal bleeding", "Anal pain", "Anal itching", "Swelling near anus", "Pain during bowel movement", "Constipation", "Mucus discharge from anus"],
    # ── Parasitic / Worm infections ───────────────────────────────────────────
    "Intestinal Worms": ["Anal itching", "Abdominal pain", "Diarrhea", "Loss of appetite", "Weight loss", "Fatigue", "Nausea", "Visible worms in stool"],
    # ── Nutritional ───────────────────────────────────────────────────────────
    "Malnutrition": ["Weight loss", "Fatigue", "Pale skin", "Weakness", "Swollen feet", "Hair loss", "Poor wound healing", "Loss of appetite"],
    # ── Dental / Oral ─────────────────────────────────────────────────────────
    "Dental Abscess": ["Tooth pain", "Jaw swelling", "Swollen lymph nodes", "Fever", "Facial pain", "Difficulty swallowing", "Pus or discharge"],
    # ── Musculoskeletal ───────────────────────────────────────────────────────
    "Arthritis": ["Joint pain", "Joint swelling", "Stiffness", "Weakness", "Fatigue", "Reduced range of motion"],
    # ── Skin ──────────────────────────────────────────────────────────────────
    "Eczema": ["Itchy skin", "Dry skin", "Skin peeling", "Red scaly skin", "Skin sores", "Rash"],
    "Acne": ["Skin sores", "Pus or discharge", "Rash", "Facial pain", "Skin lesions"],
    # ── Tropical / Endemic (Cameroon) ─────────────────────────────────────────
    "Schistosomiasis": ["Blood in urine", "Abdominal pain", "Diarrhea", "Fatigue", "Fever", "Itchy skin", "Rash", "Abdominal swelling", "Blood in stool", "Weight loss"],
    "Mpox": ["Fever", "Rash", "Swollen lymph nodes", "Headache", "Muscle aches", "Fatigue", "Blisters", "Skin sores", "Back pain", "Pustular rash"],
    "African Trypanosomiasis": ["Fever", "Headache", "Swollen lymph nodes", "Fatigue", "Muscle aches", "Confusion", "Excessive sleepiness", "Rash", "Joint pain", "Night sweats"],
    "Rabies": ["Fever", "Headache", "Fatigue", "Muscle aches", "Agitation", "Hydrophobia", "Confusion", "Muscle cramps", "Sweating", "Difficulty swallowing"],
    "Buruli Ulcer": ["Skin sores", "Skin lesions", "Swelling near skin area", "Fatigue", "Weakness", "Skin peeling"],
    # ── Fungal / Opportunistic ────────────────────────────────────────────────
    "Candidiasis": ["White patches in mouth", "Vaginal discharge", "Vaginal itching", "Fatigue", "Itchy skin", "Sore throat", "Loss of appetite"],
    # ── Bacterial / Skin ─────────────────────────────────────────────────────
    "Cellulitis": ["Skin redness", "Skin warmth", "Skin sores", "Fever", "Swollen lymph nodes", "Fatigue", "Skin lesions"],
    # ── Cardiovascular / Neurological ────────────────────────────────────────
    "Stroke": ["Severe headache", "Confusion", "Dizziness", "Blurred vision", "Nausea", "Vomiting", "Weakness", "Speech difficulty", "Facial drooping", "Loss of balance"],
    "Heart Failure": ["Shortness of breath", "Ankle swelling", "Fatigue", "Fast heartbeat", "Cough", "Dizziness", "Chest pain", "Weakness", "Night sweats"],
    # ── Endocrine ─────────────────────────────────────────────────────────────
    "Hypothyroidism": ["Fatigue", "Weight gain", "Cold intolerance", "Constipation", "Dry skin", "Hair loss", "Muscle aches", "Dizziness", "Sleep disturbances", "Weakness"],
    # ── Global Respiratory ────────────────────────────────────────────────────
    "COVID-19": ["Fever", "Cough", "Shortness of breath", "Fatigue", "Muscle aches", "Headache", "Loss of taste", "Loss of smell", "Diarrhea", "Sore throat"],
}

# ─── Cardinal (Key) Symptoms ─────────────────────────────────────────────────
# For diseases listed here, AT LEAST ONE cardinal symptom MUST be present in
# the user's reported symptoms before the disease can appear in results.
#
# These are near-pathognomonic features that strongly distinguish a disease.
# Without them, symptom overlap with other conditions is too non-specific to
# justify suggesting the disease.
#
# Diseases NOT listed here (e.g. Malaria, Typhoid, Pneumonia) have no strict
# cardinal requirement — they can be suggested on overlapping symptoms alone.
CARDINAL_SYMPTOMS: dict[str, list[str]] = {
    # ── Neurological / Musculoskeletal ─────────────────────────────────────
    # Lockjaw is pathognomonic for tetanus — fever alone never suggests it
    "Tetanus": ["Jaw stiffness"],
    # Neck rigidity is the cardinal sign of meningitis
    "Meningitis": ["Stiff neck"],
    # Cannot diagnose epilepsy without actual seizures
    "Epilepsy": ["Seizures"],
    # Must have recurrent severe unilateral headache
    "Migraine": ["Severe headache"],

    # ── Respiratory ────────────────────────────────────────────────────────
    # Chronic cough (>3 weeks) is required for TB; common cold doesn't suggest TB
    "Tuberculosis": ["Chronic cough"],
    # Must have the airway wheeze or tight chest
    "Asthma": ["Wheezing", "Chest tightness"],

    # ── Gastrointestinal / Diarrhoeal ──────────────────────────────────────
    # Rice-water profuse diarrhoea is cardinal — ordinary diarrhoea ≠ cholera
    "Cholera": ["Profuse watery diarrhea"],
    # Bloody/mucus stool is cardinal — plain diarrhoea ≠ dysentery
    "Dysentery": ["Bloody or mucus-filled diarrhea"],
    # Abdominal pain must be present for appendicitis
    "Appendicitis": ["Abdominal pain"],

    # ── Skin / Rash ────────────────────────────────────────────────────────
    # Must have characteristic itchy vesicular rash
    "Chickenpox": ["Itchy rash", "Blisters"],
    # Rash is essential for measles diagnosis
    "Measles": ["Rash"],
    # Intense, relentless itching is the hallmark of scabies
    "Scabies": ["Severe itching"],
    # Circular expanding ring rash is defining for ringworm
    "Ringworm": ["Ring-shaped rash"],
    # One-sided blistering stripe rash is cardinal for shingles
    "Herpes Zoster": ["Blisters", "Rash"],
    # Must have fungal skin signs
    "Skin Fungal Infection": ["Itchy skin", "Ring-shaped rash", "Red scaly skin"],

    # ── Eye ────────────────────────────────────────────────────────────────
    # Eye redness or discharge is required — fever alone ≠ conjunctivitis
    "Conjunctivitis": ["Red eyes", "Eye discharge"],

    # ── Metabolic / Chronic ────────────────────────────────────────────────
    # Polyuria and polydipsia are required for diabetes screening
    "Diabetes Mellitus": ["Increased thirst", "Frequent urination"],

    # ── Liver / Jaundice ───────────────────────────────────────────────────
    "Hepatitis A": ["Jaundice", "Dark urine"],
    "Hepatitis B": ["Jaundice", "Yellow eyes", "Dark urine"],
    # The disease is named for jaundice — it's definitional
    "Yellow Fever": ["Jaundice", "Yellow eyes"],

    # ── Tropical / Parasitic ───────────────────────────────────────────────
    # Intense whole-body itching is the defining feature of river blindness
    "Onchocerciasis": ["Severe itching"],
    # Lymphoedema (grossly swollen limbs) is cardinal for filariasis
    "Filariasis": ["Swollen feet"],

    # ── Urinary / Reproductive ─────────────────────────────────────────────
    # UTI must have urinary tract symptoms
    "Cystitis UTI": ["Painful urination", "Frequent urination"],
    # Renal colic (severe flank/back pain) is cardinal for kidney stones
    "Kidney Stones": ["Back pain"],
    # Must have pelvic pain for PID
    "Pelvic Inflammatory Disease": ["Pelvic pain"],

    # ── Throat ─────────────────────────────────────────────────────────────
    # Sore throat is the defining symptom of tonsillitis
    "Tonsillitis": ["Sore throat"],
    # Diphtheria must present with throat symptoms
    "Diphtheria": ["Sore throat", "Hoarse voice", "Difficulty swallowing"],
    # Mumps must have parotid swelling signs
    "Mumps": ["Parotid swelling"],

    # ── STIs ───────────────────────────────────────────────────────────────
    # Without genital discharge, gonorrhea should not appear in results
    "Gonorrhea": ["Genital discharge"],
    # Painless genital sore (chancre) is the primary-stage cardinal sign
    "Syphilis": ["Genital sores"],
    # Chlamydia: at least one genital/urinary symptom required
    "Chlamydia": ["Genital discharge", "Vaginal discharge", "Painful urination", "Pelvic pain"],
    # Painful clustered genital blisters/sores are cardinal for genital herpes
    "Genital Herpes": ["Genital sores", "Blisters"],
    # Frothy vaginal discharge or intense vaginal itching required
    "Trichomoniasis": ["Vaginal itching", "Genital discharge"],

    # ── Fever / Systemic Infections ────────────────────────────────────────
    # Malaria — cyclical fever and chills are the hallmark presentation
    "Malaria": ["Fever", "Chills"],
    # Typhoid — sustained prolonged fever distinguishes it from a common febrile illness
    "Typhoid Fever": ["Prolonged fever"],
    # Dengue — fever plus the characteristic retro-orbital (behind-eyes) pain
    "Dengue Fever": ["High fever", "Pain behind eyes"],
    # Leptospirosis — red eyes (conjunctival suffusion) + high fever are the cardinal triad
    "Leptospirosis": ["High fever", "Red eyes"],
    # Typhus — sudden very high fever plus a rash are required
    "Typhus": ["Sudden high fever", "Rash"],
    # Septicemia — high fever, altered mental status, and rapid heart rate
    "Septicemia": ["High fever", "Confusion", "Fast heartbeat"],

    # ── Respiratory ────────────────────────────────────────────────────────
    # Pneumonia — cough AND breathing difficulty must both be present
    "Pneumonia": ["Cough", "Shortness of breath"],
    # Whooping cough — paroxysmal cough with inspiratory whoop is the defining feature
    "Whooping Cough": ["Paroxysmal cough"],
    # Sinusitis — nasal congestion plus facial pressure/pain around the sinuses
    "Sinusitis": ["Nasal congestion", "Facial pain"],
    # Common cold — runny nose and sneezing are the defining presentation
    "Common Cold": ["Runny nose", "Sneezing"],

    # ── Gastrointestinal ───────────────────────────────────────────────────
    # Gastroenteritis — diarrhea AND vomiting together define it
    "Gastroenteritis": ["Diarrhea", "Vomiting"],
    # H. pylori / Peptic Ulcer — burning epigastric/stomach pain is cardinal
    "Helicobacteriosis PepticUlcer": ["Burning stomach pain"],

    # ── Skin / Soft-Tissue ─────────────────────────────────────────────────
    # Skin abscess — visible skin sore with pus or discharge
    "Skin Abscess": ["Skin sores", "Pus or discharge"],
    # Rubella — the mild macular rash (often starting on the face) is cardinal
    "Rubella": ["Rash"],

    # ── Haematological / Immunological ────────────────────────────────────
    # Iron-deficiency anaemia — pallor and fatigue are the clinical hallmarks
    "Iron Deficiency Anemia": ["Pale skin", "Fatigue"],
    # Sickle cell crisis — vaso-occlusive joint/bone pain plus pallor from haemolysis
    "Sickle Cell Crisis": ["Joint pain", "Pale skin"],

    # ── Infectious Disease / Chronic ──────────────────────────────────────
    # HIV/AIDS — without systemic markers this presentation overlaps too many conditions
    "HIV AIDS": ["Weight loss", "Night sweats", "Swollen lymph nodes"],

    # ── Allergic / Emergency ──────────────────────────────────────────────
    # Anaphylaxis — severe breathing difficulty AND hypotension/rash combination
    "Anaphylaxis": ["Shortness of breath", "Rash"],

    # ── Ear ───────────────────────────────────────────────────────────────
    # Ear pain is the defining symptom — fever alone never suggests ear infection
    "Ear Infection": ["Ear pain"],

    # ── Urological ────────────────────────────────────────────────────────
    # BPH — urinary symptoms (frequency, hesitancy, reduced stream) are definitional
    "Benign Prostatic Hyperplasia": ["Frequent urination", "Reduced urination"],

    # Brucellosis and Hypertension intentionally have NO cardinal symptoms:
    # their presentations are too non-specific to filter reliably without labs.

    # ── Anorectal ──────────────────────────────────────────────────────────────
    # Piles: must present with at least one anorectal symptom
    "Hemorrhoids (Piles)": ["Rectal bleeding", "Anal pain", "Anal itching", "Swelling near anus"],
    # ── Parasitic ──────────────────────────────────────────────────────────────
    # Worm infections: perianal itching is the cardinal sign
    "Intestinal Worms": ["Anal itching"],
    # ── Dental ─────────────────────────────────────────────────────────────────
    "Dental Abscess": ["Tooth pain", "Jaw swelling"],
    # ── Skin ───────────────────────────────────────────────────────────────────
    "Eczema": ["Itchy skin", "Dry skin"],
    # ── Tropical / Endemic (Cameroon) ─────────────────────────────────────────
    # Blood in urine (hematuria) is pathognomonic for urinary schistosomiasis
    "Schistosomiasis": ["Blood in urine", "Blood in stool"],
    # Mpox: pustular/blistering rash with lymphadenopathy is cardinal
    "Mpox": ["Rash", "Swollen lymph nodes", "Blisters"],
    # Trypanosomiasis: swollen posterior cervical nodes (Winterbottom's sign) + excessive sleepiness
    "African Trypanosomiasis": ["Excessive sleepiness", "Swollen lymph nodes"],
    # Rabies: hydrophobia (fear of water) is pathognomonic once encephalitic
    "Rabies": ["Hydrophobia", "Agitation"],
    # Buruli ulcer: painless progressive skin ulcer/lesion is cardinal
    "Buruli Ulcer": ["Skin sores", "Skin lesions"],
    # Candidiasis: white patches in mouth or genital symptoms required
    "Candidiasis": ["White patches in mouth", "Vaginal itching", "Vaginal discharge"],
    # Cellulitis: localised skin redness and warmth are cardinal
    "Cellulitis": ["Skin redness", "Skin warmth"],
    # Stroke: at least one focal neuro sign required — headache alone ≠ stroke
    "Stroke": ["Speech difficulty", "Facial drooping", "Severe headache"],
    # Heart failure: breathlessness + ankle oedema is the defining combination
    "Heart Failure": ["Shortness of breath", "Ankle swelling"],
    # Hypothyroidism: metabolic triad required
    "Hypothyroidism": ["Fatigue", "Weight gain", "Cold intolerance"],
    # COVID-19: loss of taste/smell are pathognomonic — without them it's indistinct from flu
    "COVID-19": ["Loss of taste", "Loss of smell"],
}

CATEGORIES = {
    "Malaria": "Parasitic",
    "Scabies": "Parasitic",
    "Onchocerciasis": "Parasitic",
    "Filariasis": "Parasitic",
    "Typhoid Fever": "Bacterial",
    "Cholera": "Bacterial",
    "Tuberculosis": "Respiratory",
    "Pneumonia": "Respiratory",
    "Asthma": "Respiratory",
    "Common Cold": "Respiratory",
    "Whooping Cough": "Respiratory",
    "Sinusitis": "Respiratory",
    "Dengue Fever": "Viral",
    "Chickenpox": "Viral",
    "Measles": "Viral",
    "Hepatitis A": "Viral",
    "Hepatitis B": "Viral",
    "Yellow Fever": "Viral",
    "Mumps": "Viral",
    "Rubella": "Viral",
    "Conjunctivitis": "Viral",
    "Herpes Zoster": "Viral",
    "HIV AIDS": "Viral",
    "Gastroenteritis": "Gastrointestinal",
    "Dysentery": "Gastrointestinal",
    "Helicobacteriosis PepticUlcer": "Gastrointestinal",
    "Appendicitis": "Gastrointestinal",
    "Diabetes Mellitus": "Chronic",
    "Hypertension": "Chronic",
    "Iron Deficiency Anemia": "Chronic",
    "Sickle Cell Crisis": "Genetic",
    "Epilepsy": "Neurological",
    "Migraine": "Neurological",
    "Tonsillitis": "Bacterial",
    "Ear Infection": "Bacterial",
    "Diphtheria": "Bacterial",
    "Tetanus": "Bacterial",
    "Leptospirosis": "Bacterial",
    "Typhus": "Bacterial",
    "Brucellosis": "Bacterial",
    "Septicemia": "Bacterial",
    "Skin Abscess": "Bacterial",
    "Cystitis UTI": "Urological",
    "Kidney Stones": "Urological",
    "Benign Prostatic Hyperplasia": "Urological",
    "Skin Fungal Infection": "Fungal",
    "Ringworm": "Fungal",
    "Pelvic Inflammatory Disease": "Reproductive",
    "Anaphylaxis": "Allergic",
    "Gonorrhea": "STI",
    "Syphilis": "STI",
    "Chlamydia": "STI",
    "Genital Herpes": "STI",
    "Trichomoniasis": "STI",
    "Hemorrhoids (Piles)": "Gastrointestinal",
    "Intestinal Worms": "Parasitic",
    "Malnutrition": "Nutritional",
    "Dental Abscess": "Bacterial",
    "Arthritis": "Musculoskeletal",
    "Eczema": "Skin",
    "Acne": "Skin",
    "Schistosomiasis": "Parasitic",
    "Mpox": "Viral",
    "African Trypanosomiasis": "Parasitic",
    "Rabies": "Viral",
    "Buruli Ulcer": "Bacterial",
    "Candidiasis": "Fungal",
    "Cellulitis": "Bacterial",
    "Stroke": "Neurological",
    "Heart Failure": "Chronic",
    "Hypothyroidism": "Chronic",
    "COVID-19": "Viral",
}

CURATED_DETAILS = {
    "Malaria": {
        "description": "A mosquito-borne parasitic infection common in tropical regions. It often causes fever, chills, sweating, headache, nausea, and fatigue.",
        "causes": "Caused by Plasmodium parasites transmitted through bites from infected female Anopheles mosquitoes.",
        "treatment": "Requires confirmatory testing and antimalarial treatment prescribed by a clinician. Severe symptoms need urgent medical care.",
        "prevention": ["Sleep under insecticide-treated bed nets", "Remove stagnant water around homes", "Use mosquito repellents and protective clothing", "Seek testing quickly for fever with chills"],
    },
    "Typhoid Fever": {
        "description": "A bacterial illness spread through contaminated food or water. It can cause prolonged fever, weakness, headache, abdominal pain, and bowel changes.",
        "causes": "Caused by Salmonella Typhi, usually after ingesting food or water contaminated with human waste.",
        "treatment": "Needs medical evaluation and antibiotics chosen by a clinician. Hydration and monitoring for complications are important.",
        "prevention": ["Drink safe or treated water", "Wash hands before eating and after toilet use", "Eat food that is well cooked and served hot", "Use vaccination where recommended"],
    },
    "Cholera": {
        "description": "An acute diarrheal infection that can cause rapid dehydration from profuse watery diarrhea and vomiting.",
        "causes": "Caused by Vibrio cholerae bacteria, usually from contaminated water or food.",
        "treatment": "Immediate oral rehydration is critical. Severe dehydration requires urgent care, IV fluids, and sometimes antibiotics.",
        "prevention": ["Use safe drinking water", "Practice hand hygiene", "Use latrines and safe sanitation", "Report suspected outbreaks early"],
    },
    "Pneumonia": {
        "description": "An infection of the lungs that can cause cough, fever, chest pain, shortness of breath, chills, and fatigue.",
        "causes": "Can be caused by bacteria, viruses, or fungi, with higher risk in children, older adults, and people with weakened immunity.",
        "treatment": "Treatment depends on cause and severity. Breathing difficulty, chest pain, or low oxygen symptoms require urgent care.",
        "prevention": ["Vaccination where available", "Avoid smoke exposure", "Wash hands regularly", "Seek care early for breathing difficulty"],
    },
    "Tuberculosis": {
        "description": "A bacterial infection that commonly affects the lungs and may cause chronic cough, night sweats, fever, weight loss, and coughing blood.",
        "causes": "Caused by Mycobacterium tuberculosis and spread through airborne droplets from an infectious person.",
        "treatment": "Requires a full multi-month TB treatment regimen supervised by healthcare workers. Do not stop treatment early.",
        "prevention": ["Test close contacts", "Improve ventilation", "Cover coughs", "Complete prescribed TB treatment"],
    },
    "Meningitis": {
        "description": "Inflammation around the brain and spinal cord that may cause sudden fever, stiff neck, severe headache, confusion, nausea, or light sensitivity.",
        "causes": "Can be caused by bacteria, viruses, or other infections. Bacterial meningitis is a medical emergency.",
        "treatment": "Requires urgent hospital evaluation. Bacterial meningitis needs rapid antibiotics and supportive care.",
        "prevention": ["Vaccination where available", "Seek urgent care for stiff neck with fever", "Avoid close contact with infected respiratory droplets"],
    },
    "Dengue Fever": {
        "description": "A mosquito-borne viral illness that can cause high fever, severe headache, pain behind the eyes, muscle and joint pain, rash, and bleeding.",
        "causes": "Caused by dengue viruses transmitted by Aedes mosquitoes.",
        "treatment": "Supportive care and hydration are important. Avoid self-medicating with aspirin or ibuprofen unless advised by a clinician.",
        "prevention": ["Prevent mosquito bites", "Remove standing water", "Use window screens and repellents", "Seek care for bleeding or severe abdominal pain"],
    },
    "Dysentery": {
        "description": "An intestinal infection causing diarrhea that may contain blood or mucus, abdominal pain, fever, and dehydration.",
        "causes": "Often caused by Shigella, amoebas, or other organisms spread through contaminated food, water, or hands.",
        "treatment": "Hydration is essential. Bloody diarrhea or signs of dehydration require medical care and may need targeted medication.",
        "prevention": ["Wash hands often", "Drink safe water", "Wash fruits and vegetables", "Use safe sanitation"],
    },
    "Gastroenteritis": {
        "description": "Inflammation of the stomach and intestines causing diarrhea, vomiting, nausea, abdominal pain, fever, and weakness.",
        "causes": "Can be caused by viruses, bacteria, parasites, contaminated food or water, or poor hygiene.",
        "treatment": "Focus on fluids and oral rehydration. Seek care for blood in stool, persistent vomiting, severe dehydration, or symptoms in young children.",
        "prevention": ["Wash hands", "Prepare food safely", "Drink treated water", "Avoid unsafe street food during outbreaks"],
    },
    "Asthma": {
        "description": "A chronic airway condition causing wheezing, cough, chest tightness, and shortness of breath that may flare with triggers.",
        "causes": "Triggers can include dust, smoke, infections, exercise, cold air, allergens, and air pollution.",
        "treatment": "Asthma is managed with clinician-guided inhalers and trigger control. Severe breathing difficulty needs emergency care.",
        "prevention": ["Avoid known triggers", "Keep rescue inhaler available if prescribed", "Reduce smoke and dust exposure", "Follow an asthma action plan"],
    },
    "Chickenpox": {
        "description": "A contagious viral illness causing fever, fatigue, and an itchy blister-like rash.",
        "causes": "Caused by the varicella-zoster virus and spread through respiratory droplets or direct contact with blisters.",
        "treatment": "Usually supportive, but infants, pregnant people, and immunocompromised patients need medical advice promptly.",
        "prevention": ["Vaccination", "Avoid contact with infected people", "Keep rash clean", "Do not scratch blisters"],
    },
    "Measles": {
        "description": "A highly contagious viral infection causing fever, cough, runny nose, red eyes, Koplik spots, and widespread rash.",
        "causes": "Caused by measles virus and spread through airborne respiratory droplets.",
        "treatment": "Supportive care and monitoring. Complications can be serious, especially in children, pregnant people, and malnourished patients.",
        "prevention": ["MMR vaccination", "Isolate suspected cases", "Improve nutrition and vitamin A where recommended"],
    },
    "Scabies": {
        "description": "A contagious skin infestation causing intense itching, night itching, rash, and small burrow tracks.",
        "causes": "Caused by mites that spread through close skin contact and shared bedding or clothing.",
        "treatment": "Requires scabicide treatment for the patient and close contacts, plus washing bedding and clothes.",
        "prevention": ["Treat close contacts", "Wash bedding and clothes in hot water", "Avoid sharing clothing or bedding during infection"],
    },
    "Diabetes Mellitus": {
        "description": "A chronic condition where blood sugar remains too high, causing thirst, frequent urination, fatigue, blurred vision, and slow-healing wounds.",
        "causes": "Related to insufficient insulin production, insulin resistance, genetics, weight, diet, and other risk factors.",
        "treatment": "Managed with blood sugar monitoring, diet, exercise, medicines, and regular clinical follow-up.",
        "prevention": ["Maintain healthy weight", "Exercise regularly", "Choose balanced meals", "Screen early if at risk"],
    },
    "Hypertension": {
        "description": "Persistently high blood pressure that may be silent or cause headache, dizziness, blurred vision, chest pain, or shortness of breath.",
        "causes": "Risk factors include age, family history, salt intake, kidney disease, stress, alcohol, and inactivity.",
        "treatment": "Managed with lifestyle changes, regular blood pressure checks, and medication when prescribed.",
        "prevention": ["Reduce salt intake", "Exercise regularly", "Limit alcohol", "Check blood pressure routinely"],
    },
    "Iron Deficiency Anemia": {
        "description": "Low red blood cell capacity due to insufficient iron, often causing fatigue, pale skin, dizziness, shortness of breath, and fast heartbeat.",
        "causes": "Can result from poor iron intake, blood loss, pregnancy, parasites, or absorption problems.",
        "treatment": "Treatment depends on cause and may include iron supplementation, diet changes, and investigation for blood loss.",
        "prevention": ["Eat iron-rich foods", "Treat parasites where present", "Use prenatal care in pregnancy", "Screen children and high-risk adults"],
    },
    "Cystitis UTI": {
        "description": "A urinary tract infection affecting the bladder, often causing painful urination, frequent urination, pelvic pain, and lower abdominal discomfort.",
        "causes": "Usually caused by bacteria entering the urinary tract.",
        "treatment": "Needs medical assessment when symptoms are persistent, recurrent, associated with fever, or occur during pregnancy.",
        "prevention": ["Drink enough fluids", "Do not delay urination", "Practice good hygiene", "Seek care early for fever or back pain"],
    },
    "Helicobacteriosis PepticUlcer": {
        "description": "A stomach infection linked with peptic ulcers, burning stomach pain, nausea, bloating, heartburn, and reduced appetite.",
        "causes": "Often caused by Helicobacter pylori bacteria that irritate the stomach lining.",
        "treatment": "Confirmed H. pylori infection is treated with clinician-prescribed combination therapy.",
        "prevention": ["Practice hand hygiene", "Use safe water", "Avoid unnecessary NSAID use", "Seek care for black stools or severe pain"],
    },
    "Common Cold": {
        "description": "A usually mild viral upper respiratory infection causing runny nose, sore throat, cough, sneezing, mild fever, and headache.",
        "causes": "Caused by respiratory viruses spread through droplets, close contact, and contaminated hands.",
        "treatment": "Supportive care with rest, fluids, and symptom relief. Seek care if breathing difficulty, persistent high fever, or worsening symptoms occur.",
        "prevention": ["Wash hands", "Cover coughs and sneezes", "Avoid close contact when ill", "Clean frequently touched surfaces"],
    },
    "Skin Fungal Infection": {
        "description": "A fungal infection of the skin causing itching, ring-shaped or red scaly patches, peeling skin, and skin lesions.",
        "causes": "Caused by various fungi including dermatophytes; spread through direct contact, shared items, or warm moist environments.",
        "treatment": "Antifungal creams or oral medication as prescribed. Keep affected area dry and clean.",
        "prevention": ["Keep skin dry", "Avoid sharing personal items", "Wear breathable footwear", "Treat promptly to prevent spread"],
    },
    # ── 30 new diseases ───────────────────────────────────────────────────────
    "Hepatitis A": {
        "description": "A viral liver infection spread through contaminated food or water, causing jaundice, fatigue, nausea, vomiting, and dark urine.",
        "causes": "Caused by the hepatitis A virus (HAV), typically via contaminated water or food prepared by an infected person.",
        "treatment": "No specific antiviral; supportive care with rest, fluids, and avoiding alcohol. Most cases resolve on their own.",
        "prevention": ["Vaccination", "Drink safe water", "Wash hands thoroughly", "Practice food hygiene"],
    },
    "Hepatitis B": {
        "description": "A serious liver infection caused by the hepatitis B virus, potentially becoming chronic and leading to liver cirrhosis or cancer.",
        "causes": "Spread through contact with infected blood, sexual contact, or from mother to child during birth.",
        "treatment": "Acute cases are managed with supportive care. Chronic hepatitis B requires antiviral medication under medical supervision.",
        "prevention": ["Vaccination", "Use condoms", "Avoid sharing needles or razors", "Screen pregnant women"],
    },
    "Yellow Fever": {
        "description": "A viral hemorrhagic disease transmitted by Aedes mosquitoes causing high fever, jaundice, muscle pain, and in severe cases, organ failure.",
        "causes": "Caused by the yellow fever flavivirus transmitted by Aedes aegypti and other Aedes mosquito species.",
        "treatment": "Supportive care only — rest, fluids, and symptom management. No specific antiviral exists. Severe cases need hospital care.",
        "prevention": ["Vaccination (single dose for lifelong protection)", "Mosquito control", "Use repellents and protective clothing"],
    },
    "Whooping Cough": {
        "description": "A highly contagious bacterial respiratory infection characterised by severe coughing fits that may end with a whooping sound and vomiting.",
        "causes": "Caused by Bordetella pertussis bacteria, spread through airborne droplets from coughing or sneezing.",
        "treatment": "Antibiotics (erythromycin, azithromycin) are most effective early. Hospitalisation may be needed in infants.",
        "prevention": ["Vaccination (DTaP/Tdap)", "Isolate infected individuals", "Vaccinate pregnant women to protect newborns"],
    },
    "Mumps": {
        "description": "A contagious viral infection that primarily causes painful swelling of the salivary glands (parotitis) and jaw stiffness.",
        "causes": "Caused by the mumps paramyxovirus, spread through saliva and respiratory droplets.",
        "treatment": "Supportive care: rest, fluids, pain relief (paracetamol), and cold/warm compresses on swollen glands.",
        "prevention": ["MMR vaccination", "Isolate infected individuals", "Wash hands frequently"],
    },
    "Rubella": {
        "description": "A mild contagious viral illness causing a fine pink rash, mild fever, and swollen lymph nodes. Dangerous in pregnancy.",
        "causes": "Caused by the rubella virus, spread through respiratory droplets.",
        "treatment": "Supportive care only. Pregnant women exposed to rubella require urgent specialist assessment.",
        "prevention": ["MMR vaccination", "Immunise all women of childbearing age", "Avoid contact with pregnant women if infected"],
    },
    "Sinusitis": {
        "description": "Inflammation of the sinuses causing facial pain, nasal congestion, headache, and runny nose, often following a cold.",
        "causes": "Usually caused by viral upper respiratory infections; may become bacterial. Allergies and structural issues are also triggers.",
        "treatment": "Steam inhalation, saline rinses, decongestants for symptom relief. Bacterial sinusitis may need antibiotics from a clinician.",
        "prevention": ["Treat colds promptly", "Manage allergies", "Avoid cigarette smoke", "Stay hydrated"],
    },
    "Tonsillitis": {
        "description": "Inflammation of the tonsils causing severe sore throat, difficulty swallowing, high fever, and swollen lymph nodes.",
        "causes": "Most commonly caused by group A Streptococcus bacteria or viral infections (adenovirus, EBV).",
        "treatment": "Rest, fluids, and pain relief. Bacterial tonsillitis requires antibiotics. Recurrent cases may need tonsillectomy.",
        "prevention": ["Wash hands", "Avoid sharing utensils", "Avoid close contact with infected individuals"],
    },
    "Ear Infection": {
        "description": "An infection of the middle ear (otitis media) causing ear pain, fever, hearing loss, and sometimes discharge.",
        "causes": "Often follows a respiratory infection. Caused by bacteria (S. pneumoniae, H. influenzae) or viruses.",
        "treatment": "Most mild cases resolve on their own. Antibiotics are prescribed for severe or persistent cases by a clinician.",
        "prevention": ["Vaccinate against pneumococcus and Hib", "Breastfeed infants", "Avoid secondhand smoke", "Treat respiratory infections promptly"],
    },
    "Conjunctivitis": {
        "description": "Inflammation of the conjunctiva (pink eye) causing red eyes, discharge, itching, and sensitivity to light.",
        "causes": "Can be viral, bacterial, or allergic. Viral and bacterial forms are highly contagious.",
        "treatment": "Viral: supportive (cool compresses, lubricating drops). Bacterial: antibiotic eye drops from a clinician.",
        "prevention": ["Wash hands frequently", "Do not touch eyes", "Do not share towels or eye drops", "Clean contact lenses properly"],
    },
    "Herpes Zoster": {
        "description": "Reactivation of the chickenpox virus (VZV) in nerve ganglia, causing a painful blistering rash in a stripe pattern on one side of the body.",
        "causes": "Caused by reactivation of the varicella-zoster virus (VZV), triggered by stress, immunosuppression, or ageing.",
        "treatment": "Antiviral medications (aciclovir, valaciclovir) are most effective within 72 hours of rash onset. Pain management is important.",
        "prevention": ["Shingles vaccine for older adults", "Avoid contact with people who have chickenpox if you never had it"],
    },
    "Appendicitis": {
        "description": "Acute inflammation of the appendix causing sudden worsening abdominal pain (migrating to the right lower side), fever, nausea, and vomiting.",
        "causes": "Usually caused by a blockage in the appendix lumen by stool, mucus, or infection, leading to bacterial overgrowth.",
        "treatment": "Surgical removal of the appendix (appendicectomy) is the standard treatment. Antibiotics may be used in selected mild cases.",
        "prevention": ["High-fibre diet may reduce risk", "Seek care early for persistent abdominal pain"],
    },
    "Kidney Stones": {
        "description": "Hard mineral deposits forming in the kidneys, causing severe flank or back pain, blood in urine, and painful urination.",
        "causes": "Caused by high concentrations of minerals (calcium, oxalate, uric acid) in urine, often due to dehydration or diet.",
        "treatment": "Small stones may pass with fluids and pain relief. Larger stones need lithotripsy, ureteroscopy, or surgical removal.",
        "prevention": ["Drink plenty of water daily", "Reduce salt and animal protein intake", "Limit oxalate-rich foods", "Follow dietary advice from a clinician"],
    },
    "Sickle Cell Crisis": {
        "description": "A painful episode in sickle cell disease where sickle-shaped red blood cells block blood vessels, causing severe bone pain, fatigue, and organ complications.",
        "causes": "Triggered by infection, dehydration, cold, stress, or high altitude in people with sickle cell disease.",
        "treatment": "Pain relief, fluids, oxygen, and treatment of any triggering infection under medical supervision.",
        "prevention": ["Stay well hydrated", "Avoid extreme temperatures", "Prevent infections with vaccines and prophylactic antibiotics", "Regular haematology follow-up"],
    },
    "Tetanus": {
        "description": "A life-threatening bacterial infection causing painful muscle stiffness and spasms, especially jaw stiffness (trismus/lockjaw).",
        "causes": "Caused by Clostridium tetani toxin entering through wounds, burns, or cuts exposed to soil or animal faeces.",
        "treatment": "Tetanus immunoglobulin, wound cleaning, antibiotics, and intensive care for muscle spasms. ICU admission often required.",
        "prevention": ["Vaccination (DTP, Td boosters)", "Proper wound care and cleaning", "Seek care promptly for deep wounds"],
    },
    "Diphtheria": {
        "description": "A serious bacterial infection of the throat and airways causing sore throat, hoarse voice, a grey membrane in the throat, and breathing difficulty.",
        "causes": "Caused by Corynebacterium diphtheriae, spread through respiratory droplets and contaminated surfaces.",
        "treatment": "Diphtheria antitoxin and antibiotics (penicillin, erythromycin) under hospital care.",
        "prevention": ["Vaccination (DTP)", "Isolate infected individuals", "Close contact tracing and prophylaxis"],
    },
    "Ringworm": {
        "description": "A contagious fungal skin infection (not a worm) causing ring-shaped red scaly patches, itching, and skin peeling.",
        "causes": "Caused by dermatophyte fungi; spread through direct skin contact, shared towels, bedding, or infected animals.",
        "treatment": "Topical antifungal creams (clotrimazole, miconazole) for most cases; oral antifungals for scalp or nail involvement.",
        "prevention": ["Keep skin dry", "Avoid sharing personal items", "Treat infected animals", "Wash hands after handling animals"],
    },
    "Leptospirosis": {
        "description": "A bacterial infection contracted from water or soil contaminated with animal urine, causing high fever, muscle pain, red eyes, and jaundice.",
        "causes": "Caused by Leptospira bacteria; often acquired by contact with contaminated flood water, soil, or infected animals.",
        "treatment": "Antibiotics (doxycycline, penicillin, ceftriaxone). Severe cases (Weil's disease) need intensive hospital care.",
        "prevention": ["Avoid contact with flood water", "Wear protective footwear in endemic areas", "Vaccinate livestock", "Cover cuts and wounds"],
    },
    "Typhus": {
        "description": "A group of bacterial diseases transmitted by lice, fleas, or mites, causing sudden high fever, severe headache, rash, and confusion.",
        "causes": "Epidemic typhus is caused by Rickettsia prowazekii (lice-borne). Murine typhus by R. typhi (flea-borne).",
        "treatment": "Doxycycline is the first-line treatment; usually curative when started early.",
        "prevention": ["Louse and flea control", "Improve sanitation", "Treat clothing and bedding", "Avoid contact with lice-infested individuals"],
    },
    "Brucellosis": {
        "description": "A bacterial zoonotic infection causing fever, sweating, joint pain, fatigue, and weight loss; often from consumption of unpasteurised dairy.",
        "causes": "Caused by Brucella species from infected animals (cattle, goats, pigs), spread via unpasteurised milk, cheese, or direct animal contact.",
        "treatment": "Combination antibiotic therapy (doxycycline + rifampicin or streptomycin) for 6 weeks under medical supervision.",
        "prevention": ["Pasteurise or boil milk and dairy", "Wear gloves when handling animals or carcasses", "Vaccinate livestock"],
    },
    "Septicemia": {
        "description": "A life-threatening infection in the bloodstream (sepsis) causing high fever, confusion, rapid heart rate, breathing difficulty, and low blood pressure.",
        "causes": "Usually caused by bacterial infections that spread into the blood from any site (lungs, urinary tract, skin, abdomen).",
        "treatment": "Medical emergency requiring IV antibiotics, fluids, and intensive care. Do not delay seeking emergency care.",
        "prevention": ["Treat infections promptly", "Practice hand hygiene", "Vaccinate against causative pathogens", "Seek early care for worsening illness"],
    },
    "Pelvic Inflammatory Disease": {
        "description": "An infection of the female reproductive organs causing pelvic pain, vaginal discharge, fever, and potentially infertility if untreated.",
        "causes": "Usually caused by sexually transmitted bacteria (Chlamydia, Gonorrhoea) or other vaginal bacteria ascending to the uterus and fallopian tubes.",
        "treatment": "Antibiotics (combination regimens) prescribed by a clinician. Severe cases require hospitalisation.",
        "prevention": ["Use condoms consistently", "Get tested and treated for STIs", "Avoid douching", "Seek early care for unusual discharge or pelvic pain"],
        "genderSpecific": "female",
    },
    "Benign Prostatic Hyperplasia": {
        "description": "Non-cancerous enlargement of the prostate gland causing urinary symptoms including frequent urination, weak stream, and incomplete bladder emptying.",
        "causes": "Related to hormonal changes and ageing in men. More common after age 50.",
        "treatment": "Lifestyle changes, medications (alpha-blockers, 5-alpha reductase inhibitors), or surgery depending on severity.",
        "prevention": ["Regular health check-ups after 50", "Maintain healthy weight", "Stay physically active"],
        "genderSpecific": "male",
    },
    "Migraine": {
        "description": "A neurological disorder causing recurrent severe one-sided headaches with throbbing pain, nausea, and sensitivity to light and sound.",
        "causes": "Exact cause unclear; triggers include stress, hormonal changes, certain foods, alcohol, sleep disruption, and bright lights.",
        "treatment": "Pain relief (paracetamol, ibuprofen, triptans for severe attacks). Preventive medications if attacks are frequent.",
        "prevention": ["Identify and avoid personal triggers", "Maintain regular sleep and eating schedules", "Manage stress", "Stay hydrated"],
    },
    "Epilepsy": {
        "description": "A neurological disorder characterised by recurrent unprovoked seizures due to abnormal electrical activity in the brain.",
        "causes": "Can be caused by brain injury, stroke, infections, genetic factors, or may be idiopathic (unknown cause).",
        "treatment": "Antiepileptic drugs (AEDs) under neurology supervision. Surgery or vagus nerve stimulation for drug-resistant cases.",
        "prevention": ["Protect head from injury", "Treat brain infections early", "Take AEDs as prescribed", "Avoid seizure triggers (alcohol, sleep deprivation)"],
    },
    "Onchocerciasis": {
        "description": "A parasitic infection (river blindness) caused by worms transmitted by blackfly bites, causing intense itching, skin lesions, and vision loss.",
        "causes": "Caused by Onchocerca volvulus roundworms transmitted by Simulium blackfly bites near fast-flowing rivers.",
        "treatment": "Ivermectin (annual or semi-annual doses) controls the disease. Community-wide treatment programmes exist.",
        "prevention": ["Mass drug administration with ivermectin", "Blackfly control", "Avoid rivers and blackfly habitats in endemic areas"],
    },
    "Filariasis": {
        "description": "A parasitic disease caused by thread-like worms transmitted by mosquitoes, causing lymphoedema (swollen limbs), elephantiasis, and skin thickening.",
        "causes": "Caused by Wuchereria bancrofti and other filarial worms transmitted by Culex and other mosquito species.",
        "treatment": "Diethylcarbamazine (DEC) or ivermectin and albendazole combinations. Lymphoedema management with care and hygiene.",
        "prevention": ["Mosquito bite prevention", "Mass drug administration programmes", "Use bed nets and repellents"],
    },
    "HIV AIDS": {
        "description": "HIV destroys immune cells over time, leading to AIDS — a state of severe immune deficiency making the body vulnerable to opportunistic infections.",
        "causes": "Caused by the human immunodeficiency virus (HIV), transmitted through blood, sexual contact, or mother to child.",
        "treatment": "Antiretroviral therapy (ART) suppresses the virus, preserves immunity, and allows near-normal life. Treatment is lifelong.",
        "prevention": ["Use condoms consistently", "HIV testing and knowing your status", "Pre-exposure prophylaxis (PrEP) for high-risk individuals", "Prevent mother-to-child transmission with ART"],
    },
    "Skin Abscess": {
        "description": "A localised collection of pus under the skin (boil or abscess) causing a painful, swollen, red lump that may discharge pus.",
        "causes": "Usually caused by Staphylococcus aureus bacteria entering through broken skin, hair follicles, or sweat glands.",
        "treatment": "Warm compresses for small abscesses. Surgical incision and drainage for larger or painful abscesses. Antibiotics if spreading infection.",
        "prevention": ["Maintain skin hygiene", "Do not squeeze or puncture skin lesions", "Treat cuts and wounds promptly", "Manage diabetes and immune conditions"],
    },
    "Anaphylaxis": {
        "description": "A severe life-threatening allergic reaction causing rash, breathing difficulty, swelling, rapid heart rate, and dangerous drop in blood pressure.",
        "causes": "Triggered by allergens such as insect stings, certain foods (nuts, shellfish), medications (penicillin), or latex.",
        "treatment": "MEDICAL EMERGENCY. Epinephrine (adrenaline) injection immediately, then seek emergency hospital care.",
        "prevention": ["Know and avoid allergens", "Carry an epinephrine auto-injector if prescribed", "Wear a medical alert bracelet", "Inform healthcare providers of allergies"],
    },
    # ── STIs ──────────────────────────────────────────────────────────────────
    "Gonorrhea": {
        "description": "A common bacterial sexually transmitted infection caused by Neisseria gonorrhoeae. It can infect the genitals, rectum, and throat. Many people have no symptoms, making it easy to spread unknowingly.",
        "causes": "Caused by the Neisseria gonorrhoeae bacterium, spread through unprotected vaginal, anal, or oral sex. A pregnant woman can also pass it to her baby during delivery.",
        "treatment": "Treated with antibiotics prescribed by a clinician. Both partners must be treated simultaneously. Do not self-medicate — resistance to common antibiotics is increasing.",
        "prevention": ["Use condoms consistently and correctly", "Get tested regularly if sexually active with multiple partners", "Treat both partners at the same time", "Screen pregnant women to prevent mother-to-child transmission"],
        "severity": "Medium",
    },
    "Syphilis": {
        "description": "A bacterial STI caused by Treponema pallidum that progresses in stages. The primary stage presents as a painless sore (chancre); the secondary stage causes a body rash, fever, and swollen glands. Untreated syphilis can cause serious long-term damage to the heart, brain, and nerves.",
        "causes": "Caused by the Treponema pallidum bacterium, spread through direct contact with syphilis sores during sex. Pregnant women can pass it to their unborn baby (congenital syphilis).",
        "treatment": "Penicillin injection (or other antibiotics for penicillin-allergic patients) as prescribed by a clinician. Early stages are highly treatable. Late stages require longer treatment.",
        "prevention": ["Use condoms", "Screen for syphilis regularly", "Screen all pregnant women at first antenatal visit", "Treat sexual partners", "Avoid sex with open sores"],
        "severity": "High",
    },
    "Chlamydia": {
        "description": "The most common bacterial STI worldwide. Caused by Chlamydia trachomatis, it often causes no symptoms, making it easy to spread. Untreated chlamydia can cause pelvic inflammatory disease, infertility, and complications in pregnancy.",
        "causes": "Caused by the Chlamydia trachomatis bacterium, spread through unprotected vaginal, anal, or oral sex. Newborns can be infected during birth.",
        "treatment": "Treated with antibiotics (azithromycin or doxycycline) as prescribed. Partners must also be treated. Repeat testing is recommended 3 months after treatment.",
        "prevention": ["Use condoms", "Regular STI screening", "Treat sexual partners simultaneously", "Screen pregnant women to prevent neonatal infection"],
        "severity": "Medium",
    },
    "Genital Herpes": {
        "description": "A viral STI caused by herpes simplex virus type 2 (HSV-2) and occasionally type 1 (HSV-1). Causes recurring painful blisters or sores on and around the genitals. The virus remains in the body for life but can be managed with medication.",
        "causes": "Caused by herpes simplex virus (HSV-2 primarily, HSV-1 increasingly). Spread through direct skin-to-skin contact during sex — even when no sores are visible (asymptomatic shedding).",
        "treatment": "Antiviral medications (aciclovir, valaciclovir) reduce outbreaks, shorten healing time, and reduce transmission risk. There is no cure, but treatment controls symptoms effectively.",
        "prevention": ["Use condoms (reduces but does not eliminate risk)", "Avoid sex during active outbreaks", "Inform partners of diagnosis", "Antiviral suppressive therapy reduces transmission risk"],
        "severity": "Medium",
    },
    "Trichomoniasis": {
        "description": "A very common parasitic STI caused by Trichomonas vaginalis. In women it causes vaginal itching, burning, redness, and an unpleasant-smelling discharge. Most men have no symptoms. It increases the risk of getting or spreading HIV.",
        "causes": "Caused by the protozoan parasite Trichomonas vaginalis, spread through vaginal sex. The parasite can survive on moist surfaces for a short time.",
        "treatment": "Treated with metronidazole or tinidazole antibiotics. Both partners must be treated to prevent reinfection.",
        "prevention": ["Use condoms", "Treat both partners simultaneously", "Regular STI testing", "Avoid sharing sex toys"],
        "severity": "Low",
    },
    "Hemorrhoids (Piles)": {
        "description": "Swollen blood vessels (veins) inside or around the anus and lower rectum. Very common — affecting up to 75% of people at some point. Internal hemorrhoids form inside the rectum; external hemorrhoids form under the skin around the anus. They can cause pain, itching, bleeding, and discomfort — especially when sitting or passing stool.",
        "causes": "Increased pressure in the veins around the anus from straining during bowel movements, chronic constipation or diarrhea, prolonged sitting on the toilet, pregnancy, obesity, or a low-fibre diet.",
        "treatment": "Mild cases improve with high-fibre diet, adequate water intake, and avoiding straining. Warm sitz baths (sitting in warm water 10–15 mins) help relieve pain and swelling. Pharmacy creams or suppositories provide short-term relief. Persistent, severe, or bleeding hemorrhoids need clinical evaluation. Do not assume all rectal bleeding is piles — see a doctor if bleeding continues.",
        "prevention": ["Eat high-fibre foods — vegetables, fruits, whole grains, beans", "Drink plenty of water daily (at least 2 litres)", "Do not strain or push hard during bowel movements", "Do not sit too long on the toilet", "Exercise regularly", "Treat constipation early"],
        "severity": "Low",
    },
    "Intestinal Worms": {
        "description": "Infections caused by parasitic worms (helminths) living in the intestines. Common types in Cameroon include roundworms (Ascaris), hookworms, pinworms, whipworms, and tapeworms. Very common in children and in areas with poor sanitation or contaminated water/soil.",
        "causes": "Swallowing worm eggs from contaminated food, water, or soil. Hookworms can enter through bare skin on the ground. Tapeworms can come from undercooked pork or beef.",
        "treatment": "Anthelmintic medications (mebendazole, albendazole) treat most intestinal worms effectively. A single dose or short course is usually curative. The whole household may need treatment for pinworms.",
        "prevention": ["Wash hands thoroughly before eating and after toilet use", "Wear shoes — never walk barefoot in soil", "Wash and cook vegetables thoroughly", "Drink safe or treated water", "Cook meat fully", "Deworm children regularly as recommended"],
        "severity": "Low",
    },
    "Malnutrition": {
        "description": "A condition where the body does not get enough nutrients — vitamins, minerals, proteins, calories — to maintain normal health and functions. Very common in children under 5 in Cameroon. Severe malnutrition (kwashiorkor, marasmus) can be life-threatening.",
        "causes": "Inadequate food intake, poor dietary diversity, repeated infections reducing nutrient absorption, poverty, food insecurity, and disrupted breastfeeding practices.",
        "treatment": "Mild malnutrition: increase food diversity, add protein-rich foods (beans, eggs, groundnuts, meat, fish), ensure adequate calories. Severe malnutrition in children needs urgent hospitalisation and therapeutic feeding. Treat any underlying infections.",
        "prevention": ["Breastfeed exclusively for the first 6 months", "Introduce diverse complementary foods at 6 months", "Ensure regular deworming", "Manage infections promptly", "Grow or buy protein-rich foods regularly"],
        "severity": "High",
    },
    "Dental Abscess": {
        "description": "A collection of pus (bacterial infection) in or around a tooth or in the gum. Causes intense, throbbing tooth pain that may spread to the jaw, ear, or neck. Without treatment it can spread to the jaw, neck, or brain — a medical emergency.",
        "causes": "Tooth decay, cracked tooth, gum disease, or injury allowing bacteria to enter the dental pulp or surrounding tissue.",
        "treatment": "Requires dental treatment — drainage of the abscess, antibiotics, and often root canal or tooth extraction. Pain relief with paracetamol. A spreading abscess (jaw swelling, difficulty breathing or swallowing, fever) is an emergency — go to hospital immediately.",
        "prevention": ["Brush teeth twice daily", "Use fluoride toothpaste", "Floss regularly", "Limit sugary foods and drinks", "See a dentist for tooth pain early — do not delay"],
        "severity": "Medium",
    },
    "Arthritis": {
        "description": "Inflammation of one or more joints causing pain, swelling, stiffness, and reduced range of motion. Common types include osteoarthritis (joint wear-and-tear, common in older adults) and rheumatoid arthritis (autoimmune). Reactive arthritis can follow infections like chlamydia, salmonella, or streptococcus.",
        "causes": "Osteoarthritis: cartilage breakdown from age, obesity, or repetitive use. Rheumatoid arthritis: immune system attacks joints. Reactive arthritis: triggered by infection elsewhere in the body.",
        "treatment": "Pain relief, physiotherapy, anti-inflammatory medications as prescribed. Severe or systemic arthritis needs rheumatology referral. Maintain joint movement with gentle exercise.",
        "prevention": ["Maintain healthy weight", "Exercise regularly", "Treat joint injuries promptly", "Manage infections early to prevent reactive arthritis"],
        "severity": "Medium",
    },
    "Eczema": {
        "description": "A chronic skin condition causing patches of red, itchy, inflamed, and cracked skin. Very common in children but affects all ages. It often flares and improves in cycles. Not contagious.",
        "causes": "Combination of genetic predisposition, immune system dysfunction, and environmental triggers (soaps, dust, certain fabrics, sweat, stress, dry weather). Often linked to asthma or allergic rhinitis.",
        "treatment": "Moisturise the skin regularly to prevent dryness. Avoid identified triggers. Mild topical steroid creams (as directed by a clinician) reduce flares. Keep skin cool and avoid scratching — scratching causes skin damage and infection risk.",
        "prevention": ["Moisturise skin daily", "Avoid harsh soaps and detergents", "Wear soft, breathable cotton clothing", "Identify and avoid personal triggers", "Keep fingernails short to reduce scratch damage"],
        "severity": "Low",
    },
    "Acne": {
        "description": "A very common skin condition where hair follicles become plugged with oil and dead skin cells, forming pimples, blackheads, whiteheads, or cysts — mainly on the face, chest, and back. Most common in teenagers but can affect adults.",
        "causes": "Excess oil (sebum) production, dead skin cells clogging pores, bacterial growth (Cutibacterium acnes), and hormonal changes during puberty, menstrual cycle, or stress.",
        "treatment": "Keep skin clean (gentle wash twice daily). Avoid squeezing pimples — this spreads bacteria and causes scarring. Benzoyl peroxide or salicylic acid products (available at pharmacies) help mild acne. Severe or cystic acne needs clinical assessment and may require prescription antibiotics or retinoids.",
        "prevention": ["Wash face gently twice daily with mild cleanser", "Remove make-up before sleeping", "Avoid touching face frequently", "Use non-comedogenic (non-pore-blocking) skin products", "Manage stress"],
        "severity": "Low",
    },
    # ── Tropical / Endemic (Cameroon) ─────────────────────────────────────────
    "Schistosomiasis": {
        "description": "A parasitic disease caused by blood flukes (Schistosoma worms) acquired by swimming or washing in infected freshwater. Urinary schistosomiasis (S. haematobium) causes blood in urine; intestinal schistosomiasis (S. mansoni) causes abdominal pain and bloody stool. Very common in Cameroon and sub-Saharan Africa.",
        "causes": "Caused by Schistosoma parasites whose larvae live in freshwater snails. Larvae penetrate the skin during water contact. Endemic in rivers, lakes, and irrigation areas of Cameroon including the North West Region.",
        "treatment": "Treated with praziquantel, a single-dose oral medicine provided through mass drug administration and health facilities. Seek care for blood in urine or stool even without pain.",
        "prevention": ["Avoid swimming or wading in freshwater lakes, rivers, or streams in endemic areas", "Use treated or boiled water for bathing", "Participate in community mass drug administration (praziquantel)", "Wear protective footwear when crossing streams"],
        "severity": "High",
    },
    "Mpox": {
        "description": "A viral disease caused by the Mpox (Monkeypox) virus, endemic in parts of Central and West Africa including Cameroon. It causes fever, swollen lymph nodes, and a distinctive rash that progresses from flat spots to blisters to pustules. Usually self-limiting but can be severe in immunocompromised patients or children.",
        "causes": "Caused by the Mpox virus, a member of the Orthopoxvirus family. Spreads through close contact with an infected person's rash, body fluids, respiratory droplets, or contaminated materials. Also spread from infected animals (rodents, monkeys).",
        "treatment": "Mostly supportive care: rest, fluids, pain relief. Keep rash clean and dry. Avoid touching face. Tecovirimat (antiviral) is available in some settings for severe cases. Isolate to prevent spread. Seek hospital care for breathing difficulty, eye involvement, or very severe rash.",
        "prevention": ["Avoid contact with sick animals (rodents, monkeys)", "Avoid skin-to-skin contact with people who have an unexplained rash", "Wash hands thoroughly", "Vaccination is available for high-risk contacts", "Report suspected cases to the health facility"],
        "severity": "High",
    },
    "African Trypanosomiasis": {
        "description": "Also called African Sleeping Sickness, this parasitic disease is transmitted by tsetse fly bites and affects the blood, lymph nodes, and eventually the brain. Early stage causes fever and swollen lymph nodes; late stage causes confusion, personality change, and excessive daytime sleepiness. Present in forested areas of Cameroon.",
        "causes": "Caused by Trypanosoma brucei parasites transmitted by infected tsetse flies, found in savanna and forested regions. Two subspecies affect humans: T. b. gambiense (West/Central Africa, including Cameroon) and T. b. rhodesiense (East Africa).",
        "treatment": "Requires specific antiparasitic drugs (pentamidine for early stage, eflornithine or nifurtimox-eflornithine combination for late stage). Treatment must be supervised by a clinician at a specialised facility. Early diagnosis and treatment are critical for survival.",
        "prevention": ["Avoid tsetse fly bites by wearing long-sleeved clothing in forest and savanna areas", "Avoid bright-coloured and dark-blue clothing that attract tsetse flies", "Use insect repellent", "Participate in active surveillance if in an endemic area", "Report fever or swollen lymph nodes after exposure to fly-infested areas"],
        "severity": "High",
    },
    "Rabies": {
        "description": "A fatal viral disease affecting the brain, almost always transmitted through the bite or scratch of a rabid animal — most commonly a dog in Cameroon. Once symptoms appear, rabies is nearly always fatal. Post-exposure vaccination immediately after a bite can prevent disease.",
        "causes": "Caused by the Rabies lyssavirus, transmitted through saliva of infected animals. Dogs are the main source of human rabies in Cameroon. Other animals include cats, bats, and monkeys.",
        "treatment": "If bitten: wash the wound immediately and thoroughly with soap and water for at least 15 minutes, then go to a health facility for post-exposure prophylaxis (PEP) — rabies vaccine and immunoglobulin. PEP is effective only if started promptly BEFORE symptoms appear. Once symptoms develop, rabies is fatal — seek hospital care for comfort and supportive management.",
        "prevention": ["Vaccinate dogs against rabies", "Avoid approaching stray or wild animals", "Wash any animal bite immediately with soap and water", "Seek post-exposure vaccination within hours of any suspected rabid animal bite", "Pre-exposure vaccination for high-risk individuals (veterinarians, animal handlers)"],
        "severity": "High",
    },
    "Buruli Ulcer": {
        "description": "A chronic skin disease caused by Mycobacterium ulcerans bacteria, present in Cameroon and other Central/West African countries. Starts as a painless skin swelling or nodule that breaks down into a large, destructive ulcer. Painlessness is a distinguishing feature. Without early treatment, the ulcer can destroy skin, tissue, and bone.",
        "causes": "Caused by Mycobacterium ulcerans, related to the bacteria causing tuberculosis and leprosy. Exact transmission route is not fully understood but associated with slow-moving or stagnant water environments. Not spread person-to-person.",
        "treatment": "Combination antibiotic therapy (rifampicin + clarithromycin for 8 weeks) is effective if started early. Advanced disease may require surgery and wound care. Early diagnosis is critical — seek care for any painless skin swelling, nodule, or ulcer, especially near water bodies.",
        "prevention": ["Seek early medical care for any unexplained, painless skin swelling or ulcer", "Avoid contact with stagnant or slow-moving water where possible", "Wear protective clothing in endemic areas", "Participate in community screening programmes"],
        "severity": "High",
    },
    # ── Fungal / Opportunistic ────────────────────────────────────────────────
    "Candidiasis": {
        "description": "A fungal infection caused by Candida yeasts. It can affect the mouth (oral thrush: white patches), genitals (vaginal thrush: itching, discharge), skin folds, or spread internally in immunocompromised patients. Very common in people with HIV, diabetes, or after antibiotic use.",
        "causes": "Caused by Candida albicans and related yeasts. Normally present in small amounts on skin and mucous membranes; overgrows when immunity is low, after antibiotics disturb normal flora, or with poorly controlled diabetes.",
        "treatment": "Oral thrush: antifungal oral gel or lozenges (miconazole, nystatin). Vaginal thrush: antifungal pessary or cream (clotrimazole, fluconazole tablet as prescribed). Seek care if symptoms are severe, recurrent, or if you have HIV. Treatment of underlying condition (e.g. blood sugar control) helps prevent recurrence.",
        "prevention": ["Complete only necessary antibiotic courses", "Maintain good oral and genital hygiene", "Control blood sugar if diabetic", "Treat HIV appropriately to maintain immunity", "Wear breathable cotton underwear"],
        "severity": "Medium",
    },
    # ── Bacterial / Skin ─────────────────────────────────────────────────────
    "Cellulitis": {
        "description": "A common bacterial infection of the skin and underlying tissue causing painful redness, warmth, and swelling — most often on the legs. It can spread rapidly and needs antibiotic treatment. Recurrent cellulitis is common in people with lymphoedema or poor circulation.",
        "causes": "Usually caused by Streptococcus or Staphylococcus bacteria entering through a break in the skin (cut, insect bite, wound, athlete's foot, or eczema). Risk increases with obesity, poor circulation, lymphoedema, or diabetes.",
        "treatment": "Antibiotics prescribed by a clinician (usually amoxicillin-clavulanate, cloxacillin, or similar). Elevate the affected limb. Mark the edge of redness with a pen to monitor spread. If red streaks, high fever, rapidly spreading redness, or pus appear — go to hospital urgently.",
        "prevention": ["Clean all skin cuts and wounds promptly", "Treat athlete's foot (fungal foot infection) early", "Moisturise dry, cracked skin", "Manage underlying conditions like oedema or diabetes", "Elevate legs if lymphoedema is present"],
        "severity": "Medium",
    },
    # ── Cardiovascular / Neurological ────────────────────────────────────────
    "Stroke": {
        "description": "A medical emergency where blood supply to part of the brain is cut off (ischaemic stroke) or a blood vessel bursts (haemorrhagic stroke), causing sudden neurological symptoms. A stroke can cause permanent disability or death — time is brain, act FAST. Common in people with high blood pressure, heart disease, or diabetes.",
        "causes": "Ischaemic stroke: blood clot blocks a brain artery (most common, 85%). Haemorrhagic stroke: a blood vessel ruptures. Risk factors: high blood pressure, smoking, diabetes, heart disease, high cholesterol, obesity, and family history.",
        "treatment": "EMERGENCY — call for help or go to hospital immediately. Time from symptom start to treatment determines outcome. Treatment includes clot-busting drugs (thrombolysis within 4.5 hours), blood pressure management, and rehabilitation. Do not give food or water to a person with stroke symptoms.",
        "prevention": ["Control blood pressure — the most important preventable risk", "Take prescribed medications regularly", "Quit smoking", "Exercise regularly and maintain healthy weight", "Control blood sugar and cholesterol", "Use FAST test: Face drooping / Arm weakness / Speech difficulty / Time to call emergency"],
        "severity": "High",
    },
    "Heart Failure": {
        "description": "A chronic condition where the heart is unable to pump blood efficiently enough to meet the body's needs. Causes breathlessness, ankle and leg swelling, and fatigue. It is managed not cured, but many people live well with the right treatment and lifestyle changes.",
        "causes": "Common causes in Cameroon include uncontrolled hypertension (most common), rheumatic heart disease, ischaemic heart disease, cardiomyopathy, severe anaemia, and thyroid disease. HIV-associated cardiomyopathy is also seen.",
        "treatment": "Requires medical management including diuretics (to reduce fluid), ACE inhibitors, beta-blockers, and salt restriction — all under a clinician's supervision. Seek urgent care for sudden severe breathlessness, chest pain, or inability to lie flat.",
        "prevention": ["Control blood pressure and diabetes", "Treat heart valve disease and rheumatic fever early", "Limit salt intake", "Avoid excessive alcohol", "Take HIV medication if HIV-positive to protect the heart", "Seek care for breathlessness with exertion — do not ignore it"],
        "severity": "High",
    },
    # ── Endocrine ─────────────────────────────────────────────────────────────
    "Hypothyroidism": {
        "description": "An underactive thyroid gland that produces insufficient thyroid hormone, slowing metabolism. Common symptoms include fatigue, weight gain, feeling cold, constipation, dry skin, and hair loss. Goitre (enlarged thyroid gland visible in the neck) is common in iodine-deficient areas such as the Bamenda highlands.",
        "causes": "Most commonly caused by Hashimoto's thyroiditis (autoimmune), iodine deficiency (common in highland areas like the North West Region of Cameroon), or as a result of thyroid surgery or radioactive iodine treatment.",
        "treatment": "Treated with daily oral levothyroxine (thyroid hormone replacement). Dose is adjusted by blood test (TSH level). Treatment is lifelong. Iodine deficiency-related hypothyroidism can be prevented and treated with iodised salt.",
        "prevention": ["Use iodised salt consistently", "Eat iodine-containing foods (fish, dairy)", "Screen thyroid function during pregnancy", "Seek care for unexplained weight gain, fatigue, or neck swelling"],
        "severity": "Medium",
    },
    # ── Global Respiratory ────────────────────────────────────────────────────
    "COVID-19": {
        "description": "A respiratory disease caused by the SARS-CoV-2 coronavirus, spread through droplets and aerosols from an infected person. Symptoms range from mild (cold-like illness) to severe (pneumonia, oxygen failure). High-risk groups: elderly, people with diabetes, hypertension, heart disease, obesity, or immunosuppression.",
        "causes": "Caused by SARS-CoV-2 virus, spread through breathing, coughing, sneezing, talking, or singing near an infected person. Close indoor contact without ventilation is the highest risk. Can also spread through touching contaminated surfaces and then touching face.",
        "treatment": "Mild: rest, fluids, paracetamol for fever. Seek care if breathing difficulty, chest pain, confusion, persistent high fever, or unable to keep fluids down. Severe cases need oxygen and hospital care. Antivirals (nirmatrelvir/ritonavir, remdesivir) are used in specific high-risk patients as prescribed.",
        "prevention": ["Vaccination protects against severe disease", "Wear a mask in crowded indoor spaces", "Ventilate rooms well", "Wash hands regularly", "Isolate if sick to protect others", "Seek care promptly if breathing difficulty develops"],
        "severity": "High",
    },
}


SYMPTOM_DESCRIPTIONS = {
    "Malaria": {
        "Fever": "High-grade fever (often 38.5–40°C) that comes in waves, typically spiking every 48–72 hours as parasites burst from red blood cells. The cycle goes: sudden intense cold/shivering → scorching hot fever → drenching sweat → brief relief, then repeats.",
        "Chills": "Intense, uncontrollable shaking and feeling bitterly cold even in warm weather, usually starting 30–60 minutes before the fever spike.",
        "Sweating": "Heavy, drenching sweat that follows the fever peak, often soaking clothes and bedding. This sweating phase is when the fever temporarily breaks.",
        "Headache": "Intense, pulsating pain felt behind the eyes and across the forehead, worsening with movement or bright light — distinctly more severe than a tension headache.",
        "Nausea": "Persistent queasiness that accompanies the fever spike, often making eating impossible.",
        "Vomiting": "Occurs during or shortly after the fever spike, triggered by the nausea and the parasitic toxins released into the bloodstream.",
        "Muscle aches": "Deep, widespread muscle and bone pain throughout the body, similar to severe influenza.",
        "Fatigue": "Extreme exhaustion between fever episodes — the person is unable to stand or perform normal activities.",
    },
    "Typhoid Fever": {
        "Prolonged fever": "Fever rises gradually over 3–5 days and stays persistently high (38.8–40°C), often without the periodic spiking-and-breaking pattern of malaria. It can persist for 3–4 weeks if untreated — unlike viral fevers that resolve within a week.",
        "Headache": "Dull, constant headache across the forehead, present throughout the illness.",
        "Weakness": "Progressive exhaustion and muscle weakness that increases as the days pass.",
        "Abdominal pain": "Dull or cramping pain in the right lower or central abdomen, sometimes tender when pressed.",
        "Constipation": "Common in early typhoid — the bowel slows down before diarrhoea may develop in later stages.",
        "Diarrhea": "In later stages, loose 'pea-soup' coloured stools may replace constipation.",
        "Rose spots": "Small (2–4mm), flat, faint pink spots on the chest and abdomen that appear in the first or second week. They blanch (fade) when pressed and last 2–5 days. Often missed but classic and diagnostic.",
    },
    "Cholera": {
        "Profuse watery diarrhea": "Sudden, massive, painless diarrhoea that looks like 'rice water' — pale, cloudy liquid with tiny white flecks. Volume can reach 10–20 litres per day in severe cases, unlike any other diarrhoeal illness.",
        "Vomiting": "Effortless vomiting of clear or cloudy fluid alongside the diarrhoea, typically without nausea.",
        "Muscle cramps": "Severe, very painful cramping in the leg muscles and abdomen due to rapid loss of potassium and sodium.",
        "Rapid dehydration": "Skin loses its elasticity (stays tented when pinched), eyes appear sunken, mouth becomes extremely dry, and urine output stops — all within hours.",
        "Low blood pressure": "Blood pressure drops dangerously as fluid loss leads to circulatory collapse — the person feels faint and may lose consciousness.",
    },
    "Pneumonia": {
        "Cough": "Productive cough bringing up thick, discoloured phlegm (yellow, green, or rusty-brown). The cough is painful and worsens with deep breathing — distinctly more severe than a cold cough.",
        "Fever": "High fever (38.5–40°C) with chills, often with a sudden onset. Unlike TB, it is acute rather than gradual.",
        "Chest pain": "Sharp, stabbing chest pain that worsens with every breath, cough, or movement. Located on one side where the affected lung is inflamed (pleuritic pain).",
        "Shortness of breath": "Breathing becomes rapid and laboured. The person may feel unable to get enough air, especially lying flat.",
        "Fatigue": "Extreme tiredness out of proportion to the fever, making walking or talking difficult.",
        "Chills": "Repeated episodes of shivering and feeling intensely cold, particularly at illness onset.",
    },
    "Tuberculosis": {
        "Chronic cough": "A persistent cough lasting more than 3 weeks that worsens over time — unlike a cold, it does not resolve. It starts dry, becoming productive with mucus. This duration is the key distinguishing feature.",
        "Chest pain": "A dull ache or tightness deep in the chest, sometimes worsening when breathing deeply or coughing.",
        "Coughing up blood": "Streaks of bright red blood in phlegm (haemoptysis). May range from small flecks to larger amounts. This is an urgent warning sign.",
        "Fatigue": "Progressive, severe exhaustion building over weeks — distinct from ordinary tiredness. The person becomes unable to work or perform daily tasks.",
        "Night sweats": "Drenching sweats during sleep that soak clothing and bedding despite normal or cool room temperature — a characteristic and distinguishing feature.",
        "Weight loss": "Gradual, unexplained loss of weight and muscle mass over weeks to months, often 5–10kg or more, without intentional dieting.",
    },
    "Meningitis": {
        "Sudden high fever": "Fever rises very rapidly to 39–40°C or higher, often within hours of first feeling unwell.",
        "Stiff neck": "The neck becomes rigid and extremely painful. The person cannot touch their chin to their chest — any attempt causes severe pain. This is a critical warning sign absent in most other fevers.",
        "Severe headache": "Often described as 'the worst headache of my life' — an extremely intense, diffuse, crushing pain, unlike any ordinary headache. The combination with stiff neck is highly alarming.",
        "Nausea": "Strong nausea, often with vomiting, accompanying the headache.",
        "Confusion": "Disorientation, difficulty thinking, unusual behaviour, or altered consciousness — from drowsiness to unresponsiveness.",
        "Sensitivity to light": "Even ordinary room light causes intense pain, making the person keep eyes shut and hide in darkness (photophobia). This is absent in most other headache conditions.",
    },
    "Dengue Fever": {
        "High fever": "Sudden onset of very high fever (39–40°C) starting 4–10 days after a mosquito bite. Unlike malaria, the fever is typically continuous rather than periodic.",
        "Severe headache": "Intense headache, usually felt directly behind the eyes, worsening with eye movement.",
        "Pain behind eyes": "A distinctive, deep, aching pain directly behind the eyeballs — particularly noticeable when moving the eyes. This retro-orbital pain is a characteristic feature.",
        "Joint pain": "Severe aching in joints — knees, ankles, hips — so intense that dengue was historically called 'breakbone fever'.",
        "Muscle aches": "Intense muscle pain, particularly in the back and limbs.",
        "Rash": "Appears 3–5 days after fever onset as a red flush or measles-like spots on the chest, spreading to the limbs. Distinctively shows 'white islands in a red sea' — patches of normal skin surrounded by redness. Unlike chickenpox, it is usually not itchy and does not blister.",
        "Mild bleeding": "Tiny pinpoint red or purple spots under the skin (petechiae), nosebleeds, or gum bleeding. Black stools or blood in urine are dangerous warning signs requiring urgent care.",
    },
    "Dysentery": {
        "Bloody or mucus-filled diarrhea": "Frequent passage of small amounts of stool mixed with bright red blood and/or thick mucus — slimy, bloodstained stools. Unlike cholera's rice-water diarrhoea, dysentery stool is small in volume but contains visible blood and mucus.",
        "Abdominal pain": "Severe, cramping lower abdominal pain coming in waves, typically just before passing stool.",
        "Fever": "Moderate to high fever (38–40°C) from the start.",
        "Tenesmus": "A painful, urgent feeling of needing to pass stool even when the bowel is nearly empty. The person strains repeatedly but passes only small amounts of blood and mucus — deeply distressing.",
        "Dehydration": "Progressive fluid loss causing dry mouth, reduced urine, and weakness from frequent stools.",
    },
    "Gastroenteritis": {
        "Diarrhea": "Loose or watery stools, usually without blood, 3–10 times per day.",
        "Vomiting": "Forceful ejection of stomach contents, often preceding diarrhoea by several hours.",
        "Abdominal pain": "Cramping pain across the lower or central abdomen, often relieved briefly after passing stool.",
        "Nausea": "Persistent queasiness reducing the desire to eat or drink.",
        "Fever": "Mild to moderate fever (37.5–38.5°C) — lower than in bacterial infections like typhoid.",
        "Weakness": "General tiredness mainly from fluid and electrolyte loss.",
    },
    "Asthma": {
        "Wheezing": "A high-pitched, musical whistling sound when breathing out (and sometimes in), heard clearly or even across a room. Caused by air being forced through narrowed airways — absent in most other conditions.",
        "Shortness of breath": "Feeling unable to breathe in enough air, especially with exertion, cold air, or during a flare. The person may speak in short sentences or whisper.",
        "Chest tightness": "A sensation of pressure or constriction in the chest, as if a band is being tightened around it — not painful like pleurisy, but restrictive.",
        "Cough": "Often worse at night or early morning — dry, repetitive, triggered by exercise, cold, dust, or smoke. In some people, cough is the only symptom of asthma.",
    },
    "Chickenpox": {
        "Fever": "Mild to moderate fever (37.8–38.9°C) appearing 1–2 days before the rash. In children it is usually mild; in adults it can be higher.",
        "Itchy rash": "Begins as small flat red spots (macules) → raised bumps (papules) → clear fluid-filled blisters (vesicles) → crusts over. New crops appear for 5–7 days, so all stages coexist at the same time. Starts on the scalp, face, and trunk before spreading to limbs. Unlike dengue rash, it is intensely itchy. Unlike HIV rash, it blisters.",
        "Blisters": "Clear, dewdrop-like blisters on a red base, 2–4mm in size. Each blister is delicate — it breaks easily and scabs over within 1–2 days.",
        "Fatigue": "Significant tiredness beginning before the rash and persisting throughout.",
        "Loss of appetite": "Reduced desire to eat, especially if blisters develop inside the mouth making eating painful.",
    },
    "Measles": {
        "High fever": "Begins 2–4 days before the rash and is often very high (39–40.5°C) — the highest of any common childhood illness.",
        "Cough": "A harsh, barking cough that is persistent and dry throughout the illness.",
        "Runny nose": "Profuse, watery nasal discharge from the start.",
        "Red eyes": "Marked redness and watering of the eyes with sensitivity to light, giving a sorrowful appearance.",
        "Koplik spots": "Tiny white or bluish-white spots with a red ring, seen inside the cheeks opposite the molar teeth 1–2 days before the rash appears. These are unique to measles and highly diagnostic — look for them early.",
        "Rash": "Appears day 3–5 after fever, starting at the hairline and behind the ears, then spreading downward across the face, neck, trunk, and limbs in a classic head-to-toe progression. Red, slightly raised blotches that merge into large patches. Unlike chickenpox: it does not blister and is not itchy. Unlike dengue: it progresses head-to-toe.",
    },
    "Scabies": {
        "Severe itching": "Intense, relentless itching — the hallmark. It is caused by an allergic reaction to the mite, its eggs, and waste. So severe it disrupts sleep and dominates the person's existence.",
        "Burrow tracks": "Thin, grey or skin-coloured wavy lines (3–10mm long) on the skin surface — the tunnels dug by burrowing mites. Most visible between fingers, on wrists, around the waist, genitals, and ankles. These tracks are diagnostic and absent in other itchy conditions.",
        "Rash": "Tiny red bumps and blisters scattered around burrow tracks and in skin folds — the body's allergic reaction.",
        "Skin sores": "Open sores and crusted areas from scratching, which can become secondarily infected.",
        "Night itching": "The itching becomes dramatically worse at night when warmth of the bed activates the mites — a distinguishing feature from other itchy rashes.",
    },
    "Diabetes Mellitus": {
        "Increased thirst": "Unquenchable thirst persisting despite drinking large amounts — the kidneys draw extra water to flush out excess glucose, leaving the body perpetually dehydrated.",
        "Frequent urination": "Unusually frequent, large-volume urination including waking at night multiple times. The urine may attract ants due to its sugar content — a traditional diagnostic clue.",
        "Fatigue": "Persistent tiredness and lack of energy because cells cannot use glucose efficiently for fuel despite high blood sugar.",
        "Blurred vision": "Fluctuating blurry vision caused by fluid shifts in the eye lens as blood sugar levels change.",
        "Slow-healing sores": "Cuts, blisters, or ulcers — especially on the feet — that take weeks or months to heal, or fail to heal entirely, due to poor circulation and reduced immunity.",
    },
    "Hypertension": {
        "Headache": "Usually a dull throbbing headache at the back of the head, often on waking. However, most hypertension causes no symptoms at all — it is frequently completely silent until a complication occurs.",
        "Dizziness": "Lightheadedness or imbalance, particularly when standing up suddenly.",
        "Blurred vision": "Visual disturbances or temporary loss of vision when blood pressure rises very high, from retinal vessel damage.",
        "Chest pain": "A heavy pressure in the chest if the heart is under excessive strain from persistent high pressure.",
        "Shortness of breath": "Difficulty breathing — particularly lying flat — if the heart begins to fail under the load.",
    },
    "Iron Deficiency Anemia": {
        "Fatigue": "Persistent, severe tiredness disproportionate to activity — exhausted even after rest, because the blood is carrying less oxygen to every organ and muscle.",
        "Pale skin": "Noticeable pallor of the skin, inner lower eyelid (pull down to see), gums, and nail beds — all appear lighter or whitish instead of their normal pinkish-red.",
        "Dizziness": "Lightheadedness and near-fainting, especially when standing, climbing stairs, or exerting.",
        "Shortness of breath": "Breathlessness with mild exertion — walking a short distance — because the blood cannot carry enough oxygen to meet demand.",
        "Fast heartbeat": "A racing or pounding heartbeat (palpitations) as the heart pumps faster to compensate for the oxygen deficit.",
    },
    "Cystitis UTI": {
        "Frequent urination": "An urgent, frequent need to urinate — going every few minutes — but passing only a small amount each time.",
        "Painful urination": "A burning or stinging sensation during urination (dysuria), often described as 'like passing razors'. Unlike kidney stones, the pain is during urination, not before.",
        "Pelvic pain": "A dull ache or pressure low in the pelvis, above the pubic bone.",
        "Blood in urine": "Urine appearing pink, red, or brownish from bleeding caused by bladder wall inflammation — requires medical evaluation.",
        "Lower abdominal pain": "Cramping or discomfort in the lower abdomen, especially when the bladder is full.",
    },
    "Helicobacteriosis PepticUlcer": {
        "Burning stomach pain": "A gnawing, burning pain in the upper central abdomen (epigastrium) occurring 1–3 hours after meals or when the stomach is empty — typically relieved briefly by eating or antacids, then returning.",
        "Nausea": "Persistent queasy feeling, especially in the morning or when the stomach is empty.",
        "Bloating": "A feeling of fullness or distension in the upper abdomen even after small meals.",
        "Heartburn": "A burning sensation rising from the stomach up into the chest and throat.",
        "Loss of appetite": "Reduced desire to eat, often from fear of pain after meals.",
    },
    "Common Cold": {
        "Runny nose": "Clear, watery nasal discharge in the first 1–3 days that may become thicker and yellower as the cold progresses — this colour change does not necessarily mean bacterial infection.",
        "Sore throat": "Scratchiness and mild pain at the back of the throat, usually worst on the first 1–2 days.",
        "Cough": "Initially dry and tickly, becoming productive later. Milder than pneumonia or TB cough — does not persist for weeks.",
        "Sneezing": "Frequent sneezing, particularly in the first 1–2 days.",
        "Mild fever": "Low-grade fever (37.2–38°C) if present at all. High fever in an adult is more suggestive of influenza.",
        "Headache": "Mild, generalised headache from nasal congestion and sinus pressure.",
    },
    "Skin Fungal Infection": {
        "Itchy skin": "Moderate to intense itching in the affected area, worsening in warm, sweaty conditions.",
        "Ring-shaped rash": "Circular red patches with a slightly raised, scaly, advancing border and clearer skin in the centre — the classic appearance. Distinctly different from the linear burrow tracks of scabies or the fluid blisters of chickenpox.",
        "Red scaly skin": "Reddened, flaking skin in body folds (groin, armpits, between toes) that may crack and weep.",
        "Skin peeling": "Flaking or peeling skin, especially between the toes in athlete's foot.",
        "Skin lesions": "Patches of discoloured skin — lighter or darker than surrounding skin, as in pityriasis versicolor.",
    },
    "Hepatitis A": {
        "Jaundice": "Yellowing of the skin and whites of the eyes (sclera), appearing 1–2 weeks after other symptoms. The yellow colour deepens over days, then slowly fades.",
        "Fatigue": "Profound exhaustion often appearing before jaundice — one of the earliest signs.",
        "Nausea": "Persistent queasiness and aversion to food and alcohol, often lasting weeks.",
        "Vomiting": "Frequent vomiting in the acute phase.",
        "Abdominal pain": "Dull aching pain in the upper right abdomen, directly over the liver.",
        "Dark urine": "Urine turns dark brown (like dark tea or cola) before skin jaundice becomes visible — an important early warning sign to recognise.",
        "Loss of appetite": "Total loss of interest in food, persisting for weeks.",
        "Fever": "Mild to moderate fever in the pre-jaundice phase.",
    },
    "Hepatitis B": {
        "Jaundice": "Yellow discolouration of skin and eyes, varying from mild to deep yellow depending on liver inflammation.",
        "Dark urine": "Deep amber or brown urine, appearing as the liver fails to process bilirubin.",
        "Fatigue": "Severe, prolonged fatigue that may persist for months in chronic infection.",
        "Yellow eyes": "The white part of the eyes (sclera) turns distinctly yellow — often the most visible sign.",
        "Abdominal pain": "Discomfort and tenderness in the upper right abdomen, directly over the liver.",
        "Joint pain": "Aching joints — particularly in early acute infection — sometimes appearing before jaundice.",
        "Loss of appetite": "Near-total loss of appetite that may cause significant weight loss.",
        "Nausea": "Persistent nausea and feeling sick at the smell or thought of food.",
    },
    "Yellow Fever": {
        "High fever": "Sudden onset of high fever (38.5–40°C) with an apparent improvement around day 3–4 (the 'period of remission') — this is deceptive, as a toxic phase with organ failure may follow.",
        "Jaundice": "Yellowing of skin and eyes from liver damage — the defining sign that gives the disease its name. Appears around day 4–5.",
        "Muscle aches": "Severe muscle pain, especially in the back and legs.",
        "Severe headache": "Intense frontal headache from the onset.",
        "Nausea": "Severe nausea, often with vomiting.",
        "Vomiting": "'Black vomit' — dark, coffee-ground-like material from internal bleeding — is a severe sign indicating liver and kidney failure, distinct from other causes of vomiting.",
        "Back pain": "Prominent back pain from the early phase.",
        "Yellow eyes": "The sclera turns deeply yellow from bilirubin accumulation.",
    },
    "Whooping Cough": {
        "Paroxysmal cough": "Begins as an ordinary cough for 1–2 weeks, then develops into violent, uncontrollable coughing fits: 5–10 rapid coughs in a single breath, followed by the characteristic high-pitched 'whoop' as the person gasps for air. The fits can last a minute, turn the face red or blue, and often end in vomiting. This pattern is highly distinctive.",
        "Runny nose": "Watery nasal discharge in the early cold-like stage before severe coughing begins.",
        "Fever": "Usually low-grade or absent — the violent cough, not fever, distinguishes this illness.",
        "Sneezing": "Present in the early stage.",
        "Vomiting": "Coughing fits are often severe enough to trigger vomiting, particularly in children.",
        "Fatigue": "Exhaustion from the physical effort of repeated coughing fits throughout the day and night.",
        "Weakness": "Progressive weakness as the illness continues for weeks.",
    },
    "Mumps": {
        "Parotid swelling": "Swelling of the parotid salivary glands in front of and below the ears causes the characteristic 'chipmunk cheeks' or 'hamster face' appearance. One or both sides may be affected. This is unique to mumps among common infections.",
        "Jaw stiffness": "Pain and stiffness when opening the mouth or chewing, due to the swollen glands pressing on the jaw.",
        "Fever": "Moderate fever (38–39°C) from the start.",
        "Headache": "Generalised headache accompanying the fever.",
        "Muscle aches": "Mild to moderate muscle aching.",
        "Fatigue": "Tiredness and malaise throughout the illness.",
        "Loss of appetite": "Reduced desire to eat, partly because chewing is painful.",
    },
    "Rubella": {
        "Mild fever": "Low-grade fever (37.2–38°C), usually appearing before the rash.",
        "Rash": "Fine, flat pink-to-red spots (macules) beginning on the face then spreading down the neck, trunk, and limbs over 24 hours. The face clears as the trunk rash appears. Lighter and shorter-lived (2–3 days) than measles; does not blister like chickenpox.",
        "Swollen lymph nodes": "Tender, swollen lymph nodes behind the ears, at the back of the neck, and behind the head — a characteristic feature that may appear before the rash and persist after.",
        "Red eyes": "Mild redness and watering of the eyes.",
        "Runny nose": "Mild nasal congestion or discharge.",
        "Joint pain": "Aching joints, especially fingers and wrists — more common and noticeable in adult women.",
        "Headache": "Mild, diffuse headache.",
    },
    "Sinusitis": {
        "Headache": "Pressure and pain across the forehead, cheeks, and around the eyes. Bending forward dramatically worsens the pain — a useful distinguishing feature from tension headache.",
        "Nasal congestion": "Blocked, stuffy nose making breathing through the nose difficult or impossible.",
        "Facial pain": "Tenderness and pressure when pressing over the cheekbones and forehead, directly over the sinus cavities.",
        "Runny nose": "Thick, coloured (yellow or green) nasal discharge that may drip down the back of the throat (postnasal drip).",
        "Cough": "Persistent cough from postnasal drip — mucus draining down the throat, worsening when lying down at night.",
        "Sore throat": "Irritation at the back of the throat from dripping mucus.",
        "Fever": "Low-grade fever if bacterial infection is present.",
    },
    "Tonsillitis": {
        "Sore throat": "Severe throat pain — often among the worst the person has experienced — making swallowing extremely painful. The tonsils appear enlarged, red, and often coated with white or yellow patches of pus.",
        "Difficulty swallowing": "Pain on swallowing even saliva. The person may drool, refuse liquids, or have a muffled 'hot potato' voice.",
        "Swollen lymph nodes": "Tender, enlarged lymph nodes on both sides of the neck, easily felt and visible.",
        "High fever": "High fever (38.5–40°C), often with chills.",
        "Headache": "Headache accompanying the fever.",
        "Fatigue": "Significant tiredness and malaise.",
        "Loss of appetite": "Refusal to eat because swallowing is too painful.",
    },
    "Ear Infection": {
        "Ear pain": "Sharp, stabbing, or throbbing pain inside the ear, which may be continuous or wave-like. In young children, they may tug at the ear or be unusually irritable without being able to describe the pain.",
        "Fever": "Moderate fever accompanying the ear pain.",
        "Hearing loss": "Reduced hearing or a muffled, blocked feeling in the ear from fluid buildup behind the eardrum.",
        "Headache": "Generalised headache from the infection and fever.",
        "Dizziness": "Sense of imbalance or spinning, if the inner ear is involved.",
        "Fatigue": "Tiredness accompanying the illness.",
        "Pus or discharge": "Yellow, white, or bloody fluid draining from the ear if the eardrum has ruptured — this often suddenly relieves the severe pain.",
    },
    "Conjunctivitis": {
        "Red eyes": "The white of the eye (sclera) turns bright red or pink from inflammation. Both eyes are often affected.",
        "Eye discharge": "Sticky, crusting discharge from the eye. Bacterial: thick, yellow-green — causes eyelids to seal shut on waking. Viral: watery. Allergic: stringy or ropy. The type of discharge helps identify the cause.",
        "Eye itching": "Intense itching and a gritty or sandy sensation in the eye, particularly in allergic conjunctivitis.",
        "Eye pain": "Mild discomfort or burning — severe pain suggests a more serious eye condition.",
        "Sensitivity to light": "Mild discomfort in bright light.",
        "Headache": "Mild headache from eye strain and inflammation.",
    },
    "Herpes Zoster": {
        "Blisters": "Small, fluid-filled blisters appearing in a band or strip along one nerve pathway on one side of the body — never crossing the midline. This strict one-sided distribution is diagnostic. The blisters break, weep, and crust over in 7–10 days.",
        "Rash": "Red, inflamed skin appears 2–3 days before the blisters form, strictly following the path of one nerve — a stripe on the chest, back, face, or limb.",
        "Itchy rash": "Intense itching and tingling in the affected area, often beginning days before any visible rash or blisters appear.",
        "Fever": "Mild fever at onset.",
        "Fatigue": "Tiredness and general malaise throughout the illness.",
        "Headache": "Headache, particularly if the rash involves the head or face.",
        "Sensitivity to light": "Light sensitivity if the rash involves the eye area.",
        "Skin sores": "Open, weeping sores as blisters rupture — can become secondarily infected if scratched.",
    },
    "Appendicitis": {
        "Abdominal pain": "Classically begins as vague, cramping pain around the navel, then over 12–24 hours shifts and concentrates in the lower right abdomen. It becomes constant, worsening with movement, coughing, or pressing then suddenly releasing the area (rebound tenderness). This migration of pain is highly characteristic.",
        "Fever": "Low-grade fever initially (37.5–38.5°C), rising if the appendix ruptures.",
        "Nausea": "Nausea that accompanies the onset of pain.",
        "Vomiting": "One or two episodes of vomiting after the pain begins — not usually repeated.",
        "Loss of appetite": "Complete loss of appetite from the onset.",
        "Weakness": "General malaise and weakness.",
        "Constipation": "Reduced or absent bowel movement due to pain and inflammation.",
    },
    "Kidney Stones": {
        "Back pain": "Sudden, excruciating, wave-like (colicky) pain in the back, flank, or below the ribs on one side, radiating downward toward the groin as the stone moves. One of the most severe pains a person can experience — they cannot find a comfortable position.",
        "Blood in urine": "Urine appears pink, red, or dark brown from the stone scratching the urinary tract lining.",
        "Painful urination": "Burning or stinging when urinating as the stone nears the bladder or urethra.",
        "Nausea": "Severe nausea accompanying the pain, from shared nerve pathways between the ureter and intestines.",
        "Vomiting": "May accompany severe pain episodes.",
        "Frequent urination": "Urgent need to urinate frequently when the stone is in the lower ureter near the bladder.",
        "Lower abdominal pain": "Pain moving into the lower abdomen and groin as the stone descends.",
    },
    "Sickle Cell Crisis": {
        "Joint pain": "Severe, deep, throbbing pain in bones and joints — chest, back, hips, and long bones. Caused by sickled cells blocking blood vessels (vaso-occlusive crisis). The pain is often more intense than any other pain the person has experienced.",
        "Fatigue": "Chronic, severe tiredness from anaemia — sickled red blood cells break down faster than normal ones.",
        "Pale skin": "Pallor of the skin, mucous membranes, and conjunctiva from anaemia.",
        "Chest pain": "Acute chest syndrome — chest pain with breathing difficulty — is a serious complication requiring urgent hospital care.",
        "Shortness of breath": "Difficulty breathing from acute chest syndrome or severe anaemia.",
        "Jaundice": "Yellowing of the eyes and skin from breakdown products of destroyed red blood cells.",
        "Swollen feet": "Painful swelling of hands and feet (dactylitis), particularly in young children — often the very first sign of the disease.",
    },
    "Tetanus": {
        "Jaw stiffness": "The first and most characteristic symptom — jaw muscles clamp shut (lockjaw/trismus), making it impossible to fully open the mouth. This develops 3–21 days after a wound and progresses to affect other muscles.",
        "Stiff neck": "Neck muscle rigidity follows the jaw stiffness as the toxin spreads.",
        "Muscle cramps": "Painful, generalised muscle spasms throughout the body. The back may arch violently (opisthotonus). Any stimulus — noise, light, or touch — can trigger a life-threatening whole-body spasm.",
        "Fever": "Moderate fever from muscle activity and the underlying infection.",
        "Headache": "Headache accompanying the muscular tension.",
        "Difficulty swallowing": "Difficulty swallowing from throat muscle rigidity.",
        "Sweating": "Profuse sweating from muscle spasms and autonomic nervous system involvement.",
    },
    "Diphtheria": {
        "Sore throat": "Sore throat with a thick, grey-white membrane coating the tonsils and back of the throat that bleeds when disturbed — unlike the removable white patches of tonsillitis. This membrane is diagnostic.",
        "Hoarse voice": "Hoarseness and a barking or stridor-like quality to the voice from airway involvement.",
        "Difficulty swallowing": "Throat membrane and swelling make swallowing painful.",
        "Fever": "Moderate fever — generally lower than other severe throat infections.",
        "Swollen lymph nodes": "Enlarged lymph nodes in the neck cause the 'bull neck' appearance.",
        "Fatigue": "Significant toxaemia from the bacterial toxin — the person appears ill beyond what the fever would suggest.",
        "Runny nose": "Blood-stained nasal discharge in some forms of the disease.",
    },
    "Ringworm": {
        "Ring-shaped rash": "Circular, red, scaly patches with a raised, active, advancing edge and a clearing centre — the 'ring' appearance. Multiple overlapping rings may form. Unlike HIV rash (flat, central) or chickenpox (blistered), this is distinctly circular and expanding.",
        "Itchy skin": "Persistent itching at the advancing edge of the ring, where the fungus is most active.",
        "Red scaly skin": "Redness and fine scaling inside and around the rings.",
        "Skin peeling": "Fine, powdery or sheet-like peeling at lesion edges.",
        "Skin lesions": "In scalp ringworm (tinea capitis): patchy hair loss with broken hairs and scaling — may look like dandruff with bald spots.",
        "Hair loss": "In scalp involvement, hair breaks off close to the root, leaving short stubs and bald patches — a distinctive sign.",
    },
    "Leptospirosis": {
        "High fever": "Sudden onset of high fever (38.5–40°C) with severe chills.",
        "Muscle aches": "Severe muscle pain especially in the calves and thighs — so intense that walking is difficult. This pronounced calf tenderness is a key distinguishing feature.",
        "Headache": "Intense headache, often felt behind the eyes.",
        "Red eyes": "Conjunctival suffusion — the whites of the eyes become red and bloodshot without discharge — a characteristic early finding distinct from conjunctivitis.",
        "Jaundice": "In severe leptospirosis (Weil's disease), jaundice appears after 4–7 days from liver involvement.",
        "Vomiting": "Nausea and vomiting accompanying the fever.",
        "Rash": "A transient rash may appear, though less prominent than in dengue.",
        "Dark urine": "Dark urine from kidney or liver involvement — a warning sign of severe disease.",
    },
    "Typhus": {
        "Sudden high fever": "Abrupt onset of very high fever (39–40°C) with rigors, lasting 2 weeks if untreated.",
        "Severe headache": "Intense, debilitating headache from the start — one of the most prominent features.",
        "Rash": "Appears around day 4–6, starting on the trunk and spreading to the limbs (typically sparing the face, palms, and soles). Small, flat pink or red spots that may darken and become purplish. Unlike measles (head-to-toe), typhus rash begins on the trunk. Unlike dengue, it persists longer.",
        "Muscle aches": "Severe, generalised muscle pain.",
        "Fatigue": "Extreme weakness and prostration.",
        "Confusion": "Confusion or altered consciousness in severe cases — the word 'typhus' comes from Greek for 'smoke', referring to this mental clouding.",
        "Chills": "Violent shaking chills at fever onset.",
    },
    "Brucellosis": {
        "Fever": "An undulating (wave-like) fever that rises and falls in a regular pattern, sometimes cycling over weeks — often worse in the evenings. This undulating pattern distinguishes it from most other fevers.",
        "Sweating": "Profuse sweating, especially at night, with a characteristic musty odour — a classic though uncommon feature.",
        "Joint pain": "Aching joints, especially large joints — hips, knees, sacroiliac joints — and the spine.",
        "Muscle aches": "Widespread muscle pain and weakness.",
        "Fatigue": "Profound, debilitating fatigue persisting even between fever episodes.",
        "Loss of appetite": "Reduced appetite and progressive weight loss.",
        "Back pain": "Low back pain from spinal involvement (spondylitis), a common complication of untreated brucellosis.",
        "Night sweats": "Heavy sweating during sleep, often soaking bedding.",
    },
    "Septicemia": {
        "High fever": "Very high fever or, paradoxically, abnormally low temperature (below 36°C) in severe cases — both indicate systemic infection. The temperature extremes are alarming.",
        "Confusion": "Sudden confusion, agitation, or altered consciousness — a critical warning sign indicating inadequate oxygen supply to the brain.",
        "Fast heartbeat": "Rapid heart rate (>90 beats/min) as the body tries to compensate for falling blood pressure.",
        "Shortness of breath": "Rapid breathing (>20 breaths/min) as the body attempts to correct acid-base imbalance from poor circulation.",
        "Low blood pressure": "Blood pressure drops dramatically — the person becomes cold, clammy, and may collapse. Septic shock is immediately life-threatening.",
        "Chills": "Violent shivering with the onset of fever.",
        "Sweating": "Cold, clammy skin and drenching sweat as blood pressure falls.",
    },
    "Pelvic Inflammatory Disease": {
        "Pelvic pain": "Dull, constant pain low in the abdomen, usually on both sides. May worsen during intercourse (dyspareunia), menstruation, or urination.",
        "Vaginal discharge": "Abnormal vaginal discharge — often yellow or green with an unpleasant odour — indicating active infection of the cervix and uterus.",
        "Lower abdominal pain": "Cramping lower abdominal pain that may be mild initially and gradually worsen over days.",
        "Fever": "Fever above 38°C, sometimes with chills.",
        "Painful urination": "Burning on urination if the bladder or urethra is also irritated.",
        "Missed period": "Irregular or missed periods from the infection's effect on reproductive structures.",
    },
    "Benign Prostatic Hyperplasia": {
        "Frequent urination": "Need to urinate very often, including waking multiple times at night (nocturia), even when only small amounts of urine are produced.",
        "Reduced urination": "Weak, slow, or intermittent urine stream — may start and stop, dribble at the end, require straining. The person feels the bladder is never fully empty.",
        "Sleep disturbances": "Repeated night waking to urinate, significantly disrupting sleep quality.",
        "Lower abdominal pain": "A dull sense of pressure or fullness above the pubic bone from incomplete bladder emptying.",
        "Weakness": "General fatigue from sleep disruption and potentially from kidney effects.",
        "Back pain": "Mild back or flank pain if the condition causes kidney pressure.",
    },
    "Migraine": {
        "Severe headache": "Intense, pulsating or throbbing pain — usually on one side of the head. Worsened by physical activity, light, sound, and smell. Lasts 4–72 hours without treatment. Distinguishable from tension headache by its severity, one-sidedness, and accompanying symptoms.",
        "Sensitivity to light": "Extreme pain discomfort in bright light (photophobia) — the person must go to a dark room and may be unable to function.",
        "Sensitivity to sound": "Ordinary sounds feel unbearably loud and worsen the headache.",
        "Nausea": "Persistent nausea making it impossible to eat or drink during an attack.",
        "Vomiting": "Occurs in many attacks — may temporarily relieve the headache in some people.",
        "Blurred vision": "Visual aura preceding the headache: zigzag patterns, flashing lights, blind spots, or tunnel vision, lasting 20–60 minutes. These visual disturbances before the pain are diagnostic of migraine with aura.",
        "Dizziness": "Vertigo or dizziness may accompany, particularly in vestibular migraine.",
    },
    "Epilepsy": {
        "Seizures": "Episodes of abnormal electrical brain activity ranging from brief staring spells (absence seizures) to full convulsions: stiff muscles → rhythmic jerking of the whole body → unconsciousness → possible loss of bladder control. Each episode is usually 1–3 minutes.",
        "Confusion": "A period of confusion and disorientation immediately after a seizure (postictal state), lasting minutes to hours — the person has no memory of the event.",
        "Confusion at night": "Nocturnal seizures may cause the person to wake confused and disoriented, often without realising a seizure occurred.",
        "Muscle cramps": "Involuntary muscle jerking or stiffening during the seizure.",
        "Fatigue": "Severe exhaustion following a seizure — sometimes lasting a full day — as the brain recovers.",
        "Weakness": "Weakness or temporary paralysis on one side of the body after a seizure (Todd's paralysis), lasting minutes to hours.",
        "Poor coordination": "Unsteady walking or clumsiness following a seizure, or as a persistent feature in some seizure types.",
    },
    "Onchocerciasis": {
        "Severe itching": "Intense, relentless whole-body itching among the most severe of any disease — caused by the immune response to dying microfilariae in the skin. Continuous scratching leads to thickened, scarred skin.",
        "Skin lesions": "Chronic skin changes: depigmentation (loss of colour, creating a 'leopard skin' pattern of pale and dark patches), wrinkling and thickening, and firm nodules under the skin where adult worms live.",
        "Blurred vision": "Progressive visual impairment from microfilariae invading the eye. Untreated, leads to corneal scarring and permanent blindness — known as 'river blindness'.",
        "Rash": "Papular rash and raised bumps from skin microfilariae, particularly on the torso and thighs.",
        "Skin peeling": "Dry, rough, peeling skin in chronic infection.",
        "Swollen lymph nodes": "Enlarged lymph nodes in the groin from the immune response.",
        "Weight loss": "Progressive weight loss and wasting in long-standing infection.",
    },
    "Filariasis": {
        "Swollen feet": "Massive, firm swelling of the legs, feet, or genitals (lymphoedema) from long-standing lymphatic blockage. The skin becomes thick, rough, and warty — a condition called elephantiasis. This level of swelling is unique to filariasis and lymphatic obstruction.",
        "Ankle swelling": "Pitting oedema of the ankles and lower legs in early stages, before elephantiasis develops.",
        "Skin lesions": "Thickened, folded, rough skin over swollen areas.",
        "Fever": "Episodic fever with chills during acute lymphangitis attacks, when bacteria invade the damaged lymphatics.",
        "Skin sores": "Ulcers and sores on swollen skin, prone to infection.",
        "Weakness": "Fatigue and weakness during fever episodes.",
        "Itchy skin": "Itching of the swollen, thickened skin.",
    },
    "HIV AIDS": {
        "Fatigue": "Profound, persistent tiredness not improved by rest — the immune system works continuously, and opportunistic infections drain energy. In AIDS, fatigue can be completely debilitating.",
        "Weight loss": "Unintentional loss of >10% of body weight combined with diarrhoea or fever for more than 30 days — HIV wasting syndrome. Unlike dieting, the weight loss is accompanied by illness.",
        "Night sweats": "Drenching sweats during sleep soaking the bedding and clothing, even without fever — a hallmark symptom of HIV and certain other infections.",
        "Swollen lymph nodes": "Persistent swelling of lymph nodes in the neck, armpits, and groin lasting more than 3 months without obvious infection — persistent generalised lymphadenopathy. Helps distinguish HIV from a short-term infection.",
        "Diarrhea": "Chronic or recurrent watery diarrhoea from gut opportunistic infections (e.g., cryptosporidium, CMV) that persist for weeks and contribute to weight loss.",
        "Fever": "Recurrent low-grade fevers from immune activation and opportunistic infections.",
        "Rash": "In acute HIV infection (2–4 weeks after exposure): flat, reddish-pink spots (maculopapular rash) mainly on the trunk, face, and arms — not itchy, non-blistering, lasting 1–2 weeks. Distinctly different from: chickenpox (intensely itchy, blistered), dengue (white islands in red sea), measles (head-to-toe spread with cough/runny nose).",
        "Loss of appetite": "Reduced appetite and nausea, worsened by oral thrush (white patches in the mouth) or oesophageal infections.",
        "Cough": "Persistent dry or productive cough from Pneumocystis pneumonia (PCP) or TB — both common in AIDS.",
        "Sore throat": "Recurring throat pain from oral candidiasis (thrush) — white patches on the tongue and inner cheeks.",
    },
    "Skin Abscess": {
        "Skin sores": "A painful, tender, raised lump under the skin filled with pus. The skin over it is red, warm, and tense. As it matures, the centre becomes soft and may develop a yellow-white 'head' (pointing). This is visually distinct from a rash or ring lesion.",
        "Pus or discharge": "Thick, creamy, yellow or yellow-green pus that drains when the abscess is lanced or ruptures spontaneously.",
        "Rash": "Surrounding redness and warmth (cellulitis) spreading outward from the abscess — different from the dry, scaly rings of ringworm or the blistered pattern of chickenpox.",
        "Fever": "Fever if the infection is spreading beyond the abscess.",
        "Fatigue": "Tiredness from the immune response.",
        "Swollen lymph nodes": "Tender swollen lymph nodes in the region draining the abscess (e.g., armpit nodes for a hand abscess).",
    },
    "Anaphylaxis": {
        "Rash": "Sudden onset of widespread hives (urticaria) — raised, itchy, red welts of varying sizes — or generalised flushing. Appears within minutes of exposure to the trigger. The speed of onset distinguishes it from other rashes.",
        "Shortness of breath": "Severe difficulty breathing from swelling of the airway (throat and vocal cords) and bronchospasm. The person may be unable to speak a full sentence — life-threatening within minutes.",
        "Fast heartbeat": "Rapid, weak pulse as the heart races to compensate for falling blood pressure.",
        "Dizziness": "Lightheadedness and near-fainting from sudden blood pressure drop.",
        "Low blood pressure": "Dramatic, rapid fall in blood pressure causing pallor, weakness, and collapse — anaphylactic shock.",
        "Nausea": "Sudden nausea and cramping abdominal pain.",
        "Swollen feet": "Swelling of the face, lips, tongue, and throat (angioedema) — throat swelling is immediately life-threatening.",
        "Sweating": "Pale, cold, clammy skin with profuse sweating as the body goes into shock.",
    },
    # ── STIs ──────────────────────────────────────────────────────────────────
    "Gonorrhea": {
        "Genital discharge": "Thick, creamy yellow or greenish pus-like discharge from the penis or vagina — often described as 'like toothpaste'. In men, it drips from the tip of the penis. In women, it may be mixed with normal vaginal discharge and less obvious. Unlike the watery discharge of trichomoniasis, gonorrhea discharge is thick and purulent.",
        "Painful urination": "A burning, stinging sensation when urinating — often the first noticeable symptom in men. Described as 'like passing razor blades'. Begins within 1–14 days of infection.",
        "Pelvic pain": "Dull ache or sharp pain in the lower abdomen and pelvis in women, indicating spread of infection into the uterus or fallopian tubes. Severe pelvic pain with fever may signal pelvic inflammatory disease.",
        "Vaginal discharge": "Increased vaginal discharge, often yellow or green, sometimes with an unusual odour. Many women mistake it for a yeast infection.",
        "Sore throat": "When gonorrhea infects the throat through oral sex, it causes a persistent sore throat or pain on swallowing — indistinguishable from a strep throat. Often no other genital symptoms are present.",
        "Swollen lymph nodes": "Tender swollen lymph nodes in the groin from the immune response to genital infection.",
        "Fever": "Mild fever may develop, especially if the infection has spread beyond the initial site.",
    },
    "Syphilis": {
        "Genital sores": "Primary syphilis: a single painless, firm, round ulcer (chancre) with clean edges — typically on the genitals, anus, lips, or inside the mouth. It appears 10–90 days after infection, lasts 3–6 weeks, and heals on its own even without treatment. Unlike herpes sores which are painful and clustered, the syphilis chancre is classically painless and solitary — this is the diagnostic clue.",
        "Rash": "Secondary syphilis (6–12 weeks after chancre): a copper-brown or red non-itchy rash that classically appears on the PALMS and SOLES — this specific location is highly suggestive of syphilis. The rash can also appear on the trunk and all body surfaces. Unlike most other rashes, it is usually neither itchy nor painful.",
        "Swollen lymph nodes": "Generalised painless swelling of lymph nodes throughout the body — neck, armpits, and groin — during the secondary stage.",
        "Fever": "Mild fever during secondary syphilis, part of the systemic immune response to bacterial spread.",
        "Fatigue": "Generalised tiredness, malaise, and loss of energy during the secondary phase.",
        "Headache": "Dull persistent headache during secondary syphilis from systemic infection.",
        "Muscle aches": "Widespread muscle aches and body soreness, resembling flu, in the secondary stage.",
        "Skin sores": "Flat, moist, grey-white patches (condylomata lata) on moist body areas — genitals, inner thighs, anus — during secondary syphilis. These are highly infectious.",
    },
    "Chlamydia": {
        "Genital discharge": "Mild, watery or mucoid (clear/white) penile or vaginal discharge — less thick and purulent than gonorrhea. Many people, especially women, notice no discharge at all, making chlamydia the 'silent STI'.",
        "Painful urination": "Mild burning or discomfort when urinating, less severe than gonorrhea. Often described as 'mildly uncomfortable' rather than 'burning'.",
        "Pelvic pain": "Dull, chronic pelvic ache in women from silent spread to the fallopian tubes and pelvis. Often mistaken for period pain. This is the main route to infertility if untreated.",
        "Vaginal discharge": "Slight increase in vaginal discharge, often clear or milky, with mild odour. Frequently absent, which is why chlamydia is called the 'silent' infection.",
        "Pain during intercourse": "Discomfort or pain during sex in women, from cervical inflammation and pelvic tenderness caused by the infection.",
        "Vaginal itching": "Mild itching or irritation around the vaginal opening from cervical or urethral inflammation.",
        "Lower abdominal pain": "Cramping or aching in the lower abdomen in women — a warning sign of spread to the uterus or fallopian tubes (pelvic inflammatory disease).",
    },
    "Genital Herpes": {
        "Genital sores": "Clusters of small painful blisters or sores on the genitals, buttocks, thighs, or around the anus. Unlike the single painless syphilis chancre, herpes sores are MULTIPLE, GROUPED, and PAINFUL. They burst open into shallow ulcers that ooze fluid, then crust over and heal in 2–4 weeks. Recurrent outbreaks are typically milder and shorter.",
        "Blisters": "Fluid-filled blisters in a cluster pattern — starting as small red bumps, filling with clear fluid, then breaking to form painful raw sores. The first outbreak is usually the most severe.",
        "Painful urination": "Intense burning pain when urinating if urine touches open herpes sores. May cause people to avoid urinating, leading to urinary retention.",
        "Fever": "High fever, chills, and flu-like symptoms during the first (primary) outbreak as the immune system responds strongly to the new infection. Recurrent outbreaks rarely cause fever.",
        "Fatigue": "Severe tiredness and malaise during the primary outbreak, often debilitating for several days.",
        "Muscle aches": "Widespread body aches, back pain, and muscle soreness during the primary infection — resembles severe flu.",
        "Vaginal itching": "An intense tingling, itching, or burning sensation in the genital area — often felt as a 'warning sign' (prodrome) 1–2 days before blisters appear in recurrent outbreaks.",
        "Skin sores": "After blisters burst, raw, painful ulcers form that are exquisitely tender to touch. They take 2–4 weeks to fully heal in primary infection. Subsequent outbreaks are shorter (7–10 days).",
    },
    "Trichomoniasis": {
        "Vaginal itching": "Intense itching, burning, and irritation inside the vagina and around the vulva — often described as 'impossible to ignore'. Gets worse during urination or sex. Unlike yeast infection itch (which is dry and deep), trichomonas itch is associated with discharge and redness.",
        "Genital discharge": "Frothy (bubbly), thin, yellowish-green or grey vaginal discharge with a strong fishy or foul smell — a distinctive characteristic. The frothy appearance from the gas-producing parasite is a diagnostic clue. Unlike the thick discharge of gonorrhea or the curdy discharge of thrush.",
        "Painful urination": "Burning or stinging when urinating from irritation of the urethra and surrounding tissues.",
        "Vaginal discharge": "Copious, malodorous (fishy-smelling) vaginal discharge that may stain underwear. The odour often becomes worse after sex from the pH change.",
        "Pelvic pain": "Mild discomfort or fullness in the lower abdomen during active infection.",
        "Rash": "Redness, soreness, and swelling of the vulva, vaginal opening, and inner thighs from the inflammation — the genitals look inflamed and irritated.",
        "Lower abdominal pain": "Mild lower abdominal cramping from the vaginal and cervical inflammation spreading upward.",
    },
    # ── New diseases ──────────────────────────────────────────────────────────
    "Schistosomiasis": {
        "Blood in urine": "Painless blood in urine (haematuria) — from pink tinge to frankly red urine — is the hallmark of urinary schistosomiasis (S. haematobium). The blood typically appears at the end of urination. Occurs because the parasites' eggs lodge in the bladder wall, causing inflammation and bleeding. Key distinguishing feature: pain-FREE blood in urine (unlike UTI or kidney stones which are painful).",
        "Abdominal pain": "Chronic, dull ache in the right upper abdomen from liver enlargement and portal hypertension in intestinal schistosomiasis (S. mansoni). May develop into a hard, enlarged liver and spleen.",
        "Diarrhea": "Alternating diarrhoea and constipation in intestinal schistosomiasis, sometimes with blood in the stool.",
        "Itchy skin": "Intense itching and a rash ('swimmer's itch') at the site where larvae penetrated the skin — usually on legs or arms — appearing within hours of water contact.",
        "Fatigue": "Chronic fatigue and weakness from anaemia caused by persistent blood loss and the body's immune response to the parasites.",
        "Fever": "Low-grade fever and flu-like illness (Katayama fever) during acute infection, 4–8 weeks after initial exposure.",
    },
    "Mpox": {
        "Fever": "High fever (38–40°C) appearing 1–5 days before the rash. Unlike many fevers, it is accompanied by very pronounced swollen lymph nodes — a combination that distinguishes mpox from chickenpox.",
        "Swollen lymph nodes": "Prominent, painful swelling of lymph nodes — especially in the neck, armpits, and groin — appearing BEFORE or with the rash. This is a key distinguishing feature from chickenpox (which does NOT cause swollen lymph nodes) and from smallpox.",
        "Rash": "A distinctive rash that starts on the face and spreads outward to the body, palms, and soles. It progresses through 4 stages: flat spots (macules) → raised bumps (papules) → fluid-filled blisters (vesicles) → pus-filled (pustules) → scabs. All lesions on the body are typically in the SAME stage at the same time — unlike chickenpox where different stages coexist.",
        "Blisters": "Deep-seated, firm, fluid-filled blisters that progress to pustules (filled with pus) — unlike the superficial, fragile blisters of chickenpox. More similar to the old smallpox lesions.",
        "Headache": "Severe, throbbing headache during the febrile phase.",
        "Muscle aches": "Pronounced muscle aches and back pain during the febrile phase.",
    },
    "African Trypanosomiasis": {
        "Excessive sleepiness": "Progressive daytime sleeping — the defining symptom of late-stage sleeping sickness. The infected person falls asleep at inappropriate times, cannot be roused easily, and the sleep–wake cycle is completely disrupted. This occurs because parasites cross the blood-brain barrier and infect the brain.",
        "Swollen lymph nodes": "Enlarged, rubbery, painless lymph nodes at the back of the neck (Winterbottom's sign) — a classic, highly specific early sign of West African trypanosomiasis. The doctor can feel a characteristic chain of enlarged nodes along the back of the neck.",
        "Fever": "Intermittent, recurring fever episodes that may be irregular. Notably comes and goes over weeks to months unlike malaria which has a more regular pattern.",
        "Confusion": "Progressive mental deterioration in late stage — personality changes, confusion, difficulty concentrating, memory problems. The person may become irritable or withdrawn, or show behaviour unlike their normal self.",
        "Rash": "A transient, non-itchy skin rash (trypanosomal chancre) may appear at the site of the tsetse fly bite within 1–2 weeks, lasting several weeks. Also a circular rash (trypanosomiasis rash / trypanids) on the trunk.",
    },
    "Rabies": {
        "Hydrophobia": "An intense, involuntary spasm of the throat and jaw when seeing or thinking about water — the most famous symptom of rabies encephalitis. Even attempting to drink triggers violent pharyngeal spasms. The person desperately wants water but chokes uncontrollably when trying to swallow it. This is pathognomonic for rabies.",
        "Agitation": "Extreme restlessness, anxiety, and agitation — alternating with calm periods. The person may be confused, disoriented, and frightened without reason. Alternates with periods of lucidity.",
        "Fever": "Fever (38–40°C), often with chills, appearing first. Early symptoms resemble flu: headache, fatigue, muscle aches.",
        "Confusion": "Progressive confusion, delirium, and hallucinations as the virus invades the brain.",
        "Difficulty swallowing": "Difficulty swallowing liquids and solids due to throat muscle spasms — different from a simple sore throat.",
    },
    "Buruli Ulcer": {
        "Skin sores": "A large, painless ulcer with undermined (undermining) edges — meaning the edges overhang the ulcer base, making the true extent larger than it appears. The base is typically whitish-yellowish and necrotic. Crucially, despite its large and horrifying appearance, it is PAINLESS or mildly painful — this lack of pain distinguishes it from most other severe skin infections.",
        "Skin lesions": "Starts as a painless nodule (hard lump), papule (raised spot), or plaque (flat raised area) before breaking down. The skin over the nodule becomes tethered and oedematous before the ulcer forms. The surrounding skin may look swollen and hyperpigmented.",
        "Swelling near skin area": "Diffuse, painless swelling of the skin and underlying tissue (oedematous form) — resembling a bruise or cellulitis. Can be large, covering an entire limb, without open ulceration yet.",
        "Fatigue": "General fatigue from the chronic disease process.",
    },
    "Candidiasis": {
        "White patches in mouth": "White, curd-like or creamy plaques on the tongue, inner cheeks, throat, or roof of the mouth that CANNOT be wiped off without bleeding — oral thrush. Unlike white food residue, which wipes off easily. When the tongue is red underneath the white patches, it is diagnostic. Accompanied by soreness and an altered taste.",
        "Vaginal discharge": "Thick, white, cottage-cheese-like discharge — clumpy and odourless (or mildly bread-like/yeasty smell). Unlike the fishy-smelling discharge of bacterial vaginosis or the frothy discharge of trichomoniasis.",
        "Vaginal itching": "Intense, constant itching of the vulva and inside the vagina — the most distressing symptom. The vulva is often red and swollen. Made worse by warmth, tight clothing, and sweating.",
        "Itchy skin": "Itching and moist redness in skin folds — armpits, under the breasts, groin, between toes — where warmth and moisture allow Candida to overgrow.",
        "Sore throat": "Soreness and discomfort in the throat from oral thrush — may make swallowing uncomfortable.",
    },
    "Cellulitis": {
        "Skin redness": "A spreading area of red, warm, tender skin — often starting at a skin break (cut, insect bite, crack). The redness expands over hours to days. Borders are usually irregular (unlike the well-defined red ring of ringworm). Red streaks spreading from the area suggest spread to lymphatic vessels — a serious sign.",
        "Skin warmth": "The affected skin is noticeably warmer than the surrounding normal skin when touched — from increased blood flow due to inflammation. Often felt before visible redness in darker skin tones.",
        "Fever": "Fever, chills, and general illness when the infection is significant. High fever or shaking chills suggest spread beyond the skin — seek urgent care.",
        "Skin sores": "The skin may develop blisters, small abscesses, or a puncture wound at the original entry site. Pus may drain if an abscess has formed within the cellulitis.",
        "Swollen lymph nodes": "Tender, swollen lymph nodes in the area draining the infection — e.g., groin nodes for leg cellulitis, armpit nodes for arm cellulitis — indicating the body is fighting the spread.",
    },
    "Stroke": {
        "Severe headache": "A sudden, explosive 'thunderclap' headache — often described as 'the worst headache of my life' — which is the hallmark of subarachnoid haemorrhage (a type of stroke from a burst aneurysm). Unlike tension headaches or migraines which build gradually, this headache reaches maximum intensity within seconds.",
        "Confusion": "Sudden onset of confusion, disorientation, or inability to understand what is being said — the person may be unable to tell you where they are, what day it is, or what is happening. Very different from gradual confusion of dementia.",
        "Speech difficulty": "Suddenly unable to speak clearly (slurred speech, aphasia), produce words, or find words — may speak nonsense or garbled sentences. A completely different pattern from alcohol slurring or hoarseness.",
        "Facial drooping": "One side of the face droops or feels numb — the person cannot smile symmetrically, one corner of the mouth hangs lower, the eye on the affected side may not close properly.",
        "Dizziness": "Sudden severe vertigo (room spinning) and loss of balance — especially when combined with other neurological symptoms.",
        "Blurred vision": "Sudden loss of vision in one eye, or double vision (diplopia), from blockage of the eye's blood supply or damage to eye movement centres.",
        "Weakness": "Sudden weakness or numbness on one side of the body — one arm cannot be raised as high, one leg drags, one side of the face is numb. FAST test: Face / Arm / Speech / Time.",
    },
    "Heart Failure": {
        "Shortness of breath": "Breathlessness on exertion that progressively worsens over time — eventually occurring at rest. Waking from sleep unable to breathe (paroxysmal nocturnal dyspnoea) or needing to sleep propped up with multiple pillows (orthopnoea) are characteristic. Caused by fluid accumulating in the lungs (pulmonary oedema).",
        "Ankle swelling": "Bilateral (both sides) ankle and leg swelling that pits when pressed (pitting oedema). Worse at the end of the day, improves slightly overnight when lying flat. Caused by fluid retention from the failing heart's inability to pump blood forward.",
        "Fatigue": "Profound, persistent tiredness even with minimal activity — from reduced cardiac output delivering less oxygen to muscles. Patients often describe feeling exhausted just walking across a room.",
        "Cough": "A chronic, non-productive cough — especially at night or when lying flat. Caused by fluid accumulating around the lungs (pleural effusion) or within the lungs. Unlike a cold cough, it does not produce coloured sputum.",
        "Fast heartbeat": "Palpitations — awareness of a racing or irregular heartbeat as the heart compensates for reduced pump function by beating faster.",
    },
    "Hypothyroidism": {
        "Fatigue": "Deep, persistent tiredness not relieved by sleep — described as 'bone-deep exhaustion'. Even after 10 hours of sleep, the person wakes feeling unrested. Unlike depression fatigue (psychological), hypothyroid fatigue is primarily physical with slow muscle movement.",
        "Weight gain": "Gradual weight gain despite no change in diet or activity — often 3–10 kg over months. The weight is partly from true fat accumulation and partly from fluid retention (myxoedema). Unlike weight gain from overeating, it responds poorly to diet changes alone.",
        "Cold intolerance": "Persistent feeling of being cold even in warm weather — wearing extra layers when others are comfortable. Caused by the reduced metabolic rate meaning the body generates less heat.",
        "Constipation": "Slow bowel movements, often passing stool only every 3–5 days with dry, hard stool. From reduced gut motility due to low thyroid hormone.",
        "Dry skin": "Rough, dry, flaking skin that does not respond to ordinary moisturisers. The skin may feel thickened or 'doughy'. Hair is brittle, coarse, and falls out easily. Eyebrows thin especially at the outer third.",
        "Hair loss": "Diffuse hair thinning over the entire scalp — not patchy like alopecia. Hair becomes brittle, breaks easily, and falls out in larger amounts than normal.",
    },
    "COVID-19": {
        "Fever": "Fever typically 38–40°C, often associated with chills. Unlike malaria, it does not follow a cyclical pattern and is usually continuous rather than spiking.",
        "Cough": "Persistent dry cough — not producing sputum in mild cases. A productive cough with coloured sputum may develop in severe disease with pneumonia.",
        "Shortness of breath": "Breathlessness, especially on exertion. Silent hypoxaemia (low oxygen without obvious breathlessness) is dangerous — oxygen saturation may drop significantly before the person feels breathless.",
        "Loss of taste": "Sudden, complete loss of taste (ageusia) — food becomes completely flavourless. Appears 2–14 days after infection. One of the most distinctive features of COVID-19, uncommon in other respiratory infections.",
        "Loss of smell": "Sudden, complete loss of smell (anosmia) — cannot detect strong smells at all. Often occurs before other symptoms or in people with mild disease who have no fever or cough.",
        "Fatigue": "Severe, debilitating fatigue — often the most distressing symptom. In Long COVID, fatigue may persist for months after the initial infection clears.",
        "Muscle aches": "Widespread muscle pain and body aches, often severe, particularly in the back and thighs.",
    },
}


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _load_json(path: str):
    file_path = Path(path)
    if file_path.exists():
        return json.loads(file_path.read_text(encoding="utf-8"))
    return None


def _normalize_disease(raw: dict) -> dict:
    name = raw.get("name") or raw.get("disease") or "Unknown Disease"
    curated = CURATED_DETAILS.get(name, {})
    raw_sections = raw.get("sections") or {}
    sections = {
        "Overview": curated["description"],
        "Causes": curated["causes"],
        "Treatment": curated["treatment"],
        "Prevention": "\n".join(curated["prevention"]),
    } if curated else raw_sections
    description = (
        curated.get("description")
        or raw.get("description")
        or sections.get("Description")
        or sections.get("Definition")
        or ""
    )
    symptoms = raw.get("symptoms") or CORE_SYMPTOMS.get(name) or []

    HIGH_SEVERITY = {
        "Malaria", "Typhoid Fever", "Cholera", "Pneumonia", "Tuberculosis",
        "Meningitis", "Dengue Fever", "Yellow Fever", "Hepatitis B", "Whooping Cough",
        "Tetanus", "Diphtheria", "Leptospirosis", "Typhus", "Septicemia",
        "Sickle Cell Crisis", "Appendicitis", "Kidney Stones", "Epilepsy",
        "Onchocerciasis", "Filariasis", "HIV AIDS", "Anaphylaxis",
        "Pelvic Inflammatory Disease", "Malnutrition",
        # New high-severity diseases
        "Schistosomiasis", "Mpox", "African Trypanosomiasis", "Rabies",
        "Buruli Ulcer", "Stroke", "Heart Failure", "COVID-19",
    }
    severity = raw.get("severity") or ("High" if name in HIGH_SEVERITY else "Medium")

    FEATURED = {"Malaria", "Typhoid Fever", "Cholera", "Pneumonia", "HIV AIDS", "Tuberculosis"}

    return {
        "id": raw.get("id") or slugify(name),
        "slug": raw.get("slug") or slugify(name),
        "name": name,
        "disease": name,
        "category": raw.get("category") or CATEGORIES.get(name, "General"),
        "featured": raw.get("featured", name in FEATURED),
        "severity": severity,
        "symptoms": symptoms,
        "description": description[:600] if description else f"Encyclopedia information for {name}.",
        "causes": curated.get("causes") or raw.get("causes") or sections.get("Causes and symptoms") or sections.get("Causes") or "",
        "treatment": curated.get("treatment") or raw.get("treatment") or sections.get("Treatment") or "",
        "prevention": curated.get("prevention") or raw.get("prevention") or [sections.get("Prevention", "")],
        "sections": sections,
        "genderSpecific": curated.get("genderSpecific") or raw.get("genderSpecific"),
        "symptom_descriptions": SYMPTOM_DESCRIPTIONS.get(name, {}),
    }


FALLBACK_DISEASES = [_normalize_disease({"disease": name}) for name in CORE_SYMPTOMS]
_structured = _load_json("data_pipeline/mediguard_structured.json")

if _structured:
    # Merge structured JSON with any new diseases not yet in JSON
    existing_names = {item.get("name") or item.get("disease") for item in _structured}
    extra = [
        {"disease": name}
        for name in CORE_SYMPTOMS
        if name not in existing_names
    ]
    DISEASES = [_normalize_disease(item) for item in _structured + extra]
else:
    DISEASES = FALLBACK_DISEASES

SYMPTOMS = (
    _load_json("data_pipeline/symptoms_list.json")
    or sorted({symptom for disease in DISEASES for symptom in disease["symptoms"]})
)
