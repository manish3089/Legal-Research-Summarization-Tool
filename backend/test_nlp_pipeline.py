# This is test_nlp_pipeline.py
from nlp_module.extractive_summarization import summarize
from nlp_module.text_preprocessing import preprocess_text, extract_entities

sample_text = """
Case No. 123/2021. The Honorable Judge Smith presided over the matter in the High Court of Karnataka.
The plaintiff argued that the contract was void due to coercion. On March 15th, the defendant presented new evidence.
Justice Rao dismissed the arguments citing lack of jurisdiction. The CID Bengaluru later reopened the investigation.
"""
print("Original Text:\n", sample_text)

cleaned = preprocess_text(sample_text)
print("\nPreprocessed Text:\n", cleaned)

entities = extract_entities(sample_text)
print("\nExtracted Entities:\n", entities)

summary = summarize(sample_text)
print("\nSummary:\n",summary)
