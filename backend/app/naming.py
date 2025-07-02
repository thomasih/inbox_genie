from typing import List, Protocol
from transformers import pipeline

class IFolderNamer(Protocol):
    def name_folder(self, samples: List[str]) -> str:
        ...

class LocalLLMFolderNamer(IFolderNamer):
    def __init__(self):
        self.generator = pipeline("text-generation", model="google/flan-t5-small")
    def name_folder(self, samples: List[str]) -> str:
        prompt = "Here are some email snippets:\n" + "\n".join(f"- {s}" for s in samples)
        prompt += "\nSuggest a concise folder name (1–2 words):"
        result = self.generator(prompt, max_length=20, do_sample=False)
        return result[0]["generated_text"].strip()
