"""
Test script for evaluation metrics
Demonstrates how to evaluate summary quality
"""

import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from nlp_module.evaluation_metrics import quick_evaluate, SummarizationEvaluator

# Sample legal text
sample_original = """
The High Court of Karnataka heard the case of State v. Kumar on January 15, 2023.
The appellant was charged under Section 302 of the Indian Penal Code for murder.
The Court examined the evidence presented by the prosecution, including witness testimonies
and forensic reports. After careful consideration, the Court held that the prosecution
failed to establish the guilt of the accused beyond reasonable doubt. The Court observed
that the evidence was circumstantial and insufficient. Consequently, the appellant was
acquitted of all charges. The judgment was delivered by Justice Ramesh Kumar on March 10, 2023.
"""

sample_summary = """
The High Court of Karnataka acquitted Kumar in a murder case under Section 302 IPC.
The Court held that prosecution evidence was circumstantial and insufficient to prove
guilt beyond reasonable doubt. Justice Ramesh Kumar delivered the judgment on March 10, 2023.
"""

def test_basic_evaluation():
    """Test basic evaluation without reference summary."""
    print("=" * 70)
    print("BASIC EVALUATION TEST (Without Reference Summary)")
    print("=" * 70)
    
    results = quick_evaluate(sample_original, sample_summary)
    
    print("\n📊 EVALUATION RESULTS:\n")
    
    # Overall Quality Score
    print(f"🎯 Overall Quality Score: {results['overall_quality_score']}/100")
    print("-" * 70)
    
    # Compression Stats
    print("\n📉 Compression Analysis:")
    comp = results['compression']
    print(f"  • Original Words: {comp['original_words']}")
    print(f"  • Summary Words: {comp['summary_words']}")
    print(f"  • Compression Ratio: {comp['compression_ratio']}")
    print(f"  • Compression: {comp['compression_percentage']}%")
    
    # Coherence
    print(f"\n🔗 Coherence Score: {results['coherence']}")
    
    # Entity Coverage
    print("\n👥 Entity Coverage:")
    ent = results['entity_coverage']
    print(f"  • Preservation Rate: {ent['entity_preservation']}")
    print(f"  • Entities Preserved: {ent['entities_preserved']}/{ent['entities_total']}")
    if 'preserved_entities' in ent:
        print(f"  • Examples: {', '.join(ent['preserved_entities'][:5])}")
    
    # Keyword Coverage
    print("\n🔑 Legal Keyword Coverage:")
    kw = results['keyword_coverage']
    print(f"  • Coverage Rate: {kw['keyword_coverage']}")
    print(f"  • Keywords Preserved: {kw['keywords_preserved']}/{kw['keywords_total']}")
    
    print("\n" + "=" * 70)
    return results


def test_full_evaluation():
    """Test evaluation with reference summary."""
    print("\n" + "=" * 70)
    print("FULL EVALUATION TEST (With Reference Summary)")
    print("=" * 70)
    
    # Gold standard reference summary
    reference_summary = """
    The High Court of Karnataka acquitted the appellant Kumar in the murder case
    under Section 302 IPC. The prosecution evidence was found to be circumstantial
    and insufficient. The judgment was delivered on March 10, 2023 by Justice Ramesh Kumar.
    """
    
    evaluator = SummarizationEvaluator()
    results = evaluator.evaluate_summary(
        sample_original, 
        sample_summary, 
        reference_summary
    )
    
    print("\n📊 COMPREHENSIVE EVALUATION RESULTS:\n")
    
    # Overall Score
    print(f"🎯 Overall Quality Score: {results['overall_quality_score']}/100")
    print("-" * 70)
    
    # ROUGE Scores
    if 'rouge_scores' in results:
        print("\n📈 ROUGE Scores:")
        rouge = results['rouge_scores']
        print(f"  • ROUGE-1 F1: {rouge['rouge1']['f1']}")
        print(f"  • ROUGE-2 F1: {rouge['rouge2']['f1']}")
        print(f"  • ROUGE-L F1: {rouge['rougeL']['f1']}")
        print(f"  • Average F1: {rouge['average_f1']}")
    
    # Semantic Similarity
    if 'semantic_similarity' in results:
        print(f"\n🧬 Semantic Similarity: {results['semantic_similarity']}")
    
    # Other metrics
    print(f"\n🔗 Coherence: {results['coherence']}")
    print(f"👥 Entity Preservation: {results['entity_coverage']['entity_preservation']}")
    print(f"🔑 Keyword Coverage: {results['keyword_coverage']['keyword_coverage']}")
    
    print("\n" + "=" * 70)
    return results


def test_quality_interpretation():
    """Interpret quality scores."""
    print("\n" + "=" * 70)
    print("QUALITY SCORE INTERPRETATION")
    print("=" * 70)
    
    results = quick_evaluate(sample_original, sample_summary)
    score = results['overall_quality_score']
    
    print(f"\nYour Quality Score: {score}/100\n")
    
    if score >= 80:
        rating = "Excellent ⭐⭐⭐⭐⭐"
        comment = "Outstanding summary quality with high accuracy and coherence."
    elif score >= 70:
        rating = "Very Good ⭐⭐⭐⭐"
        comment = "High quality summary with good preservation of key information."
    elif score >= 60:
        rating = "Good ⭐⭐⭐"
        comment = "Acceptable summary quality, some improvements possible."
    elif score >= 50:
        rating = "Fair ⭐⭐"
        comment = "Summary needs improvement in accuracy or completeness."
    else:
        rating = "Poor ⭐"
        comment = "Summary quality is low, significant improvements needed."
    
    print(f"Rating: {rating}")
    print(f"Assessment: {comment}")
    
    # Recommendations
    print("\n💡 Recommendations:")
    
    if results['entity_coverage']['entity_preservation'] < 0.7:
        print("  • Improve entity preservation (aim for >0.70)")
    
    if results['coherence'] < 0.75:
        print("  • Enhance summary coherence (aim for >0.75)")
    
    if results['keyword_coverage']['keyword_coverage'] < 0.6:
        print("  • Include more critical legal keywords")
    
    if results['compression']['compression_ratio'] > 0.6:
        print("  • Consider more aggressive compression")
    elif results['compression']['compression_ratio'] < 0.3:
        print("  • Summary might be too compressed, add more detail")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    print("\n🧪 LEGAL SUMMARIZATION EVALUATION METRICS TEST\n")
    
    try:
        # Test 1: Basic evaluation
        print("Test 1: Running basic evaluation...")
        test_basic_evaluation()
        
        # Test 2: Full evaluation with reference
        print("\nTest 2: Running full evaluation with reference...")
        test_full_evaluation()
        
        # Test 3: Quality interpretation
        print("\nTest 3: Interpreting quality scores...")
        test_quality_interpretation()
        
        print("\n✅ All tests completed successfully!")
        print("\n💡 Usage in your code:")
        print("="*70)
        print("""
from nlp_module.evaluation_metrics import quick_evaluate

# Evaluate your summary
results = quick_evaluate(original_text, generated_summary)
print(f"Quality Score: {results['overall_quality_score']}/100")

# Check specific metrics
print(f"Entity Preservation: {results['entity_coverage']['entity_preservation']}")
print(f"Coherence: {results['coherence']}")
        """)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        print("\nMake sure you have installed: pip install rouge-score")
        import traceback
        traceback.print_exc()
