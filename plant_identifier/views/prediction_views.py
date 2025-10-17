# plant_identifier/views/prediction_views.py

import os
import json
import re
import random
import requests
from requests.exceptions import ReadTimeout, ConnectionError as ReqConnError

import torch
from torchvision import transforms
from PIL import Image

from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


# =============================================================================
# Public JSON mappings (loaded at import time so random_views.py can import them)
# =============================================================================

BASE_DIR = getattr(settings, "BASE_DIR", os.getcwd())
JSON_DIR = os.path.join(BASE_DIR, "json")

def _safe_load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[prediction_views] Warning: failed to load {path}: {e}")
        return default

# Exposed names expected by random_views.py:
class_idx_to_species_id = _safe_load_json(
    os.path.join(JSON_DIR, "class_idx_to_species_id.json"),
    {}
)

_cmn = _safe_load_json(
    os.path.join(JSON_DIR, "plantnet300k_species_id_2_CmnName.json"),
    {}
)
species_id_to_cmn_name = {str(k).strip(): v for k, v in _cmn.items()}

_scn = _safe_load_json(
    os.path.join(JSON_DIR, "plantnet300K_species_id_2_ScnName.json"),
    {}
)
species_id_to_scn_name = {str(k).strip(): v for k, v in _scn.items()}


# =============================================================================
# Tiny CORS shim for dev
# =============================================================================

def _corsify(request, response):
    origin = request.headers.get("Origin")
    allowed = getattr(settings, "CORS_ALLOWED_ORIGINS", [])
    if origin and origin in allowed:
        response["Access-Control-Allow-Origin"] = origin
        response["Vary"] = "Origin"
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Headers"] = "content-type, x-csrftoken, authorization"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# =============================================================================
# LLM explanation endpoint (/api/explain/) using Ollama text model
# =============================================================================

TEXT_MODEL = os.getenv("OLLAMA_TEXT_MODEL", "Allen_Rodas11/llama3-plant")
OLLAMA_HOST = (os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434") or "").rstrip("/")

# Tunables
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "180"))
OLLAMA_NUM_PREDICT     = int(os.getenv("OLLAMA_NUM_PREDICT", "360"))
OLLAMA_TEMPERATURE     = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))

BINOMIAL_G = re.compile(r"^[A-Z][a-z-]+$")
BINOMIAL_S = re.compile(r"^[a-z][a-z-]+$")

def normalize_binomial(name: str | None) -> str | None:
    """Extract 'Genus species' anywhere within a provided string."""
    if not isinstance(name, str):
        return None
    cleaned = re.sub(r"[(),]", " ", name.strip())
    tokens = [t for t in re.split(r"\s+", cleaned) if t]
    for i in range(len(tokens) - 1):
        g, s = tokens[i], tokens[i + 1]
        if BINOMIAL_G.match(g) and BINOMIAL_S.match(s):
            return f"{g} {s}"
    return None

def nonplant_label(name: str) -> bool:
    s = (name or "").strip().lower()
    return s in {"unknown", "no plant", "not a plant", "none", "unclassified"}

def _ollama_generate(payload: dict, timeout: int) -> dict:
    r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json() or {}

