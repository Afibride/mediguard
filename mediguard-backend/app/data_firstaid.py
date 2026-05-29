"""
MediGuard First Aid Dataset
===========================
Structured first aid guidance for common accidents and emergencies.

Each entry contains:
  - title          : Display name
  - severity       : "critical" | "urgent" | "moderate"
  - summary        : One-line description shown before the steps
  - steps          : Numbered first-aid actions (ordered, actionable)
  - do_not         : Common mistakes to avoid
  - seek_emergency : Red-flag signs that require immediate emergency care
  - keywords       : Terms that trigger this entry (used for detection)
"""

FIRST_AID_DATA: dict[str, dict] = {

    # ── BURNS ────────────────────────────────────────────────────────────────
    "burn": {
        "title": "Burns",
        "severity": "urgent",
        "summary": (
            "Burns are injuries to skin and tissue caused by heat, chemicals, electricity, or radiation. "
            "Quick first aid greatly reduces pain, infection risk, and scarring."
        ),
        "steps": [
            "Stop the burning: move the person away from the heat source. For chemical burns, brush off dry chemicals first, then rinse.",
            "Cool the burn immediately: hold the burned area under cool (not ice-cold) running water for at least 10–20 minutes.",
            "Remove jewellery or tight clothing near the burned area before swelling starts — but never pull off anything stuck to the skin.",
            "Cover loosely with a clean, non-fluffy bandage or a clean cloth. Do not use cotton wool directly on the burn.",
            "Give paracetamol or ibuprofen for pain if available and the person is conscious.",
            "Keep the person warm (use a blanket on unaffected areas) to prevent shock.",
            "For facial burns: watch for swelling around the airway, hoarseness, or difficulty breathing — these are emergencies.",
            "For large burns (bigger than the person's palm), burns on the face/hands/genitals/joints, or any third-degree burn: go to the nearest hospital immediately.",
        ],
        "do_not": [
            "Do NOT use ice, ice-cold water, butter, toothpaste, oil, or any home remedy on burns — these worsen tissue damage.",
            "Do NOT burst blisters — they protect against infection.",
            "Do NOT remove clothing that is stuck to the burned skin.",
            "Do NOT wrap tightly — this can restrict blood flow.",
        ],
        "seek_emergency": [
            "Burn covers a large area (larger than the palm of your hand)",
            "Burn on face, hands, feet, genitals, or a major joint",
            "Burn goes deep (white, brown, or black skin — third degree)",
            "Burn caused by electricity or strong chemicals",
            "Person is an infant, young child, or elderly",
            "Signs of shock: pale skin, rapid breathing, confusion, weakness",
            "Smoke inhalation or difficulty breathing",
        ],
        "keywords": [
            "burn", "burnt", "burned", "burning", "fire", "scald", "scalded", "hot water burn",
            "chemical burn", "acid burn", "electrical burn", "flame burn", "smoke inhalation",
            "brulure", "brulé",
        ],
    },

    # ── CUTS & LACERATIONS ────────────────────────────────────────────────────
    "cut": {
        "title": "Cuts, Lacerations & Wounds",
        "severity": "moderate",
        "summary": (
            "Most cuts can be managed with basic first aid. Deep, gaping, or contaminated wounds need professional care."
        ),
        "steps": [
            "Apply pressure: press a clean cloth or gauze firmly over the wound and hold for 10–15 minutes without peeking.",
            "Elevate the injured part above heart level if possible to slow bleeding.",
            "Once bleeding stops, gently clean the wound with clean running water. Remove visible dirt carefully.",
            "Apply a thin layer of antiseptic (e.g., povidone-iodine, chlorhexidine) if available.",
            "Cover with a sterile bandage or clean cloth and tape. Change the dressing daily.",
            "Check tetanus vaccination status — a booster may be needed for deep or dirty wounds.",
            "Watch for signs of infection over the following days: increasing redness, warmth, swelling, pus, or fever.",
        ],
        "do_not": [
            "Do NOT remove a deeply embedded object (e.g., glass, metal) — stabilise it and get to hospital.",
            "Do NOT use bare hands to apply pressure — use a cloth, glove, or plastic bag if available.",
            "Do NOT clean a wound with alcohol directly — it damages healing tissue; use water or diluted antiseptic.",
            "Do NOT close a gaping wound with tape alone if it is deep — it may need stitches.",
        ],
        "seek_emergency": [
            "Bleeding that will not stop after 15 minutes of direct pressure",
            "Deep wound (can see fat, muscle, or bone)",
            "Wound is gaping and needs stitches",
            "Cut on the face, hands, or over a joint",
            "Object embedded in the wound",
            "Animal or human bite (high infection risk — needs antibiotics and possible rabies assessment)",
            "Signs of infection: pus, spreading redness, fever, red streaks from the wound",
            "Person has not had a tetanus shot in 5–10 years",
        ],
        "keywords": [
            "cut", "cuts", "laceration", "wound", "gash", "slash",
            "bleeding wound", "wound is bleeding", "cut is bleeding", "blood won't stop",
            "knife cut", "glass cut", "sharp object", "machete cut", "deep cut",
            "stab wound", "puncture", "puncture wound", "dog bite", "animal bite",
            "blessure", "coupure", "saignement",
        ],
    },

    # ── BROKEN BONES / FRACTURES ─────────────────────────────────────────────
    "fracture": {
        "title": "Broken Bones (Fractures)",
        "severity": "urgent",
        "summary": (
            "A fracture is a break or crack in a bone. Do not attempt to straighten the bone. "
            "Immobilise it and get professional care."
        ),
        "steps": [
            "Keep the person still and calm. Do not move them unless there is immediate danger.",
            "Do NOT try to straighten or align the bone yourself.",
            "Immobilise the injured area: use a splint (a rigid support such as a rolled-up newspaper, stick, or board) padded with cloth, and tie it above and below the injury — not on the fracture site.",
            "If the bone is protruding through the skin (open/compound fracture): cover it loosely with a clean cloth. Do NOT push the bone back in.",
            "Elevate the limb gently if possible to reduce swelling.",
            "Apply an ice pack (wrapped in cloth) for 15–20 minutes to reduce swelling — do not place ice directly on skin.",
            "Give paracetamol for pain if the person is conscious and able to swallow.",
            "Transport to the nearest hospital — keep the limb immobilised during transport.",
            "For suspected spinal/neck fractures: DO NOT move the person unless they are in immediate danger. Support the head and neck, call for emergency help.",
        ],
        "do_not": [
            "Do NOT try to straighten a fractured limb.",
            "Do NOT allow the person to eat or drink — they may need surgery.",
            "Do NOT move someone with a suspected spinal fracture unless absolutely necessary.",
            "Do NOT use a tight tourniquet unless there is life-threatening uncontrollable bleeding.",
        ],
        "seek_emergency": [
            "Open (compound) fracture — bone visible through the skin",
            "Suspected fracture of the spine, neck, pelvis, or skull",
            "Fracture with numbness, tingling, or loss of movement below the injury",
            "Fracture with signs of shock: pale/cold/clammy skin, rapid weak pulse, confusion",
            "Multiple fractures from a serious accident",
            "Fracture in a child",
            "Deformity, severe swelling, or inability to bear weight",
        ],
        "keywords": [
            "fracture", "fractured", "broken bone", "broke my", "broke his", "broke her",
            "broken leg", "broken arm", "broken wrist", "broken ankle",
            "broken collar bone", "broken rib", "broken hip", "broken finger",
            "compound fracture", "open fracture", "hairline fracture",
            "crack in bone", "bone break", "my bone", "bone pain",
            "fracture du", "os cassé", "os brisé",
        ],
    },

    # ── SNAKE BITES ───────────────────────────────────────────────────────────
    "snakebite": {
        "title": "Snake Bites",
        "severity": "critical",
        "summary": (
            "Snake bites are medical emergencies in Cameroon, where venomous species (gaboon viper, "
            "green mamba, puff adder, spitting cobra) are present. Act fast — antivenom must be given at hospital."
        ),
        "steps": [
            "Move the person away from the snake immediately. Do NOT try to catch or kill the snake.",
            "Keep the person calm and as still as possible — movement speeds up venom spread.",
            "Lay the person down with the bitten limb below heart level.",
            "Remove watches, rings, tight clothing, or footwear from the bitten limb before swelling starts.",
            "Clean the bite area gently with clean water and soap. Cover loosely with a clean bandage.",
            "Mark the edge of swelling with a pen and note the time — this helps medical staff track spread.",
            "Get to the nearest hospital with antivenom as fast as possible — this is the most important step.",
            "Try to remember or photograph the snake's appearance for the medical team (colour, pattern, head shape).",
            "If the person becomes unconscious and stops breathing: begin CPR.",
        ],
        "do_not": [
            "Do NOT cut the bite, suck the venom, or apply a tourniquet — these do not work and cause harm.",
            "Do NOT apply ice or cold water to the bite.",
            "Do NOT give alcohol, aspirin, or ibuprofen (these increase bleeding risk).",
            "Do NOT apply electric shock.",
            "Do NOT allow the person to walk if it can be avoided.",
        ],
        "seek_emergency": [
            "ALL suspected venomous snake bites are emergencies — go to hospital immediately",
            "Swelling spreading up the limb",
            "Bleeding from the bite or elsewhere (gums, eyes)",
            "Difficulty breathing, drooping eyelids, or inability to swallow",
            "Confusion, weakness, or collapse",
            "Nausea, vomiting, or abdominal pain after the bite",
            "Any bite on the face, neck, or trunk",
        ],
        "keywords": [
            "snake", "snakebite", "snake bite", "bitten by snake", "viper", "cobra",
            "mamba", "puff adder", "python bite", "reptile bite", "venomous snake",
            "serpent", "morsure de serpent",
        ],
    },

    # ── ROAD TRAFFIC / CAR ACCIDENTS ─────────────────────────────────────────
    "road_accident": {
        "title": "Road Traffic Accidents",
        "severity": "critical",
        "summary": (
            "Road accidents can cause life-threatening injuries. Check for danger, assess consciousness, "
            "control bleeding, and immobilise spinal injuries before moving anyone."
        ),
        "steps": [
            "Check for danger: ensure the scene is safe. Turn off the vehicle engine if possible. Warn oncoming traffic.",
            "Call for emergency help: shout for help, send someone to alert a hospital or police.",
            "Check consciousness: tap the person's shoulder and shout 'Are you okay?'",
            "Open the airway: if unconscious, gently tilt the head back and lift the chin to open the airway. Look, listen, feel for breathing.",
            "If not breathing: begin CPR — 30 chest compressions followed by 2 rescue breaths. Continue until help arrives.",
            "Control severe bleeding: apply firm direct pressure with a clean cloth. Do not remove it if it soaks through — add more on top.",
            "Spinal precaution: if the person is unconscious, or has neck/back pain, or the accident was high-impact, do NOT move them unless there is fire or immediate drowning risk — movement can paralyse.",
            "Keep the person warm and reassure them while waiting for help.",
            "Do not give anything to eat or drink — they may need surgery.",
        ],
        "do_not": [
            "Do NOT move a person with a suspected neck or spinal injury unless they are in immediate danger.",
            "Do NOT remove a helmet from a motorcyclist unless they are not breathing and you cannot manage the airway otherwise.",
            "Do NOT leave the person alone if they are unconscious.",
            "Do NOT give food, water, or alcohol.",
        ],
        "seek_emergency": [
            "Person is unconscious or cannot be woken",
            "Person is not breathing normally",
            "Severe bleeding that cannot be controlled",
            "Suspected spinal or neck injury",
            "Chest injuries with difficulty breathing",
            "Deformity of limbs, pelvis, or chest",
            "Confusion, weakness, or unequal pupils",
            "All serious road accidents — go to hospital even if the person feels fine (internal injuries)",
        ],
        "keywords": [
            "car accident", "road accident", "road traffic accident", "rta", "hit by car",
            "motorcycle accident", "vehicle accident", "collision", "crash", "ran over",
            "knocked down", "hit by a bike", "motor accident", "okada accident",
            "accident de voiture", "accident de moto", "accident de la route",
        ],
    },

    # ── CHOKING ───────────────────────────────────────────────────────────────
    "choking": {
        "title": "Choking",
        "severity": "critical",
        "summary": (
            "Choking occurs when an object blocks the airway. Act within seconds — "
            "brain damage begins after 4 minutes without oxygen."
        ),
        "steps": [
            "Ask 'Are you choking?' — if the person CAN cough forcefully, encourage them to keep coughing.",
            "If they CANNOT cough, speak, or breathe: call for emergency help immediately.",
            "5 Back blows: stand behind and slightly to the side. Support the chest with one hand. Give 5 firm blows between the shoulder blades with the heel of your other hand.",
            "5 Abdominal thrusts (Heimlich manoeuvre): stand behind the person. Make a fist above the navel but below the ribs. Cover with the other hand. Give 5 quick inward-and-upward thrusts.",
            "Alternate 5 back blows and 5 abdominal thrusts until the object is dislodged or the person loses consciousness.",
            "If unconscious: lower them to the floor, call for help, and start CPR. Each time you open the airway to give a rescue breath, look for and remove any visible object.",
            "For infants under 1 year: use 5 back blows + 5 chest thrusts (NOT abdominal thrusts). Support the head; never shake.",
            "For pregnant women: use chest thrusts instead of abdominal thrusts.",
        ],
        "do_not": [
            "Do NOT perform a blind finger sweep in the mouth — only remove an object if you can clearly see it.",
            "Do NOT give abdominal thrusts to infants under 1 year or heavily pregnant women — use chest thrusts.",
            "Do NOT slap the back of someone who is still coughing effectively.",
        ],
        "seek_emergency": [
            "The object cannot be dislodged after several cycles",
            "Person becomes unconscious",
            "Infant or young child is choking",
            "After any choking episode where the airway was compromised — medical review needed",
        ],
        "keywords": [
            "choking", "choke", "choked", "airway blocked", "can't breathe", "food stuck",
            "throat blocked", "something stuck in throat", "heimlich", "swallowed wrong",
            "etouffement", "s'étouffe", "avaler de travers",
        ],
    },

    # ── DROWNING / NEAR-DROWNING ──────────────────────────────────────────────
    "drowning": {
        "title": "Drowning / Near-Drowning",
        "severity": "critical",
        "summary": (
            "Near-drowning victims need immediate airway management and CPR. "
            "Always call emergency services — secondary drowning can occur hours later."
        ),
        "steps": [
            "Remove the person from the water SAFELY. Do not put yourself at risk — use a rope, clothing, or reach from the bank if possible.",
            "Call for emergency help immediately.",
            "Check breathing: if not breathing, start CPR — 5 rescue breaths first, then 30 compressions + 2 breaths. Continue until breathing resumes or help arrives.",
            "If breathing: place in the recovery position (on their side). Keep the airway clear.",
            "Keep the person warm: remove wet clothing and cover with a dry blanket or clothing.",
            "Do NOT leave the person alone — secondary drowning can cause symptoms up to 24 hours later.",
            "All near-drowning survivors should be assessed at a hospital, even if they seem fine.",
        ],
        "do_not": [
            "Do NOT turn a near-drowning victim upside down to drain water — this wastes time and does not work.",
            "Do NOT delay CPR to remove water from the lungs.",
            "Do NOT leave them unsupervised even if they appear recovered.",
        ],
        "seek_emergency": [
            "Always — every near-drowning is a hospital emergency",
            "Difficulty breathing, coughing, or gurgling sounds",
            "Confusion, blue lips, or loss of consciousness",
            "Any water submersion in young children",
        ],
        "keywords": [
            "drowning", "drowned", "near drowning", "water submersion", "fell into water",
            "swimming accident", "river accident", "lake accident", "underwater",
            "noyade", "noyé",
        ],
    },

    # ── HEAD INJURIES ─────────────────────────────────────────────────────────
    "head_injury": {
        "title": "Head Injuries",
        "severity": "urgent",
        "summary": (
            "Head injuries range from mild concussion to life-threatening brain bleeding. "
            "Symptoms may be delayed — always monitor carefully."
        ),
        "steps": [
            "Keep the person still and calm. Do not move them if a spinal injury is possible.",
            "Check consciousness: speak to them. If unconscious and not breathing, begin CPR.",
            "Control scalp bleeding: apply firm pressure with a clean cloth. Scalp wounds bleed heavily even when minor.",
            "Do NOT apply direct pressure if you suspect a skull fracture (visible deformity, depressed area, clear fluid from nose/ears).",
            "Place a conscious person in a comfortable position with their head and shoulders slightly raised.",
            "Do NOT give aspirin or ibuprofen — use paracetamol only if needed for pain.",
            "Watch for 24 hours: confusion, worsening headache, repeated vomiting, unequal pupils, weakness on one side, or difficulty waking up.",
            "Do NOT leave a concussed person alone to sleep — wake them every 2 hours to check responsiveness.",
        ],
        "do_not": [
            "Do NOT remove a helmet if you suspect a spinal or neck injury.",
            "Do NOT give aspirin or ibuprofen after head injury (increases bleeding risk).",
            "Do NOT allow a person with concussion to return to sports or strenuous activity before medical clearance.",
            "Do NOT leave an unconscious person lying on their back — use the recovery position.",
        ],
        "seek_emergency": [
            "Loss of consciousness, even briefly",
            "Confusion, disorientation, or memory loss",
            "Repeated vomiting",
            "Severe or worsening headache",
            "Unequal pupils or blurred vision",
            "Slurred speech or weakness on one side",
            "Clear fluid from nose or ears (may indicate skull fracture)",
            "Seizure after head injury",
            "Child with any head injury from a significant fall or impact",
        ],
        "keywords": [
            "head injury", "hit head", "hit my head", "hit his head", "hit her head",
            "head trauma", "knocked head", "knocked my head", "concussion",
            "skull fracture", "head wound", "bump on head", "fell and hit head",
            "bang my head", "bang head", "banged head",
            "traumatisme crânien", "chute tête",
        ],
    },

    # ── ELECTRIC SHOCK ────────────────────────────────────────────────────────
    "electric_shock": {
        "title": "Electric Shock",
        "severity": "critical",
        "summary": (
            "Electric shock can cause cardiac arrest, internal burns, and muscle damage "
            "even when external injuries look minor. Always call emergency services."
        ),
        "steps": [
            "DO NOT touch the person until the power source is off — you can be electrocuted too.",
            "Turn off the electricity at the main switch or fuse box. If you cannot, use a dry non-conductive object (dry wooden stick, plastic) to push the source away — never metal or wet objects.",
            "Once safe, check the person: are they conscious? Breathing?",
            "If not breathing: begin CPR immediately — 30 chest compressions then 2 breaths. Continue until help arrives.",
            "Call for emergency help.",
            "Lay the person down and elevate legs slightly unless you suspect a spinal injury.",
            "Do not move them unnecessarily — electric shocks can cause internal injuries not visible externally.",
            "Keep them warm and reassure them.",
            "For lightning strike victims: it is safe to touch them — begin CPR if needed.",
        ],
        "do_not": [
            "Do NOT touch the person until you are certain the power is off.",
            "Do NOT use water near an electrical source.",
            "Do NOT assume the person is fine because external burns look minor — internal damage may be severe.",
        ],
        "seek_emergency": [
            "ALL electric shock victims should be seen at a hospital — always",
            "Loss of consciousness, seizures, or confusion",
            "Chest pain, irregular heartbeat, or difficulty breathing",
            "Burns at entry and exit points",
            "Lightning strike",
        ],
        "keywords": [
            "electric shock", "electrocuted", "electrocution", "touched live wire",
            "electrical burn", "power line", "lightning strike", "lightning bolt",
            "shocked by electricity", "choc électrique", "électrocuté",
        ],
    },

    # ── POISONING / OVERDOSE ──────────────────────────────────────────────────
    "poisoning": {
        "title": "Poisoning & Overdose",
        "severity": "critical",
        "summary": (
            "Poisoning from chemicals, plants, contaminated food, or overdose of medications "
            "can be life-threatening. Do not induce vomiting unless specifically told to by a medical professional."
        ),
        "steps": [
            "Identify the poison if possible: note what was taken, how much, and when.",
            "Call emergency services or go to the nearest hospital immediately.",
            "If the person is unconscious: place in the recovery position to prevent choking. Begin CPR if not breathing.",
            "If the person swallowed a chemical or unknown substance: do NOT induce vomiting unless instructed by a medical professional.",
            "For skin contact with chemicals: remove contaminated clothing and rinse the skin with large amounts of water for 15–20 minutes.",
            "For eye contact with chemicals: flush the eye with clean water for 15–20 minutes.",
            "Bring the container, packet, or any sample of the suspected poison to the hospital.",
            "If a child has swallowed medication or household chemicals: go to hospital immediately.",
        ],
        "do_not": [
            "Do NOT induce vomiting unless directed by medical staff (some chemicals cause more damage coming back up).",
            "Do NOT give milk, food, or water to dilute poisons unless instructed.",
            "Do NOT leave a poisoned person alone.",
        ],
        "seek_emergency": [
            "All suspected poisoning or overdose — always a hospital emergency",
            "Unconsciousness, seizures, or difficulty breathing",
            "Chemical burns in the mouth or throat",
            "Child who has swallowed any medication or household chemical",
            "Overdose of any medication (prescription or otherwise)",
        ],
        "keywords": [
            "poisoning", "poisoned", "overdose", "swallowed poison", "swallowed chemicals",
            "swallowed bleach", "swallowed kerosene", "swallowed petrol",
            "swallowed pills", "swallowed tablets", "swallowed medicine",
            "swallowed medication", "swallowed a pill",
            "drank bleach", "drank kerosene", "drank chemicals",
            "drug overdose", "medication overdose", "took too many pills",
            "ingested poison", "intoxication", "empoisonnement",
        ],
    },

    # ── SPRAIN / STRAIN ───────────────────────────────────────────────────────
    "sprain": {
        "title": "Sprains & Strains",
        "severity": "moderate",
        "summary": (
            "Sprains are ligament injuries (e.g. twisted ankle); strains are muscle/tendon injuries. "
            "Use the RICE method immediately."
        ),
        "steps": [
            "Rest: stop using the injured part immediately. Avoid putting weight on a sprained ankle.",
            "Ice: apply an ice pack or a bag of frozen items wrapped in a cloth for 15–20 minutes every 2–3 hours during the first 48 hours. Do not put ice directly on skin.",
            "Compression: wrap with an elastic bandage — snug but not tight enough to cut circulation. Loosen if fingers/toes become numb or blue.",
            "Elevation: raise the injured limb above heart level to reduce swelling (prop it on pillows).",
            "Paracetamol or ibuprofen can help with pain and swelling if there are no contraindications.",
            "After 48–72 hours, gentle movement can begin as tolerated.",
            "If unsure whether a bone is broken, treat as a fracture and seek medical care.",
        ],
        "do_not": [
            "Do NOT apply heat in the first 48 hours — it increases swelling.",
            "Do NOT massage the injured area in the first 24 hours.",
            "Do NOT walk or use the limb if there is severe pain, inability to bear weight, or suspicion of a fracture.",
        ],
        "seek_emergency": [
            "Inability to bear weight at all after a sprained ankle",
            "Significant deformity or severe swelling",
            "Numbness or loss of sensation",
            "No improvement after 2–3 days",
            "Suspected fracture (heard or felt a crack, point tenderness over bone)",
        ],
        "keywords": [
            "sprain", "sprained my", "sprained ankle", "sprained knee", "sprained wrist",
            "twisted ankle", "twisted knee", "twisted wrist",
            "pulled muscle", "rolled ankle", "torn ligament",
            "ankle injury", "entorse", "claquage",
        ],
    },

    # ── EYE INJURIES ──────────────────────────────────────────────────────────
    "eye_injury": {
        "title": "Eye Injuries",
        "severity": "urgent",
        "summary": (
            "Eye injuries can cause permanent vision loss if not treated promptly. "
            "Avoid rubbing the eye and cover it gently."
        ),
        "steps": [
            "For chemicals in the eye: irrigate immediately with large amounts of clean water for 15–20 minutes. Hold the eye open and let water flow from the inner corner outward. Seek emergency care after.",
            "For foreign body (dust, sand, small particle): blink repeatedly; flush with clean water. Do NOT rub. If not dislodged, cover the eye and go to a clinic.",
            "For penetrating injuries (sharp object in the eye): do NOT remove the object. Cover both eyes loosely with a clean cloth and go to hospital immediately.",
            "For blunt trauma (punch, hit to eye): apply a cold compress (not ice directly). Seek care if vision changes, severe pain, or visible bleeding.",
            "Keep the person calm and still. Avoid any pressure on the injured eye.",
            "Always seek medical care for any eye injury involving chemicals, sharp objects, or vision changes.",
        ],
        "do_not": [
            "Do NOT rub the eye.",
            "Do NOT attempt to remove an embedded object.",
            "Do NOT patch or apply pressure to an eye with a suspected penetrating injury.",
            "Do NOT use eye drops or medications without medical advice for injuries.",
        ],
        "seek_emergency": [
            "Chemical splash — any substance in the eye",
            "Visible object embedded in the eye",
            "Any change in vision, blurring, or loss of vision",
            "Severe pain, sensitivity to light, or tears won't stop",
            "Blood visible in the eye or around the iris",
        ],
        "keywords": [
            "eye injury", "injured eye", "something in eye", "foreign body in eye",
            "chemical in eye", "acid in eye", "bleach in eye", "eye pain",
            "eye trauma", "black eye", "hit in eye", "stabbed in eye",
            "blessure à l'oeil", "produit dans l'oeil",
        ],
    },

    # ── NOSEBLEED ─────────────────────────────────────────────────────────────
    "nosebleed": {
        "title": "Nosebleed (Epistaxis)",
        "severity": "moderate",
        "summary": (
            "Most nosebleeds stop within 10–15 minutes with simple first aid. "
            "Do NOT tilt the head back."
        ),
        "steps": [
            "Have the person sit upright and lean slightly forward — this prevents blood from flowing down the throat.",
            "Pinch the soft part of the nose (just below the bony bridge) firmly. Breathe through the mouth.",
            "Hold continuous pressure for 10–15 minutes without releasing. Do NOT keep checking — this disrupts clotting.",
            "Apply a cold compress or ice pack (wrapped in cloth) to the bridge of the nose and forehead.",
            "After bleeding stops, avoid blowing the nose, bending over, or strenuous activity for several hours.",
            "If the nosebleed restarts, repeat the above. If it continues past 30 minutes, seek medical care.",
        ],
        "do_not": [
            "Do NOT tilt the head back — blood can flow into the throat causing vomiting or choking.",
            "Do NOT pack the nose tightly with cotton wool — it can stick and restart bleeding when removed.",
            "Do NOT give aspirin (increases bleeding).",
        ],
        "seek_emergency": [
            "Nosebleed after a head injury or blow to the face — may indicate skull fracture",
            "Bleeding does not stop after 30 minutes of continuous pressure",
            "Blood is flowing down the back of the throat in large amounts",
            "Person is on blood thinners or has a known clotting disorder",
            "Signs of significant blood loss (dizziness, weakness, pale skin)",
        ],
        "keywords": [
            "nosebleed", "nose bleed", "bleeding nose", "blood from nose",
            "epistaxis", "saignement du nez", "nez qui saigne",
        ],
    },

    # ── ANAPHYLAXIS / SEVERE ALLERGIC REACTION ────────────────────────────────
    "anaphylaxis": {
        "title": "Severe Allergic Reaction (Anaphylaxis)",
        "severity": "critical",
        "summary": (
            "Anaphylaxis is a life-threatening allergic reaction. It can occur within seconds to minutes "
            "after exposure to an allergen (bee sting, food, medication). Use adrenaline/epinephrine if available."
        ),
        "steps": [
            "Call emergency services immediately.",
            "If an adrenaline auto-injector (EpiPen) is available: use it in the outer thigh. Repeat after 5–10 minutes if no improvement.",
            "Lie the person down with legs elevated (unless they have difficulty breathing — then sit them upright).",
            "If they stop breathing: begin CPR.",
            "Remove the trigger if possible (e.g., remove a bee sting by scraping, not squeezing).",
            "If an antihistamine is the only drug available, give it — but know it does NOT replace adrenaline and does not treat anaphylaxis alone.",
            "Keep the person warm and monitor constantly until emergency help arrives.",
        ],
        "do_not": [
            "Do NOT give antihistamines alone as the only treatment — they are not fast enough for anaphylaxis.",
            "Do NOT leave the person alone.",
            "Do NOT allow the person to stand or walk if they are lightheaded.",
        ],
        "seek_emergency": [
            "ALL anaphylaxis reactions — always a hospital emergency, even after adrenaline",
            "Difficulty breathing, wheezing, or stridor",
            "Swelling of the face, lips, tongue, or throat",
            "Sudden drop in blood pressure, dizziness, or collapse",
            "Loss of consciousness",
            "Severe rash, hives, or skin flushing with any of the above",
        ],
        "keywords": [
            "anaphylaxis", "anaphylactic", "severe allergy", "allergic reaction",
            "bee sting reaction", "wasp sting reaction", "nut allergy reaction",
            "food allergy reaction", "medication allergy", "epipen", "swelling throat",
            "throat closing", "reaction allergique grave", "choc anaphylactique",
        ],
    },

    # ── HEART ATTACK ──────────────────────────────────────────────────────────
    "heart_attack": {
        "title": "Heart Attack (Cardiac Emergency)",
        "severity": "critical",
        "summary": (
            "A heart attack happens when blood supply to the heart muscle is blocked. "
            "Time is muscle — get to hospital immediately."
        ),
        "steps": [
            "Call emergency services immediately. Time is critical — every minute of delay causes more heart damage.",
            "Sit the person down in a comfortable position — sitting or half-lying with knees bent.",
            "Loosen tight clothing around the neck and chest.",
            "If the person is conscious and NOT allergic to aspirin: give one adult aspirin (300mg) to chew and swallow (not to swallow whole).",
            "If they lose consciousness and stop breathing normally: begin CPR — 30 compressions, 2 rescue breaths.",
            "If an AED (defibrillator) is available: switch it on and follow the voice prompts.",
            "Stay with the person and reassure them. Keep them still and calm.",
        ],
        "do_not": [
            "Do NOT leave the person alone.",
            "Do NOT give aspirin if they are allergic or have been told not to take it.",
            "Do NOT give food or drink.",
            "Do NOT allow the person to drive themselves to hospital.",
        ],
        "seek_emergency": [
            "Crushing, tight, or heavy chest pain — especially if it spreads to the left arm, jaw, neck, or back",
            "Chest pain with sweating, nausea, shortness of breath, or dizziness",
            "Sudden severe shortness of breath",
            "Loss of consciousness or collapse",
            "Any suspected heart attack — always call emergency services",
        ],
        "keywords": [
            "heart attack", "cardiac arrest", "chest pain severe", "crushing chest pain",
            "heart pain", "heart problem", "my heart", "cardiac emergency",
            "myocardial infarction", "crise cardiaque", "infarctus",
        ],
    },

    # ── STROKE ────────────────────────────────────────────────────────────────
    "stroke": {
        "title": "Stroke",
        "severity": "critical",
        "summary": (
            "A stroke occurs when blood supply to part of the brain is cut off. "
            "Use the FAST test: Face drooping, Arm weakness, Speech difficulty, Time to call emergency."
        ),
        "steps": [
            "Use the FAST test:\n  F – Face: ask them to smile. Is one side drooping?\n  A – Arms: ask them to raise both arms. Does one drift down?\n  S – Speech: ask them to repeat a simple phrase. Is it slurred or strange?\n  T – Time: If YES to any of the above, call emergency services immediately.",
            "Keep the person calm and still. Do NOT give food or drink.",
            "If conscious: lay them down with their head and shoulders slightly elevated.",
            "If unconscious but breathing: place in the recovery position.",
            "If not breathing: begin CPR.",
            "Note the exact time symptoms started — this is critical for the medical team to decide on treatment.",
            "Do NOT give aspirin (it can worsen a haemorrhagic stroke).",
        ],
        "do_not": [
            "Do NOT give aspirin — a stroke may be caused by bleeding, not a clot.",
            "Do NOT give food or water — swallowing may be affected.",
            "Do NOT delay — stroke treatment is time-sensitive ('time is brain').",
        ],
        "seek_emergency": [
            "ANY suspected stroke — call emergency services immediately, go to the nearest hospital",
            "Sudden face drooping or numbness",
            "Sudden arm or leg weakness, especially on one side",
            "Sudden speech problems (slurred, confused, or inability to speak)",
            "Sudden vision problems",
            "Sudden severe headache with no clear cause",
            "Loss of consciousness or sudden confusion",
        ],
        "keywords": [
            "stroke", "brain stroke", "face drooping", "arm weakness one side",
            "slurred speech", "sudden headache severe", "paralysis", "AVC",
            "accident vasculaire", "attaque cérébrale",
        ],
    },

    # ── INSECT STINGS / BEE STINGS ───────────────────────────────────────────
    "insect_sting": {
        "title": "Insect Stings & Bites (Bees, Wasps, Scorpions)",
        "severity": "moderate",
        "summary": (
            "Most insect stings cause local pain and swelling only. "
            "However, scorpion stings and multiple bee stings in Cameroon can be serious."
        ),
        "steps": [
            "Remove the sting (bee stings leave a barb): scrape it off with a flat edge (credit card, fingernail) — do NOT use tweezers or squeeze, as this injects more venom.",
            "Wash the area with soap and water.",
            "Apply a cold compress (ice wrapped in cloth) for 10 minutes to reduce pain and swelling.",
            "Take paracetamol or ibuprofen for pain. An antihistamine (e.g. cetirizine) can help with itching and local reaction.",
            "Elevate the affected limb if swelling is significant.",
            "Watch for signs of allergy over 30–60 minutes: spreading rash, swelling of face/lips/throat, difficulty breathing, or dizziness — these are emergencies.",
            "For scorpion stings: keep the person calm, immobilise the stung limb, and go to hospital — antivenom may be needed.",
        ],
        "do_not": [
            "Do NOT squeeze the bee sting — it injects more venom.",
            "Do NOT apply mud, herbs, or tobacco to the sting site.",
            "Do NOT ignore multiple stings — they can cause systemic reactions.",
        ],
        "seek_emergency": [
            "Signs of anaphylaxis: throat swelling, difficulty breathing, collapse, rapid pulse",
            "Scorpion sting — especially in children",
            "Multiple bee or wasp stings (50+ stings can be toxic even without allergy)",
            "Sting inside the mouth or throat",
            "Known allergy to insect stings",
        ],
        "keywords": [
            "bee sting", "wasp sting", "insect bite", "insect sting", "scorpion sting",
            "stung by bee", "stung by wasp", "stung by scorpion", "hornet sting",
            "piqûre d'abeille", "piqûre de guêpe", "piqûre de scorpion",
        ],
    },

    # ── FAINTING / LOSS OF CONSCIOUSNESS ─────────────────────────────────────
    "fainting": {
        "title": "Fainting / Loss of Consciousness",
        "severity": "urgent",
        "summary": (
            "Fainting is a brief loss of consciousness due to reduced blood flow to the brain. "
            "If the person does not regain consciousness quickly, treat as an emergency."
        ),
        "steps": [
            "Lay the person on their back and elevate their legs 15–30 cm (to improve blood flow to the brain) — unless they have a head, neck, or spinal injury.",
            "Loosen any tight clothing around the neck and waist.",
            "Ensure a clear airway: tilt the head back gently, lift the chin.",
            "If they do not regain consciousness within 1–2 minutes or are not breathing normally: begin CPR and call emergency services.",
            "If breathing and regaining consciousness: keep them lying down for a few minutes. Help them sit up slowly — do not rush.",
            "Once recovered: give a small amount of water and something light to eat if available and they can swallow.",
            "Do not allow them to stand up immediately — dizziness is common on recovery.",
        ],
        "do_not": [
            "Do NOT leave an unconscious person alone.",
            "Do NOT give anything to eat or drink until they are fully conscious.",
            "Do NOT elevate the legs if a spinal injury is possible.",
        ],
        "seek_emergency": [
            "Fainting that lasts more than 1–2 minutes",
            "Person does not regain consciousness",
            "Fainting with a seizure",
            "Fainting during exercise (can indicate a heart problem)",
            "Head injury from the fall when fainting",
            "Person is elderly, pregnant, diabetic, or on blood pressure medication",
            "Fainting with chest pain, shortness of breath, or irregular heartbeat",
        ],
        "keywords": [
            "fainted", "fainting", "passed out", "unconscious", "collapsed",
            "lost consciousness", "fell unconscious", "blacked out",
            "évanouissement", "perte de connaissance", "syncope",
        ],
    },

    # ── GENERAL FIRST AID QUERY ───────────────────────────────────────────────
    # NOTE: keywords here are intentionally narrow — the is_first_aid_request()
    # function handles broad triggers ("accident", "what to do", etc.) and falls
    # back to this entry when no specific type is matched.
    "general_firstaid": {
        "title": "General First Aid (DRABC)",
        "severity": "moderate",
        "summary": "Basic first aid principles for any emergency situation.",
        "steps": [
            "**D — Danger**: Ensure the scene is safe for you and the casualty before approaching.",
            "**R — Response**: Check if the person is conscious — tap shoulders, shout 'Are you okay?'",
            "**A — Airway**: Open the airway by tilting the head back and lifting the chin.",
            "**B — Breathing**: Look, listen, and feel for normal breathing for up to 10 seconds.",
            "**C — Circulation (CPR)**: If not breathing normally, begin CPR — 30 chest compressions then 2 rescue breaths. Push hard and fast (5–6 cm deep) in the centre of the chest at 100–120 per minute.",
            "**Call for help**: Send someone to call emergency services or the nearest hospital while you give first aid.",
            "**Treat and monitor**: Control bleeding, keep the person warm, and reassure them until help arrives.",
        ],
        "do_not": [
            "Do NOT move a casualty with a possible spinal injury.",
            "Do NOT give food or water to an unconscious person.",
            "Do NOT panic — stay calm, think clearly, and do the most important thing first.",
        ],
        "seek_emergency": [
            "Any life-threatening emergency — always call for help",
            "Unconsciousness or difficulty breathing",
            "Severe bleeding",
            "Suspected poisoning, overdose, or severe allergic reaction",
        ],
        # Narrow keywords — broad triggers are handled by is_first_aid_request()
        "keywords": [
            "first aid", "premiers secours",
            "cpr", "resuscitation", "mouth to mouth",
            "drabc", "recover position", "recovery position",
        ],
    },
}


