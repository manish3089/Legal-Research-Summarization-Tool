import spacy
import nltk
from nltk.corpus import stopwords
import re
import time
from collections import defaultdict

# Download necessary NLTK resources
def download_nltk_resources():
    resources = ['stopwords', 'punkt', 'averaged_perceptron_tagger', 'maxent_ne_chunker', 'words']
    for resource in resources:
        try:
            nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' 
                          else f'taggers/{resource}' if resource == 'averaged_perceptron_tagger'
                          else f'chunkers/{resource}' if resource == 'maxent_ne_chunker'
                          else f'corpora/{resource}')
        except LookupError:
            nltk.download(resource)

download_nltk_resources()

# Load SpaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading SpaCy model...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

stop_words = set(stopwords.words('english'))

# Add legal-specific stopwords
legal_stopwords = {
    'plaintiff', 'defendant', 'petitioner', 'respondent', 'appellant', 'appellee',
    'thereof', 'therein', 'thereto', 'herein', 'hereof', 'hereto',
    'whereby', 'whereas', 'pursuant', 'aforesaid'
}
stop_words.update(legal_stopwords)

# Legal terminology mapping for standardization
legal_term_mapping = {
    "hon'ble": "honorable",
    "hon.": "honorable",
    "vs.": "versus",
    "v.": "versus",
    "etc.": "etcetera",
    "i.e.": "that is",
    "e.g.": "for example",
}

# Define patterns for various legal entities
CASE_ID_PATTERNS = [
    r'(Case\s*No\.?\s*\d+[/-]\d+)',
    r'(Criminal\s*Case\s*No\.?\s*\d+(?:[/-]\d+)?)',
    r'(Civil\s*Case\s*No\.?\s*\d+(?:[/-]\d+)?)',
    r'(Suit\s*No\.?\s*\d+(?:[/-]\d+)?)',
    r'(Appeal\s*No\.?\s*\d+(?:[/-]\d+)?)',
    r'(Application\s*No\.?\s*\d+(?:[/-]\d+)?)',
    r'(Petition\s*No\.?\s*\d+(?:[/-]\d+)?)',
    r'(Writ\s*Petition\s*No\.?\s*\d+(?:[/-]\d+)?)',
    r'(\d+\s*of\s*\d{4})',  # Format: 123 of 2023
]

COURT_PATTERNS = [
    r'(Supreme\s*Court(?:\s*of\s*[A-Za-z\s]+)?)',
    r'(High\s*Court(?:\s*of\s*[A-Za-z\s]+)?)',
    r'(District\s*Court(?:\s*of\s*[A-Za-z\s]+)?)',
    r'(Sessions\s*Court(?:\s*of\s*[A-Za-z\s]+)?)',
    r'(Family\s*Court(?:\s*of\s*[A-Za-z\s]+)?)',
    r'(Magistrate\s*Court(?:\s*of\s*[A-Za-z\s]+)?)',
    r'(Civil\s*Court(?:\s*of\s*[A-Za-z\s]+)?)',
    r'(Criminal\s*Court(?:\s*of\s*[A-Za-z\s]+)?)',
    r'(Tribunal(?:\s*of\s*[A-Za-z\s]+)?)',
]

LAW_PATTERNS = [
    r'((?:The\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Act,?\s+\d{4})',  # Format: The Evidence Act, 1872
    r'((?:The\s+)?[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+Code,?\s+\d{4})',  # Format: The Criminal Procedure Code, 1973
    r'(Section\s+\d+(?:[A-Z])?(?:\s+of\s+the\s+[A-Za-z\s]+(?:Act|Code),?\s+\d{4})?)',  # Section 302 of the IPC
    r'(Article\s+\d+(?:[A-Z])?(?:\s+of\s+the\s+[A-Za-z\s]+)?)',  # Article 21 of the Constitution
    r'((?:The\s+)?Constitution(?:\s+of\s+[A-Za-z\s]+)?)',  # The Constitution of India
]

ORG_PATTERNS = [
    r'(CID\s*[A-Za-z]+)',
    r'(Police\s*Station\s*[A-Za-z\s]+)',
    r'(Department\s*of\s*[A-Za-z\s]+)',
    r'(Ministry\s*of\s*[A-Za-z\s]+)',
    r'(Bar\s*Association\s*of\s*[A-Za-z\s]+)',
    r'(Law\s*Society\s*of\s*[A-Za-z\s]+)',
]

