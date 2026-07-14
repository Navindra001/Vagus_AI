"""
Management command: python manage.py seed_cases
Seeds the database with 11 varied patient cases across specialties.
"""
from django.core.management.base import BaseCommand
from apps.cases.models import PatientCase

CASES = [
    {
        "title": "Chest Pain — Possible ACS",
        "patient_name": "James Thornton",
        "age": 58,
        "gender": "Male",
        "condition": "Acute coronary syndrome",
        "specialty": "cardiology",
        "difficulty": "core",
        "patient_role": "anxious but cooperative, tends to downplay symptoms",
        "expected_diagnosis": "Acute coronary syndrome (NSTEMI)",
        "patient_story": (
            "James Thornton is a 58-year-old retired lorry driver. He has been "
            "experiencing a heavy, tight sensation in his chest for the past 3 hours. "
            "The pain radiates to his left arm and jaw. He feels sweaty and slightly "
            "short of breath. He smokes 15 cigarettes a day and has done so for 30 years. "
            "He takes amlodipine for hypertension. His father died of a heart attack aged 62. "
            "He drinks about 14 units of alcohol per week. He is scared but tries to appear calm. "
            "He has never had chest pain like this before. He lives with his wife."
        ),
    },
    {
        "title": "Shortness of Breath — COPD Exacerbation",
        "patient_name": "Margaret Ellis",
        "age": 67,
        "gender": "Female",
        "condition": "COPD exacerbation",
        "specialty": "respiratory",
        "difficulty": "foundation",
        "patient_role": "tired and breathless, speaks in short sentences",
        "expected_diagnosis": "Acute COPD exacerbation",
        "patient_story": (
            "Margaret Ellis is a 67-year-old retired shop assistant with known COPD. "
            "Over the past 4 days her breathlessness has worsened significantly. "
            "She has increased her reliever inhaler use to 8 times per day. "
            "She has a productive cough with green sputum — normally her sputum is white. "
            "She smoked for 40 years, stopping 5 years ago. She is on tiotropium and salbutamol. "
            "She is allergic to penicillin (rash). She lives alone and is worried about managing at home. "
            "She has had two hospital admissions for COPD in the last year."
        ),
    },
    {
        "title": "Low Mood — Depression Presentation",
        "patient_name": "Daniel Osei",
        "age": 29,
        "gender": "Male",
        "condition": "Major depressive disorder",
        "specialty": "psychiatry",
        "difficulty": "core",
        "patient_role": "withdrawn, gives brief answers, needs encouragement to open up",
        "expected_diagnosis": "Major depressive disorder",
        "patient_story": (
            "Daniel Osei is a 29-year-old software developer. He has felt persistently low "
            "for the past 3 months. He has lost interest in football, which he used to love. "
            "He is sleeping 11 hours a night but still wakes exhausted. He has lost 6 kg "
            "without trying. He finds it hard to concentrate at work and has been underperforming. "
            "He denies active suicidal ideation but admits things feel 'pointless'. "
            "He drinks 4–5 beers most evenings to help him sleep. "
            "His relationship ended 4 months ago. He has no psychiatric history. "
            "He is reluctant to discuss his feelings in detail."
        ),
    },
    {
        "title": "Headache — Subarachnoid Haemorrhage",
        "patient_name": "Sophie Brennan",
        "age": 42,
        "gender": "Female",
        "condition": "Subarachnoid haemorrhage",
        "specialty": "neurology",
        "difficulty": "advanced",
        "patient_role": "frightened, articulate, describes symptoms precisely",
        "expected_diagnosis": "Subarachnoid haemorrhage",
        "patient_story": (
            "Sophie Brennan is a 42-year-old teacher. She developed the worst headache of "
            "her life suddenly while at her desk — 'like a thunderclap, out of nowhere'. "
            "The headache came on over seconds, rated 10/10. She briefly lost consciousness. "
            "She has photophobia and neck stiffness. She vomited once. "
            "She has no significant past medical history. She does not smoke. "
            "She takes the combined oral contraceptive pill. Her mother had a brain aneurysm. "
            "She is very anxious and keeps asking if she is going to be okay."
        ),
    },
    {
        "title": "Knee Pain — Osteoarthritis",
        "patient_name": "Patricia Adeyemi",
        "age": 63,
        "gender": "Female",
        "condition": "Osteoarthritis of the knee",
        "specialty": "musculoskeletal",
        "difficulty": "foundation",
        "patient_role": "cheerful, chatty, tends to go off on tangents",
        "expected_diagnosis": "Osteoarthritis of the right knee",
        "patient_story": (
            "Patricia Adeyemi is a 63-year-old retired nurse. She has had gradual right knee "
            "pain for 2 years, worse in the past 6 months. The pain is worse going downstairs "
            "and after prolonged sitting — she gets stiffness for about 20 minutes in the morning. "
            "It improves with movement. She takes ibuprofen from the chemist which helps a little. "
            "Her BMI is 31. She has type 2 diabetes managed with metformin. "
            "No trauma to the knee. She is worried it might be 'something serious'."
        ),
    },
    {
        "title": "Abdominal Pain — Appendicitis",
        "patient_name": "Ryan Kowalski",
        "age": 22,
        "gender": "Male",
        "condition": "Acute appendicitis",
        "specialty": "gastro",
        "difficulty": "core",
        "patient_role": "stoic, minimises pain, was dragged in by his mother",
        "expected_diagnosis": "Acute appendicitis",
        "patient_story": (
            "Ryan Kowalski is a 22-year-old university student. He has had abdominal pain "
            "since yesterday. It started around the navel and has moved to the right lower "
            "abdomen over 12 hours. He rates it 7/10. He has lost his appetite completely — "
            "unusual for him. He vomited twice. He has a temperature. "
            "He has not opened his bowels today. He has no past medical history and takes no medication. "
            "He doesn't want to make a fuss and keeps saying 'it's probably nothing'."
        ),
    },
    {
        "title": "Increased Thirst — New Type 1 Diabetes",
        "patient_name": "Amara Diallo",
        "age": 17,
        "gender": "Female",
        "condition": "Type 1 diabetes mellitus",
        "specialty": "endocrine",
        "difficulty": "core",
        "patient_role": "nervous teenager, her mother is in the waiting room",
        "expected_diagnosis": "New onset type 1 diabetes mellitus",
        "patient_story": (
            "Amara Diallo is a 17-year-old student. Over the past 6 weeks she has been "
            "excessively thirsty, drinking 4–5 litres of water per day. She is urinating "
            "very frequently — waking 3 times a night. She has lost 5 kg without dieting. "
            "She feels exhausted all the time and her vision has been slightly blurry. "
            "She had a urine dipstick at school that showed glucose and ketones. "
            "No family history of diabetes. She is generally healthy, no medications. "
            "She is worried about what this means for her A-levels and driving."
        ),
    },
    {
        "title": "Palpitations — Atrial Fibrillation",
        "patient_name": "Norman Whitfield",
        "age": 71,
        "gender": "Male",
        "condition": "Atrial fibrillation",
        "specialty": "cardiology",
        "difficulty": "core",
        "patient_role": "hard of hearing, asks for things to be repeated, jovial personality",
        "expected_diagnosis": "Atrial fibrillation",
        "patient_story": (
            "Norman Whitfield is a 71-year-old retired headteacher. He has had episodes of "
            "palpitations for the past 2 months — feeling like his heart is 'fluttering' or "
            "'racing irregularly'. Episodes last 20–30 minutes and can come on at rest or "
            "during activity. He feels slightly breathless during attacks. "
            "He has hypertension and type 2 diabetes. He takes ramipril, amlodipine, "
            "and metformin. He does not smoke. He drinks about 10 units of alcohol per week "
            "(more at Christmas, he jokes). His mother had a stroke at 75."
        ),
    },
    {
        "title": "Back Pain — Cauda Equina",
        "patient_name": "Leila Nazari",
        "age": 35,
        "gender": "Female",
        "condition": "Cauda equina syndrome",
        "specialty": "musculoskeletal",
        "difficulty": "advanced",
        "patient_role": "in significant pain, slightly distressed, cooperative",
        "expected_diagnosis": "Cauda equina syndrome — surgical emergency",
        "patient_story": (
            "Leila Nazari is a 35-year-old physiotherapist with a 3-year history of lower back pain. "
            "Over the last 48 hours her pain has dramatically worsened and now radiates down both legs. "
            "She has bilateral leg weakness and numbness in a saddle distribution. "
            "She has had urinary retention — she has not passed urine in 12 hours despite feeling the urge. "
            "She has no bowel sensation currently. She is very scared. "
            "She takes ibuprofen and has tried physiotherapy. No trauma. No previous surgery. "
            "She is keen to downplay the bladder/bowel symptoms due to embarrassment."
        ),
    },
    {
        "title": "Tiredness — Hypothyroidism",
        "patient_name": "Fiona Campbell",
        "age": 44,
        "gender": "Female",
        "condition": "Hypothyroidism",
        "specialty": "endocrine",
        "difficulty": "foundation",
        "patient_role": "articulate, has Googled her symptoms, comes with a list of questions",
        "expected_diagnosis": "Hypothyroidism",
        "patient_story": (
            "Fiona Campbell is a 44-year-old accountant. Over the past 6 months she has felt "
            "increasingly tired despite sleeping 9 hours. She has gained 8 kg without changing her diet. "
            "She feels the cold much more than before. She has become constipated (opens bowels every 4 days). "
            "Her skin feels dry and her hair has thinned noticeably. She feels low in mood. "
            "Her periods have become heavier over the past 3 months. "
            "Her sister was diagnosed with hypothyroidism last year. "
            "She takes no regular medication. She is a non-smoker and drinks socially."
        ),
    },
    {
        "title": "Cough — Lung Cancer Red Flags",
        "patient_name": "David Martins",
        "age": 62,
        "gender": "Male",
        "condition": "Suspected lung cancer",
        "specialty": "respiratory",
        "difficulty": "advanced",
        "patient_role": "dismissive of symptoms, initially reluctant to discuss them",
        "expected_diagnosis": "Suspected lung cancer — urgent 2-week wait referral",
        "patient_story": (
            "David Martins is a 62-year-old builder. He has had a persistent cough for 3 months "
            "which has not improved. He coughed up blood twice last week — 'just a spot' he says. "
            "He has lost about 8 kg over 3 months, which he attributes to 'not eating properly'. "
            "He has been increasingly breathless on exertion. He smokes 20 cigarettes a day and "
            "has done so for 45 years. He has no significant past medical history. "
            "He is very reluctant to discuss his symptoms and keeps changing the subject. "
            "His wife convinced him to come. He fears the worst but doesn't want to say so."
        ),
    },
]


class Command(BaseCommand):
    help = "Seed the database with 11 patient cases"

    def handle(self, *args, **options):
        created = 0
        for data in CASES:
            _, was_created = PatientCase.objects.get_or_create(
                title=data["title"],
                defaults=data,
            )
            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {created} new case(s). Total: {PatientCase.objects.count()}"
            )
        )
