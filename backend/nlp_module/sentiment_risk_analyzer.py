from textblob import TextBlob
import nltk
from nltk.tokenize import sent_tokenize
import re
from collections import Counter

class ForensicSentimentRiskAnalyzer:
    def __init__(self):
        # Crime risk mapping
        self.crime_risk_mapping = {
            "murder": "High Risk",
            "homicide": "High Risk",
            "fraud": "Medium Risk",
            "theft": "Medium Risk",
            "robbery": "Medium Risk",
            "assault": "Medium Risk",
            "harassment": "Low Risk",
            "vandalism": "Low Risk",
            "bribery": "Medium Risk",
            "kidnapping": "High Risk",
            "drug trafficking": "High Risk",
            "corruption": "Medium Risk",
            "unknown": "Unknown"
        }
        
        # Legal sentiment modifier terms
        self.legal_negative_terms = [
            "violent", "dangerous", "premeditated", "malicious", "heinous", 
            "repeated", "aggravated", "armed", "deliberate", "threatening",
            "illegal", "unlawful", "unauthorized", "criminal", "felony",
            "intentional", "hostile", "severe", "extreme", "brutal",
            "extensive", "significant", "substantial", "disturbing", "harmful",
            "offensive", "deadly", "exploitative", "manipulative", "coercive"
        ]
        
        self.legal_positive_terms = [
            "cooperative", "remorseful", "mitigating", "self-defense", "apologetic",
            "first-time", "minor", "minimal", "negligible", "unintentional",
            "accidental", "misunderstanding", "justified", "proportionate", "necessary",
            "reasonable", "lawful", "authorized", "legitimate", "exonerating",
            "rehabilitated", "reformed", "supervised", "assisting", "collaborating"
        ]
        
        # Risk intensifiers/reducers
        self.risk_intensifiers = [
            "repeat", "serial", "multiple", "organized", "gang", "syndicate",
            "weapon", "firearm", "knife", "explosives", "drugs", "narcotics",
            "children", "minor", "elderly", "disabled", "vulnerable", "public",
            "official", "government", "international", "cross-border", "large-scale",
            "sophisticated", "planned", "coordinated", "extensive", "professional"
        ]
        
        self.risk_reducers = [
            "first offense", "clean record", "isolated", "singular", "contained",
            "supervised", "monitored", "restricted", "limited", "local",
            "surrendered", "cooperated", "assisted", "helped", "minimal",
            "small", "petty", "minor", "inconsequential", "restitution",
            "compensation", "apology", "reconciliation", "rehabilitation"
        ]

    def analyze_sentiment(self, text):
        """
        Enhanced sentiment analysis that considers legal terminology and context
        """
        # Basic sentiment from TextBlob
        blob = TextBlob(text)
        basic_polarity = blob.sentiment.polarity
        
        # Count occurrences of legal sentiment terms
        text_lower = text.lower()
        negative_count = sum(text_lower.count(term) for term in self.legal_negative_terms)
        positive_count = sum(text_lower.count(term) for term in self.legal_positive_terms)
        
        # Apply legal terminology adjustment
        adjusted_polarity = basic_polarity
        
        # If we have legal terminology, weight it more heavily
        if negative_count > 0 or positive_count > 0:
            legal_sentiment = (positive_count - negative_count) / (positive_count + negative_count + 1)
            # Combine with 70% weight on legal terms, 30% on general sentiment
            adjusted_polarity = (0.3 * basic_polarity) + (0.7 * legal_sentiment)
        
        # Analyze by sentence for more nuanced understanding
        sentences = sent_tokenize(text)
        sentence_sentiments = []
        
        for sentence in sentences:
            sent_blob = TextBlob(sentence)
            sentence_sentiments.append(sent_blob.sentiment.polarity)
        
        # Check for sentiment variability/extremes
        sentiment_variability = max(sentence_sentiments) - min(sentence_sentiments) if sentence_sentiments else 0
        extreme_sentences = sum(1 for s in sentence_sentiments if abs(s) > 0.5)
        
        # Final sentiment classification with confidence
        if adjusted_polarity > 0.2:
            sentiment = "Positive"
            confidence = min(0.5 + adjusted_polarity, 0.95)
        elif adjusted_polarity < -0.2:
            sentiment = "Negative"
            confidence = min(0.5 + abs(adjusted_polarity), 0.95)
        else:
            sentiment = "Neutral"
            confidence = 1.0 - sentiment_variability  # Lower confidence if high variability
        
        return {
            "category": sentiment,
            "score": adjusted_polarity,
            "confidence": confidence,
            "variability": sentiment_variability,
            "extreme_sentences": extreme_sentences
        }

    def analyze_risk(self, text, crime_type="unknown"):
        """
        Enhanced risk analysis that considers multiple factors
        """
        # Get sentiment analysis
        sentiment_result = self.analyze_sentiment(text)
        sentiment = sentiment_result["category"]
        
        # Get base risk from crime type
        crime_based_risk = self.crime_risk_mapping.get(crime_type.lower(), "Unknown")
        
        # Convert risk level to numeric scale for calculations
        risk_numeric = {
            "High Risk": 3,
            "Medium Risk": 2,
            "Low Risk": 1,
            "Unknown": 1.5
        }
        
        base_risk = risk_numeric.get(crime_based_risk, 1.5)
        
        # Check for risk modifiers in text
        text_lower = text.lower()
        
        # Count risk intensifiers and reducers
        intensifier_count = sum(text_lower.count(term) for term in self.risk_intensifiers)
        reducer_count = sum(text_lower.count(term) for term in self.risk_reducers)
        
        # Calculate risk modifier (-1.0 to +1.0)
        total_modifiers = intensifier_count + reducer_count
        risk_modifier = 0
        if total_modifiers > 0:
            risk_modifier = (intensifier_count - reducer_count) / total_modifiers
        
        # Apply sentiment adjustment
        if sentiment == "Negative":
            sentiment_factor = 0.5
        elif sentiment == "Neutral":
            sentiment_factor = 0
        else:  # Positive sentiment
            sentiment_factor = -0.5
        
        # Calculate final risk score (1-3 scale)
        final_risk_score = base_risk + (risk_modifier * 0.5) + sentiment_factor
        final_risk_score = max(1, min(3, final_risk_score))  # Keep in range 1-3
        
        # Convert back to categorical risk
        if final_risk_score >= 2.5:
            risk_level = "High Risk"
        elif final_risk_score >= 1.5:
            risk_level = "Medium Risk"
        else:
            risk_level = "Low Risk"
            
        # Calculate confidence level
        if crime_based_risk == "Unknown" or total_modifiers == 0:
            confidence = 0.6  # Lower confidence with less information
        else:
            confidence = min(0.7 + (total_modifiers / 20), 0.95)  # More modifiers = more confidence
            
        # Risk factors for explanation
        risk_factors = []
        if crime_based_risk in ["High Risk", "Medium Risk"]:
            risk_factors.append(f"Crime type ({crime_type})")
        
        if intensifier_count > 0:
            # Find which intensifiers were mentioned
            mentioned_intensifiers = [term for term in self.risk_intensifiers if term in text_lower]
            if mentioned_intensifiers:
                risk_factors.append(f"Risk intensifiers: {', '.join(mentioned_intensifiers[:3])}")
                
        if sentiment == "Negative":
            risk_factors.append("Negative sentiment context")
            
        # Risk mitigators for explanation
        risk_mitigators = []
        if reducer_count > 0:
            # Find which reducers were mentioned
            mentioned_reducers = [term for term in self.risk_reducers if term in text_lower]
            if mentioned_reducers:
                risk_mitigators.append(f"Risk reducers: {', '.join(mentioned_reducers[:3])}")
                
        if sentiment == "Positive":
            risk_mitigators.append("Positive sentiment context")
            
        return {
            "level": risk_level,
            "score": final_risk_score,
            "confidence": confidence,
            "base_risk": crime_based_risk,
            "risk_factors": risk_factors,
            "risk_mitigators": risk_mitigators,
            "sentiment_impact": sentiment
        }
        
    def analyze_recidivism_indicators(self, text):
        """
        Analyze text for indicators of potential recidivism
        """
        text_lower = text.lower()
        
        # Factors that may indicate higher recidivism risk
        recidivism_indicators = {
            "prior_convictions": ["previous conviction", "prior conviction", "criminal history", 
                                 "criminal record", "repeat offender", "prior offense", 
                                 "previous offense", "history of", "pattern of"],
            "substance_abuse": ["drug use", "alcohol abuse", "substance abuse", "addiction", 
                              "intoxicated", "under the influence", "dependency"],
            "lack_of_support": ["no fixed address", "homeless", "unemployment", "unemployed", 
                              "no support", "isolated", "estranged", "broken family"],
            "antisocial_behavior": ["antisocial", "aggressive", "hostility", "impulsive", 
                                  "reckless", "no remorse", "unapologetic", "defiant"],
            "young_offender": ["juvenile", "young offender", "teenager", "adolescent", "youth"]
        }
        
        # Check for protective factors
        protective_factors = {
            "social_support": ["family support", "community support", "stable relationship", 
                             "stable employment", "employment", "job", "housing", "residence"],
            "rehabilitation": ["rehabilitation", "treatment", "therapy", "counseling", 
                             "program", "course", "education", "training"],
            "remorse": ["remorse", "regret", "apology", "apologetic", "sorry", 
                      "understands", "recognition", "acknowledges"]
        }
        
        # Count occurrences of each factor
        risk_counts = {}
        for category, terms in recidivism_indicators.items():
            count = sum(text_lower.count(term) for term in terms)
            if count > 0:
                risk_counts[category] = count
                
        protective_counts = {}
        for category, terms in protective_factors.items():
            count = sum(text_lower.count(term) for term in terms)
            if count > 0:
                protective_counts[category] = count
        
        # Calculate recidivism risk score
        risk_score = sum(risk_counts.values()) - sum(protective_counts.values())
        
        # Categorize risk
        if risk_score >= 3:
            recidivism_risk = "High"
        elif risk_score >= 1:
            recidivism_risk = "Medium"
        elif risk_score <= -2:
            recidivism_risk = "Very Low"
        elif risk_score < 0:
            recidivism_risk = "Low"
        else:
            recidivism_risk = "Moderate"
            
        return {
            "risk_level": recidivism_risk,
            "score": risk_score,
            "risk_indicators": dict(risk_counts),
            "protective_factors": dict(protective_counts)
        }
        
    def analyze_context_specificity(self, text):
        """
        Analyze how specific the context is for more accurate risk assessment
        """
        # Indicators of specific context
        specificity_indicators = [
            r'\b\d+\s*(year|month|week|day|hour|minute)s?\b', # Time periods
            r'\$\s*\d+[\d,\.]*\b',  # Dollar amounts
            r'\b\d{1,2}\/\d{1,2}\/\d{2,4}\b',  # Dates
            r'\b\d{1,2}:\d{2}\b',  # Times
            r'\b\d+\s*(percent|%)\b',  # Percentages
            r'\b[A-Z][a-z]+ (Street|Avenue|Road|Lane|Drive|Court|Plaza|Boulevard|Hwy|Highway)\b', # Addresses
            r'\b[A-Z][a-z]+, [A-Z]{2}\b',  # City, State format
        ]
        
        # Count specificity indicators
        specificity_count = 0
        for pattern in specificity_indicators:
            specificity_count += len(re.findall(pattern, text))
            
        # Named entities could also indicate specificity
        named_entities = re.findall(r'\b[A-Z][a-zA-Z]+ [A-Z][a-zA-Z]+\b', text)
        specificity_count += len(named_entities)
        
        # Adjust confidence based on specificity
        if specificity_count >= 10:
            specificity_level = "Very High"
            confidence_modifier = 0.2
        elif specificity_count >= 6:
            specificity_level = "High"
            confidence_modifier = 0.15
        elif specificity_count >= 3:
            specificity_level = "Medium"
            confidence_modifier = 0.1
        elif specificity_count >= 1:
            specificity_level = "Low"
            confidence_modifier = 0.05
        else:
            specificity_level = "Very Low"
            confidence_modifier = 0
            
        return {
            "level": specificity_level,
            "confidence_modifier": confidence_modifier,
            "specificity_indicators": specificity_count
        }

    def full_analysis(self, text, crime_type="unknown"):
        """
        Comprehensive analysis of text for forensic purposes
        """
        # Get detailed sentiment analysis
        sentiment_analysis = self.analyze_sentiment(text)
        
        # Get detailed risk analysis
        risk_analysis = self.analyze_risk(text, crime_type)
        
        # Get recidivism indicators
        recidivism_analysis = self.analyze_recidivism_indicators(text)
        
        # Get context specificity
        context_analysis = self.analyze_context_specificity(text)
        
        # Adjust confidence based on context specificity
        adjusted_confidence = min(risk_analysis["confidence"] + context_analysis["confidence_modifier"], 0.95)
        
        # Generate key insights
        key_insights = []
        
        # From sentiment
        if sentiment_analysis["category"] == "Negative" and sentiment_analysis["score"] < -0.5:
            key_insights.append("Highly negative sentiment may indicate aggravating factors")
        elif sentiment_analysis["category"] == "Positive" and sentiment_analysis["score"] > 0.5:
            key_insights.append("Positive sentiment may indicate mitigating circumstances")
        
        # From risk factors
        if risk_analysis["risk_factors"]:
            key_insights.append(f"Risk factors identified: {', '.join(risk_analysis['risk_factors'])}")
        
        # From risk mitigators
        if risk_analysis["risk_mitigators"]:
            key_insights.append(f"Risk mitigating factors: {', '.join(risk_analysis['risk_mitigators'])}")
            
        # From recidivism
        if recidivism_analysis["risk_level"] in ["High", "Medium"]:
            risk_indicators = list(recidivism_analysis["risk_indicators"].keys())
            if risk_indicators:
                key_insights.append(f"Potential recidivism concerns: {', '.join(risk_indicators[:2])}")
        
        # From context
        if context_analysis["level"] in ["Low", "Very Low"]:
            key_insights.append("Limited specific details may affect analysis confidence")
        
        return {
            "Sentiment": sentiment_analysis,
            "Risk_Level": risk_analysis,
            "Recidivism_Indicators": recidivism_analysis,
            "Context_Specificity": context_analysis,
            "Overall_Confidence": adjusted_confidence,
            "Key_Insights": key_insights
        }