# Person titles to look for
PERSON_TITLES = [
    "judge", "justice", "adv.", "advocate", "solicitor", "barrister", 
    "attorney", "counsel", "prosecutor", "magistrate", "hon'ble", 
    "honorable", "hon.", "chief justice", "cj", "j."
]

def preprocess_text(text, preserve_case=False):
    """
    Tokenize, remove stopwords and punctuation, lemmatize, and preserve key entities.

    Parameters:
    text (str): The input text to preprocess.
    preserve_case (bool): Whether to preserve case of the original text.

    Returns:
    str: The preprocessed text as a single string.
    """
    if not text:
        raise ValueError("Input text cannot be empty.")

    # Standardize legal terminology
    for term, replacement in legal_term_mapping.items():
        text = re.sub(r'\b' + re.escape(term) + r'\b', replacement, text, flags=re.IGNORECASE)

    # Extract entities and case IDs first using regex
    case_ids = []
    for pattern in CASE_ID_PATTERNS:
        case_ids.extend(re.findall(pattern, text, re.IGNORECASE))
    
    case_ids_lower = [cid.lower() for cid in case_ids] if not preserve_case else case_ids
    
    # Extract law references
    law_refs = []
    for pattern in LAW_PATTERNS:
        law_refs.extend(re.findall(pattern, text, re.IGNORECASE))
    
    law_refs_lower = [ref.lower() for ref in law_refs] if not preserve_case else law_refs

    doc = nlp(text)
    
    # First collect entity spans to avoid splitting them
    entity_spans = []
    for ent in doc.ents:
        if ent.label_ in ['DATE', 'CARDINAL', 'ORDINAL', 'TIME', 'MONEY', 'PERCENT', 'QUANTITY']:
            entity_text = ent.text if preserve_case else ent.text.lower()
            entity_spans.append((ent.start, ent.end, entity_text))
    
    # Process tokens and add them to lemmas
    lemmas = case_ids_lower.copy() + law_refs_lower.copy()  # Start with extracted IDs and laws
    
    i = 0
    while i < len(doc):
        # Check if this token is part of an entity span
        is_in_entity = False
        entity_text = None
        
        for start, end, text in entity_spans:
            if start <= i < end:
                # This token is part of an entity
                is_in_entity = True
                entity_text = text
                i = end  # Skip to the end of the entity
                break
        
        if is_in_entity:
            # Add the whole entity text if not already added
            if entity_text not in lemmas:
                lemmas.append(entity_text)
        else:
            token = doc[i]
            # Skip tokens already included in case_ids or law_refs
            if not any(token.text.lower() in cid.lower() for cid in case_ids) and \
               not any(token.text.lower() in ref.lower() for ref in law_refs):
                if token.ent_type_ in ['DATE', 'CARDINAL', 'ORDINAL', 'TIME', 'MONEY', 'PERCENT', 'QUANTITY']:
                    token_text = token.text if preserve_case else token.text.lower()
                    lemmas.append(token_text)
                elif token.is_alpha and token.text.lower() not in stop_words:
                    token_text = token.text if preserve_case else token.lemma_.lower()
                    lemmas.append(token_text)
            i += 1

    # Join lemmas into a single string
    preprocessed_text = " ".join(lemmas)

    # Clean up punctuation spacing
    preprocessed_text = re.sub(r'\s+([.,:;!?])', r'\1', preprocessed_text)  # Remove space before punctuation
    preprocessed_text = re.sub(r'([.,:;!?])\s+', r'\1 ', preprocessed_text)  # Ensure space after punctuation
    return preprocessed_text.strip()


