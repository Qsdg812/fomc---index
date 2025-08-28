from typing import List
import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# FinBERT 분류 모델 (재무 문장용 3-클래스)
_MODEL_NAME = os.getenv("FINBERT_MODEL", "ProsusAI/finbert")

# 전역 캐시 (Actions 런타임에서 1회만 로드)
_tokenizer = None
_model = None
_device = "cpu"  # GitHub Actions CPU 환경

def _load():
    global _tokenizer, _model
    if _tokenizer is not None and _model is not None:
        return
    _tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
    _model = AutoModelForSequenceClassification.from_pretrained(_MODEL_NAME)
    _model.eval()
    _model.to(_device)

def _logits_to_label_indices(logits: torch.Tensor) -> List[int]:
    """
    FinBERT 로짓 순서: [negative, neutral, positive]
    argmax 인덱스를 [-1, 0, 1]로 매핑
    """
    idx = logits.argmax(dim=-1).tolist()
    if isinstance(idx, int):
        idx = [idx]
    return [{0: -1, 1: 0, 2: 1}[i] for i in idx]

def predict_labels(sentences: List[str]) -> List[int]:
    """
    입력: 문장 리스트
    출력: 각 문장의 레이블 [-1(부정), 0(중립), 1(긍정)]
    """
    if not sentences:
        return []
    _load()

    labels: List[int] = []
    bs = int(os.getenv("FINBERT_BATCH", "16"))  # 배치 크기 조절 가능
    max_len = int(os.getenv("FINBERT_MAXLEN", "256"))

    # 토크나이저 병렬 경고 끄기(로그 깔끔)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    for i in range(0, len(sentences), bs):
        chunk = sentences[i : i + bs]
        toks = _tokenizer(
            chunk,
            padding=True,
            truncation=True,
            max_length=max_len,
            return_tensors="pt",
        )
        with torch.no_grad():
            out = _model(**{k: v.to(_device) for k, v in toks.items()})
            logits = out.logits.cpu()
        labels.extend(_logits_to_label_indices(logits))
    return labels
