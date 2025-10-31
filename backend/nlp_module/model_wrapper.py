import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from abstractive_summarization import AbstractiveSummarizer
from extractive_summarization import summarize as extractive_summarize

class HybridSummarizer:
    """Wrapper for your extractive + abstractive pipeline."""
    
    def __init__(self, extraction_ratio=0.65, abstractive_compression=0.6):
        self.abstractive_model = AbstractiveSummarizer()
        self.extraction_ratio = extraction_ratio
        self.abstractive_compression = abstractive_compression
    
    def summarize(self, text, num_sentences=6):
        """Full pipeline: extractive -> abstractive."""
        # Step 1: Extractive
        extractive_summary = extractive_summarize(
            text,
            method='hybrid',
            compression_ratio=self.extraction_ratio,
            top_n=None
        )
        
        # Step 2: Abstractive
        abstractive_summary = self.abstractive_model.abstractive_summarize(
            extractive_summary,
            num_sentences=num_sentences,
            compression_ratio=self.abstractive_compression
        )
        
        return abstractive_summary


class ExtractiveOnlySummarizer:
    """Extractive-only summarizer for legal documents."""
    
    def __init__(self, extraction_ratio=0.35):
        self.extraction_ratio = extraction_ratio
    
    def summarize(self, text):
        """Extract key sentences from legal document."""
        summary = extractive_summarize(
            text,
            method='hybrid',
            compression_ratio=self.extraction_ratio,
            top_n=None
        )
        return summary


if __name__ == "__main__":
    import pandas as pd
    from datasets import load_dataset
    from tqdm import tqdm
    
    # Initialize your model
    your_model = HybridSummarizer
    
    # Load dataset
    print("Loading ZeroLexSumm dataset...")
    ds = load_dataset("CJWeiss/ZeroLexSumm", "zero_billsum")
    train_data = ds['train']
    
    print(f"Dataset loaded: {len(train_data)} documents")
    print(f"Columns: {train_data[0].keys()}")
    
    # Generate summaries
    your_summaries = []
    for example in tqdm(train_data, desc="Generating summaries"):
        try:
            text = example['input']
            summary = your_model.summarize(text)
            your_summaries.append(summary)
        except Exception as e:
            print(f"Error: {e}")
            your_summaries.append("[ERROR]")
    
    # Create DataFrame
    df = pd.DataFrame({
        "id": range(len(train_data)),
        "source_text": [ex.get('text') or ex.get('source_text') for ex in train_data],
        "reference_summary": [ex.get('summary') or ex.get('reference_summary') for ex in train_data],
        "generated_summary": your_summaries
    })
    
    # Save to CSV
    df.to_csv("hybrid_summaries.csv", index=False)
    print(f"✓ Saved {len(df)} summaries to hybrid_summaries.csv")
