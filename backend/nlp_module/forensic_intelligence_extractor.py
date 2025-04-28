import re
import spacy
import numpy as np
from spacy.matcher import DependencyMatcher
from collections import defaultdict

# Load your spaCy model
nlp = spacy.load("en_core_web_sm")

class ForensicIntelligenceExtractor:
    def __init__(self):
        self.crime_keywords = {
            "murder": "High",
            "homicide": "High",
            "fraud": "Medium",
            "theft": "Medium",
            "robbery": "Medium",
            "assault": "Medium",
            "harassment": "Low",
            "vandalism": "Low",
            "bribery": "Medium",
            "kidnapping": "High",
            "drug trafficking": "High",
            "corruption": "Medium"
        }
        
        # Outcome keywords and phrases
        self.outcome_indicators = {
            "convicted": "convicted",
            "found guilty": "convicted",
            "sentenced to": "convicted",
            "pleaded guilty": "convicted",
            "convicted of": "convicted",
            "acquitted": "acquitted",
            "not guilty": "acquitted",
            "dismissed": "acquitted",
            "charges dropped": "acquitted",
            "released": "acquitted"
        }
        
        # Initialize a dependency matcher for relationship extraction
        self.matcher = DependencyMatcher(nlp.vocab)
        
        # Define patterns for relationship extraction
        self.define_relationship_patterns()

    def define_relationship_patterns(self):
        # Pattern for "X is the father of Y"
        family_pattern = [
            # X is head of the sentence
            {"RIGHT_ID": "person1", "RIGHT_ATTRS": {"POS": "PROPN"}},
            # "is" or other copula connecting X to the relationship
            {"LEFT_ID": "person1", "REL_OP": ">", "RIGHT_ID": "is", "RIGHT_ATTRS": {"DEP": "ROOT", "LEMMA": {"IN": ["be", "is", "was", "are"]}}},
            # "the" article before relationship term
            {"LEFT_ID": "is", "REL_OP": ">", "RIGHT_ID": "the", "RIGHT_ATTRS": {"DEP": "det"}},
            # Relationship term (father, mother, brother, etc.)
            {"LEFT_ID": "the", "REL_OP": ">", "RIGHT_ID": "relation", "RIGHT_ATTRS": {"POS": "NOUN"}},
            # "of" connecting to second person
            {"LEFT_ID": "relation", "REL_OP": ">", "RIGHT_ID": "of", "RIGHT_ATTRS": {"DEP": "prep", "LOWER": "of"}},
            # The second person
            {"LEFT_ID": "of", "REL_OP": ">", "RIGHT_ID": "person2", "RIGHT_ATTRS": {"POS": "PROPN"}}
        ]
        
        self.matcher.add("FAMILY_RELATION", [family_pattern])

    def extract_case_number(self, text):
        match = re.search(r'(Case\s*No\.?\s*\d+/\d+)', text, re.IGNORECASE)
        confidence = 0.9 if match else 0.0
        return {"value": match.group(1) if match else None, "confidence": confidence}

    def detect_crime_type(self, text):
        # Simple keyword matching
        best_match = None
        max_confidence = 0.0
        
        # Process document once
        doc = nlp(text.lower())
        
        for crime, severity in self.crime_keywords.items():
            # Check for direct mentions
            if crime.lower() in text.lower():
                confidence = 0.8  # Base confidence for direct match
                
                # Check if the crime is mentioned in a context that suggests it's the main crime
                if re.search(rf'charged with {crime}', text.lower()) or \
                   re.search(rf'accused of {crime}', text.lower()) or \
                   re.search(rf'convicted of {crime}', text.lower()):
                    confidence = 0.95  # Higher confidence for contextual match
                
                if confidence > max_confidence:
                    max_confidence = confidence
                    best_match = crime.capitalize()
        
        # TODO: Add ML-based crime classification here
        # This would involve training a text classifier on legal documents
        # and using it to predict crime types with associated probabilities
        
        return {"value": best_match if best_match else "Unknown", "confidence": max_confidence}

    def extract_people_roles(self, text):
        doc = nlp(text)
        people = {
            "Judge": {"value": None, "confidence": 0.0}, 
            "Victim": {"value": None, "confidence": 0.0}, 
            "Suspect": {"value": None, "confidence": 0.0}
        }
        
        for sent in doc.sents:
            sentence = sent.text.lower()
            
            # Judge extraction
            if "judge" in sentence or "justice" in sentence or "presiding" in sentence:
                for ent in sent.ents:
                    if ent.label_ == "PERSON":
                        # Higher confidence if directly preceded by "Judge" or "Justice"
                        preceding_text = text[max(0, ent.start_char - 10):ent.start_char].lower()
                        if "judge" in preceding_text or "justice" in preceding_text:
                            people["Judge"] = {"value": ent.text, "confidence": 0.9}
                        else:
                            people["Judge"] = {"value": ent.text, "confidence": 0.7}
            
            # Suspect extraction
            if any(word in sentence for word in ["accused", "suspect", "charged", "defendant", "perpetrator"]):
                for ent in sent.ents:
                    if ent.label_ == "PERSON":
                        # Calculate confidence based on proximity to key terms
                        if any(word in ent.sent.text.lower() for word in ["charged with", "accused of", "defendant"]):
                            people["Suspect"] = {"value": ent.text, "confidence": 0.85}
                        else:
                            people["Suspect"] = {"value": ent.text, "confidence": 0.7}
            
            # Victim extraction
            if any(word in sentence for word in ["victim", "complainant", "plaintiff", "injured"]):
                for ent in sent.ents:
                    if ent.label_ == "PERSON":
                        # Calculate confidence based on proximity to key terms
                        if "victim" in ent.sent.text.lower():
                            people["Victim"] = {"value": ent.text, "confidence": 0.85}
                        else:
                            people["Victim"] = {"value": ent.text, "confidence": 0.7}
        
        return people

    def extract_relationships(self, text):
        """Extract relationships between people mentioned in the text"""
        doc = nlp(text)
        relationships = []
        
        # Use the dependency matcher
        matches = self.matcher(doc)
        
        for match_id, token_ids in matches:
            pattern_name = self.matcher.vocab.strings[match_id]
            
            if pattern_name == "FAMILY_RELATION":
                # Extract person names and relationship type
                person1_id = token_ids[0]  # Index based on pattern definition
                relation_id = token_ids[3]
                person2_id = token_ids[5]
                
                person1 = doc[person1_id].text
                relation = doc[relation_id].text
                person2 = doc[person2_id].text
                
                relationships.append({
                    "person1": person1,
                    "relation": relation,
                    "person2": person2,
                    "confidence": 0.85
                })
        
        # Additional rule-based relationship extraction
        for sent in doc.sents:
            sent_text = sent.text.lower()
            
            # Check for simple relationship patterns
            for rel_word in ["husband", "wife", "brother", "sister", "father", "mother", "son", "daughter"]:
                if rel_word in sent_text:
                    names = [ent.text for ent in sent.ents if ent.label_ == "PERSON"]
                    if len(names) >= 2:
                        relationships.append({
                            "person1": names[0],
                            "relation": rel_word,
                            "person2": names[1],
                            "confidence": 0.7  # Lower confidence for this simpler extraction
                        })
        
        return relationships

    def detect_case_outcome(self, text):
        """Detect the outcome of the case (convicted, acquitted, etc.)"""
        doc = nlp(text.lower())
        
        outcome = None
        confidence = 0.0
        evidence = ""
        
        # Check for outcome indicators
        for sentence in doc.sents:
            sent_text = sentence.text.lower()
            
            for indicator, result in self.outcome_indicators.items():
                if indicator in sent_text:
                    # Find nearby person entities
                    nearby_persons = [ent.text for ent in sentence.ents if ent.label_ == "PERSON"]
                    
                    # Determine if we have a suspect who this outcome applies to
                    suspect_near = any(person.lower() in sent_text for person in 
                                     [self.extract_people_roles(text)["Suspect"]["value"]] 
                                     if self.extract_people_roles(text)["Suspect"]["value"])
                    
                    if nearby_persons or suspect_near:
                        outcome = result
                        confidence = 0.85 if suspect_near else 0.7
                        evidence = sentence.text
                        break
        
        return {
            "value": outcome,
            "confidence": confidence,
            "evidence": evidence
        }

    def extract_incident_date(self, text):
        doc = nlp(text)
        
        # Look for phrases like "on [DATE]", "occurred on [DATE]"
        date_patterns = [
            r"occurred on (\d{1,2}[thstrdnd]* [A-Za-z]+ \d{4})",
            r"occurred on ([A-Za-z]+ \d{1,2}[thstrdnd]*, \d{4})",
            r"on (\d{1,2}[thstrdnd]* [A-Za-z]+ \d{4})",
            r"on ([A-Za-z]+ \d{1,2}[thstrdnd]*, \d{4})",
            r"dated (\d{1,2}[thstrdnd]* [A-Za-z]+ \d{4})",
            r"dated ([A-Za-z]+ \d{1,2}[thstrdnd]*, \d{4})"
        ]
        
        best_match = None
        confidence = 0.0
        
        # First try pattern matching for higher confidence
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                best_match = match.group(1)
                confidence = 0.9
                break
        
        # Fall back to spaCy entity recognition
        if not best_match:
            for ent in doc.ents:
                if ent.label_ == "DATE":
                    # Check if this date is likely to be the incident date
                    context = doc[max(0, ent.start-3):min(len(doc), ent.end+3)].text.lower()
                    if any(word in context for word in ["incident", "crime", "occurred", "happened", "committed"]):
                        best_match = ent.text
                        confidence = 0.8
                        break
                    else:
                        # Could be another date (court date, etc.)
                        best_match = ent.text
                        confidence = 0.5
        
        return {"value": best_match, "confidence": confidence}

    def extract_location(self, text):
        doc = nlp(text)
        location = None
        confidence = 0.0
        
        # Look for location phrases
        location_phrases = [
            r"occurred (at|in) ([A-Za-z\s,]+)",
            r"committed (at|in) ([A-Za-z\s,]+)",
            r"happened (at|in) ([A-Za-z\s,]+)"
        ]
        
        # Try pattern matching for higher confidence
        for pattern in location_phrases:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(2).strip()
                confidence = 0.85
                break
        
        # Fall back to spaCy entity recognition
        if not location:
            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC", "FAC"]:
                    # Check if this entity is likely to be the crime location
                    context = doc[max(0, ent.start-3):min(len(doc), ent.end+3)].text.lower()
                    if any(word in context for word in ["at", "in", "location", "scene", "occurred", "committed"]):
                        location = ent.text
                        confidence = 0.75
                        break
                    else:
                        # Could be another location
                        location = ent.text
                        confidence = 0.5
        
        return {"value": location, "confidence": confidence}

    def assess_severity(self, crime_type):
        if isinstance(crime_type, dict) and "value" in crime_type:
            crime = crime_type["value"].lower()
        else:
            crime = crime_type.lower()
            
        severity = self.crime_keywords.get(crime, "Unknown")
        confidence = 0.9 if severity != "Unknown" else 0.5
        
        return {"value": severity, "confidence": confidence}

    def extract_court(self, text):
        court_patterns = [
            r'(High\s*Court\s*of\s*[A-Za-z]+)',
            r'(Supreme\s*Court\s*of\s*[A-Za-z]+)',
            r'(District\s*Court\s*of\s*[A-Za-z]+)',
            r'(Sessions\s*Court\s*of\s*[A-Za-z]+)'
        ]
        
        for pattern in court_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {"value": match.group(1), "confidence": 0.9}
        
        # Fallback to find any mention of court
        general_court = re.search(r'([A-Za-z]+\s*Court)', text, re.IGNORECASE)
        if general_court:
            return {"value": general_court.group(1), "confidence": 0.7}
            
        return {"value": None, "confidence": 0.0}

    def extract_intelligence(self, text):
        intelligence = {}
        
        # Extract all information with confidence scores
        intelligence["Case_Number"] = self.extract_case_number(text)
        intelligence["Crime_Type"] = self.detect_crime_type(text)
        intelligence["Incident_Date"] = self.extract_incident_date(text)
        intelligence["Location"] = self.extract_location(text)
        
        # People and their roles
        people_roles = self.extract_people_roles(text)
        intelligence.update(people_roles)
        
        # Court information
        intelligence["Court"] = self.extract_court(text)
        
        # Severity assessment
        intelligence["Severity"] = self.assess_severity(intelligence["Crime_Type"]["value"])
        
        # New features
        intelligence["Relationships"] = self.extract_relationships(text)
        intelligence["Case_Outcome"] = self.detect_case_outcome(text)
        
        return intelligence
