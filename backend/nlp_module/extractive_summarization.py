import spacy
import numpy as np
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging

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


def hybrid_summarize(text, top_n=None, compression_ratio=0.5, textrank_weight=0.6, tfidf_weight=0.4):
    """
    Summarizes text using a hybrid approach combining TextRank and TF-IDF.
    
    Parameters:
        text (str): The input text.
        top_n (int): Number of top sentences (if None, uses compression_ratio).
        compression_ratio (float): Percentage of sentences to extract (0.4-0.7).
        textrank_weight (float): Weight given to TextRank scores (0.0-1.0).
        tfidf_weight (float): Weight given to TF-IDF scores (0.0-1.0).
        
    Returns:
        str: Extractive summary.
    """
    if textrank_weight + tfidf_weight != 1.0:
        raise ValueError("Weights must sum to 1.0")
        
    sentences = split_sentences(text)

    legal_markers = ['<HD>', '<IS>', 'Section', 'held that', 'Court held']
    boost_scores = np.zeros(len(sentences))
    for i, sent in enumerate(sentences):
        if any(marker in sent for marker in legal_markers):
            boost_scores[i] = 0.2  # 20% boost
    
    # Calculate top_n based on compression ratio if not provided
    if top_n is None:
        top_n = calculate_extraction_ratio(len(sentences), compression_ratio)
    
    if len(sentences) < top_n:
        return " ".join(sentences)

    # Rest of your existing code remains the same
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(sentences)
    
    sim_matrix = cosine_similarity(X)
    np.fill_diagonal(sim_matrix, 0)
    nx_graph = nx.from_numpy_array(sim_matrix)
    textrank_scores = np.array(list(nx.pagerank(nx_graph).values()))
    
    if textrank_scores.max() != textrank_scores.min():
        textrank_scores = (textrank_scores - textrank_scores.min()) / (textrank_scores.max() - textrank_scores.min())
    
    tfidf_scores = X.sum(axis=1).A1
    
    if tfidf_scores.max() != tfidf_scores.min():
        tfidf_scores = (tfidf_scores - tfidf_scores.min()) / (tfidf_scores.max() - tfidf_scores.min())
    
    combined_scores = textrank_weight * textrank_scores + tfidf_weight * tfidf_scores + boost_scores
    ranked_indices = np.argsort(combined_scores)[::-1][:top_n]
    selected = [sentences[i] for i in sorted(ranked_indices)]
    
     # Ensure proper sentence separation
    return ". ".join([s.rstrip('.') for s in selected]) + "."  # Add period separation


def summarize(text, method='hybrid', top_n=None, compression_ratio=0.5, textrank_weight=0.6, tfidf_weight=0.4):
    """
    Unified summarization function supporting multiple methods.
    
    Parameters:
        text (str): The input text.
        method (str): One of 'hybrid', 'textrank', or 'tfidf'.
        top_n (int): Number of sentences (if None, uses compression_ratio).
        compression_ratio (float): Percentage of sentences to extract (0.4-0.7).
        textrank_weight (float): Weight for TextRank in hybrid method.
        tfidf_weight (float): Weight for TF-IDF in hybrid method.
        
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
