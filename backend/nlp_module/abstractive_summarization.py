import sys
import os

# Add the project root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from backend.nlp_module.text_preprocessing import preprocess_text

from transformers import BartForConditionalGeneration, BartTokenizer
import torch
import nltk
from nltk.tokenize import sent_tokenize

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt_tab')

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
        self.max_input_length = 1024  # BART's max token length
        self.max_output_length = 150  # Max length for generated summary

    def preprocess_input(self, text):
        """
        Preprocess the input text using the existing preprocess_text function and sentence tokenization.
        
        Parameters:
        text (str): Input text to preprocess.
        
        Returns:
        str: Preprocessed text ready for summarization.
        """
        try:
            # Apply existing preprocessing
            processed_text = preprocess_text(text)
            # Split into sentences
            sentences = sent_tokenize(processed_text)
            # Join sentences to ensure coherent input
            return " ".join(sentences)
        except Exception as e:
            print(f"Error during preprocessing: {e}")
            return text  # Fallback to original text

    def chunk_text(self, text):
        """
        Split long text into chunks to fit within BART's token limit.
        
        Parameters:
        text (str): Input text to chunk.
        
        Returns:
        list: List of text chunks.
        """
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_tokens = self.tokenizer.encode(sentence, add_special_tokens=False)
            if current_length + len(sentence_tokens) > self.max_input_length - 50:  # Buffer for special tokens
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

            # Calculate dynamic max_length based on num_sentences
            avg_tokens_per_sentence = 20  # Approximate tokens per sentence
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
            # Preprocess the input text
            processed_text = self.preprocess_input(text)

            # Chunk the text if it's too long
            chunks = self.chunk_text(processed_text)

            # Summarize each chunk
            summaries = []
            sentences_per_chunk = max(1, num_sentences // max(1, len(chunks)))  # Distribute sentences

            for chunk in chunks:
                summary = self.summarize_chunk(chunk, sentences_per_chunk)
                if summary:
                    summaries.append(summary)

            # Combine summaries
            final_summary = " ".join(summaries)

            # Post-process to ensure approximate sentence count
            final_sentences = sent_tokenize(final_summary)
            if len(final_sentences) > num_sentences:
                final_sentences = final_sentences[:num_sentences]
                final_summary = " ".join(final_sentences)

            return final_summary.strip() if final_summary else "Summarization failed."
        except Exception as e:
            print(f"Error during abstractive summarization: {e}")
            return f"Summarization error: {e}"

# Example usage
if __name__ == "__main__":
    sample_text = """
    Natural language processing (NLP) is a subfield of linguistics, computer science, and artificial intelligence concerned with the interactions between computers and human language, in particular how to program computers to process and analyze large amounts of natural language data. The goal is a computer capable of "understanding" the contents of documents, including the contextual nuances of the language within them. The technology can then accurately extract information and insights contained in the documents as well as categorize and organize the documents themselves.
    
    Challenges in natural language processing frequently involve speech recognition, natural language understanding, and natural language generation. The process of natural language processing has several steps including lexical analysis, parsing, semantic analysis, discourse integration, and pragmatic analysis. Each step has its own challenges and approaches.
    
    Modern NLP approaches are based on machine learning, especially statistical machine learning. Many different classes of machine-learning algorithms have been applied to natural-language-processing tasks. These algorithms take as input a large set of "features" that are generated from the input data.
    
    Some of the earliest-used machine learning algorithms, such as decision trees, produced systems of hard if-then rules similar to existing hand-written rules. However, part-of-speech tagging introduced the use of hidden Markov models to natural language processing, and increasingly, research has focused on statistical models, which make soft, probabilistic decisions based on attaching real-valued weights to the features making up the input data.
    """
    
    summarizer = AbstractiveSummarizer()
    summary = summarizer.abstractive_summarize(sample_text, num_sentences=3)
    print(f"Abstractive Summary:\n{summary}")