def extract_entities(text):
    """
    Extracts named entities from legal text with enhanced recognition for legal-specific entities.

    Parameters:
    text (str): The input text from which to extract entities.

    Returns:
    dict: A dictionary containing lists of extracted entities.
    """
    if not text:
        raise ValueError("Input text cannot be empty.")

    # Start timing
    start_time = time.time()

    doc = nlp(text)
    entities = {
        "PERSON": [],
        "ORG": [],
        "DATE": [],
        "GPE": [],
        "CASE_ID": [],
        "COURT": [],
        "LAW": [],
        "JUDGE": [],
        "MONEY": []
    }

    # Extract basic named entities from spaCy
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            # Check if preceded by a title
            start_idx = max(0, ent.start - 2)  # Look up to 2 tokens before
            preceding_text = " ".join([t.text.lower() for t in doc[start_idx:ent.start]])
            
            # Check if any title is in the preceding text
            has_title = any(title in preceding_text for title in PERSON_TITLES)
            
            if has_title:
                # Find the specific title
                for title in PERSON_TITLES:
                    if title in preceding_text:
                        title_position = preceding_text.find(title)
                        # Get all text from the title to the end of preceding text
                        full_title = preceding_text[title_position:].strip()
                        full_name = f"{full_title} {ent.text}"
                        if "judge" in full_title or "justice" in full_title:
                            entities["JUDGE"].append(full_name)
                        else:
                            entities["PERSON"].append(full_name)
                        break
            else:
                entities["PERSON"].append(ent.text)
                
        elif ent.label_ == "ORG":
            # Remove "the" from organization names
            org_name = re.sub(r'^the\s+', '', ent.text, flags=re.IGNORECASE)
            entities["ORG"].append(org_name)
        elif ent.label_ == "MONEY":
            entities["MONEY"].append(ent.text)
        elif ent.label_ in entities:
            entities[ent.label_].append(ent.text)

    # Extract case numbers using regex
    for pattern in CASE_ID_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["CASE_ID"].extend(matches)

    # Extract courts using regex
    for pattern in COURT_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            entities["COURT"].append(match)
            # Remove from organizations if present
            if match in entities["ORG"]:
                entities["ORG"].remove(match)

    # Extract law references
    for pattern in LAW_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["LAW"].extend(matches)

    # Extract organizations
    for pattern in ORG_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["ORG"].extend(matches)

    # Check for judges not caught by NER
    judge_patterns = [
        r'((?:Justice|Judge|Hon\'ble|Honorable|J\.)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s+(?:J\.|Justice))'
    ]
    
    for pattern in judge_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Check if this judge is already in PERSON or JUDGE list
            if not any(match in p for p in entities["PERSON"]) and not any(match in j for j in entities["JUDGE"]):
                entities["JUDGE"].append(match)
                # Remove from PERSON if present
                if match in entities["PERSON"]:
                    entities["PERSON"].remove(match)

    # Remove redundant entities (e.g., keep "High Court of Karnataka" over "High Court")
    for entity_type in ["ORG", "COURT"]:
        filtered_entities = []
        entities_list = entities[entity_type]
        
        for entity in entities_list:
            # Only add org if it's not a substring of another longer org
            if not any(entity != other and entity in other for other in entities_list):
                filtered_entities.append(entity)
        
        entities[entity_type] = filtered_entities

    # Move judges from PERSON to JUDGE if they contain judge indicators
    judge_indicators = ["judge", "justice", "j.", "hon'ble", "honorable", "chief justice"]
    persons_to_remove = []
    
    for person in entities["PERSON"]:
        lower_person = person.lower()
        if any(indicator in lower_person for indicator in judge_indicators):
            entities["JUDGE"].append(person)
            persons_to_remove.append(person)
    
    for person in persons_to_remove:
        entities["PERSON"].remove(person)

    # Remove duplicates while preserving order
    for key in entities:
        entities[key] = list(dict.fromkeys(entities[key]))

    # Calculate processing time
    processing_time = time.time() - start_time
    
    # Add empty stats dictionary for additional stats
    stats = {
        "processing_time_ms": round(processing_time * 1000, 2),
        "entity_counts": {k: len(v) for k, v in entities.items()},
        "total_entities": sum(len(v) for v in entities.items())
    }
    
    return entities, stats


