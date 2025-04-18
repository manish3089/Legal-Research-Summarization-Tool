import nltk
import heapq
import re

# Download necessary resources
nltk.download('punkt')
nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

def extractive_summarize(text, num_sentences=3):
    # Clean the text
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'👦[0-9]*👦', ' ', text)
    
    # Tokenize into sentences
    sentences = sent_tokenize(text)
    
    # Create a frequency table for words
    stop_words = set(stopwords.words("english"))
    word_frequencies = {}
    for word in word_tokenize(text.lower()):
        if word not in stop_words and word.isalnum():
            word_frequencies[word] = word_frequencies.get(word, 0) + 1

    # Score sentences based on word frequency
    sentence_scores = {}
    for sentence in sentences:
        for word in word_tokenize(sentence.lower()):
            if word in word_frequencies:
                sentence_scores[sentence] = sentence_scores.get(sentence, 0) + word_frequencies[word]

    # Get the top N sentences
    summary_sentences = heapq.nlargest(num_sentences, sentence_scores, key=sentence_scores.get)
    summary = ' '.join(summary_sentences)
    
    return summary

# Example usage
if _name_ == "_main_":
    sample_text = """
    The AI-Powered Forensic Document Summarization System is designed to help forensic experts process large volumes of text.
    It uses natural language processing techniques to extract meaningful summaries from forensic reports and legal documents.
    The tool is efficient, scalable, and can be integrated into digital forensics workflows.
    """
    summary = extractive_summarize(sample_text, num_sentences=2)
    print("Summary:\n", summary)
