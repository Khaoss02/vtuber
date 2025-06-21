from transformers import AutoModel, AutoTokenizer
import torch

class HFLocalChat:
    """
    Carga un modelo *multimodal* Qwen2.5‑VL‑3B‑Instruct localmente y
    expone un método `chat(prompt) -> str`.
    """
    def __init__(self, model_name: str = "Qwen/Qwen2.5-VL-3B-Instruct"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

        self.model = AutoModel.from_pretrained(
            model_name,
            device_map={"": "cpu"},  # forzamos CPU para evitar errores
            torch_dtype=torch.float32,
            trust_remote_code=True,
        )
        # ¡NO hagas .to(device)! porque device_map ya gestiona el mapeo

    def chat(self, prompt: str, max_new_tokens: int = 150) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
