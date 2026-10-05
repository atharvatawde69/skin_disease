"""Plain-language, educational information shown next to a prediction. Not medical advice."""

RISK_LABEL = {
    "high": "Needs prompt attention",
    "medium": "Should be checked",
    "low": "Usually harmless, keep an eye on it",
}

CLASS_INFO = {
    "mel": {
        "risk": "high",
        "what": ("Melanoma is a cancer of the pigment-producing skin cells. It is the most serious common skin "
                 "cancer because it can spread to other organs if it is found late. Found early, it is usually "
                 "treatable."),
        "look": ("Often an asymmetric dark spot with an uneven border and several colours (brown, black, red, white "
                 "or blue), or a mole that has recently grown or changed."),
        "next": ["Book an appointment with a dermatologist soon. Do not wait for it to hurt or itch.",
                 "Take a clear photo and note the date, so changes can be tracked.",
                 "Only a doctor can confirm this, usually with a small biopsy."],
    },
    "bcc": {
        "risk": "medium",
        "what": ("Basal cell carcinoma is the most common type of skin cancer. It grows slowly and rarely spreads, "
                 "but it can damage the skin around it if it is left untreated."),
        "look": "Often a pearly or shiny bump, a flat scar-like patch, or a sore that bleeds and does not heal.",
        "next": ["See a dermatologist to have it examined in the coming weeks.",
                 "A small biopsy confirms the diagnosis.",
                 "It is highly treatable, most often with a minor procedure."],
    },
    "akiec": {
        "risk": "medium",
        "what": ("Actinic keratosis is a rough, scaly patch caused by years of sun exposure. Some patches can turn "
                 "into squamous cell skin cancer. Intraepithelial carcinoma (Bowen's disease) is an early cancer "
                 "limited to the top skin layer."),
        "look": ("Rough, dry, scaly spots on sun-exposed areas such as the face, scalp, ears and hands, often easier "
                 "to feel than to see."),
        "next": ["Have a dermatologist look at it. Treatment is simple when it is done early.",
                 "Protect the area from the sun with shade, a hat and SPF 30 or higher sunscreen.",
                 "Check your other sun-exposed skin too, as these patches often appear in groups."],
    },
    "nv": {
        "risk": "low",
        "what": "A melanocytic nevus is a common mole. Most people have many of them and nearly all are harmless.",
        "look": "Evenly coloured, round or oval, with a smooth edge and a stable size.",
        "next": ["No treatment is needed if it has not changed.",
                 "Check your moles every month or two using the ABCDE rules below.",
                 "See a doctor if it grows, changes colour or shape, bleeds, itches or looks different from your "
                 "other moles."],
    },
    "bkl": {
        "risk": "low",
        "what": ("Benign keratosis-like lesions include seborrheic keratoses and sun spots. They are harmless "
                 "growths of the top skin layer and become more common with age."),
        "look": "Waxy, rough or 'stuck-on' brown or tan spots with a sharply defined edge.",
        "next": ["No treatment is needed unless it bothers you or catches on clothing.",
                 "Some melanomas can look similar, so have a doctor check any spot that changes quickly, bleeds or "
                 "looks unusual.",
                 "A dermatologist can remove it if you want."],
    },
    "df": {
        "risk": "low",
        "what": ("A dermatofibroma is a small, harmless, firm bump in the skin, often on the legs. It is usually "
                 "linked to a minor injury such as an insect bite or a shaving cut."),
        "look": "Brown or pink and firm, about the size of a pencil eraser. It often dimples inward when pinched.",
        "next": ["No treatment is needed.",
                 "See a doctor if it grows quickly, bleeds, hurts or changes colour.",
                 "A dermatologist can remove it if you want."],
    },
    "vasc": {
        "risk": "low",
        "what": "Vascular lesions are growths made of small blood vessels, such as cherry angiomas. Most are harmless.",
        "look": "Bright red, purple or blue spots or bumps that may turn pale when pressed.",
        "next": ["Most need no treatment.",
                 "See a doctor if one bleeds repeatedly, grows quickly or changes appearance.",
                 "Dark, blood-vessel-like spots can sometimes be mistaken for melanoma, so ask a dermatologist if "
                 "you are unsure."],
    },
}
