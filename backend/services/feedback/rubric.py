"""
OSCE rubric — 10 history-taking domains.
"""

OSCE_RUBRIC = {
    "domains": [
        {
            "key": "presenting_complaint",
            "label": "Presenting complaint",
            "max_score": 10,
            "keywords": [["what brings you", "how can i help", "what seems to be", "reason for coming"]],
        },
        {
            "key": "history_of_pc",
            "label": "History of presenting complaint",
            "max_score": 10,
            "keywords": [
                ["when did"],
                ["how long"],
                ["describe", "feel like", "character"],
                ["worse", "better", "reliev"],
            ],
        },
        {
            "key": "past_medical_history",
            "label": "Past medical history",
            "max_score": 10,
            "keywords": [
                ["medical condition", "health condition", "past history"],
                ["hospital", "admitted"],
                ["operation", "surgery"],
            ],
        },
        {
            "key": "drug_history",
            "label": "Drug history and allergies",
            "max_score": 10,
            "keywords": [
                ["medication", "medicine", "tablet", "pill"],
                ["allerg", "reaction"],
                ["over the counter", "pharmacy"],
            ],
        },
        {
            "key": "family_history",
            "label": "Family history",
            "max_score": 10,
            "keywords": [["family", "parents", "mother", "father", "sibling", "relative"]],
        },
        {
            "key": "social_history",
            "label": "Social history",
            "max_score": 10,
            "keywords": [
                ["smok", "cigarette"],
                ["alcohol", "drink", "unit"],
                ["work", "job", "occupation"],
            ],
        },
        {
            "key": "ice",
            "label": "Ideas, concerns & expectations",
            "max_score": 10,
            "keywords": [
                ["think", "what do you think", "causing"],
                ["worr", "concern", "scared", "fear"],
                ["hoping", "expect", "like me to"],
            ],
        },
        {
            "key": "systems_review",
            "label": "Systems review",
            "max_score": 10,
            "keywords": [["any other symptom", "anything else", "generally"]],
        },
        {
            "key": "summarising",
            "label": "Summarising",
            "max_score": 10,
            "keywords": [["let me check", "to summarise", "to recap", "have i understood", "just to confirm"]],
        },
        {
            "key": "communication",
            "label": "Communication",
            "max_score": 10,
            "keywords": [],   # LLM-only domain — no keyword rule
        },
    ],
    "pass_mark":   60,
    "distinction": 80,
}
