"""
load_indian_laws.py — Bulk Load Indian Legal Documents into RAG System
This script loads Indian legal texts (IPC, CrPC, Constitution, etc.) into the RAG vector database
"""

import os
import sys
import logging
from pathlib import Path
from rag_module.rag_engine import LegalRAG

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class IndianLawLoader:
    """Load Indian legal corpus into RAG system."""
    
    def __init__(self):
        self.rag = LegalRAG()
        self.laws_directory = "data/indian_laws"
        os.makedirs(self.laws_directory, exist_ok=True)
    
    def load_text_file(self, file_path):
        """Load text from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None
    
    def load_all_laws(self):
        """Load all legal documents from the indian_laws directory."""
        laws_path = Path(self.laws_directory)
        
        if not laws_path.exists():
            logger.error(f"Directory not found: {self.laws_directory}")
            logger.info("Please create this directory and add your legal documents.")
            return
        
        # Find all text and PDF files
        files = list(laws_path.glob("**/*.txt")) + list(laws_path.glob("**/*.pdf"))
        
        if not files:
            logger.warning(f"No files found in {self.laws_directory}")
            logger.info("\nPlease add legal documents in the following format:")
            logger.info("  - IPC_sections.txt (Indian Penal Code)")
            logger.info("  - CrPC_sections.txt (Criminal Procedure Code)")
            logger.info("  - Constitution_of_India.txt")
            logger.info("  - Indian_Evidence_Act.txt")
            logger.info("  - etc.")
            return
        
        logger.info(f"📚 Found {len(files)} legal documents to load")
        
        successful = 0
        failed = 0
        
        for file_path in files:
            logger.info(f"\n📄 Processing: {file_path.name}")
            
            try:
                if file_path.suffix == '.txt':
                    text = self.load_text_file(file_path)
                elif file_path.suffix == '.pdf':
                    text = self.extract_text_from_pdf(file_path)
                else:
                    logger.warning(f"Unsupported file type: {file_path.suffix}")
                    continue
                
                if text and len(text.strip()) > 100:
                    success = self.rag.add_document(text, filename=file_path.name)
                    if success:
                        logger.info(f"✅ Successfully loaded: {file_path.name}")
                        successful += 1
                    else:
                        logger.error(f"❌ Failed to load: {file_path.name}")
                        failed += 1
                else:
                    logger.warning(f"⚠️ Skipped (too short): {file_path.name}")
                    failed += 1
                    
            except Exception as e:
                logger.error(f"❌ Error processing {file_path.name}: {e}")
                failed += 1
        
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 LOADING SUMMARY:")
        logger.info(f"   ✅ Successful: {successful}")
        logger.info(f"   ❌ Failed: {failed}")
        logger.info(f"   📚 Total documents in RAG: {len(self.rag.documents)}")
        logger.info(f"{'='*60}")
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF files."""
        try:
            import fitz  # PyMuPDF
            text = ""
            with fitz.open(pdf_path) as doc:
                for page in doc:
                    text += page.get_text()
            return text
        except ImportError:
            logger.error("PyMuPDF not installed. Install with: pip install PyMuPDF")
            return None
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return None
    
    def load_sample_ipc_sections(self):
        """Load sample IPC sections (for testing)."""
        logger.info("\n📝 Loading sample IPC sections for testing...")
        
        sample_ipc = """
INDIAN PENAL CODE - KEY SECTIONS

Section 302 IPC - Punishment for Murder: Whoever commits murder shall be punished with death or imprisonment for life, and shall also be liable to fine. This is one of the most serious offences under the Indian Penal Code.

Section 304 IPC - Punishment for Culpable Homicide Not Amounting to Murder: Whoever commits culpable homicide not amounting to murder shall be punished with imprisonment for life, or imprisonment of either description for a term which may extend to ten years, and shall also be liable to fine, if the act by which the death is caused is done with the intention of causing death, or of causing such bodily injury as is likely to cause death. This section deals with cases where there is intention to cause death but without premeditation that constitutes murder.

Section 376 IPC - Punishment for Rape: Whoever, except in the cases provided for in sub-section (2), commits rape, shall be punished with rigorous imprisonment of either description for a term which shall not be less than ten years, but which may extend to imprisonment for life, and shall also be liable to fine. This is a serious sexual offence under Indian criminal law.

Section 420 IPC - Cheating and Dishonestly Inducing Delivery of Property: Whoever cheats and thereby dishonestly induces the person deceived to deliver any property to any person, or to make, alter or destroy the whole or any part of a valuable security, or anything which is signed or sealed, and which is capable of being converted into a valuable security, shall be punished with imprisonment of either description for a term which may extend to seven years, and shall also be liable to fine. This section deals with fraud and cheating offences.

Section 498A IPC - Husband or Relative of Husband Subjecting Woman to Cruelty: Whoever, being the husband or the relative of the husband of a woman, subjects such woman to cruelty shall be punished with imprisonment for a term which may extend to three years and shall also be liable to fine. Cruelty includes both physical and mental harassment. This is a cognizable and non-bailable offence.

Section 323 IPC - Punishment for Voluntarily Causing Hurt: Whoever, except in the case provided for by section 334, voluntarily causes hurt, shall be punished with imprisonment of either description for a term which may extend to one year, or with fine which may extend to one thousand rupees, or with both. This covers simple hurt or injury caused to another person.

Section 379 IPC - Punishment for Theft: Whoever commits theft shall be punished with imprisonment of either description for a term which may extend to three years, or with fine, or with both. Theft is defined as dishonestly taking movable property out of the possession of another person without their consent.

Section 406 IPC - Punishment for Criminal Breach of Trust: Whoever commits criminal breach of trust shall be punished with imprisonment of either description for a term which may extend to three years, or with fine, or with both. This applies when someone entrusted with property dishonestly misappropriates it or converts it to their own use.
"""
        
        success = self.rag.add_document(sample_ipc, filename="IPC_Sample_Sections.txt")
        if success:
            logger.info("✅ Sample IPC sections loaded successfully")
        else:
            logger.error("❌ Failed to load sample IPC sections")


def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("🇮🇳 INDIAN LAW KNOWLEDGE BASE LOADER")
    logger.info("=" * 60)
    
    loader = IndianLawLoader()
    
    # Check if user wants to load sample data
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        logger.info("\n📝 Loading sample data for testing...")
        loader.load_sample_ipc_sections()
    else:
        # Load all documents from the directory
        loader.load_all_laws()
    
    logger.info("\n✅ Knowledge base loading complete!")
    logger.info("💡 Your RAG system can now answer questions about Indian laws.")


if __name__ == "__main__":
    main()
