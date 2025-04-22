import re
import nltk
import spacy
import numpy as np
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import stopwords
from transformers import pipeline

# Download NLTK stopwords
def download_nltk_resources():
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

download_nltk_resources()

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words('english'))

# ----------- Preprocessing and Entity Extraction -----------

def preprocess_text(text):
    if not text:
        raise ValueError("Input text cannot be empty.")
    case_ids = re.findall(r'(Case\s*No\.?\s*\d+/\d+)', text)
    case_ids_lower = [cid.lower() for cid in case_ids]

    doc = nlp(text)
    entity_spans = []
    for ent in doc.ents:
        if ent.label_ in ['DATE', 'CARDINAL', 'ORDINAL']:
            entity_spans.append((ent.start, ent.end, ent.text.lower()))

    lemmas = case_ids_lower.copy()
    i = 0
    while i < len(doc):
        is_in_entity = False
        entity_text = None
        for start, end, ent_text in entity_spans:
            if start <= i < end:
                is_in_entity = True
                entity_text = ent_text
                i = end
                break
        if is_in_entity:
            if entity_text not in lemmas:
                lemmas.append(entity_text)
        else:
            token = doc[i]
            if not any(token.text.lower() in cid for cid in case_ids_lower):
                if token.ent_type_ in ['DATE', 'CARDINAL', 'ORDINAL', 'TIME']:
                    lemmas.append(token.text.lower())
                elif token.is_alpha and token.text.lower() not in stop_words:
                    lemmas.append(token.lemma_.lower())
            i += 1

    preprocessed_text = " ".join(lemmas)
    preprocessed_text = re.sub(r'\s+([.,:;!?])', r'\1', preprocessed_text)
    preprocessed_text = re.sub(r'([.,:;!?])\s+', r'\1 ', preprocessed_text)
    return preprocessed_text.strip()

def extract_entities(text):
    doc = nlp(text)
    entities = {
        "PERSON": [], "ORG": [], "DATE": [], "GPE": [], "CASE_ID": []
    }

    for ent in doc.ents:
        if ent.label_ == "PERSON":
            if ent.start > 0 and doc[ent.start - 1].text.lower() in ["judge", "justice"]:
                full_name = f"{doc[ent.start - 1].text} {ent.text}"
                entities["PERSON"].append(full_name)
            else:
                entities["PERSON"].append(ent.text)
        elif ent.label_ == "ORG":
            org_name = ent.text.replace("the ", "")
            entities["ORG"].append(org_name)
        elif ent.label_ in entities:
            entities[ent.label_].append(ent.text)

    case_ids = re.findall(r'(Case\s*No\.?\s*\d+/\d+)', text)
    entities["CASE_ID"].extend(case_ids)

    org_patterns = [r'High\s*Court\s*of\s*[A-Za-z]+', r'CID\s*[A-Za-z]+']
    for pattern in org_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            entities["ORG"].append(match)

    filtered_orgs = []
    for org in entities["ORG"]:
        if not any(org != other and org in other for other in entities["ORG"]):
            filtered_orgs.append(org)
    entities["ORG"] = filtered_orgs

    for key in entities:
        entities[key] = list(dict.fromkeys(entities[key]))

    return entities

# ----------- Sentence Splitting -----------

def split_sentences(text):
    doc = nlp(text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]

# ----------- Extractive Summarization -----------

def textrank_summarize(text, top_n=3):
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

    original_indices = [sentences.index(s) for s in selected]
    selected = [selected[i] for i in np.argsort(original_indices)]

    return " ".join(selected)

def tfidf_summarize(text, top_n=3):
    sentences = split_sentences(text)
    if len(sentences) < top_n:
        return " ".join(sentences)

    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(sentences)
    scores = X.sum(axis=1).A1

    ranked_indices = np.argsort(scores)[::-1][:top_n]
    selected = [sentences[i] for i in sorted(ranked_indices)]

    return " ".join(selected)

def hybrid_summarize(text, top_n=3, textrank_weight=0.6, tfidf_weight=0.4):
    if textrank_weight + tfidf_weight != 1.0:
        raise ValueError("Weights must sum to 1.0")

    sentences = split_sentences(text)
    if len(sentences) < top_n:
        return " ".join(sentences)

    vectorizer = TfidfVectorizer(stop_words='english')
    X = vectorizer.fit_transform(sentences)

    sim_matrix = cosine_similarity(X)
    np.fill_diagonal(sim_matrix, 0)
    nx_graph = nx.from_numpy_array(sim_matrix)
    textrank_scores = np.array(list(nx.pagerank(nx_graph).values()))
    textrank_scores = (textrank_scores - textrank_scores.min()) / (textrank_scores.ptp() or 1)

    tfidf_scores = X.sum(axis=1).A1
    tfidf_scores = (tfidf_scores - tfidf_scores.min()) / (tfidf_scores.ptp() or 1)

    combined = textrank_weight * textrank_scores + tfidf_weight * tfidf_scores
    ranked_indices = np.argsort(combined)[::-1][:top_n]
    selected = [sentences[i] for i in sorted(ranked_indices)]

    return " ".join(selected)

# ----------- Abstractive Summarization -----------

summarizer_model = pipeline("summarization", model="facebook/bart-large-cnn")

def abstractive_summarize(text, max_length=130, min_length=30):
    if not text.strip():
        return ""
    return summarizer_model(text, max_length=max_length, min_length=min_length, do_sample=False)[0]['summary_text']

# ----------- Main summarization wrapper -----------

def summarize(text, method='hybrid', top_n=3, textrank_weight=0.6, tfidf_weight=0.4):
    if method == 'textrank':
        return textrank_summarize(text, top_n)
    elif method == 'tfidf':
        return tfidf_summarize(text, top_n)
    elif method == 'hybrid':
        return hybrid_summarize(text, top_n, textrank_weight, tfidf_weight)
    elif method == 'abstractive':
        return abstractive_summarize(text)
    else:
        raise ValueError("Unsupported method. Choose from 'textrank', 'tfidf', 'hybrid', or 'abstractive'.")

