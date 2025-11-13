"""
download_laws.py — Helper script to download Indian legal documents
This script provides utilities to fetch legal documents from official sources
"""

import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class LegalDocumentDownloader:
    """Helper class to guide downloading Indian legal documents."""
    
    def __init__(self):
        self.base_dir = Path("../data/indian_laws")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Official sources and their download links
        self.documents = {
            "criminal_law": {
                "IPC_Full": {
                    "name": "Indian Penal Code (IPC) - 1860",
                    "url": "https://www.indiacode.nic.in/handle/123456789/2263?sam_handle=123456789/1362",
                    "alternative_url": "https://legislative.gov.in/sites/default/files/A1860-45.pdf",
                    "priority": 1
                },
                "CrPC_1973": {
                    "name": "Code of Criminal Procedure (CrPC) - 1973",
                    "url": "https://www.indiacode.nic.in/handle/123456789/2279?sam_handle=123456789/1362",
                    "priority": 1
                },
                "Evidence_Act_1872": {
                    "name": "Indian Evidence Act - 1872",
                    "url": "https://www.indiacode.nic.in/handle/123456789/2188?sam_handle=123456789/1362",
                    "priority": 2
                }
            },
            "constitutional_law": {
                "Constitution_of_India": {
                    "name": "Constitution of India",
                    "url": "https://legislative.gov.in/constitution-of-india/",
                    "priority": 1
                }
            },
            "civil_law": {
                "CPC_1908": {
                    "name": "Code of Civil Procedure (CPC) - 1908",
                    "url": "https://www.indiacode.nic.in/handle/123456789/2191?sam_handle=123456789/1362",
                    "priority": 2
                },
                "Contract_Act_1872": {
                    "name": "Indian Contract Act - 1872",
                    "url": "https://www.indiacode.nic.in/handle/123456789/2187?sam_handle=123456789/1362",
                    "priority": 2
                },
                "Companies_Act_2013": {
                    "name": "Companies Act - 2013",
                    "url": "https://www.indiacode.nic.in/handle/123456789/2114?sam_handle=123456789/1362",
                    "priority": 3
                }
            },
            "special_acts": {
                "IT_Act_2000": {
                    "name": "Information Technology Act - 2000",
                    "url": "https://www.indiacode.nic.in/handle/123456789/1999?sam_handle=123456789/1362",
                    "priority": 2
                },
                "POCSO_Act_2012": {
                    "name": "POCSO Act - 2012",
                    "url": "https://www.indiacode.nic.in/handle/123456789/2079?sam_handle=123456789/1362",
                    "priority": 3
                },
                "Domestic_Violence_Act_2005": {
                    "name": "Domestic Violence Act - 2005",
                    "url": "https://www.indiacode.nic.in/handle/123456789/2045?sam_handle=123456789/1362",
                    "priority": 3
                }
            }
        }
    
    def show_download_instructions(self):
        """Display comprehensive download instructions."""
        logger.info("=" * 70)
        logger.info("📥 INDIAN LEGAL DOCUMENTS DOWNLOAD GUIDE")
        logger.info("=" * 70)
        logger.info("")
        logger.info("📂 Folder structure created at: data/indian_laws/")
        logger.info("")
        logger.info("🎯 PRIORITY DOWNLOADS (Start with these):")
        logger.info("")
        
        priority_1 = []
        for category, docs in self.documents.items():
            for doc_id, info in docs.items():
                if info.get("priority") == 1:
                    priority_1.append((category, doc_id, info))
        
        for i, (category, doc_id, info) in enumerate(priority_1, 1):
            logger.info(f"{i}. {info['name']}")
            logger.info(f"   📁 Save to: data/indian_laws/{category}/{doc_id}.txt (or .pdf)")
            logger.info(f"   🔗 URL: {info['url']}")
            if 'alternative_url' in info:
                logger.info(f"   🔗 Alternative: {info['alternative_url']}")
            logger.info("")
        
        logger.info("=" * 70)
        logger.info("📋 COMPLETE DOCUMENT LIST:")
        logger.info("=" * 70)
        
        for category, docs in self.documents.items():
            logger.info(f"\n📂 {category.upper().replace('_', ' ')}")
            logger.info("-" * 70)
            for doc_id, info in docs.items():
                priority_star = "⭐" * info.get("priority", 1)
                logger.info(f"\n  {priority_star} {info['name']}")
                logger.info(f"  📄 Filename: {doc_id}.txt or {doc_id}.pdf")
                logger.info(f"  🔗 {info['url']}")
        
        logger.info("\n" + "=" * 70)
        logger.info("📖 HOW TO DOWNLOAD:")
        logger.info("=" * 70)
        logger.info("""
1. Visit each URL in your web browser
2. Download the PDF or copy the text
3. Save files in the appropriate folders:
   - data/indian_laws/criminal_law/
   - data/indian_laws/civil_law/
   - data/indian_laws/constitutional_law/
   - data/indian_laws/special_acts/

4. Files can be either:
   ✅ .txt format (better accuracy)
   ✅ .pdf format (supported directly)

5. After downloading, run:
   cd backend
   python load_indian_laws.py
        """)
        
        logger.info("=" * 70)
        logger.info("💡 QUICK TIP:")
        logger.info("=" * 70)
        logger.info("""
If links don't work directly:
1. Go to https://www.indiacode.nic.in/
2. Search for the act name
3. Download from search results
        """)
        
        logger.info("=" * 70)
        logger.info("✅ NEXT STEPS:")
        logger.info("=" * 70)
        logger.info("""
1. Download at least the Priority 1 documents (IPC, CrPC, Constitution)
2. Save them in the correct folders
3. Run: python load_indian_laws.py
4. Test your RAG system!
        """)
    
    def check_downloaded_files(self):
        """Check which files have been downloaded."""
        logger.info("\n" + "=" * 70)
        logger.info("📊 CHECKING DOWNLOADED FILES...")
        logger.info("=" * 70)
        
        total_files = 0
        found_files = []
        missing_files = []
        
        for category, docs in self.documents.items():
            category_path = self.base_dir / category
            category_path.mkdir(exist_ok=True)
            
            for doc_id, info in docs.items():
                # Check for both .txt and .pdf
                txt_file = category_path / f"{doc_id}.txt"
                pdf_file = category_path / f"{doc_id}.pdf"
                
                total_files += 1
                
                if txt_file.exists():
                    found_files.append((category, doc_id, "txt", info['name']))
                    logger.info(f"✅ Found: {category}/{doc_id}.txt")
                elif pdf_file.exists():
                    found_files.append((category, doc_id, "pdf", info['name']))
                    logger.info(f"✅ Found: {category}/{doc_id}.pdf")
                else:
                    missing_files.append((category, doc_id, info['name']))
        
        logger.info("\n" + "=" * 70)
        logger.info(f"📈 SUMMARY: {len(found_files)}/{total_files} documents downloaded")
        logger.info("=" * 70)
        
        if missing_files:
            logger.info("\n⚠️  MISSING DOCUMENTS:")
            for category, doc_id, name in missing_files:
                logger.info(f"  ❌ {name}")
                logger.info(f"     Expected at: data/indian_laws/{category}/{doc_id}.txt or .pdf")
        
        if found_files:
            logger.info("\n✅ You can now load these documents by running:")
            logger.info("   cd backend")
            logger.info("   python load_indian_laws.py")
        
        return len(found_files), total_files


def main():
    """Main function."""
    downloader = LegalDocumentDownloader()
    
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        # Check what's been downloaded
        found, total = downloader.check_downloaded_files()
        if found == 0:
            logger.info("\n💡 No files found. Use this script without --check to see download instructions.")
    else:
        # Show download instructions
        downloader.show_download_instructions()
        
        # Also check current status
        logger.info("\n" + "=" * 70)
        found, total = downloader.check_downloaded_files()


if __name__ == "__main__":
    main()