def call_text_llm(prompt: str) -> str:
    """Call Ollama once; on timeout/connection warm up the model and retry once."""
    body = {
        "model": TEXT_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": OLLAMA_NUM_PREDICT,
            "temperature": OLLAMA_TEMPERATURE,
        },
        "keep_alive": "10m",
    }
    try:
        data = _ollama_generate(body, timeout=OLLAMA_TIMEOUT_SECONDS)
        return data.get("response", "") or ""
    except (ReadTimeout, ReqConnError):
        # Warm-up minimal call then retry full request once
        _ollama_generate(
            {
                "model": TEXT_MODEL,
                "prompt": "ok",
                "stream": False,
                "options": {"num_predict": 1},
                "keep_alive": "10m",
            },
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        data = _ollama_generate(body, timeout=OLLAMA_TIMEOUT_SECONDS)
        return data.get("response", "") or ""
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")

@csrf_exempt
def explain_llm(request):
    # Preflight
    if request.method == "OPTIONS":
        return _corsify(request, HttpResponse(status=200))
    if request.method != "POST":
        return _corsify(request, JsonResponse({"error": "POST required"}, status=405))

    # Parse body
    try:
        body = json.loads(request.body or "{}") or {}
    except Exception:
        body = {}

    raw_sci = body.get("scientificName") if isinstance(body.get("scientificName"), str) else ""
    sci = normalize_binomial(raw_sci)
    com = body.get("commonName") if isinstance(body.get("commonName"), str) else ""
    region = body.get("region") if isinstance(body.get("region"), str) else "Unknown"

    # If uncertain, return 400 so the frontend can show a clear message
    if (not sci) or nonplant_label(sci):
        return _corsify(request, JsonResponse(
            {"error": "Identification is uncertain; no explanation generated."},
            status=400,
        ))

    # ---- Bullet–point format: EXACT headings + 3–5 bullets per section ----
    prompt = f"""
You are a botanical expert. Provide a concise, practical overview.

Plant: "{sci}" (common: "{com}") — Region: "{region}"

Write EXACTLY these six markdown sections, in this order.
For EACH section, return 3–5 bullet points, and make every bullet start with "- " (dash + space).
Do not include any prose outside of the bullets.

**Medicinal Uses:**
- ...

**Culinary Uses:**
- ...

**Toxicity Risks:**
- ...

**Cultural Significance:**
- ...

**Ecological Role:**
- ...

**Cultivation Tips:**
- ...

Rules:
- Do NOT add or rename headings.
- Use short, factual bullets (no fluff).
- If the info is not well established, include a bullet: "- Not well-established."
""".strip()

    try:
        text = call_text_llm(prompt)
        if not text.strip():
            return _corsify(request, JsonResponse(
                {"error": "LLM returned empty text"},
                status=502,
            ))
        return _corsify(request, JsonResponse({"explanation": text, "model": TEXT_MODEL}, status=200))
    except Exception as e:
        return _corsify(request, JsonResponse(
            {"error": "Failed to get explanation from LLM.", "details": str(e)},
            status=502,
        ))


# =============================================================================
# CNN Predict endpoint (/predict/) – lazy-loaded model & transforms
# =============================================================================

_use_gpu = False
_device = None
_model = None
_transform = None

def _lazy_load_stack():
    global _device, _model, _transform
    if _model is not None:
        return

    _device = torch.device('cuda' if _use_gpu else 'cpu')

    model_path = os.path.join(BASE_DIR, "models", "efficientnet_b3.pt")
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}")

    _model = torch.jit.load(model_path, map_location=_device)
    _model.to(_device).eval()

    global transforms
    _transform = transforms.Compose([
        transforms.Resize(300),
        transforms.CenterCrop(300),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])

def _sample_image_for_species(species_id_str: str):
    media_root = getattr(settings, "MEDIA_ROOT", os.path.join(BASE_DIR, "media"))
    media_url  = getattr(settings, "MEDIA_URL", "/media/")
    folder = os.path.join(media_root, "images", species_id_str)
    if not os.path.isdir(folder):
        return None
    files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    if not files:
        return None
    choice = random.choice(files)
    return f"{media_url.rstrip('/')}/images/{species_id_str}/{choice}"

@csrf_exempt
def predict(request):
    # Preflight
    if request.method == "OPTIONS":
        return _corsify(request, HttpResponse(status=200))
    if request.method != "POST" or not request.FILES.get("image"):
        return _corsify(request, JsonResponse({"error": "POST an image with key 'image'."}, status=400))

    try:
        _lazy_load_stack()
    except Exception as e:
        return _corsify(request, JsonResponse({"error": f"Model init failed: {e}"}, status=500))

    try:
        image_file = request.FILES["image"]
        image = Image.open(image_file).convert("RGB")
        image = _transform(image).unsqueeze(0).to(_device)

        with torch.no_grad():
            output = _model(image)
            probs = torch.nn.functional.softmax(output, dim=1)
            top_prob, predicted_idx = torch.max(probs, dim=1)
            confidence = float(top_prob.item())
            predicted_idx = int(predicted_idx.item())

        species_id = class_idx_to_species_id.get(str(predicted_idx), None)
        species_id_str = str(species_id).strip() if species_id is not None else None

        common_name = species_id_to_cmn_name.get(species_id_str, "Unknown")
        scientific_name = species_id_to_scn_name.get(species_id_str, "Unknown")

        sample_image_url = _sample_image_for_species(species_id_str) if species_id_str else None

        return _corsify(request, JsonResponse({
            "predicted_index": predicted_idx,
            "species_id": int(species_id) if species_id is not None else 0,
            "common_name": common_name,
            "scientific_name": scientific_name,
            "confidence": confidence,
            "sample_image": sample_image_url or "Not available",
        }))

    except Exception as e:
        return _corsify(request, JsonResponse({"error": str(e)}, status=400))
