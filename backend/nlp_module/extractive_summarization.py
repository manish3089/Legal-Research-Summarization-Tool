import spacy
import numpy as np
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
import re

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def split_sentences(text):
    """Uses SpaCy to split text into sentences with legal document handling."""
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    
    word_count = len(text.split())
    
    # Legal documents: expect 1 sentence per 40-50 words (longer sentences)
    expected_sentences = max(5, word_count // 45)
    
    if len(sentences) < expected_sentences:
        import re
        logger.warning(f"SpaCy found {len(sentences)} sentences from {word_count} words, using legal doc fallback")
        
        # Legal document patterns
        patterns = [
            r'(?<=[.!?])\s+(?=[A-Z(])',  # Period + space + capital/opening paren
            r'(?<=\.)\s*(?=\(\d+\))',     # Before numbered paragraphs like "(1)"
            r'(?<=\.)\s*(?=[A-Z][A-Z])',  # Before all-caps words like "IT", "THIS"
        ]
        
        combined_pattern = '|'.join(patterns)
        sentences = re.split(combined_pattern, text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 5]
        
        logger.info(f"Legal doc fallback created {len(sentences)} sentences")
    
    logger.info(f"Final split: {len(sentences)} sentences")
    return sentences



def calculate_extraction_ratio(total_sentences, compression_ratio=0.5):
    """
    Calculate number of sentences to extract based on compression ratio.
    
    Parameters:
        total_sentences (int): Total number of sentences in document.
        compression_ratio (float): Ratio of sentences to extract (0.4-0.7 recommended).
        
    Returns:
        int: Number of sentences to extract.
    """
    extracted_count = max(3, int(total_sentences * compression_ratio))
    return min(extracted_count, total_sentences)


def calculate_legal_importance_scores(sentences):
    """
    Calculate legal importance scores for sentences based on legal markers and patterns.
    Returns normalized scores between 0 and 1.
    """
    # Enhanced legal markers with weights
    critical_markers = {
        'held that': 0.35, 'Court held': 0.35, 'ruled that': 0.35,
        'judgment': 0.30, 'concluded': 0.30, 'determined': 0.30,
        'finding': 0.25, 'established': 0.25, 'decided': 0.25,
        'Section': 0.20, 'Article': 0.20, 'Clause': 0.20,
        'appellant': 0.15, 'respondent': 0.15, 'petitioner': 0.15,
        'evidence': 0.15, 'testimony': 0.15, 'witness': 0.15,
        'therefore': 0.10, 'consequently': 0.10, 'accordingly': 0.10
    }
    
    scores = np.zeros(len(sentences))
    for i, sent in enumerate(sentences):
        sent_lower = sent.lower()
        for marker, weight in critical_markers.items():
            if marker.lower() in sent_lower:
                scores[i] += weight
        
        # Boost for citations (e.g., "[2023] 1 SCC 123")
        if re.search(r'\[\d{4}\]\s*\d+\s+[A-Z]+\s+\d+', sent):
            scores[i] += 0.20
        
        # Boost for case names (e.g., "X v. Y")
        if re.search(r'\b[A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+', sent):
            scores[i] += 0.15
    
    # Normalize
    if scores.max() > 0:
        scores = scores / scores.max()
    
    return scores


def calculate_position_scores(num_sentences):
    """
    Calculate position-based importance scores.
    Legal documents: beginning and end are most important.
    """
    scores = np.zeros(num_sentences)
    
    # First 15% get high score
    first_section = max(1, int(num_sentences * 0.15))
    scores[:first_section] = 0.25
    
    # Last 10% get medium-high score
    last_section = max(1, int(num_sentences * 0.10))
    scores[-last_section:] = 0.20
    
    # Middle section gets lower score (gradual decay)
    middle_start = first_section
    middle_end = num_sentences - last_section
    if middle_end > middle_start:
        scores[middle_start:middle_end] = np.linspace(0.15, 0.10, middle_end - middle_start)
    
    return scores


def calculate_sentence_coherence(sentences, sim_matrix):
    """
    Calculate coherence score based on similarity to surrounding sentences.
    """
    coherence_scores = np.zeros(len(sentences))
    
    for i in range(len(sentences)):
        # Average similarity to adjacent sentences
        adjacent_sims = []
        if i > 0:
            adjacent_sims.append(sim_matrix[i, i-1])
        if i < len(sentences) - 1:
            adjacent_sims.append(sim_matrix[i, i+1])
        
        if adjacent_sims:
            coherence_scores[i] = np.mean(adjacent_sims)
    
    # Normalize
    if coherence_scores.max() > 0:
        coherence_scores = coherence_scores / coherence_scores.max()
    
    return coherence_scores


def hybrid_summarize(text, top_n=None, compression_ratio=0.5, textrank_weight=0.4, tfidf_weight=0.3):
    """
    Enhanced hybrid summarization with legal-specific features.
    
    Parameters:
        text (str): The input text.
        top_n (int): Number of top sentences (if None, uses compression_ratio).
        compression_ratio (float): Percentage of sentences to extract (0.4-0.7).
        textrank_weight (float): Weight for TextRank (default 0.4).
        tfidf_weight (float): Weight for TF-IDF (default 0.3).
        
    Returns:
        str: Extractive summary.
    """
    # Weights: textrank(0.4) + tfidf(0.3) + legal(0.2) + position(0.05) + coherence(0.05) = 1.0
    legal_weight = 0.2
    position_weight = 0.05
    coherence_weight = 0.05
    
    total_weight = textrank_weight + tfidf_weight + legal_weight + position_weight + coherence_weight
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(f"Weights must sum to 1.0 (current: {total_weight})")
        
    sentences = split_sentences(text)
    
    # Calculate top_n based on compression ratio if not provided
    if top_n is None:
        top_n = calculate_extraction_ratio(len(sentences), compression_ratio)
    
    if len(sentences) < top_n:
        return " ".join(sentences)
    
    # TF-IDF vectorization with legal domain terms
    vectorizer = TfidfVectorizer(
        stop_words='english',
        ngram_range=(1, 2),  # Include bigrams for legal phrases
        max_features=500
    )
    X = vectorizer.fit_transform(sentences)
    
    # TextRank scores
    sim_matrix = cosine_similarity(X)
    np.fill_diagonal(sim_matrix, 0)
    nx_graph = nx.from_numpy_array(sim_matrix)
    textrank_scores = np.array(list(nx.pagerank(nx_graph, alpha=0.85).values()))
    
    # Normalize TextRank
    if textrank_scores.max() != textrank_scores.min():
        textrank_scores = (textrank_scores - textrank_scores.min()) / (textrank_scores.max() - textrank_scores.min())
    
    # TF-IDF scores
    tfidf_scores = X.sum(axis=1).A1
    if tfidf_scores.max() != tfidf_scores.min():
        tfidf_scores = (tfidf_scores - tfidf_scores.min()) / (tfidf_scores.max() - tfidf_scores.min())
    
    # Legal importance scores
    legal_scores = calculate_legal_importance_scores(sentences)
    
    # Position scores
    position_scores = calculate_position_scores(len(sentences))
    
    # Coherence scores
    coherence_scores = calculate_sentence_coherence(sentences, sim_matrix)
    
    # Combined scoring
    combined_scores = (
        textrank_weight * textrank_scores +
        tfidf_weight * tfidf_scores +
        legal_weight * legal_scores +
        position_weight * position_scores +
        coherence_weight * coherence_scores
    )
    
    # Select top sentences
    ranked_indices = np.argsort(combined_scores)[::-1][:top_n]
    selected = [sentences[i] for i in sorted(ranked_indices)]
    
    # Ensure proper sentence separation
    return ". ".join([s.rstrip('.') for s in selected]) + "."


def summarize(text, method='hybrid', top_n=None, compression_ratio=0.5, textrank_weight=0.4, tfidf_weight=0.3):
    """
    Unified summarization function supporting multiple methods.
    
    Parameters:
        text (str): The input text.
        method (str): One of 'hybrid', 'textrank', or 'tfidf'.
        top_n (int): Number of sentences (if None, uses compression_ratio).
        compression_ratio (float): Percentage of sentences to extract (0.4-0.7).
        textrank_weight (float): Weight for TextRank in hybrid method (default 0.4).
        tfidf_weight (float): Weight for TF-IDF in hybrid method (default 0.3).
        
    Returns:
        str: Extractive summary.
    """
    if method == 'hybrid':
        return hybrid_summarize(text, top_n, compression_ratio, textrank_weight, tfidf_weight)
    elif method == 'textrank':
        return textrank_summarize(text, top_n, compression_ratio)
    elif method == 'tfidf':
        return tfidf_summarize(text, top_n, compression_ratio)
    else:
        raise ValueError("Method must be 'hybrid', 'textrank', or 'tfidf'")


def textrank_summarize(text, top_n=None, compression_ratio=0.5):
    """Summarizes text using TextRank."""
    sentences = split_sentences(text)
    
    if top_n is None:
        top_n = calculate_extraction_ratio(len(sentences), compression_ratio)
    
    if len(sentences) < top_n:
        return " ".join(sentences)

    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(sentences)
    sim_matrix = cosine_similarity(X)
    np.fill_diagonal(sim_matrix, 0)
    nx_graph = nx.from_numpy_array(sim_matrix)
    scores = nx.pagerank(nx_graph)

    ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
    selected = [s for _, s in ranked_sentences[:top_n]]
    original_indices = [sentences.index(s) for s in selected]
    selected = [selected[i] for i in np.argsort(original_indices)]
    
    return " ".join(selected)


def tfidf_summarize(text, top_n=None, compression_ratio=0.5):
    """Summarizes text based on TF-IDF scores."""
    sentences = split_sentences(text)
    
    if top_n is None:
        top_n = calculate_extraction_ratio(len(sentences), compression_ratio)
    
    if len(sentences) < top_n:
        return " ".join(sentences)

    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(sentences)
    sentence_scores = X.sum(axis=1).A1

    ranked_indices = np.argsort(sentence_scores)[::-1][:top_n]
    selected = [sentences[i] for i in sorted(ranked_indices)]

    return " ".join(selected)
