# scripts/ingest_docs.py
"""
Sample script to ingest knowledge into Pathfinder AI.
Run this to populate your vector database with sample data.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag.knowledge_manager import get_knowledge_manager


def ingest_sample_data():
    """Ingest sample marketing knowledge."""
    km = get_knowledge_manager()
    
    print("=" * 60)
    print("Ingesting Sample Knowledge into Pathfinder AI")
    print("=" * 60)
    print()
    
    # ── Sample Trend Data ──────────────────────────────────
    trend_1 = """
    AI-Powered Personalization in Marketing (2024-2025)
    
    The adoption of AI-powered personalization tools has accelerated dramatically.
    67% of marketers report improved email open rates when using dynamic content
    based on user behavior signals. Key applications include:
    
    - Personalized email subject lines and content blocks
    - Dynamic website experiences based on browsing history
    - Predictive product recommendations
    - Real-time ad creative optimization
    
    However, Gen Z audiences (72%) express privacy concerns and prefer transparency
    about data usage. Brands that clearly communicate their data practices see
    35% higher engagement rates.
    
    ROI Impact: Companies implementing AI personalization report average 15-25%
    increase in conversion rates and 20% improvement in customer lifetime value.
    """
    
    km.ingest_document(
        content=trend_1,
        doc_type="trends",
        metadata={
            "source": "Marketing Technology Trends Report 2024",
            "industry": "marketing",
            "geography": "global",
            "audience": "marketers",
            "campaign_type": "digital",
            "date": "2024-Q4"
        }
    )
    
    trend_2 = """
    Short-Form Video Dominance (2024-2025)
    
    Short-form video (under 60 seconds) now accounts for 82% of all consumer
    internet traffic. TikTok, Instagram Reels, and YouTube Shorts drive this trend.
    
    Key findings:
    - Average engagement rate: 5.3% (vs 1.2% for static images)
    - Optimal length: 15-30 seconds for maximum completion rates
    - User-generated content (UGC) style performs 3x better than polished ads
    - Sound-on viewing has increased to 65% (up from 45% in 2023)
    
    Brands successfully leveraging this format see 40% lower customer acquisition
    costs compared to traditional display advertising.
    """
    
    km.ingest_document(
        content=trend_2,
        doc_type="trends",
        metadata={
            "source": "Social Media Marketing Benchmark Study 2024",
            "industry": "social_media",
            "geography": "global",
            "audience": "consumers",
            "campaign_type": "social",
            "date": "2024-Q3"
        }
    )
    
    # ── Sample Case Study ──────────────────────────────────
    case_1 = """
    Nike 'You Can't Stop Us' Campaign (2020)
    
    Objective: Unite athletes and sports fans during pandemic isolation
    
    Strategy:
    - Split-screen video technique showing 53 athletes in perfect synchronicity
    - Emphasized shared human experience across all sports and backgrounds
    - Leveraged Nike's archive footage (4000+ hours reviewed)
    - Message: Sport unites us, isolation can't stop us
    
    Execution:
    - 90-second hero film
    - Launched across TV, social media, and digital platforms
    - Minimal text, emotion-driven storytelling
    
    Results:
    - 80+ million views in first week
    - 6% increase in brand favorability scores
    - 15% increase in Nike Training Club app downloads
    - Won multiple creative awards (Cannes Lions Grand Prix)
    
    Key Learning: Authentic emotional connection + technical innovation resonates
    deeply. The split-screen technique was not just creative but symbolic of unity.
    """
    
    km.ingest_document(
        content=case_1,
        doc_type="case_studies",
        metadata={
            "source": "Campaign Case Study Archive",
            "industry": "sportswear",
            "geography": "global",
            "audience": "athletes",
            "campaign_type": "brand_awareness",
            "date": "2020",
            "brand": "Nike"
        }
    )
    
    case_2 = """
    Spotify Wrapped (Annual Campaign)
    
    Objective: Drive user engagement and social sharing at year-end
    
    Strategy:
    - Personalized data visualization of each user's listening habits
    - Gamified experience with shareable social cards
    - Creates FOMO and encourages non-users to sign up
    
    Execution:
    - Available in-app for 2 weeks each December
    - Unique shareable graphics for each user
    - Amplified by influencers and celebrities sharing their own Wrapped
    
    Results (2023):
    - 156 million users engaged with Wrapped
    - #SpotifyWrapped trended globally for 5 consecutive days
    - 425 million social shares
    - 21% increase in new subscriber sign-ups in December
    
    Key Learning: Data personalization + social shareability = viral growth.
    Users become brand ambassadors when the experience is uniquely theirs.
    """
    
    km.ingest_document(
        content=case_2,
        doc_type="case_studies",
        metadata={
            "source": "Digital Campaign Best Practices 2023",
            "industry": "music_streaming",
            "geography": "global",
            "audience": "music_listeners",
            "campaign_type": "engagement",
            "date": "2023",
            "brand": "Spotify"
        }
    )
    
    # ── Sample Market Research ─────────────────────────────
    research_1 = """
    Gen Z Purchase Behavior Study (2024)
    
    Key Findings:
    
    1. Brand Values Matter: 73% of Gen Z consumers actively research brand
       values before purchase. Top priorities:
       - Sustainability and environmental impact (81%)
       - Diversity and inclusion (76%)
       - Transparent supply chains (68%)
    
    2. Social Proof Over Traditional Ads: 
       - 85% trust peer reviews and UGC over brand advertising
       - Influencer recommendations drive 62% of purchase decisions
       - Micro-influencers (10K-100K followers) seen as more authentic than celebrities
    
    3. Platform Preferences:
       - TikTok and Instagram primary discovery platforms (79%)
       - YouTube for product research and tutorials (71%)
       - Facebook declining rapidly (only 23% active daily usage)
    
    4. Price Sensitivity vs Values:
       - 68% willing to pay 10-20% premium for sustainable products
       - 54% prefer second-hand/vintage over fast fashion
       - Buy-now-pay-later adoption: 45% use regularly
    
    Implications for Marketers:
    - Lead with values, not just product features
    - Invest in authentic creator partnerships
    - Prioritize TikTok and Instagram for discovery
    - Transparency in messaging is non-negotiable
    """
    
    km.ingest_document(
        content=research_1,
        doc_type="market_research",
        metadata={
            "source": "Gen Z Consumer Insights Report 2024",
            "industry": "consumer_goods",
            "geography": "US",
            "audience": "gen_z",
            "campaign_type": "research",
            "date": "2024-Q2"
        }
    )
    
    print()
    print("=" * 60)
    print("Sample Data Ingestion Complete!")
    print("=" * 60)
    print()
    print("Collection Statistics:")
    stats = km.get_collection_stats()
    for collection, count in stats.items():
        print(f"  {collection:20s}: {count:3d} chunks")
    print()


if __name__ == "__main__":
    ingest_sample_data()