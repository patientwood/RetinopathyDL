
import io
from pathlib import Path

import torch
import timm
from PIL import Image
import torchvision.transforms as T
from fastapi import HTTPException

MODEL_PATH = Path("MODELS") / "maxvit_tiny_tf_224_binary_best.pt"
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

_preprocess = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

def load_model(device: torch.device):

    if not MODEL_PATH.exists():
        raise RuntimeError(f"Model file not found at: {MODEL_PATH}")
    
    model = timm.create_model(
        "maxvit_tiny_tf_224.in1k",
        pretrained=False,
        num_classes=2,
    )

    state = torch.load(
        MODEL_PATH,
        map_location=device,
        weights_only=False,
    )

    model.load_state_dict(state)
    model.to(device)
    model.eval()
    model = model.float()
    return model

def read_imagefile(file_bytes: bytes) -> Image.Image:
    try:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Unsupported or corrupt image.")
    return img

def preprocess_image(pil_img: Image.Image, device: torch.device) -> torch.Tensor:
    x = _preprocess(pil_img)
    x = x.unsqueeze(0)
    x = x.to(device=device, dtype=torch.float32)
    return x

def predict_image(file_bytes: bytes, model: torch.nn.Module, device: torch.device):
    pil_img = read_imagefile(file_bytes)
    x = preprocess_image(pil_img, device)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, 1)[0]

    no_dr = float(probs[0].item())
    dr    = float(probs[1].item())
    pred  = "DR" if dr >= no_dr else "No_DR"

    return {
        "pred_class": pred,
        "prob_no_dr": no_dr,
        "prob_dr": dr,
        "raw": [no_dr, dr],
    }

