from typing import List
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ProsusAI/finbert
_model = None
_tokenizer = None

def _load():
    global _model, _tokenizer
    if _model is None:
        name = "ProsusAI/finbert"
        _tokenizer = AutoTokenizer.from_pretrained(name)
        _model = AutoModelForSequenceClassification.from_pretrained(name)
        _model.eval()

def _to_label(logits) -> int:
    # FinBERT: [negative, neutral, positive] 순
    idx = int(logits.argmax(dim=-1))
    return {0: -1, 1: 0, 2: 1}[idx]

def predict_labels(sentences: List[str]) -> List[int]:
    _load()
    labels = []
    bs = 16
    for i in range(0, len(sentences), bs):
        chunk = sentences[i:i+bs]
        toks = _tokenizer(
            chunk, padding=True, truncation=True, max_length=256, return_tensors="pt"
        )
        with torch.no_grad():
            out = _model(**toks).logits
        labels.extend([_to_label(row) for row in out])
    return labels
