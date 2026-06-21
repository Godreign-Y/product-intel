import faiss
import numpy as np
from typing import List, Dict, Any

class VectorStoreIndex:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        # Use IndexFlatIP (Inner Product) wrapped in IndexIDMap to map vectors to custom IDs
        self.index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))
        self.id_to_metadata = {}

    def add_vectors(self, vectors: List[List[float]], ids: List[int], metadata: List[Dict[str, Any]]):
        """
        Normalizes vectors and adds them to the FAISS index with matching custom integer IDs.
        """
        if not vectors:
            return
        np_vectors = np.array(vectors, dtype=np.float32)
        
        # Normalize vectors to unit length for cosine similarity
        norms = np.linalg.norm(np_vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0.0, 1.0, norms)
        np_vectors = np_vectors / norms
        
        np_ids = np.array(ids, dtype=np.int64)
        self.index.add_with_ids(np_vectors, np_ids)
        
        for idx, meta in zip(ids, metadata):
            self.id_to_metadata[idx] = meta

    def search(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches the FAISS index with the query vector and returns scores and metadata.
        """
        if self.index.ntotal == 0:
            return []
            
        np_query = np.array([query_vector], dtype=np.float32)
        norm = np.linalg.norm(np_query)
        if norm > 0.0:
            np_query = np_query / norm
            
        distances, indices = self.index.search(np_query, limit)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            # FAISS returns -1 if there are not enough items in the index
            if idx == -1 or idx not in self.id_to_metadata:
                continue
            results.append({
                "id": int(idx),
                "score": float(dist),
                "metadata": self.id_to_metadata[idx]
            })
        return results

    def clear(self):
        """
        Clears the FAISS index.
        """
        self.index = faiss.IndexIDMap(faiss.IndexFlatIP(self.dimension))
        self.id_to_metadata = {}
