"""
rag_engine.py — Legal RAG Engine (Retrieval-Augmented Generation)
Version: 3.1 | Compatible with app.py integration
"""

import os
import json
import logging
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ----------------- Logging -----------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


class LegalRAG:
    """
    A lightweight Retrieval-Augmented Generation (RAG) engine for legal document search.
    """

    def __init__(self):
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.model_name = "pszemraj/led-large-book-summary"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

        self.vector_store_path = "vector_store/legal_faiss.index"
        self.metadata_path = "vector_store/legal_metadata.json"

        self.dimension = self.embedder.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []

        # Try loading existing data
        self._load_existing_data()
        logger.info("✅ LegalRAG initialized successfully.")

    # ============================================================
    #                  Internal Utilities
    # ============================================================

    def _load_existing_data(self):
        """Load previous vector index and metadata if available."""
        if os.path.exists(self.vector_store_path) and os.path.exists(self.metadata_path):
            try:
                self.index = faiss.read_index(self.vector_store_path)
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
                logger.info(f"📂 Loaded existing vector store with {len(self.documents)} entries.")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load existing FAISS index: {e}")

    def _save_index(self):
        """Persist index and metadata to disk."""
        os.makedirs(os.path.dirname(self.vector_store_path), exist_ok=True)
        faiss.write_index(self.index, self.vector_store_path)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, indent=2)
        logger.info("💾 RAG index saved successfully.")

    # ============================================================
    #                      Add Documents
    # ============================================================

    def add_document(self, text, filename=None):
        """
        Adds a document into FAISS index for semantic search.
        Args:
            text (str): Raw document text.
            filename (str, optional): Original filename for tracking.
        """
        try:
            if not text.strip():
                logger.warning("⚠️ Skipped empty text.")
                return False

            # Split into paragraphs/sentences
            chunks = [chunk.strip() for chunk in text.split("\n") if len(chunk.strip()) > 30]
            if not chunks:
                chunks = [text]

            # Generate embeddings
            embeddings = self.embedder.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
            self.index.add(np.array(embeddings).astype("float32"))

            # Add metadata
            for chunk in chunks:
                self.documents.append({
                    "filename": filename or "unknown_document",
                    "content": chunk
                })

            self._save_index()
            logger.info(f"✅ Added document '{filename or 'unknown'}' with {len(chunks)} chunks to FAISS index.")
            return True

        except Exception as e:
            logger.error(f"Error adding document to RAG index: {e}")
            return False

    # ============================================================
    #                      Semantic Search
    # ============================================================

    def search(self, query, top_k=3):
        """
        Retrieve top similar documents to a query.
        Returns a list of matched text segments.
        """
        try:
            if len(self.documents) == 0:
                logger.warning("⚠️ No documents in index to search.")
                return []

            query_vector = self.embedder.encode([query], convert_to_numpy=True)
            distances, indices = self.index.search(np.array(query_vector).astype("float32"), top_k)

            results = []
            for idx, score in zip(indices[0], distances[0]):
                if 0 <= idx < len(self.documents):
                    results.append({
                        "content": self.documents[idx]["content"],
                        "filename": self.documents[idx]["filename"],
                        "score": float(score)
                    })
            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    # ============================================================
    #                      Answer Generation
    # ============================================================

    def generate_answer(self, query, context_docs):
        """
        Generate a concise answer using LED summarization model.
        """
        try:
            if not context_docs:
                return "No relevant information found in RAG database."

            context_text = " ".join([doc["content"] for doc in context_docs])
            prompt = f"Question: {query}\nRelevant Information: {context_text}\nAnswer:"

            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=1024, truncation=True)
            outputs = self.model.generate(**inputs, max_new_tokens=150)
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            return answer.strip() or "No answer generated."
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return "An error occurred while generating an answer."
