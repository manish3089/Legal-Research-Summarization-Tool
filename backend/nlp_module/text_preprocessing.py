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
    """Minimal preprocessing for legal documents."""
    
    # Remove XML-like tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

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

