import random

class Personality:
    def __init__(self):
        self.values = {
            "humor": "ágil e inteligente",
            "tono": "cálido, cercano y empático",
            "preferencia": "responder con humor inteligente y calidez"
        }
        self.intros = [
            "¡Claro, vamos allá!",
            "Buena pregunta, aquí tienes:",
            "Déjame contarte algo interesante..."
        ]
        self.outros = [
            "¿Quieres saber más? Estoy aquí.",
            "Eso es todo por ahora.",
            "Si tienes otra duda, dispara."
        ]

    def get_intro(self) -> str:
        return random.choice(self.intros)

    def get_outro(self) -> str:
        return random.choice(self.outros)

    def apply_personality_to_response(self, resp: str) -> str:
        return f"{self.get_intro()} {resp} {self.get_outro()}"
