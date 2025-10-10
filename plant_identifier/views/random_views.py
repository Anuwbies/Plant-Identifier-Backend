import random
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from .prediction_views import (
    class_idx_to_species_id,
    species_id_to_cmn_name,
    species_id_to_scn_name,
)

@csrf_exempt
@require_GET
def random_plants(request):
    try:
        # Randomly select 50 class indices
        random_class_indices = random.sample(list(class_idx_to_species_id.keys()), 50)
        results = []

        for idx in random_class_indices:
            species_id = class_idx_to_species_id[idx]
            species_id_str = str(species_id).strip()

            common_name = species_id_to_cmn_name.get(species_id_str, "Unknown")
            scientific_name = species_id_to_scn_name.get(species_id_str, "Unknown")

            # Try to get one sample image from the folder
            sample_image_url = None
            species_folder = os.path.join("media", "images", species_id_str)
            if os.path.isdir(species_folder):
                files = [
                    f for f in os.listdir(species_folder)
                    if os.path.isfile(os.path.join(species_folder, f))
                ]
                if files:
                    sample_image_url = f"/media/images/{species_id_str}/{files[0]}"

            # Append plant info including index and species_id
            results.append({
                "index": int(idx),
                "species_id": int(species_id),
                "common_name": common_name,
                "scientific_name": scientific_name,
                "sample_image": sample_image_url or "Not available",
            })

        return JsonResponse({"plants": results}, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
