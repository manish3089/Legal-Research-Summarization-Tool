# This is text_preprocessing.py
import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string
import re
from nltk.data import find

def download_nltk_resources():
    try:
        find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    try:
        find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

download_nltk_resources()

# Load spaCy model
nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    """
    Tokenize, remove stopwords and punctuation, and lemmatize the input text.
    """
    # Step 1: Tokenize
    tokens = word_tokenize(text)

    # Step 2: Remove punctuation, lowercase, and filter stopwords
    filtered = [
        word.lower()
        for word in tokens
        if word.isalnum() and word.lower() not in stop_words
    ]

    # Step 3: Lemmatize using spaCy
    doc = nlp(" ".join(filtered))
    lemmas = [token.lemma_ for token in doc]

    return " ".join(lemmas)


def extract_entities(text):
    """
    Extracts named entities from the text including custom pattern for case numbers.
    """
    doc = nlp(text)
    entities = {
        "PERSON": [],
        "ORG": [],
        "DATE": [],
        "GPE": [],
        "CASE_ID": []
    }

    # Built-in NER
    for ent in doc.ents:
        if ent.label_ in entities:
            entities[ent.label_].append(ent.text)

    # Custom regex for case numbers like "Case No. 123/2023"
    case_ids = re.findall(r'(Case\s*No\.?\s*\d+/\d+)', text)
    entities["CASE_ID"].extend(case_ids)

    return entities
