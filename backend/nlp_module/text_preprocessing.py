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
    Enhanced entity extraction with comprehensive legal patterns.

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
        "CASE_ID": [],
        "CITATIONS": [],
        "STATUTES": []
    }

    # Enhanced title detection for legal professionals
    legal_titles = ["judge", "justice", "magistrate", "advocate", "counsel", 
                    "attorney", "solicitor", "barrister", "commissioner"]
    
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # Include titles
            if ent.start > 0 and doc[ent.start - 1].text.lower() in legal_titles:
                full_name = f"{doc[ent.start - 1].text} {ent.text}"
                entities["PERSON"].append(full_name)
            else:
                entities["PERSON"].append(ent.text)
        elif ent.label_ == "ORG":
            # Clean organization names
            org_name = re.sub(r'^the\s+', '', ent.text, flags=re.IGNORECASE)
            entities["ORG"].append(org_name)
        elif ent.label_ in entities:
            entities[ent.label_].append(ent.text)

    # Enhanced case number patterns
    case_patterns = [
        r'Case\s*No\.?\s*\d+[/-]\d+',  # Case No. 123/2023
        r'[A-Z]{2,}\s*No\.?\s*\d+[/-]\d+',  # CRL No. 456/2022
        r'Crl\.?\s*A\.?\s*No\.?\s*\d+[/-]\d+',  # Crl.A.No. 789/2021
        r'[A-Z]+\s*Appeal\s*No\.?\s*\d+',  # Civil Appeal No. 123
        r'Writ\s*Petition\s*\(?[A-Z]+\)?\s*No\.?\s*\d+',  # Writ Petition (Crl) No. 456
    ]
    for pattern in case_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["CASE_ID"].extend(matches)

    # Legal citation patterns (e.g., [2023] 1 SCC 123, AIR 2022 SC 456)
    citation_patterns = [
        r'\[\d{4}\]\s+\d+\s+[A-Z]{2,}\s+\d+',  # [2023] 1 SCC 123
        r'\b[A-Z]{2,}\s+\d{4}\s+[A-Z]{2,}\s+\d+',  # AIR 2022 SC 456
        r'\(\d{4}\)\s+\d+\s+[A-Z]{2,}\s+\d+',  # (2023) 1 SCC 123
    ]
    for pattern in citation_patterns:
        matches = re.findall(pattern, text)
        entities["CITATIONS"].extend(matches)

    # Statute references (Section X, Article Y, IPC, CrPC, etc.)
    statute_patterns = [
        r'Section\s+\d+[A-Z]?(?:\(\d+\))?(?:\s+of\s+[^.]+)?',  # Section 302(1) of IPC
        r'Article\s+\d+[A-Z]?(?:\(\d+\))?',  # Article 14(1)
        r'\b(?:IPC|CrPC|CPC|IEA)\s+Section\s+\d+',  # IPC Section 420
        r'Rule\s+\d+[A-Z]?',  # Rule 3A
    ]
    for pattern in statute_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["STATUTES"].extend(matches)

    # Enhanced organization patterns
    org_patterns = [
        r'(?:High|Supreme|District|Sessions)\s+Court\s+of\s+[A-Za-z\s]+',
        r'High\s+Court\s+at\s+[A-Za-z]+',
        r'Supreme\s+Court\s+of\s+India',
        r'\b[A-Z]{2,}\s+(?:Commission|Bureau|Department|Authority)',
        r'CID\s+[A-Za-z]+'
    ]
    for pattern in org_patterns:
        matches = re.findall(pattern, text)
        entities["ORG"].extend(matches)

    # Remove redundant ORG entities
    filtered_orgs = []
    for org in entities["ORG"]:
        if not any(org != other_org and org in other_org for other_org in entities["ORG"]):
            filtered_orgs.append(org)
    entities["ORG"] = filtered_orgs

    # Remove duplicates while preserving order
    for key in entities:
        entities[key] = list(dict.fromkeys(entities[key]))

    return entities

