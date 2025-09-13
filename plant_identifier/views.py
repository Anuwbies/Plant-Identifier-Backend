from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from plant_identifier.form import UserRegistrationForm

@api_view(['POST'])
def registerUser(request):
    form = UserRegistrationForm(request.data)
    if form.is_valid():
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password'])
        user.save()
        return Response({'success': 'User created successfully!'}, status=status.HTTP_201_CREATED)
    else:
        return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
    
#==================================================================================================================

import torch
from torchvision import transforms
from PIL import Image
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os

# Config
use_gpu = False
device = torch.device('cuda' if use_gpu else 'cpu') 

# Load TorchScript model
model = torch.jit.load('models/efficientnet_b3.pt', map_location=device)
model.to(device)
model.eval()

# Load JSON mappings with UTF-8 encoding and clean keys
with open('json/class_idx_to_species_id.json', 'r', encoding='utf-8') as f:
    class_idx_to_species_id = json.load(f)

with open('json/plantnet300k_species_id_2_CmnName.json', 'r', encoding='utf-8') as f:
    species_id_to_cmn_name = json.load(f)
    species_id_to_cmn_name = {k.strip(): v for k, v in species_id_to_cmn_name.items()}

with open('json/plantnet300K_species_id_2_ScnName.json', 'r', encoding='utf-8') as f:
    species_id_to_scn_name = json.load(f)
    species_id_to_scn_name = {k.strip(): v for k, v in species_id_to_scn_name.items()}

# Preprocessing pipeline
transform = transforms.Compose([
    transforms.Resize(300),
    transforms.CenterCrop(300),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

CONFIDENCE_THRESHOLD = 0.6

@csrf_exempt
def predict(request):
    if request.method == "POST" and request.FILES.get("image"):
        try:
            # Load and preprocess input image
            image_file = request.FILES["image"]
            image = Image.open(image_file).convert("RGB")
            image = transform(image).unsqueeze(0).to(device)

            # Inference
            with torch.no_grad():
                output = model(image)
                probs = torch.nn.functional.softmax(output, dim=1)
                top_prob, predicted_idx = torch.max(probs, dim=1)
                confidence = top_prob.item()
                predicted_idx = predicted_idx.item()

            # Map predicted index to scientific and common names
            species_id = class_idx_to_species_id.get(str(predicted_idx), None)
            species_id_str = str(species_id).strip() if species_id is not None else None

            common_name = species_id_to_cmn_name.get(species_id_str, "Unknown")
            scientific_name = species_id_to_scn_name.get(species_id_str, "Unknown")

            # Find the first image in the folder for this species
            sample_image_url = None
            if species_id_str:
                species_folder = os.path.join("media", "images", species_id_str)
                if os.path.isdir(species_folder):
                    files = os.listdir(species_folder)
                    files = [f for f in files if os.path.isfile(os.path.join(species_folder, f))]
                    if files:
                        first_image = files[0]
                        sample_image_url = f"/media/images/{species_id_str}/{first_image}"

            return JsonResponse({
                "predicted_index": predicted_idx,
                "common_name": common_name,
                "scientific_name": scientific_name,
                "confidence": confidence,
                "sample_image": sample_image_url if sample_image_url else "Not available"
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "POST an image with key 'image'."}, status=400)

#==================================================================================================================

import random
from django.views.decorators.http import require_GET

@csrf_exempt
@require_GET
def random_plants(request):
    try:
        # Pick 20 random class indices from the available keys
        random_class_indices = random.sample(list(class_idx_to_species_id.keys()), 20)

        results = []
        for idx in random_class_indices:
            species_id = class_idx_to_species_id[idx]
            species_id_str = str(species_id).strip()

            common_name = species_id_to_cmn_name.get(species_id_str, "Unknown")
            scientific_name = species_id_to_scn_name.get(species_id_str, "Unknown")

            # Get one sample image if available
            sample_image_url = None
            species_folder = os.path.join("media", "images", species_id_str)
            if os.path.isdir(species_folder):
                files = os.listdir(species_folder)
                files = [f for f in files if os.path.isfile(os.path.join(species_folder, f))]
                if files:
                    sample_image_url = f"/media/images/{species_id_str}/{files[0]}"

            results.append({
                "common_name": common_name,
                "scientific_name": scientific_name,
                "sample_image": sample_image_url if sample_image_url else "Not available"
            })

        return JsonResponse({"plants": results}, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
