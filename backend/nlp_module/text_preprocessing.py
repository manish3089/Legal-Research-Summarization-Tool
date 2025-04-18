import spacy
import nltk
from nltk.corpus import stopwords
import re

# Download necessary NLTK resources
def download_nltk_resources():
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        nltk.download('stopwords')

download_nltk_resources()

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")
stop_words = set(stopwords.words('english'))

# preprocess_text function (unchanged)
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
        
        for start, end, text in entity_spans:
            if start <= i < end:
                is_in_entity = True
                entity_text = text
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
    """
    Extracts named entities from the text including custom pattern for case numbers.

    Parameters:
    text (str): The input text from which to extract entities.

    Returns:
    dict: A dictionary containing lists of extracted entities.
    """
    if not text:
        raise ValueError("Input text cannot be empty.")

    doc = nlp(text)
    entities = {
        "PERSON": [],
        "ORG": [],
        "DATE": [],
        "GPE": [],
        "CASE_ID": []
    }

    # Custom logic to handle titles like "Judge"
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # Include titles like "Judge" or "Justice"
            if ent.start > 0 and doc[ent.start - 1].text.lower() in ["judge", "justice"]:
                full_name = f"{doc[ent.start - 1].text} {ent.text}"
                entities["PERSON"].append(full_name)
            else:
                entities["PERSON"].append(ent.text)
        elif ent.label_ == "ORG":
            # Remove "the" from organization names
            org_name = ent.text.replace("the ", "")
            entities["ORG"].append(org_name)
        elif ent.label_ in entities:
            entities[ent.label_].append(ent.text)

    # Custom regex for case numbers
    case_ids = re.findall(r'(Case\s*No\.?\s*\d+/\d+)', text)
    entities["CASE_ID"].extend(case_ids)

    # Post-processing to capture missed organizations
    org_patterns = [
        r'High\s*Court\s*of\s*[A-Za-z]+',  # Matches "High Court of Karnataka"
        r'CID\s*[A-Za-z]+'  # Matches "CID Bengaluru"
    ]
    for pattern in org_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            entities["ORG"].append(match)

    # Remove redundant ORG entities (e.g., keep "High Court of Karnataka" over "High Court")
    filtered_orgs = []
    for org in entities["ORG"]:
        # Only add org if it's not a substring of another longer org
        if not any(org != other_org and org in other_org for other_org in entities["ORG"]):
            filtered_orgs.append(org)
    entities["ORG"] = filtered_orgs

    # Remove duplicates while preserving order
    for key in entities:
        entities[key] = list(dict.fromkeys(entities[key]))

    return entities

