"""
evaluation_metrics.py - Quality metrics for legal summarization
Provides ROUGE scores, coherence metrics, and factual consistency checks
"""

import numpy as np
from rouge_score import rouge_scorer
import spacy
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Load models
nlp = spacy.load('en_core_web_sm')
embedder = None  # Lazy load


def get_embedder():
    """Lazy load sentence transformer for efficiency."""
    global embedder
    if embedder is None:
        embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return embedder


class SummarizationEvaluator:
    """
    Comprehensive evaluation metrics for legal document summarization.
    """
    
    def __init__(self):
        self.rouge_scorer = rouge_scorer.RougeScorer(
            ['rouge1', 'rouge2', 'rougeL'], 
            use_stemmer=True
        )
    
    def calculate_rouge_scores(self, reference, hypothesis):
        """
        Calculate ROUGE-1, ROUGE-2, and ROUGE-L scores.
        
        Args:
            reference (str): Reference/gold standard summary
            hypothesis (str): Generated summary to evaluate
            
        Returns:
            dict: ROUGE scores with precision, recall, F1
        """
        try:
            scores = self.rouge_scorer.score(reference, hypothesis)
            
            results = {}
            for metric, score in scores.items():
                results[metric] = {
                    'precision': round(score.precision, 4),
                    'recall': round(score.recall, 4),
                    'f1': round(score.fmeasure, 4)
                }
            
            # Average F1 score
            avg_f1 = np.mean([results[m]['f1'] for m in results])
            results['average_f1'] = round(avg_f1, 4)
            
            return results
            
        except Exception as e:
            logger.error(f"ROUGE calculation error: {e}")
            return {'error': str(e)}
    
    def calculate_semantic_similarity(self, reference, hypothesis):
        """
        Calculate semantic similarity between reference and hypothesis using embeddings.
        
        Args:
            reference (str): Reference text
            hypothesis (str): Generated text
            
        Returns:
            float: Cosine similarity score (0-1)
        """
        try:
            embedder = get_embedder()
            ref_emb = embedder.encode([reference])
            hyp_emb = embedder.encode([hypothesis])
            
            similarity = cosine_similarity(ref_emb, hyp_emb)[0][0]
            return round(float(similarity), 4)
            
        except Exception as e:
            logger.error(f"Semantic similarity error: {e}")
            return 0.0
    
    def calculate_coherence_score(self, text):
        """
        Calculate coherence by measuring sentence-to-sentence similarity.
        
        Args:
            text (str): Text to evaluate
            
        Returns:
            float: Average coherence score (0-1)
        """
        try:
            doc = nlp(text)
            sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.strip()) > 10]
            
            if len(sentences) < 2:
                return 1.0  # Single sentence is perfectly coherent
            
            embedder = get_embedder()
            embeddings = embedder.encode(sentences)
            
            # Calculate average similarity between adjacent sentences
            coherence_scores = []
            for i in range(len(embeddings) - 1):
                sim = cosine_similarity([embeddings[i]], [embeddings[i+1]])[0][0]
                coherence_scores.append(sim)
            
            avg_coherence = np.mean(coherence_scores)
            return round(float(avg_coherence), 4)
            
        except Exception as e:
            logger.error(f"Coherence calculation error: {e}")
            return 0.0
    
    def calculate_compression_ratio(self, original_text, summary):
        """
        Calculate compression ratio of summary vs original.
        
        Args:
            original_text (str): Original document
            summary (str): Generated summary
            
        Returns:
            dict: Compression statistics
        """
        orig_words = len(original_text.split())
        summ_words = len(summary.split())
        
        compression = summ_words / orig_words if orig_words > 0 else 0
        
        return {
            'original_words': orig_words,
            'summary_words': summ_words,
            'compression_ratio': round(compression, 4),
            'compression_percentage': round(compression * 100, 2)
        }
    
    def detect_legal_entity_coverage(self, original_text, summary):
        """
        Check how well the summary preserves important legal entities.
        
        Args:
            original_text (str): Original document
            summary (str): Generated summary
            
        Returns:
            dict: Entity preservation metrics
        """
        try:
            orig_doc = nlp(original_text)
            summ_doc = nlp(summary)
            
            # Extract key entity types
            key_labels = ['PERSON', 'ORG', 'DATE', 'GPE', 'LAW', 'CARDINAL']
            
            orig_entities = set([
                ent.text.lower() 
                for ent in orig_doc.ents 
                if ent.label_ in key_labels
            ])
            
            summ_entities = set([
                ent.text.lower() 
                for ent in summ_doc.ents 
                if ent.label_ in key_labels
            ])
            
            if not orig_entities:
                return {'entity_preservation': 1.0, 'entities_preserved': 0, 'entities_total': 0}
            
            preserved = len(orig_entities.intersection(summ_entities))
            total = len(orig_entities)
            preservation_rate = preserved / total if total > 0 else 0
            
            return {
                'entity_preservation': round(preservation_rate, 4),
                'entities_preserved': preserved,
                'entities_total': total,
                'preserved_entities': list(orig_entities.intersection(summ_entities))[:10]
            }
            
        except Exception as e:
            logger.error(f"Entity coverage error: {e}")
            return {'entity_preservation': 0.0}
    
    def calculate_legal_keyword_coverage(self, original_text, summary):
        """
        Check preservation of critical legal keywords.
        
        Args:
            original_text (str): Original document
            summary (str): Generated summary
            
        Returns:
            dict: Keyword coverage metrics
        """
        legal_keywords = [
            'held', 'judgment', 'court', 'section', 'article', 'appellant',
            'respondent', 'petition', 'evidence', 'witness', 'ruling', 'appeal',
            'conviction', 'acquittal', 'sentence', 'verdict', 'decided'
        ]
        
        orig_lower = original_text.lower()
        summ_lower = summary.lower()
        
        orig_keywords = [kw for kw in legal_keywords if kw in orig_lower]
        summ_keywords = [kw for kw in legal_keywords if kw in summ_lower]
        
        preserved = len(set(orig_keywords).intersection(set(summ_keywords)))
        total = len(set(orig_keywords))
        
        coverage = preserved / total if total > 0 else 0
        
        return {
            'keyword_coverage': round(coverage, 4),
            'keywords_preserved': preserved,
            'keywords_total': total
        }
    
    def evaluate_summary(self, original_text, summary, reference_summary=None):
        """
        Comprehensive evaluation of a generated summary.
        
        Args:
            original_text (str): Original document
            summary (str): Generated summary
            reference_summary (str, optional): Gold standard summary for ROUGE
            
        Returns:
            dict: Complete evaluation metrics
        """
        logger.info("📊 Evaluating summary quality...")
        
        results = {
            'compression': self.calculate_compression_ratio(original_text, summary),
            'coherence': self.calculate_coherence_score(summary),
            'entity_coverage': self.detect_legal_entity_coverage(original_text, summary),
            'keyword_coverage': self.calculate_legal_keyword_coverage(original_text, summary)
        }
        
        if reference_summary:
            results['rouge_scores'] = self.calculate_rouge_scores(reference_summary, summary)
            results['semantic_similarity'] = self.calculate_semantic_similarity(reference_summary, summary)
        
        # Calculate overall quality score (0-100)
        quality_components = [
            results['coherence'] * 30,  # 30% weight
            results['entity_coverage']['entity_preservation'] * 25,  # 25% weight
            results['keyword_coverage']['keyword_coverage'] * 20,  # 20% weight
        ]
        
        if reference_summary:
            quality_components.append(results['rouge_scores']['average_f1'] * 25)  # 25% weight
        
        overall_quality = sum(quality_components)
        results['overall_quality_score'] = round(overall_quality, 2)
        
        logger.info(f"✅ Overall Quality Score: {results['overall_quality_score']}/100")
        
        return results


def quick_evaluate(original_text, summary):
    """
    Quick evaluation without reference summary.
    
    Args:
        original_text (str): Original document
        summary (str): Generated summary
        
    Returns:
        dict: Basic evaluation metrics
    """
    evaluator = SummarizationEvaluator()
    return evaluator.evaluate_summary(original_text, summary)
