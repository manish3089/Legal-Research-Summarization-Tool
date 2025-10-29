import sys
import os
import logging

# Add the project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Configure logger for this module
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

from backend.nlp_module.text_preprocessing import preprocess_text
from backend.nlp_module.extractive_summarization import summarize as extractive_summarize

from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import spacy
from nlp_module.text_preprocessing import preprocess_text

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

class AbstractiveSummarizer:
    """
    A class to perform abstractive summarization using BART model.
    """
    def __init__(self,  model_name="santoshtyss/lt5-small"):
        """
        Initialize the BART model and tokenizer.
        
        Parameters:
        model_name (str): Name of the pretrained BART model to use.
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)
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
            logger.error(f"Error during chunk summarization: {e}")
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
            processed_text = preprocess_text(text)
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
            logger.error(f"Error during abstractive summarization: {e}")
            return f"Summarization error: {e}"

    def hybrid_summarize(self, text, num_sentences=3, abstractive_weight=0.5):
        """
        Create a hybrid summary combining both extractive and abstractive methods.
        
        Parameters:
        text (str): The input text to summarize.
        num_sentences (int): Approximate number of sentences in the final summary.
        abstractive_weight (float): Weight given to abstractive summary (0.0-1.0).
                                  Extractive weight will be (1 - abstractive_weight).
        
        Returns:
        dict: A dictionary containing both summaries and the combined summary.
        """
        try:
            # Get extractive summary
            extractive_result = extractive_summarize(text, method='hybrid', top_n=num_sentences)
            
            # Get abstractive summary
            abstractive_result = self.abstractive_summarize(text, num_sentences=num_sentences)
            
            # Combine summaries
            combined_summary = f"{abstractive_result}\n\nKey points (extracted):\n{extractive_result}"
            
            return {
                'combined_summary': combined_summary,
                'abstractive_summary': abstractive_result,
                'extractive_summary': extractive_result
            }
            
        except Exception as e:
            logger.error(f"Error during hybrid summarization: {e}")
            return {
                'error': f"Hybrid summarization error: {e}",
                'abstractive_summary': None,
                'extractive_summary': None,
                'combined_summary': None
            }

# Example usage
if __name__ == "__main__":
    # Demo usage when running this module directly. Uses logging instead of printing
    sample_text = """
    Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence...
    """
    summarizer = AbstractiveSummarizer()
    
    # Get hybrid summary
    hybrid_results = summarizer.hybrid_summarize(sample_text, num_sentences=3)
    
    logger.info("Hybrid Summary Results:")
    logger.info("Combined Summary:\n%s", hybrid_results['combined_summary'])
    logger.info("\nAbstractive Summary:\n%s", hybrid_results['abstractive_summary'])
    logger.info("\nExtractive Summary:\n%s", hybrid_results['extractive_summary'])
