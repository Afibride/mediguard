import hashlib
import math
import re

EMBEDDING_DIM = 384


def embed_text(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    """Deterministic local embedding used when sentence-transformers is unavailable."""
    vector = [0.0] * dim
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]
