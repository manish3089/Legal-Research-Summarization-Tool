"""
rag_engine.py — Legal RAG Engine (Retrieval-Augmented Generation)
Version: 3.1 | Compatible with app.py integration
"""

import os
import json
import logging
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from collections import Counter
import re

# ----------------- Logging -----------------
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


class LegalRAG:
    """
    Enhanced RAG engine with hybrid search, reranking, and legal-specific improvements.
    """

    def __init__(self):
        # Use smaller model that works on limited memory systems
        self.embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        
        # Reranker for improved relevance
        try:
            self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            self.use_reranker = True
            logger.info("✅ Reranker loaded successfully")
        except Exception as e:
            logger.warning(f"⚠️ Reranker not available: {e}")
            self.use_reranker = False
        
        # Generation model - use base model for better accuracy
        self.model_name = "google/flan-t5-base"  # 250MB - better accuracy
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
            logger.info("✅ Generation model (flan-t5-base) loaded successfully")
        except Exception as e:
            logger.warning(f"⚠️ Could not load generation model: {e}")
            self.tokenizer = None
            self.model = None

        self.vector_store_path = "vector_store/legal_faiss.index"
        self.metadata_path = "vector_store/legal_metadata.json"

        self.dimension = self.embedder.get_sentence_embedding_dimension()
        # Use IndexHNSWFlat for faster search on larger datasets
        self.index = faiss.IndexHNSWFlat(self.dimension, 32)
        self.documents = []
        
        # BM25 data for hybrid search
        self.bm25_index = []

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
        Adds a document into FAISS index and builds BM25 index.
        Args:
            text (str): Raw document text.
            filename (str, optional): Original filename for tracking.
        """
        try:
            if not text.strip():
                logger.warning("⚠️ Skipped empty text.")
                return False

            # Enhanced chunking: Split on paragraphs and long sentences
            chunks = []
            paragraphs = text.split("\n")
            
            for para in paragraphs:
                para = para.strip()
                if len(para) > 100:  # Longer paragraphs
                    # Split long paragraphs into smaller chunks (500-800 chars)
                    words = para.split()
                    current_chunk = []
                    current_len = 0
                    
                    for word in words:
                        current_chunk.append(word)
                        current_len += len(word) + 1
                        
                        if current_len >= 600:  # Target ~600 chars per chunk
                            chunk_text = ' '.join(current_chunk)
                            if len(chunk_text) > 30:
                                chunks.append(chunk_text)
                            current_chunk = []
                            current_len = 0
                    
                    if current_chunk:
                        chunk_text = ' '.join(current_chunk)
                        if len(chunk_text) > 30:
                            chunks.append(chunk_text)
                            
                elif len(para) > 30:  # Short but valid paragraphs
                    chunks.append(para)
            
            if not chunks:
                chunks = [text]

            # Generate semantic embeddings
            embeddings = self.embedder.encode(chunks, convert_to_numpy=True, show_progress_bar=False)
            self.index.add(np.array(embeddings).astype("float32"))

            # Build BM25 index
            for chunk in chunks:
                tokens = self._tokenize(chunk)
                self.bm25_index.append(tokens)
                
                # Add metadata
                self.documents.append({
                    "filename": filename or "unknown_document",
                    "content": chunk
                })

            self._save_index()
            logger.info(f"✅ Added document '{filename or 'unknown'}' with {len(chunks)} chunks to RAG index.")
            return True

        except Exception as e:
            logger.error(f"Error adding document to RAG index: {e}")
            return False

    # ============================================================
    #                      BM25 Helper Functions
    # ============================================================
    
    def _tokenize(self, text):
        """Simple tokenization for BM25."""
        # Legal-aware tokenization: preserve case references, sections
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens
    
    def _bm25_score(self, query_tokens, doc_tokens, k1=1.5, b=0.75):
        """Calculate BM25 score between query and document."""
        if not self.bm25_index:
            return 0.0
        
        # Document frequency and average length
        doc_freq = Counter(doc_tokens)
        doc_len = len(doc_tokens)
        
        if doc_len == 0:
            return 0.0
        
        # Calculate average document length
        avg_doc_len = np.mean([len(d) for d in self.bm25_index]) if self.bm25_index else doc_len
        
        score = 0.0
        N = len(self.bm25_index)
        
        for term in query_tokens:
            if term not in doc_freq:
                continue
            
            # Term frequency in document
            tf = doc_freq[term]
            
            # Document frequency (how many docs contain this term)
            df = sum(1 for doc in self.bm25_index if term in doc)
            
            # IDF calculation
            idf = np.log((N - df + 0.5) / (df + 0.5) + 1.0)
            
            # BM25 formula
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * (doc_len / avg_doc_len))
            score += idf * (numerator / denominator)
        
        return score

    # ============================================================
    #                   Hybrid Search with Reranking
    # ============================================================

    def search(self, query, top_k=3, hybrid_weight=0.7):
        """
        Hybrid search combining semantic (FAISS) and lexical (BM25) retrieval.
        
        Parameters:
            query: Search query
            top_k: Number of results to return
            hybrid_weight: Weight for semantic search (0-1), BM25 gets (1-hybrid_weight)
        
        Returns:
            List of matched text segments with scores
        """
        try:
            if len(self.documents) == 0:
                logger.warning("⚠️ No documents in index to search.")
                return []

            # Semantic search with FAISS
            query_vector = self.embedder.encode([query], convert_to_numpy=True)
            # Retrieve more candidates for reranking
            candidate_k = min(top_k * 3, len(self.documents))
            distances, indices = self.index.search(np.array(query_vector).astype("float32"), candidate_k)

            # Normalize semantic scores (L2 distance -> similarity)
            max_dist = distances[0].max() if distances[0].max() > 0 else 1.0
            semantic_scores = 1.0 - (distances[0] / max_dist)
            
            # BM25 lexical search
            query_tokens = self._tokenize(query)
            bm25_scores = []
            
            for idx in indices[0]:
                if 0 <= idx < len(self.bm25_index):
                    bm25_score = self._bm25_score(query_tokens, self.bm25_index[idx])
                    bm25_scores.append(bm25_score)
                else:
                    bm25_scores.append(0.0)
            
            # Normalize BM25 scores
            bm25_scores = np.array(bm25_scores)
            if bm25_scores.max() > 0:
                bm25_scores = bm25_scores / bm25_scores.max()
            
            # Hybrid scoring
            hybrid_scores = hybrid_weight * semantic_scores + (1 - hybrid_weight) * bm25_scores
            
            # Collect candidates
            candidates = []
            for idx, score in zip(indices[0], hybrid_scores):
                if 0 <= idx < len(self.documents):
                    candidates.append({
                        "content": self.documents[idx]["content"],
                        "filename": self.documents[idx]["filename"],
                        "score": float(score),
                        "idx": idx
                    })
            
            # Sort by hybrid score
            candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
            
            # Reranking with cross-encoder
            if self.use_reranker and len(candidates) > top_k:
                try:
                    pairs = [[query, c["content"]] for c in candidates[:min(10, len(candidates))]]
                    rerank_scores = self.reranker.predict(pairs)
                    
                    # Update scores with reranker
                    for i, score in enumerate(rerank_scores):
                        if i < len(candidates):
                            candidates[i]["score"] = float(score)
                    
                    # Re-sort after reranking
                    candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
                    logger.info("✅ Applied reranking")
                except Exception as e:
                    logger.warning(f"⚠️ Reranking failed: {e}")
            
            # Return top_k results
            results = candidates[:top_k]
            
            # Remove idx field from results
            for r in results:
                r.pop('idx', None)
            
            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    # ============================================================
    #                      Answer Generation
    # ============================================================

    def generate_answer(self, query, context_docs):
        """
        Generate answer using flan-t5-small with optimized prompting.
        """
        try:
            if not context_docs:
                return "No relevant information found in the indexed legal documents. Please upload relevant documents first."

            # Build clean context (limit to avoid token overflow)
            context_parts = []
            for i, doc in enumerate(context_docs, 1):
                # Truncate very long chunks
                content = doc['content'][:400] if len(doc['content']) > 400 else doc['content']
                context_parts.append(f"Source {i}: {content}")
            
            context_text = "\n\n".join(context_parts)
            
            # Simple, direct prompt for small model - FLAN-T5 works best with task-style prompts
            prompt = f"""Answer this question based on the legal context provided.