# ── Keyword → entry key lookup ────────────────────────────────────────────────
# Built at import time from the keywords lists above.

_FIRSTAID_KEYWORD_MAP: dict[str, str] = {}
for _key, _entry in FIRST_AID_DATA.items():
    for _kw in _entry.get("keywords", []):
        _FIRSTAID_KEYWORD_MAP[_kw.lower()] = _key


def detect_first_aid_type(query: str) -> str | None:
    """Return the FIRST_AID_DATA key that best matches the query, or None."""
    text = query.lower()
    # Longest-match first so "car accident" beats "accident"
    for kw in sorted(_FIRSTAID_KEYWORD_MAP, key=len, reverse=True):
        if kw in text:
            return _FIRSTAID_KEYWORD_MAP[kw]
    return None


def is_first_aid_request(query: str) -> bool:
    """Return True when the query is clearly about an accident or emergency, not a disease."""
    text = query.lower()

    # Positive triggers — these clearly indicate an accident / injury
    accident_triggers = [
        "accident", "first aid", "how to treat", "how do i treat",
        "emergency", "broken", "fracture", "fractured",
        "sprained", "sprain", "burned", "burnt", "cut myself",
        "choked", "choking", "drowned", "drowning", "bitten by",
        "snake bite", "snake attack", "electrocuted", "electric shock",
        "unconscious", "fainted", "fainting", "collapsed",
        "poisoned", "overdose", "nosebleed",
        "swallowed", "ingested", "drank bleach", "drank chemicals",
        "premiers secours", "urgence",
    ]

    # Check for any accident trigger
    if any(trigger in text for trigger in accident_triggers):
        # Make sure it is not a disease-name query like "what is malaria"
        non_accident_overrides = [
            "what is ", "tell me about", "symptoms of", "causes of",
            "treatment of", "prevention of",
        ]
        if not any(ov in text for ov in non_accident_overrides):
            return True

    # Direct keyword match also qualifies
    return detect_first_aid_type(query) is not None


def format_first_aid_response(entry_key: str, query: str) -> str:
    """Format a first-aid entry as a clear, structured response string."""
    entry = FIRST_AID_DATA.get(entry_key)
    if not entry:
        return ""

    severity_emoji = {
        "critical": "🚨",
        "urgent": "⚠️",
        "moderate": "ℹ️",
    }.get(entry["severity"], "ℹ️")

    lines = [
        f"{severity_emoji} **First Aid: {entry['title']}**",
        "",
        entry["summary"],
        "",
        "**Step-by-step first aid:**",
    ]
    for i, step in enumerate(entry["steps"], 1):
        lines.append(f"{i}. {step}")

    if entry.get("do_not"):
        lines.append("")
        lines.append("**What NOT to do:**")
        for item in entry["do_not"]:
            lines.append(f"- {item}")

    if entry.get("seek_emergency"):
        lines.append("")
        lines.append("**🏥 Go to hospital / seek emergency care if:**")
        for item in entry["seek_emergency"]:
            lines.append(f"- {item}")

    lines.append("")
    lines.append(
        "This guidance is for immediate first aid only. "
        "Always seek professional medical care as soon as possible. "
        "MediGuard is not a substitute for trained emergency responders or a qualified clinician."
    )

    return "\n".join(lines)
