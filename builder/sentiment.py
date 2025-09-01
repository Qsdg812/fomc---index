from typing import List
import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

_MODEL_NAME = os.getenv("FINBERT_MODEL", "ProsusAI/finbert")
_tokenizer = None
_model = None
_device = "cpu"

def _load():
    global _tokenizer, _model
    if _tokenizer is not None and _model is not None:
        return
    _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
    _model = AutoModelForSequenceClassification.from_pretrained(_MODEL_NAME)
    _model.eval()
    _model.to(_device)

def _logits_to_label_indices(logits: torch.Tensor) -> List[int]:
    idx = logits.argmax(dim=-1).tolist()
    if isinstance(idx, int):
        idx = [idx]
    return [{0: -1, 1: 0, 2: 1}[i] for i in idx]  # [neg, neu, pos] → [-1,0,1]

def predict_labels(sentences: List[str]) -> List[int]:
    if not sentences:
        return []
    _load()

    labels: List[int] = []
    bs = int(os.getenv("FINBERT_BATCH", "16"))
    max_len = int(os.getenv("FINBERT_MAXLEN", "256"))
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    for i in range(0, len(sentences), bs):
        chunk = sentences[i : i + bs]
        toks = _tokenizer(
            chunk, padding=True, truncation=True, max_length=max_len, return_tensors="pt"
        )
        with torch.no_grad():
            out = _model(**{k: v.to(_device) for k, v in toks.items()})
            logits = out.logits.cpu()
        labels.extend(_logits_to_label_indices(logits))
    return labels
