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

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

class AbstractiveSummarizer:
    """
    A class to perform abstractive summarization using t5 model.
    """
    def __init__(self, model_name="santoshtyss/lt5-small"):
        """
        Initialize the LT5 model and tokenizer.
        
        Parameters:
        model_name (str): Name of the pretrained LT5 model to use.
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)
        # Use model's actual max length, not arbitrary value
        self.max_input_length = getattr(self.model.config, 'n_positions', 512)  # Should be 512 for T5
        self.max_output_length = 512  # Significantly increased for longer summaries
        logger.info(f"Model max input length: {self.max_input_length}")

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
        Split long text into chunks.
        
        Parameters:
        text (str): Input text to chunk.
        
        Returns:
        list: List of text chunks.
        """
        sentences = self.spacy_sent_tokenize(text)
        # Filter out very short or malformed sentences
        sentences = [s for s in sentences if len(s.split()) >= 5]
    
        if not sentences:
            return [text]  # Return original if no valid sentences
        
        chunks = []
        current_chunk = []
        current_length = 0

        # Use actual max_input_length (512)
        max_chunk_tokens = self.max_input_length - 50  # Leave room for prefix

        for sentence in sentences:
            sentence_tokens = self.tokenizer.encode(sentence, add_special_tokens=False)
            if current_length + len(sentence_tokens) > max_chunk_tokens:
                if current_chunk:
                    chunks.append(". ".join(current_chunk) + ".")
                current_chunk = [sentence]
                current_length = len(sentence_tokens)
            else:
                current_chunk.append(sentence)
                current_length += len(sentence_tokens)

        if current_chunk:
            chunks.append(". ".join(current_chunk) + ".")

        return chunks if chunks else [text]

    def summarize_chunk(self, chunk, num_sentences=3, min_length_ratio=0.6):
        """
        Summarize a single chunk of text using LT5.
        
        Parameters:
        chunk (str): Text chunk to summarize.
        num_sentences (int): Approximate number of sentences in the summary.
        min_length_ratio (float): Minimum output length as ratio of input (0.5-0.7).

        Returns:
        str: Summarized text for the chunk.
        """
        try:
            # Prepare prefix for legal domain
            prefix = "Summarize: "
            input_text = prefix + chunk
            
            inputs = self.tokenizer(
                input_text,
                max_length=self.max_input_length,
                truncation=True,
                padding="max_length",
                return_tensors="pt"
            ).to(self.device)

            # Calculate lengths based on input size to prevent over-compression
            input_token_count = inputs.input_ids.ne(self.tokenizer.pad_token_id).sum().item()
        
            # Dynamic length calculation - maintain 50-70% of input length
            dynamic_min_length = int(input_token_count * min_length_ratio)
            dynamic_max_length = min(int(input_token_count * 0.9), self.max_output_length)  # Allow up to 90% of input
        
            # Set reasonable bounds
            dynamic_min_length = max(100, min(dynamic_min_length, 300))
            dynamic_max_length = max(dynamic_min_length + 50, min(dynamic_max_length, 400))

            logger.info(f"Input tokens: {input_token_count}, Min: {dynamic_min_length}, Max: {dynamic_max_length}")

            summary_ids = self.model.generate(
                inputs.input_ids,
                num_beams=2,
                length_penalty=0.4,  # Changed from 0.8 - LOWER penalty = LONGER output
                max_length=dynamic_max_length,
                min_length=dynamic_min_length,  # Much higher minimum
                no_repeat_ngram_size=3,
                repetition_penalty=1.5,  # Reduced from 2.0 to be less aggressive
                early_stopping=True,
                forced_eos_token_id=self.tokenizer.eos_token_id
           )

            summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            return summary
        except Exception as e:
            logger.error(f"Error during chunk summarization: {e}")
        return ""

    def _has_excessive_repetition(self, text):
        """Check if text has excessive repetition."""
        words = text.lower().split()
        if len(words) < 10:
            return False
    
        # Check for repeated words
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
    
        # If any word (except common ones) appears more than 30% of the time
        common_words = {'the', 'a', 'an', 'to', 'of', 'and', 'in', 'is', 'for', 're'}
        for word, count in word_counts.items():
            if word not in common_words and count > len(words) * 0.3:
                return True
    
        return False

    def abstractive_summarize(self, extractive_summary, num_sentences=3, compression_ratio=0.6):
        """
        Refine an extractive summary using abstractive summarization.
        
        Parameters:
        extractive_summary (str): The output from extractive summarization to refine.
        num_sentences (int): Approximate number of sentences in the final summary.
        
        Returns:
        str: The abstractive summary generated from the extractive summary.
        """
        if not extractive_summary or extractive_summary.isspace():
            return "No text to summarize."
        
        # Check if extractive summary is too short
        words = extractive_summary.split()
        sentences_in_extractive = len(self.spacy_sent_tokenize(extractive_summary))
        
        logger.info(f"Extractive summary: {len(words)} words, {sentences_in_extractive} sentences")

        try:
            chunks = self.chunk_text(extractive_summary)
            summaries = []

            # Adjust sentences per chunk based on extractive length
            # Goal: Keep 50-70% of extractive sentences
            target_sentence_count = max(num_sentences, int(sentences_in_extractive * compression_ratio))
            sentences_per_chunk = max(4, target_sentence_count // max(1, len(chunks)))

            logger.info(f"Target sentences: {target_sentence_count}, Per chunk: {sentences_per_chunk}")

            for i, chunk in enumerate(chunks):  # Added enumerate
                logger.info(f"Processing chunk {i+1}/{len(chunks)}")
                summary = self.summarize_chunk(chunk, sentences_per_chunk, min_length_ratio=compression_ratio)
                
                if summary:
                    # Check for repetition patterns
                    if self._has_excessive_repetition(summary):
                        logger.warning(f"Chunk {i+1} has excessive repetition, skipping")
                        continue
                    
                    sentences = self.spacy_sent_tokenize(summary)
                    if sentences:
                        # Remove incomplete last sentence if it doesn't end with punctuation
                        if sentences and not sentences[-1].endswith(('.', '!', '?')):
                            sentences = sentences[:-1]
                        
                        clean_summary = " ".join(sentences)
                        summaries.append(clean_summary)

            if not summaries:
                logger.error("No valid summaries generated")
                return "Summarization failed - no valid output generated."

            final_summary = " ".join(summaries)
            final_sentences = self.spacy_sent_tokenize(final_summary)
            
            # Keep target number of sentences
            final_summary = " ".join(final_sentences[:target_sentence_count])

            logger.info(f"Final summary: {len(final_summary.split())} words, {len(final_sentences[:target_sentence_count])} sentences")

            return final_summary.strip() if final_summary else "Summarization failed."
        except Exception as e:
          logger.error(f"Error during abstractive summarization: {e}")
        return f"Summarization error: {e}"