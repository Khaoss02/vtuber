from PIL import ImageGrab
import torch
from transformers import AutoProcessor, AutoModelForVision2Seq

class HFScreenAgent:
    def __init__(self, model_name="C:/vtuber/models/qwen2.5-vl-3b-instruct", load_in_8bit=False):
        # Detecta device, pero no uses .to() manual si usas device_map="auto"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        self.processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
        self.model = AutoModelForVision2Seq.from_pretrained(
            model_name,
            trust_remote_code=True,
            device_map="auto",
            load_in_8bit=load_in_8bit,
        )
        # No uses self.model.to(self.device) para evitar el error de meta tensor

    @staticmethod
    def grab_screen():
        return ImageGrab.grab()

    def chat(self, text: str, include_screen=True, max_new_tokens=128) -> str:
        images = [self.grab_screen()] if include_screen else None
        inputs = self.processor(images=images, text=text, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False)
        return self.processor.decode(outputs[0], skip_special_tokens=True)
