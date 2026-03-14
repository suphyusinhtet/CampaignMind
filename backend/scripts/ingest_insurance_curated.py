"""
Ingest curated insurance-focused knowledge for better Trend/Case/Landscape outputs.

Usage:
  cd backend
  python scripts/ingest_insurance_curated.py
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from rag.knowledge_manager import get_knowledge_manager


def ingest_curated_insurance_data():
    km = get_knowledge_manager()

    docs = [
        (
            "trends",
            """
            Digital & Social Trends in Car Insurance (Europe, 2024-2025)

            Trend 1: Social video dominance for insurance awareness.
            TikTok and YouTube are leading awareness channels for younger insurance shoppers.
            Short-form video explainers perform best when they simplify policy choices.

            Trend 2: Search behavior favors plain-language terms.
            Search demand clusters around "car insurance", "insurance quote", and "cheap car insurance";
            complex fintech terminology has lower user intent in mass market segments.

            Trend 3: Digital self-service expectations.
            Customers increasingly expect quote-to-purchase digital journeys, transparent coverage
            comparisons, and app-based policy management.
            """,
            {
                "source": "Insurance Digital Behavior Brief 2025",
                "industry": "insurance",
                "geography": "Europe",
                "audience": "car_insurance_customers",
                "campaign_type": "awareness",
                "date": "2025-Q1",
            },
        ),
        (
            "trends",
            """
            Car Insurance Media Patterns (Europe, 2024)

            - Paid social reach is strongest when paired with search retargeting.
            - Video creative with concrete proof points (price clarity, response speed, claims support)
              outperforms generic brand-led ads.
            - Trust markers (review counts, claims service evidence, transparent exclusions)
              materially increase click-to-quote rates.
            """,
            {
                "source": "European Insurance Media Benchmark 2024",
                "industry": "insurance",
                "geography": "Europe",
                "audience": "digital_first_drivers",
                "campaign_type": "performance_marketing",
                "date": "2024-Q4",
            },
        ),
        (
            "case_studies",
            """
            Allianz - Motor Awareness Campaign (EU)

            Objective: Increase top-of-funnel awareness for digital-first motor insurance.
            Strategy: Short-form social video, creator explainers, and quote-journey optimization.
            Learning: Creative that explains coverage differences clearly drives higher qualified traffic.
            """,
            {
                "source": "Brand News",
                "industry": "insurance",
                "geography": "Europe",
                "audience": "young_drivers",
                "campaign_type": "awareness",
                "date": "2024",
                "brand": "Allianz",
            },
        ),
        (
            "case_studies",
            """
            Zurich - "We don't just cover. We care."

            Objective: Build trust and emotional preference in a commoditized insurance market.
            Strategy: Multi-channel storytelling across digital, social, and TV with customer-first narratives.
            Learning: Emotional trust framing can differentiate when product features are similar.
            """,
            {
                "source": "Engage",
                "industry": "insurance",
                "geography": "Global",
                "audience": "mass_market",
                "campaign_type": "brand_awareness",
                "date": "2024",
                "brand": "Zurich",
            },
        ),
        (
            "case_studies",
            """
            Linear Assicurazioni - Chatbot for Social Quotes

            Objective: Reduce quote friction and increase social lead capture.
            Strategy: Social chatbot flow for instant quote discovery and qualification.
            Product Features Highlighted: instant quote flow, digital self-service, support escalation.
            Learning: Conversational quote journeys improve response speed perception.
            """,
            {
                "source": "Brand News",
                "industry": "insurance",
                "geography": "Italy",
                "audience": "digital_first_drivers",
                "campaign_type": "lead_generation",
                "date": "2024",
                "brand": "Linear",
            },
        ),
        (
            "case_studies",
            """
            Verti - Data-Driven Digital Awareness Program

            Objective: Improve awareness and policy subscriptions in digital channels.
            Strategy: Data-led audience segmentation with targeted social and search campaigns.
            Product Features Highlighted: modular cover options, flexible purchase journey.
            Learning: Segment-specific creative lifts quote intent versus one-size-fits-all messaging.
            """,
            {
                "source": "Brand News",
                "industry": "insurance",
                "geography": "Italy",
                "audience": "price_sensitive_drivers",
                "campaign_type": "awareness",
                "date": "2024",
                "brand": "Verti",
            },
        ),
        (
            "market_research",
            """
            Italy Car Insurance Competitor Snapshot (Digital-First Segment)

            Competitors: Genertel, Linear, Verti, Prima, Quixa.
            Typical product mix: third-party only, third-party fire and theft, fully comprehensive, optional breakdown.
            Core digital features: instant quote, app policy management, online claims tracking, modular add-ons.
            Common positioning: convenience, speed, affordability, flexibility.
            """,
            {
                "source": "Italian Motor Insurance Competitive Snapshot 2025",
                "industry": "insurance",
                "geography": "Italy",
                "audience": "b2c_drivers",
                "campaign_type": "landscape",
                "date": "2025-Q1",
            },
        ),
        (
            "market_research",
            """
            Product Feature and Distribution Patterns in Italian Auto Insurance

            Distribution model:
            - Digital-first insurers rely on direct online/app acquisition.
            - Incumbents combine agent networks with digital servicing.

            Product feature patterns:
            - parity on baseline coverage tiers;
            - differentiation via UX quality, quote speed, claims confidence messaging,
              telematics options, and partnership add-ons.
            """,
            {
                "source": "Italy Auto Insurance Feature Benchmark 2024",
                "industry": "insurance",
                "geography": "Italy",
                "audience": "car_owners",
                "campaign_type": "product_strategy",
                "date": "2024-Q4",
            },
        ),
        (
            "market_research",
            """
            Car Insurance Positioning Landscape (Europe)

            Most insurers cluster around:
            - price competitiveness
            - broad coverage messaging
            - convenience claims

            Whitespace opportunities:
            - transparent coverage education
            - claims journey confidence and speed proof
            - personalization with explicit data transparency
            """,
            {
                "source": "European Motor Insurance Landscape 2025",
                "industry": "insurance",
                "geography": "Europe",
                "audience": "car_owners",
                "campaign_type": "landscape",
                "date": "2025-Q1",
            },
        ),
    ]

    total_chunks = 0
    for doc_type, content, metadata in docs:
        total_chunks += km.ingest_document(content=content, doc_type=doc_type, metadata=metadata)

    print(f"Ingested insurance curated data. Total chunks: {total_chunks}")
    print("Collection stats:", km.get_collection_stats())


if __name__ == "__main__":
    ingest_curated_insurance_data()
