import os
from flask import Flask, request, render_template
import torch
import timm
from PIL import Image
from torchvision import transforms

# Flask app
app = Flask(__name__)

# Config
MODEL_NAME = "vit_base_patch16_384"
CHECKPOINT_PATH = "best.pt"
IMG_SIZE = 384

# Load model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load checkpoint
checkpoint = torch.load("best.pt", map_location="cpu")

# Create model
model = timm.create_model("vit_base_patch16_384", pretrained=False, num_classes=35)

# Handle DDP-trained checkpoints (remove "module." prefix)
state_dict = checkpoint["model"]
new_state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}

model.load_state_dict(new_state_dict)
model.eval()


# Preprocessing
transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.5, 0.5, 0.5),
                         std=(0.5, 0.5, 0.5))
])

# Your 35 classes
CLASS_NAMES = [
    'Acne And Rosacea Photos',
    'Actinic Keratosis Basal Cell Carcinoma And Other Malignant Lesions',
    'Atopic Dermatitis Photos',
    'Ba  Cellulitis',
    'Ba Impetigo',
    'Benign',
    'Bullous Disease Photos',
    'Cellulitis Impetigo And Other Bacterial Infections',
    'Eczema Photos',
    'Exanthems And Drug Eruptions',
    'Fu Athlete Foot',
    'Fu Nail Fungus',
    'Fu Ringworm',
    'Hair Loss Photos Alopecia And Other Hair Diseases',
    'Heathy',
    'Herpes Hpv And Other Stds Photos',
    'Light Diseases And Disorders Of Pigmentation',
    'Lupus And Other Connective Tissue Diseases',
    'Malignant',
    'Melanoma Skin Cancer Nevi And Moles',
    'Nail Fungus And Other Nail Disease',
    'Pa Cutaneous Larva Migrans',
    'Poison Ivy Photos And Other Contact Dermatitis',
    'Psoriasis Pictures Lichen Planus And Related Diseases',
    'Rashes',
    'Scabies Lyme Disease And Other Infestations And Bites',
    'Seborrheic Keratoses And Other Benign Tumors',
    'Systemic Disease',
    'Tinea Ringworm Candidiasis And Other Fungal Infections',
    'Urticaria Hives',
    'Vascular Tumors',
    'Vasculitis Photos',
    'Vi Chickenpox',
    'Vi Shingles',
    'Warts Molluscum And Other Viral Infections'
]

@app.route("/", methods=["GET", "POST"])
def index():
    prediction = None
    if request.method == "POST":
        if "file" not in request.files:
            return render_template("index.html", prediction="No file uploaded")
        file = request.files["file"]
        if file.filename == "":
            return render_template("index.html", prediction="No file selected")

        # Save and process image
        img_path = os.path.join("static", file.filename)
        file.save(img_path)
        image = Image.open(img_path).convert("RGB")
        input_tensor = transform(image).unsqueeze(0).to(device)

        # Run inference
        with torch.no_grad():
            outputs = model(input_tensor)
            _, pred_idx = torch.max(outputs, 1)
            prediction = CLASS_NAMES[pred_idx.item()]

        return render_template("index.html", prediction=prediction, img_path=img_path)

    return render_template("index.html", prediction=prediction)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
