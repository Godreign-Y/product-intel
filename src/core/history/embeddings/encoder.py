import hashlib
import numpy as np
from src.utils.logger import setup_logger

logger = setup_logger("embeddings_encoder")

class SentenceTransformerEncoder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.is_fallback = False
        
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading SentenceTransformer model '{model_name}'...")
            self.model = SentenceTransformer(model_name)
            logger.info("SentenceTransformer loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Could not load SentenceTransformer ('{str(e)}'). "
                "Switching to resilient deterministic word-hashing fallback (384 dimensions)."
            )
            self.is_fallback = True

    def encode(self, text: str) -> list:
        """
        Encodes text into a list of 384 floats.
        """
        if not text:
            return [0.0] * 384
            
        if not self.is_fallback and self.model is not None:
            try:
                embedding = self.model.encode(text)
                # Ensure it returns list
                if hasattr(embedding, "tolist"):
                    return embedding.tolist()
                return list(embedding)
            except Exception as e:
                logger.error(f"Failed to run model encoder: {e}. Falling back to hash encoding.")
                
        # Resilient fallback encoder
        return self._encode_fallback(text)

    def _encode_fallback(self, text: str, dimensions: int = 384) -> list:
        """
        Generates a deterministic 384-dimensional normalized vector
        based on md5 hashing of individual words.
        """
        words = text.lower().split()
        vector = np.zeros(dimensions)
        if not words:
            return vector.tolist()
            
        for word in words:
            # MD5 hash
            h_hex = hashlib.md5(word.encode("utf-8")).hexdigest()
            h_int = int(h_hex, 16)
            
            # Select bin and weight
            idx = h_int % dimensions
            weight = ((h_int // dimensions) % 100) / 100.0
            vector[idx] += (weight + 0.1)
            
        # L2 Normalize the vector to maintain cosine distance consistency
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
            
        return vector.tolist()
