import json
import re
from pathlib import Path


CORE_SYMPTOMS = {
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
}

CATEGORIES = {
    "Malaria": "Parasitic",
    "Scabies": "Parasitic",
    "Typhoid Fever": "Bacterial",
    "Cholera": "Bacterial",
    "Tuberculosis": "Respiratory",
    "Pneumonia": "Respiratory",
    "Asthma": "Respiratory",
    "Common Cold": "Respiratory",
    "Dengue Fever": "Viral",
    "Chickenpox": "Viral",
    "Measles": "Viral",
    "Gastroenteritis": "Gastrointestinal",
    "Dysentery": "Gastrointestinal",
    "Diabetes Mellitus": "Chronic",
    "Hypertension": "Chronic",
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
    description = curated.get("description") or raw.get("description") or sections.get("Description") or sections.get("Definition") or ""
    symptoms = raw.get("symptoms") or CORE_SYMPTOMS.get(name) or []
    return {
        "id": raw.get("id") or slugify(name),
        "slug": raw.get("slug") or slugify(name),
        "name": name,
        "disease": name,
        "category": raw.get("category") or CATEGORIES.get(name, "General"),
        "featured": raw.get("featured", name in {"Malaria", "Typhoid Fever", "Cholera", "Pneumonia"}),
        "severity": raw.get("severity") or ("High" if name in {"Malaria", "Typhoid Fever", "Cholera", "Pneumonia", "Tuberculosis", "Meningitis", "Dengue Fever"} else "Medium"),
        "symptoms": symptoms,
        "description": description[:600] if description else f"Encyclopedia information for {name}.",
        "causes": curated.get("causes") or raw.get("causes") or sections.get("Causes and symptoms") or sections.get("Causes") or "",
        "treatment": curated.get("treatment") or raw.get("treatment") or sections.get("Treatment") or "",
        "prevention": curated.get("prevention") or raw.get("prevention") or [sections.get("Prevention", "")],
        "sections": sections,
    }


FALLBACK_DISEASES = [_normalize_disease({"disease": name}) for name in CORE_SYMPTOMS]
_structured = _load_json("data_pipeline/mediguard_structured.json")
DISEASES = [_normalize_disease(item) for item in _structured] if _structured else FALLBACK_DISEASES
SYMPTOMS = _load_json("data_pipeline/symptoms_list.json") or sorted({symptom for disease in DISEASES for symptom in disease["symptoms"]})
