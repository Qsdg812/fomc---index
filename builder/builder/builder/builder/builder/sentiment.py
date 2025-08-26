import numpy as np
from typing import List


# Replace this with your real model (FinBERT etc.).
# Input: list of sentences → Output: list of labels in {-1, 0, 1}


def predict_labels(sentences: List[str]) -> List[int]:
rng = np.random.default_rng(42)
return rng.choice([0, 1, -1], size=len(sentences)).tolist()
