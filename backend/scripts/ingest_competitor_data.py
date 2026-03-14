# scripts/ingest_competitor_data.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.knowledge_manager import get_knowledge_manager

def ingest_competitor_data():
    km = get_knowledge_manager()
    
    # Italian Car Insurance Competitors (from your screenshot)
    competitors = [
        {
            "company": "Genertel",
            "product": "Genertel Auto",
            "industry": "insurance",
            "geography": "Italy",
            "segment": "Car, B2C, digital-first, price-sensitive, tech-savvy",
            "distribution": "Direct (Online, App)",
            "summary": "Digital-first, low-cost, flexible car insurance with app-based management",
            "strategic_focus": "Direct digital convenience, price leadership",
            "content": """Genertel - Italian Car Insurance Competitor Analysis
            
Company: Genertel
Product: Genertel Auto
Market: Italy, Digital Car Insurance

Target Segments:
- B2C customers
- Digital-first consumers
- Price-sensitive buyers
- Tech-savvy users

Distribution Model:
- Direct sales (Online)
- Mobile app platform
- No intermediaries

Product Offering:
- Third-party only car insurance
- Third-party fire and theft
- Fully comprehensive coverage
- Optional breakdown cover

Strategic Positioning:
- Digital-first approach
- Low-cost pricing strategy
- Flexible coverage options
- App-based policy management
- Instant online quotes
- Self-service customer experience

Key Differentiators:
- Pure digital player (no physical branches)
- Price competitive
- Strong mobile app experience
- Quick quote and purchase process

Competitive Advantages:
- Lower operational costs due to digital model
- Fast customer acquisition
- High price transparency
- Easy policy management through app

Target Customer Profile:
- Age: 25-45 years
- Tech-savvy
- Comfortable with online transactions
- Price-conscious
- Values convenience over personal service
"""
        },
        {
            "company": "Linear",
            "product": "Linear RC Auto",
            "industry": "insurance",
            "geography": "Italy",
            "segment": "Car, B2C, digital, price-sensitive",
            "distribution": "Direct (Online)",
            "summary": "Online only, simple and customizable car insurance",
            "strategic_focus": "Digital efficiency, price-sensitive segment",
            "content": """Linear - Italian Car Insurance Competitor Analysis
            
Company: Linear
Product: Linear RC Auto
Market: Italy, Digital Car Insurance

Strategic Summary:
Online-only, simple and customizable car insurance targeting price-sensitive digital customers

Distribution Model:
- 100% Direct online sales
- No physical branches
- No agent network

Product Features:
- Simplified product offering
- Customizable coverage levels
- Third-party liability
- Optional add-ons (fire, theft, comprehensive)
- Pay-per-kilometer options

Target Customers:
- Price-sensitive consumers
- Digital natives
- Low-mileage drivers
- Urban residents

Competitive Strategy:
- Extreme price focus
- Minimal overhead costs
- Simplified customer experience
- Fast online quote process

Strengths:
- Highly competitive pricing
- Simple, transparent product structure
- Quick purchase process
- Digital efficiency

Market Positioning:
- Value brand
- No-frills insurance
- Digital convenience
- Transparent pricing
"""
        },
        {
            "company": "Verti",
            "product": "Verti Auto",
            "industry": "insurance",
            "geography": "Italy",
            "segment": "Car, B2C, digital, flexible payers",
            "distribution": "Direct (Online, App)",
            "summary": "Fully digital, flexible payment, strong on digital marketing",
            "strategic_focus": "Digital innovation, flexible offers",
            "content": """Verti - Italian Car Insurance Competitor Analysis

Company: Verti
Product: Verti Auto
Market: Italy, Digital Car Insurance

Strategic Summary:
Fully digital car insurance with innovative payment flexibility and strong digital marketing presence

Distribution:
- Direct online platform
- Mobile app
- Digital-first customer journey

Innovation Focus:
- Flexible payment options
- Monthly/quarterly/annual payments
- Pay-per-kilometer programs
- Usage-based insurance

Product Range:
- Third-party liability
- Fire and theft coverage
- Comprehensive insurance
- Roadside assistance add-ons

Target Segments:
- Digital-savvy consumers
- Flexible payment preference
- Value seekers
- Modern lifestyle customers

Marketing Strengths:
- Strong digital marketing campaigns
- Social media presence
- Performance marketing expertise
- Data-driven customer acquisition

Competitive Advantages:
- Payment flexibility
- Digital user experience
- Marketing sophistication
- Brand visibility in digital channels

Strategic Focus:
- Digital innovation
- Customer experience optimization
- Flexible offers and customization
- Data-driven marketing
"""
        },
        # Add more competitors...
    ]
    
    # Ingest each competitor
    for comp in competitors:
        km.ingest_document(
            content=comp["content"],
            doc_type="market_research",
            metadata={
                "company": comp["company"],
                "product": comp["product"],
                "industry": comp["industry"],
                "geography": comp["geography"],
                "segment": comp["segment"],
                "distribution": comp["distribution"],
                "strategic_focus": comp["strategic_focus"],
                "source": "Competitive Intelligence Database",
                "date": "2024-Q4"
            }
        )
        print(f"✅ Ingested: {comp['company']} - {comp['product']}")
    
    print(f"\n✅ Successfully ingested {len(competitors)} competitor profiles!")
    
    # Verify
    stats = km.get_collection_stats()
    print(f"\nKnowledge Base Stats:")
    for doc_type, count in stats.items():
        print(f"  - {doc_type}: {count}")

if __name__ == "__main__":
    ingest_competitor_data()