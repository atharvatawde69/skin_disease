"""HAM10000 class definitions. No heavy imports so the web app can use it cheaply."""

# Order matters: the index in this list is the class id the models are trained on.
CLASS_CODES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]

CLASS_NAMES = {
    "akiec": "Actinic keratosis / intraepithelial carcinoma",
    "bcc": "Basal cell carcinoma",
    "bkl": "Benign keratosis-like lesion",
    "df": "Dermatofibroma",
    "mel": "Melanoma",
    "nv": "Melanocytic nevus (common mole)",
    "vasc": "Vascular lesion",
}

# Cancerous or pre-cancerous classes: a wrong "benign" answer here is the costly mistake.
NEEDS_ATTENTION = {"akiec", "bcc", "mel"}

# ImageNet statistics, required because the ResNet is initialised from ImageNet weights.
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)
