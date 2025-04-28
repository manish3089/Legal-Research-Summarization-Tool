import sys
import os

# Add the project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.nlp_module.text_preprocessing import preprocess_text

from transformers import BartForConditionalGeneration, BartTokenizer
import torch
import spacy
from nlp_module.text_preprocessing import preprocess_text

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

class AbstractiveSummarizer:
    """
    A class to perform abstractive summarization using BART model.
    """
    def __init__(self, model_name="facebook/bart-large-cnn"):
        """
        Initialize the BART model and tokenizer.
        
        Parameters:
        model_name (str): Name of the pretrained BART model to use.
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = BartTokenizer.from_pretrained(model_name)
        self.model = BartForConditionalGeneration.from_pretrained(model_name).to(self.device)
        self.max_input_length = 1024
        self.max_output_length = 150

    def spacy_sent_tokenize(self, text):
        """
        Use spaCy to tokenize text into sentences.
        
        Parameters:
        text (str): Input text.
        
        Returns:
        list: List of sentences.
        """
        doc = nlp(text)
        return [sent.text.strip() for sent in doc.sents]

    def chunk_text(self, text):
        """
        Split long text into chunks to fit within BART's token limit.
        
        Parameters:
        text (str): Input text to chunk.
        
        Returns:
        list: List of text chunks.
        """
        sentences = self.spacy_sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_tokens = self.tokenizer.encode(sentence, add_special_tokens=False)
            if current_length + len(sentence_tokens) > self.max_input_length - 50:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = len(sentence_tokens)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence_tokens)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def summarize_chunk(self, chunk, num_sentences=3):
        """
        Summarize a single chunk of text using BART.
        
        Parameters:
        chunk (str): Text chunk to summarize.
        num_sentences (int): Approximate number of sentences in the summary.
        
        Returns:
        str: Summarized text for the chunk.
        """
        try:
            inputs = self.tokenizer(
                chunk,
                max_length=self.max_input_length,
                truncation=True,
                padding="max_length",
                return_tensors="pt"
            ).to(self.device)

            avg_tokens_per_sentence = 20
            dynamic_max_length = min(self.max_output_length, num_sentences * avg_tokens_per_sentence)

            summary_ids = self.model.generate(
                inputs.input_ids,
                num_beams=4,
                max_length=dynamic_max_length,
                min_length=30,
                early_stopping=True
            )

            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            return summary
        except Exception as e:
            print(f"Error during chunk summarization: {e}")
            return ""

    def abstractive_summarize(self, text, num_sentences=3):
        """
        Main function to create an abstractive summary of text.
        
        Parameters:
        text (str): The input text to summarize.
        num_sentences (int): Approximate number of sentences in the summary.
        
        Returns:
        str: The abstractive summary.
        """
        if not text or text.isspace():
            return "No text to summarize."

        try:
            processed_text = self.preprocess_input(text)
            chunks = self.chunk_text(processed_text)

            summaries = []
            sentences_per_chunk = max(1, num_sentences // max(1, len(chunks)))

            for chunk in chunks:
                summary = self.summarize_chunk(chunk, sentences_per_chunk)
                if summary:
                    summaries.append(summary)

            final_summary = " ".join(summaries)
            final_sentences = self.spacy_sent_tokenize(final_summary)
            if len(final_sentences) > num_sentences:
                final_summary = " ".join(final_sentences[:num_sentences])

            return final_summary.strip() if final_summary else "Summarization failed."
        except Exception as e:
            print(f"Error during abstractive summarization: {e}")
            return f"Summarization error: {e}"

# Example usage
if __name__ == "__main__":
    sample_text = """
    Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence...
    """
    summarizer = AbstractiveSummarizer()
    summary = summarizer.abstractive_summarize(sample_text, num_sentences=3)
    print(f"Abstractive Summary:\n{summary}")
