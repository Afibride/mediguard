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
    "Whooping Cough": ["Cough", "Runny nose", "Fever", "Sneezing", "Vomiting", "Fatigue", "Weakness"],
    "Mumps": ["Swollen lymph nodes", "Jaw stiffness", "Fever", "Headache", "Muscle aches", "Fatigue", "Loss of appetite"],
    "Rubella": ["Mild fever", "Rash", "Swollen lymph nodes", "Red eyes", "Runny nose", "Joint pain", "Headache"],
    "Sinusitis": ["Headache", "Nasal congestion", "Facial pain", "Runny nose", "Cough", "Sore throat", "Fever"],
    "Tonsillitis": ["Sore throat", "Difficulty swallowing", "Swollen lymph nodes", "High fever", "Headache", "Fatigue", "Loss of appetite"],
    "Ear Infection": ["Ear pain", "Fever", "Hearing loss", "Headache", "Dizziness", "Fatigue", "Pus or discharge"],
    "Conjunctivitis": ["Red eyes", "Eye discharge", "Itchy skin", "Eye pain", "Sensitivity to light", "Headache"],
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
    "Pelvic Inflammatory Disease": ["Pelvic pain", "Vaginal discharge", "Lower abdominal pain", "Fever", "Painful urination", "Missed period"],
    "Benign Prostatic Hyperplasia": ["Frequent urination", "Reduced urination", "Sleep disturbances", "Lower abdominal pain", "Weakness", "Back pain"],
    "Migraine": ["Severe headache", "Sensitivity to light", "Sensitivity to sound", "Nausea", "Vomiting", "Blurred vision", "Dizziness"],
    "Epilepsy": ["Seizures", "Confusion", "Confusion at night", "Muscle cramps", "Fatigue", "Weakness", "Poor coordination"],
    "Onchocerciasis": ["Severe itching", "Skin lesions", "Blurred vision", "Rash", "Skin peeling", "Swollen lymph nodes", "Weight loss"],
    "Filariasis": ["Swollen feet", "Ankle swelling", "Skin lesions", "Fever", "Skin sores", "Weakness", "Itchy skin"],
    "HIV AIDS": ["Fatigue", "Weight loss", "Night sweats", "Swollen lymph nodes", "Diarrhea", "Fever", "Rash", "Loss of appetite", "Cough", "Sore throat"],
    "Skin Abscess": ["Skin sores", "Pus or discharge", "Rash", "Fever", "Fatigue", "Swollen lymph nodes"],
    "Anaphylaxis": ["Rash", "Shortness of breath", "Fast heartbeat", "Dizziness", "Low blood pressure", "Nausea", "Swollen feet", "Sweating"],
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
        "Pelvic Inflammatory Disease",
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