Context:
{context_text}

Question: {query}

Answer:"""

            # Tokenize with shorter limit for small model
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=800, truncation=True)
            
            # Generate with optimized parameters for flan-t5-small
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=150,  # Shorter for small model
                min_length=20,
                num_beams=4,  # More beams for better quality
                length_penalty=0.8,  # Favor slightly shorter answers
                no_repeat_ngram_size=3,
                early_stopping=True,
                do_sample=False,  # Deterministic for consistency
                temperature=1.0
            )
            answer = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Clean up the answer
            answer = answer.strip()
            
            # If answer is too short or just echoes context, provide a structured response
            if len(answer) < 15 or answer.lower().startswith("source"):
                # Fallback: Create structured answer from context
                answer = self._create_structured_answer(query, context_docs)
            
            return answer if answer else "Unable to generate a specific answer from the available information."
            
        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return "An error occurred while generating an answer. Please try rephrasing your question."
    
    def _create_structured_answer(self, query, context_docs):
        """
        Create a structured answer when model generation is poor.
        """
        answer_parts = []
        
        # Extract key information from context
        for i, doc in enumerate(context_docs, 1):
            content = doc['content'].strip()
            filename = doc['filename']
            
            # Take first 200 chars as relevant excerpt
            excerpt = content[:200] + "..." if len(content) > 200 else content
            answer_parts.append(f"[Source {i} - {filename}]: {excerpt}")
        
        # Add interpretation based on query keywords
        intro = "Based on the legal documents:"
        
        if "matter" in query.lower() or "case" in query.lower():
            intro = "The case matter involves:"
        elif "issue" in query.lower() or "question" in query.lower():
            intro = "The legal issues discussed include:"
        elif "held" in query.lower() or "decision" in query.lower():
            intro = "The court's holding:"
        elif "fact" in query.lower():
            intro = "Key facts from the documents:"
        
        return f"{intro}\n\n" + "\n\n".join(answer_parts)
