import nltk
import numpy as np
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.cluster.util import cosine_distance
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

def preprocess_text(text):
    """
    Clean and preprocess the input text
    """
    # Remove extra whitespace and convert to lowercase
    text = ' '.join(text.split())
    
    # Handle potential encoding issues
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    return text

def sentence_similarity_cosine(sent1, sent2, stopwords=None):
    """
    Calculate cosine similarity between two sentences
    """
    if stopwords is None:
        stopwords = []
    
    # Convert sentences to lowercase and tokenize
    sent1 = [word.lower() for word in word_tokenize(sent1)]
    sent2 = [word.lower() for word in word_tokenize(sent2)]
    
    # Remove stopwords
    sent1 = [word for word in sent1 if word not in stopwords]
    sent2 = [word for word in sent2 if word not in stopwords]
    
    # If either sentence is empty after preprocessing, return 0 similarity
    if len(sent1) == 0 or len(sent2) == 0:
        return 0.0
    
    # Create a set of all unique words in both sentences
    all_words = list(set(sent1 + sent2))
    
    # Create word frequency vectors
    vector1 = [0] * len(all_words)
    vector2 = [0] * len(all_words)
    
    # Fill the vectors with word frequencies
    for word in sent1:
        vector1[all_words.index(word)] += 1
    
    for word in sent2:
        vector2[all_words.index(word)] += 1
    
    # Calculate cosine distance and convert to similarity
    return 1 - cosine_distance(vector1, vector2)

def build_similarity_matrix(sentences, stop_words):
    """
    Create similarity matrix between all sentences
    """
    # Create an empty similarity matrix
    similarity_matrix = np.zeros((len(sentences), len(sentences)))
    
    # Calculate similarity for each pair of sentences
    for i in range(len(sentences)):
        for j in range(len(sentences)):
            if i == j:  # Same sentence
                similarity_matrix[i][j] = 1.0
            else:
                similarity_matrix[i][j] = sentence_similarity_cosine(
                    sentences[i], sentences[j], stop_words)
    
    return similarity_matrix

def textrank_summarization(text, num_sentences=3):
    """
    Use TextRank algorithm to extract top sentences
    """
    # Preprocess text
    text = preprocess_text(text)
    
    # Split into sentences
    sentences = sent_tokenize(text)
    
    # Handle case where text has fewer sentences than requested
    if len(sentences) <= num_sentences:
        return " ".join(sentences)
    
    # Get stopwords
    stop_words = set(stopwords.words('english'))
    
    # Create similarity matrix
    sentence_similarity_matrix = build_similarity_matrix(sentences, stop_words)
    
    # Apply PageRank algorithm
    nx_graph = nx.from_numpy_array(sentence_similarity_matrix)
    scores = nx.pagerank(nx_graph)
    
    # Sort sentences by score
    ranked_sentences = sorted(((scores[i], sentence) for i, sentence in enumerate(sentences)), 
                             reverse=True)
    
    # Get top sentences while preserving the original order
    top_sentence_indices = sorted([sentences.index(ranked_sentences[i][1]) 
                                  for i in range(min(num_sentences, len(ranked_sentences)))])
    summary = [sentences[i] for i in top_sentence_indices]
    
    return " ".join(summary)

def tfidf_summarization(text, num_sentences=3):
    """
    Use TF-IDF to extract top sentences
    """
    # Preprocess text
    text = preprocess_text(text)
    
    # Split into sentences
    sentences = sent_tokenize(text)
    
    # Handle case where text has fewer sentences than requested
    if len(sentences) <= num_sentences:
        return " ".join(sentences)
    
    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words='english')
    
    # Generate TF-IDF matrix
    tfidf_matrix = vectorizer.fit_transform(sentences)
    
    # Calculate sentence scores based on TF-IDF values
    sentence_scores = []
    for i in range(len(sentences)):
        score = np.sum(tfidf_matrix[i].toarray())
        sentence_scores.append((score, i))
    
    # Sort sentences by score
    ranked_sentences = sorted(sentence_scores, reverse=True)
    
    # Get top sentences while preserving the original order
    top_sentence_indices = sorted([ranked_sentences[i][1] 
                                  for i in range(min(num_sentences, len(ranked_sentences)))])
    summary = [sentences[i] for i in top_sentence_indices]
    
    return " ".join(summary)

def extractive_summarize(text, num_sentences=3, method='textrank'):
    """
    Main function to create an extractive summary of text
    
    Parameters:
    text (str): The input text to summarize
    num_sentences (int): Number of sentences in the summary
    method (str): Summarization method ('textrank' or 'tfidf')
    
    Returns:
    str: The extractive summary
    """
    if not text or text.isspace():
        return "No text to summarize."
    
    try:
        if method.lower() == 'tfidf':
            return tfidf_summarization(text, num_sentences)
        else:  # Default to TextRank
            return textrank_summarization(text, num_sentences)
    except Exception as e:
        print(f"Error during summarization: {e}")
        return f"Summarization error: {e}"

# Example usage
if _name_ == "_main_":
    sample_text = """
    Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language, in particular how to program computers to process and analyze large amounts of natural language data. The goal is a computer capable of "understanding" the contents of documents, including the contextual nuances of the language within them. The technology can then accurately extract information and insights contained in the documents as well as categorize and organize the documents themselves.
    
    Challenges in natural language processing frequently involve speech recognition, natural language understanding, and natural language generation. The process of natural language processing has several steps including lexical analysis, parsing, semantic analysis, discourse integration, and pragmatic analysis. Each step has its own challenges and approaches.
    
    Modern NLP approaches are based on machine learning, especially statistical machine learning. Many different classes of machine-learning algorithms have been applied to natural-language-processing tasks. These algorithms take as input a large set of "features" that are generated from the input data.
    
    Some of the earliest-used machine learning algorithms, such as decision trees, produced systems of hard if-then rules similar to existing hand-written rules. However, part-of-speech tagging introduced the use of hidden Markov models to natural language processing, and increasingly, research has focused on statistical models, which make soft, probabilistic decisions based on attaching real-valued weights to the features making up the input data.
    """
    
    summary = extractive_summarize(sample_text, num_sentences=3)
    print(f"Summary:\n{summary}")
