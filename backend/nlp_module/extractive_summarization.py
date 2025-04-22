import spacy
import numpy as np
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

def split_sentences(text):
    """Uses SpaCy to split text into sentences."""
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

def hybrid_summarize(text, top_n=3, textrank_weight=0.6, tfidf_weight=0.4):
    """
    Summarizes text using a hybrid approach combining TextRank and TF-IDF.
    
    Parameters:
        text (str): The input text.
        top_n (int): Number of top sentences to include in the summary.
        textrank_weight (float): Weight given to TextRank scores (0.0-1.0).
        tfidf_weight (float): Weight given to TF-IDF scores (0.0-1.0).
        
    Returns:
        str: Extractive summary.
    """
    # Validate weights
    if textrank_weight + tfidf_weight != 1.0:
        raise ValueError("Weights must sum to 1.0")
        
    sentences = split_sentences(text)
    if len(sentences) < top_n:
        return " ".join(sentences)

    # TF-IDF vectorization
    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(sentences)
    
    # TextRank scores
    sim_matrix = cosine_similarity(X)
    np.fill_diagonal(sim_matrix, 0)
    nx_graph = nx.from_numpy_array(sim_matrix)
    textrank_scores = np.array(list(nx.pagerank(nx_graph).values()))
    
    # Normalize TextRank scores to range [0,1]
    if textrank_scores.max() != textrank_scores.min():
        textrank_scores = (textrank_scores - textrank_scores.min()) / (textrank_scores.max() - textrank_scores.min())
    
    # TF-IDF scores (sum of TF-IDF values for each sentence)
    tfidf_scores = X.sum(axis=1).A1  # Flatten to 1D array
    
    # Normalize TF-IDF scores to range [0,1]
    if tfidf_scores.max() != tfidf_scores.min():
        tfidf_scores = (tfidf_scores - tfidf_scores.min()) / (tfidf_scores.max() - tfidf_scores.min())
    
    # Combine scores with weights
    combined_scores = textrank_weight * textrank_scores + tfidf_weight * tfidf_scores
    
    # Get top sentences by combined score
    ranked_indices = np.argsort(combined_scores)[::-1][:top_n]
    
    # Keep sentences in original order
    selected = [sentences[i] for i in sorted(ranked_indices)]
    
    return " ".join(selected)

def summarize(text, method='hybrid', top_n=3, textrank_weight=0.6, tfidf_weight=0.4):
    """
    Unified summarization function supporting multiple methods.
    
    Parameters:
        text (str): The input text.
        method (str): One of 'hybrid', 'textrank', or 'tfidf'.
        top_n (int): Number of top sentences to include in the summary.
        textrank_weight (float): Weight for TextRank in hybrid method.
        tfidf_weight (float): Weight for TF-IDF in hybrid method.
        
    Returns:
        str: Extractive summary.
    """
    if method == 'hybrid':
        return hybrid_summarize(text, top_n, textrank_weight, tfidf_weight)
    elif method == 'textrank':
        return textrank_summarize(text, top_n)
    elif method == 'tfidf':
        return tfidf_summarize(text, top_n)
    else:
        raise ValueError("Method must be 'hybrid', 'textrank', or 'tfidf'")

def textrank_summarize(text, top_n=3):
    """Summarizes text using TextRank (based on sentence similarity)."""
    sentences = split_sentences(text)
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
    
    # Sort by original order
    original_indices = [sentences.index(s) for s in selected]
    selected = [selected[i] for i in np.argsort(original_indices)]
    
    return " ".join(selected)

def tfidf_summarize(text, top_n=3):
    """Summarizes text based on sentence importance via TF-IDF score sum."""
    sentences = split_sentences(text)
    if len(sentences) < top_n:
        return " ".join(sentences)

    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(sentences)
    sentence_scores = X.sum(axis=1).A1  # Flatten to 1D array

    ranked_indices = np.argsort(sentence_scores)[::-1][:top_n]
    selected = [sentences[i] for i in sorted(ranked_indices)]  # Preserve order

    return " ".join(selected)