def analyze_legal_document(text):
    """
    Perform comprehensive analysis of a legal document, including preprocessing,
    entity extraction, and basic statistics.
    
    Parameters:
    text (str): The legal document text
    
    Returns:
    dict: Analysis results including preprocessed text, entities, and statistics
    """
    if not text:
        raise ValueError("Input text cannot be empty.")
        
    # Get document statistics
    word_count = len(text.split())
    sentence_count = len(nltk.sent_tokenize(text))
    char_count = len(text)
    
    # Calculate average sentence length
    avg_sentence_length = word_count / max(1, sentence_count)
    
    # Preprocess text
    preprocessed_text = preprocess_text(text)
    
    # Extract entities
    entities, extraction_stats = extract_entities(text)
    
    # Create frequency distribution of non-stopwords
    words = [word.lower() for word in nltk.word_tokenize(text) 
             if word.isalpha() and word.lower() not in stop_words]
    
    freq_dist = defaultdict(int)
    for word in words:
        freq_dist[word] += 1
    
    # Get top keywords (excluding named entities)
    all_entities_text = []
    for entity_list in entities.values():
        for entity in entity_list:
            all_entities_text.extend(entity.lower().split())
    
    keywords = {word: count for word, count in freq_dist.items() 
                if count > 1 and word not in all_entities_text}
    top_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Compile analysis results
    analysis = {
        "document_stats": {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "character_count": char_count,
            "avg_sentence_length": round(avg_sentence_length, 1)
        },
        "preprocessed_text": preprocessed_text,
        "entities": entities,
        "top_keywords": dict(top_keywords),
        "extraction_stats": extraction_stats
    }
    
    return analysis


# Example usage and testing function
def test_with_sample():
    """Test the system with sample legal texts"""
    samples = [
        # Sample 1: Basic case reference
        """Case No. 123/2023. John Doe was present on 12th March 2023 at the High Court of Karnataka. 
        The case was heard in front of Judge Smith. Organization involved: CID Bengaluru.""",
        
        # Sample 2: More complex legal document with citations
        """IN THE SUPREME COURT OF INDIA
        CRIMINAL APPEAL NO. 1456 OF 2019
        
        Rajesh Kumar & Anr.                 ...Appellants
                    Versus
        State of Maharashtra & Ors.         ...Respondents
        
        BEFORE:
        Hon'ble Justice A.K. Sikri
        Hon'ble Justice S. Abdul Nazeer
        
        For the Appellants: Mr. Sanjay Hegde, Senior Advocate
        For the Respondents: Ms. Indira Jaising, Senior Advocate
        
        The appeal arises from proceedings under Section 302 of the Indian Penal Code, 1860 and
        Section 120B read with Section 34 of the IPC. The incident occurred on 15th January, 2018
        at Police Station Colaba, Mumbai. A sum of Rs. 50,000/- was paid as compensation.""",
        
        # Sample 3: Writ petition with complex references
        """WRIT PETITION (CIVIL) NO. 118 OF 2022
        
        IN THE MATTER OF:
        XYZ Welfare Association            ...Petitioner
                    VERSUS
        Union of India & Others            ...Respondents
        
        The petition challenges the constitutional validity of the Environment Protection (Amendment) Act, 2022.
        The hearing is scheduled for 23rd September 2022 before the Constitutional Bench headed by Chief Justice Ramana.
        The matter pertains to Article 21 and Article 48A of the Constitution of India."""
    ]
    
    results = []
    
    for i, sample in enumerate(samples):
        print(f"\n\n=== PROCESSING SAMPLE {i+1} ===")
        print(f"ORIGINAL TEXT:\n{sample}\n")
        
        analysis = analyze_legal_document(sample)
        
        print(f"PREPROCESSED TEXT:\n{analysis['preprocessed_text']}\n")
        print("EXTRACTED ENTITIES:")
        for entity_type, entities in analysis['entities'].items():
            if entities:  # Only print non-empty entity types
                print(f"- {entity_type}: {entities}")
        
        print("\nDOCUMENT STATISTICS:")
        for stat, value in analysis['document_stats'].items():
            print(f"- {stat}: {value}")
        
        print("\nTOP KEYWORDS:")
        for word, count in analysis['top_keywords'].items():
            print(f"- {word}: {count}")
        
        print(f"\nProcessing time: {analysis['extraction_stats']['processing_time_ms']} ms")
        
        results.append(analysis)
    
    return results

if __name__ == "__main__":
    test_with_sample()
