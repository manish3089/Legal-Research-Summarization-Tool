"""
Create a clean test PDF from text file and optionally test the system.
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os

def create_legal_pdf(text_file, output_pdf):
    """Convert text file to clean PDF."""
    
    # Read text
    with open(text_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF
    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor='black',
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor='black',
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor='black',
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    # Build document
    story = []
    
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 0.1 * inch))
            continue
        
        # Title (all caps lines)
        if line.isupper() and len(line) < 50:
            story.append(Paragraph(line, title_style))
        
        # Section headings (lines ending with colon or short capitalized)
        elif line.endswith(':') or (line[0].isupper() and len(line.split()) <= 5):
            story.append(Paragraph(line, heading_style))
        
        # Body text
        else:
            # Escape special characters for reportlab
            line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(line, body_style))
    
    # Generate PDF
    doc.build(story)
    print(f"✅ PDF created: {output_pdf}")

if __name__ == "__main__":
    text_file = "test_legal_case.txt"
    output_pdf = "test_legal_case_clean.pdf"
    
    if os.path.exists(text_file):
        create_legal_pdf(text_file, output_pdf)
        print(f"\n📄 Clean test PDF ready: {output_pdf}")
        print("\n🧪 Next steps:")
        print("1. Upload 'test_legal_case_clean.pdf' in the Streamlit app")
        print("2. Check if summary is clean and readable")
        print("3. Test RAG with questions like:")
        print("   - 'What is this case about?'")
        print("   - 'What compensation was awarded?'")
        print("   - 'What were the legal issues?'")
    else:
        print(f"❌ Text file not found: {text_file}")
