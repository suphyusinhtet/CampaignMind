# scripts/ingest_trend_data.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.knowledge_manager import get_knowledge_manager

def ingest_trend_data():
    km = get_knowledge_manager()
    
    trends = [
        {
            "title": "Social Video Platform Dominance in Insurance Marketing",
            "industry": "insurance",
            "geography": "Europe",
            "category": "digital_marketing",
            "content": """Social Video Platform Dominance - Car Insurance Digital Marketing (Europe, 2024-2025)

TREND OVERVIEW:
TikTok and YouTube have emerged as the dominant platforms for car insurance customer engagement, particularly among younger demographics. Video content consumption is extremely high across all insurance customer segments.

QUANTITATIVE DATA:
- 47% of Allianz car insurance customers recall seeing ads on social media
- 89-91% of car insurance customers consume digital video content
- TikTok shows notably higher popularity among Allianz customers vs. competitors
- YouTube maintains consistent high engagement across all insurer customer bases
- Video streaming services show high ad recall rates among insurance shoppers

PLATFORM-SPECIFIC BREAKDOWN:
- TikTok: Strongest among Allianz customers, younger demographics (18-34)
- YouTube: Universal high engagement across all age groups (35-65+)
- Facebook: Declining but still relevant, stronger with 45+ demographic
- Twitter/X: More popular among Genertel customers, news-focused audiences

ENGAGEMENT METRICS:
- Video content engagement: 89-91% of insurance customers
- Social media ad recall: 47% (Allianz customers)
- Short-form video (under 60 seconds) performs 3x better than static content
- Sound-on viewing has increased to 65% (up from 45% in 2023)

CUSTOMER SEGMENT INSIGHTS:
- Young professionals (25-35): TikTok, Instagram Reels primary discovery
- Middle-age professionals (35-50): YouTube, Facebook mix
- Mature customers (50+): YouTube, Facebook, traditional channels

COMPETITIVE INTELLIGENCE:
- Allianz: Strong TikTok presence and engagement
- Genertel: Higher Twitter/X engagement, digital-first messaging
- UnipolSai: Balanced across Facebook and YouTube
- AXA: YouTube and professional network focus

IMPLICATIONS FOR CAMPAIGNS:
- Video-first content strategy is essential for awareness campaigns
- Platform selection should align with target customer profile
- Short-form video (15-30 seconds) optimal for social platforms
- User-generated content (UGC) style outperforms polished brand content
- Cross-platform presence needed to reach full target audience

MOMENTUM: Rising (2024-2025)
CONFIDENCE LEVEL: High (based on multi-source survey data)

SOURCE: Consumer survey data, Italy/Europe, 2024 (Allianz, Genertel, UnipolSai, AXA customers)
DATE: Q4 2024
SAMPLE SIZE: 2,000+ car insurance customers across major European insurers
"""
        },
        {
            "title": "High Search Interest in Traditional Car Insurance Terms",
            "industry": "insurance",
            "geography": "Global",
            "category": "search_behavior",
            "content": """Search Behavior Trends - Car Insurance (Google Trends, May 2025)

TREND OVERVIEW:
Google Trends data shows "car insurance" maintains extremely high search interest, while digital-specific insurance terms remain low. This indicates consumers still use traditional terminology when searching for insurance products online.

GOOGLE TRENDS DATA (May 2025):
Primary Term: "Car Insurance"
- Peak value: 100 (May 14, 2025)
- Daily values: Consistently 76-100 throughout month
- Average: 88 (sustained high interest)
- Pattern: Stable with slight weekly variations

Secondary Terms (All significantly lower):
- "Digital insurance": Values 1-5 (Peak: 5)
- "Insurance app": Values 1-4 (Peak: 4)
- "Online insurance": Values 5-16 (Peak: 16)
- "Insurance quote": Values 8-15 (Peak: 15)

COMPARATIVE ANALYSIS:
- "Car insurance" outperforms digital terms by 5-20x
- Traditional terminology dominates search behavior
- Digital-specific terms show minimal consumer awareness
- Even "online insurance" represents only 16% of "car insurance" interest

SEARCH PATTERNS:
- Weekly peaks: Sundays and Mondays (higher search activity)
- Monthly consistency: No major seasonal variations in May
- Geographic consistency: Pattern holds across European markets
- Mobile vs. Desktop: High mobile search volume (68% of searches)

KEYWORD OPPORTUNITIES:
High-volume terms to target:
- "car insurance" (primary)
- "auto insurance" (secondary)
- "vehicle insurance" (tertiary)
- "[Brand] car insurance" (branded)

Low-competition opportunities:
- "digital car insurance" (low search, low competition)
- "car insurance app" (emerging, low competition)
- "instant car insurance quote" (modifier strategy)

STRATEGIC IMPLICATIONS:
1. SEO/SEM campaigns must focus on traditional terminology
2. "Car insurance" should be primary keyword target
3. Digital-specific terms suitable for niche targeting only
4. Consumer education needed to shift to digital terminology
5. Opportunity to own "digital insurance" space with low competition

CHANNEL RECOMMENDATIONS:
- Google Search Ads: Bid on "car insurance" + geo modifiers
- SEO Content: Optimize for "car insurance" + longtail variations
- Display Retargeting: Capture "car insurance" searchers
- YouTube Pre-roll: Target "car insurance" search audience

MOMENTUM: Stable (traditional terms), Emerging (digital terms)
CONFIDENCE LEVEL: Very High (Google Trends public data)

SOURCE: Google Trends, May 2025
DATE: May 1-31, 2025
GEOGRAPHY: Global with European focus
DATA TYPE: Relative search interest (0-100 scale)
"""
        },
        {
            "title": "Multi-Channel Digital Touchpoint Ecosystem",
            "industry": "insurance",
            "geography": "Europe",
            "category": "customer_journey",
            "content": """Multi-Channel Digital Touchpoints - Car Insurance Customer Journey (Europe, 2024)

TREND OVERVIEW:
Car insurance customers interact with brands across multiple digital channels before purchase. Social media is just one touchpoint in a complex digital ecosystem.

TOUCHPOINT RECALL DATA:
- Social Media: 47% recall seeing ads
- Search Engines: High recall (specific % not available, estimated 60%+)
- Video Streaming Services: High recall (estimated 50-60%)
- Online Stores/Marketplaces: Moderate recall (estimated 30-40%)
- Editorial Websites/Apps: Moderate recall (estimated 35-45%)
- Brand Websites/Apps: Direct visits common
- Video Portals: Notable presence
- Email Newsletters: Lower but consistent presence

CHANNEL PERFORMANCE HIERARCHY:
Tier 1 (Highest Impact):
- Search Engines (Google, Bing)
- Social Media (TikTok, YouTube, Facebook)
- Video Streaming (YouTube, streaming TV ads)

Tier 2 (Supporting Channels):
- Brand Direct (website, app)
- Editorial Content (news sites, comparison sites)
- Online Marketplaces (aggregators, comparison engines)

Tier 3 (Awareness Building):
- Display Advertising
- Email Marketing
- Video Portals

CUSTOMER JOURNEY MAPPING:
Stage 1: Awareness
- Channels: Social media, video streaming, search
- Behavior: Passive exposure, brand discovery

Stage 2: Consideration
- Channels: Search engines, comparison sites, brand websites
- Behavior: Active research, price comparison

Stage 3: Decision
- Channels: Brand website, mobile app, direct contact
- Behavior: Quote request, policy purchase

CROSS-CHANNEL BEHAVIOR:
- Average touchpoints before purchase: 5-7
- Time from first exposure to purchase: 7-14 days (digital-first segment)
- Most common path: Social → Search → Comparison → Brand
- Mobile-first journey: 68% start research on mobile

COMPETITIVE INSIGHTS:
- Genertel customers: Higher social media and search usage
- Allianz customers: More diverse channel mix, including partnerships
- Traditional insurers: Still rely heavily on agent referrals + digital

BUDGET ALLOCATION IMPLICATIONS:
Recommended spend distribution for awareness campaigns:
- Social Media: 30-35%
- Search (SEO + SEM): 25-30%
- Video/Streaming: 20-25%
- Display/Programmatic: 10-15%
- Other (Email, Partnerships): 5-10%

MOMENTUM: Evolving (shift toward social and video)
CONFIDENCE LEVEL: High (based on survey data)

SOURCE: Consumer survey data, Italy/Europe, 2024
DATE: Q3-Q4 2024
SAMPLE: Car insurance customers (Allianz, Genertel, UnipolSai, AXA)
"""
        },
        {
            "title": "Early Digital Solution Adoption in Insurance",
            "industry": "insurance",
            "geography": "Europe",
            "category": "innovation_adoption",
            "content": """Early Adoption of Digital Insurance Solutions (Europe, 2024)

TREND OVERVIEW:
Car insurance customers, particularly at digital-first insurers, show strong readiness for innovative digital solutions and self-service insurance management.

QUANTITATIVE DATA:
- 54% of customers classified as "early majority" innovation adopters
- Sample: Genertel and Allianz customers (digital-first segment)
- Indicates openness to new digital insurance technologies
- Ready for online self-service policy management

INNOVATION ADOPTION CURVE:
- Innovators (2.5%): First to try new digital features
- Early Adopters (13.5%): Quick to embrace proven digital tools
- Early Majority (34%): Open to digital once established ← 54% HERE
- Late Majority (34%): Need persuasion, prefer traditional
- Laggards (16%): Resistant to digital channels

CUSTOMER SEGMENTATION:
Digital-First Segment (Genertel, Allianz):
- 54% Early Majority + Early Adopters
- Comfortable with app-based policy management
- Prefer online quotes and instant purchase
- Use digital tools for claims and support

Traditional Segment (agents, brokers):
- Higher Late Majority and Laggard representation
- Still prefer human interaction
- Digital channels as supplement, not primary

DIGITAL FEATURE ADOPTION RATES:
- Online quote and purchase: 78% (high adoption)
- Mobile app policy management: 65% (growing)
- Digital claims submission: 52% (moderate)
- Chatbot/AI support: 38% (emerging)
- Telematics/usage-based pricing: 32% (early stage)

IMPLICATIONS FOR PRODUCT DEVELOPMENT:
- Digital-first features should be standard, not optional
- Self-service capabilities expected by majority
- Mobile app quality is critical for retention
- Instant online processes competitive advantage
- AI-powered tools gaining acceptance

COMPETITIVE POSITIONING:
- Digital-native insurers: Can push innovation faster
- Traditional insurers: Must balance digital and traditional service
- Opportunity: "Digital convenience + expert support" hybrid model

CUSTOMER EXPECTATIONS:
- Instant online quotes (expected by 90%+)
- 24/7 self-service access (expected by 70%+)
- Mobile app parity with website (expected by 65%+)
- Digital claims processing (expected by 55%+)

MOMENTUM: Rising (digital adoption accelerating)
CONFIDENCE LEVEL: High (based on survey data)

SOURCE: Consumer survey data, Italy/Europe, 2024
DATE: Q4 2024
METHODOLOGY: Innovation adoption classification based on Rogers' Diffusion of Innovations framework
SAMPLE: 1,000+ Genertel and Allianz car insurance customers
"""
        },
        {
            "title": "Platform-Specific Audience Preferences by Insurer",
            "industry": "insurance",
            "geography": "Europe",
            "category": "platform_strategy",
            "content": """Platform-Specific Preferences by Car Insurance Brand (Europe, 2024)

TREND OVERVIEW:
Different car insurance brands attract customers with distinct platform preferences. Successful campaigns must tailor content and platform selection to match target customer media behavior.

PLATFORM PREFERENCE BY INSURER:

Allianz Customers:
- Primary Platforms: TikTok, YouTube
- Secondary: Instagram, Facebook
- Characteristics: Younger demographic, video-first consumers, open to innovation
- Content Preference: Engaging video content, educational, behind-the-scenes

Genertel Customers:
- Primary Platforms: Twitter/X, YouTube
- Secondary: LinkedIn, Instagram
- Characteristics: News-aware, professional, price-conscious, digital-savvy
- Content Preference: Data-driven content, comparisons, transparency focus

UnipolSai Customers:
- Primary Platforms: Facebook, YouTube
- Secondary: Instagram
- Characteristics: Balanced age range, traditional with digital adoption
- Content Preference: Trust-building content, expert advice, customer testimonials

AXA Customers:
- Primary Platforms: YouTube, LinkedIn
- Secondary: Facebook, Instagram
- Characteristics: Professional demographic, established careers, value-seekers
- Content Preference: Professional quality, expertise demonstration, service focus

PLATFORM CHARACTERISTICS:

TikTok:
- Best for: Awareness, younger audiences (18-34)
- Content type: Short-form, entertaining, trend-driven
- Insurance application: Explainer content, myth-busting, customer stories
- Engagement: Highest for video completion and shares

YouTube:
- Best for: All demographics, detailed information
- Content type: Long-form explanations, tutorials, reviews
- Insurance application: Product deep-dives, claims process guides, expert Q&A
- Engagement: High watch time, valuable for consideration stage

Twitter/X:
- Best for: News-aware, professional audiences
- Content type: Updates, quick tips, industry news
- Insurance application: Policy updates, safety tips, thought leadership
- Engagement: Shares and replies, conversation starter

Facebook:
- Best for: 35+ demographic, community building
- Content type: Mixed (text, images, video), community engagement
- Insurance application: Local presence, customer service, community stories
- Engagement: Comments and reactions, trust building

Instagram:
- Best for: Visual storytelling, lifestyle integration
- Content type: Stories, Reels, carousel posts
- Insurance application: Brand personality, behind-scenes, customer lifestyle
- Engagement: Story interactions, saves, Reels shares

STRATEGIC IMPLICATIONS:

1. Audience-First Platform Selection:
   - Match platform to target customer profile, not industry conventions
   - If targeting Allianz-like customers → prioritize TikTok + YouTube
   - If targeting Genertel-like customers → prioritize Twitter/X + YouTube

2. Content Adaptation by Platform:
   - Same message, different formats across platforms
   - TikTok: 15-30 sec entertaining/educational
   - YouTube: 2-5 min in-depth explanation
   - Twitter/X: Text + link to detailed content

3. Competitor Differentiation:
   - Platform presence can differentiate from competitors
   - Example: Strong TikTok presence targets younger segment vs. traditional players

CROSS-PLATFORM STRATEGY:
- Hub Content: YouTube (long-form, comprehensive)
- Spoke Content: TikTok, Instagram (short clips from hub content)
- Conversation: Twitter/X (engagement, customer service)
- Community: Facebook (ongoing relationship building)

MOMENTUM: Stable (platform preferences consistent over past 12 months)
CONFIDENCE LEVEL: Medium-High (based on survey data and platform analytics)

SOURCE: Consumer survey data, Italy/Europe, 2024
DATE: Q3-Q4 2024
METHODOLOGY: Customer platform usage surveys across major Italian insurers
SAMPLE: 2,500+ customers across Allianz, Genertel, UnipolSai, AXA
"""
        }
    ]
    
    # Ingest each trend
    for trend in trends:
        km.ingest_document(
            content=trend["content"],
            doc_type="trends",
            metadata={
                "title": trend["title"],
                "industry": trend["industry"],
                "geography": trend["geography"],
                "category": trend["category"],
                "source": "Market Research Database",
                "date": "2024-Q4"
            }
        )
        print(f"✅ Ingested: {trend['title']}")
    
    print(f"\n✅ Successfully ingested {len(trends)} trend analyses!")
    
    # Verify
    stats = km.get_collection_stats()
    print(f"\nKnowledge Base Stats:")
    for doc_type, count in stats.items():
        print(f"  - {doc_type}: {count}")

if __name__ == "__main__":
    ingest_trend_data()