# This is test_nlp_pipeline.py
from nlp_module.text_preprocessing import preprocess_text, extract_entities

sample_text = """
Case No. 123/2023. John Doe was present on 12th March 2023 at the High Court of Karnataka. 
The case was heard in front of Judge Smith. Organization involved: CID Bengaluru.
"""

print("Original Text:\n", sample_text)

cleaned = preprocess_text(sample_text)
print("\nPreprocessed Text:\n", cleaned)

entities = extract_entities(sample_text)
print("\nExtracted Entities:\n", entities)
