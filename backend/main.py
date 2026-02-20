# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict
import asyncio
from datetime import datetime

from agents.brief_analyzer import BriefAnalyzerAgent
from agents.trend_agent import TrendAgent
from agents.case_intelligence import CaseIntelligenceAgent
from agents.market_landscape import MarketLandscapeAgent
from agents.insight_generator import InsightGeneratorAgent
from agents.orchestrator import MasterOrchestrator
from routers.conversations import router as conversations_router
from config.settings import settings


# Initialize FastAPI app
app = FastAPI(
    title="Pathfinder AI API",
    description="Multi-agent system for enhancing marketing campaign briefs",
    version="1.0.0"
)

# CORS — allow the frontend origin (locked down; not open wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount conversation routes (auth-protected multi-turn chat)
app.include_router(conversations_router)


# Request/Response Models
class BriefEnhancementRequest(BaseModel):
    """Request model for brief enhancement."""
    brief: str = Field(..., description="The marketing campaign brief to enhance")
    include_trends: bool = Field(True, description="Include trend analysis")
    include_cases: bool = Field(True, description="Include case study analysis")
    include_landscape: bool = Field(True, description="Include market landscape analysis")
    filters: Optional[Dict[str, str]] = Field(None, description="Optional filters for RAG queries")
    n_results: int = Field(5, ge=1, le=10, description="Number of RAG results per query (1-10)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brief": "Campaign Objective: Launch awareness campaign for new sustainable sneaker line\nTarget Audience: Environmentally conscious millennials and Gen Z\nProduct: Eco-friendly sneakers made from recycled ocean plastic\nTimeline: Q2 2025\nGeography: United States, urban markets",
                "include_trends": True,
                "include_cases": True,
                "include_landscape": True,
                "n_results": 5
            }
        }


class BriefEnhancementResponse(BaseModel):
    """Response model for brief enhancement."""
    status: str
    brief_analysis: str
    trend_analysis: Optional[str] = None
    case_analysis: Optional[str] = None
    landscape_analysis: Optional[str] = None
    final_insights: str
    processing_time_seconds: float
    timestamp: str


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    message: str
    timestamp: str


# API Endpoints
@app.get("/", response_model=HealthCheckResponse)
async def root():
    """Root endpoint - API health check."""
    return HealthCheckResponse(
        status="healthy",
        message="Pathfinder AI API is running",
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status="healthy",
        message="All systems operational",
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/api/v1/enhance-brief", response_model=BriefEnhancementResponse)
async def enhance_brief(request: BriefEnhancementRequest):
    """
    Main endpoint: Enhance a marketing campaign brief using the Master Orchestrator.
    
    The orchestrator intelligently:
    1. Analyzes the brief for completeness
    2. Determines which specialist agents are needed
    3. Runs agents in parallel for speed
    4. Synthesizes all analyses into strategic insights
    
    Returns a comprehensive brief enhancement with recommendations.
    """
    start_time = datetime.utcnow()
    
    try:
        # Use the Master Orchestrator
        print(f"[{datetime.utcnow().isoformat()}] Initializing Master Orchestrator...")
        orchestrator = MasterOrchestrator()
        
        # Run orchestration
        results = await orchestrator.enhance_brief(
            brief=request.brief,
            filters=request.filters,
            n_results=request.n_results
        )
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        print(f"[{datetime.utcnow().isoformat()}] Brief enhancement complete in {processing_time:.2f}s")
        
        return BriefEnhancementResponse(
            status="success",
            brief_analysis=results["brief_analysis"],
            trend_analysis=results["trend_analysis"],
            case_analysis=results["case_analysis"],
            landscape_analysis=results["landscape_analysis"],
            final_insights=results["final_insights"],
            processing_time_seconds=processing_time,
            timestamp=end_time.isoformat()
        )
    
    except Exception as e:
        print(f"[{datetime.utcnow().isoformat()}] ERROR: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Brief enhancement failed: {str(e)}"
        )


def _extract_brief_context(brief: str) -> Dict[str, str]:
    """
    Extract key context from the brief for RAG queries.
    In production, this could use NLP or the brief_analysis JSON output.
    For now, we use simple keyword extraction.
    """
    brief_lower = brief.lower()
    
    context = {}
    
    # Extract objective
    if "awareness" in brief_lower:
        context["objective"] = "brand awareness"
    elif "conversion" in brief_lower or "sales" in brief_lower:
        context["objective"] = "conversion sales"
    elif "retention" in brief_lower or "loyalty" in brief_lower:
        context["objective"] = "retention loyalty"
    else:
        context["objective"] = "general marketing"
    
    # Extract industry keywords
    industry_keywords = []
    if "sneaker" in brief_lower or "footwear" in brief_lower or "shoe" in brief_lower:
        industry_keywords.append("footwear")
    if "sustainable" in brief_lower or "eco" in brief_lower or "recycled" in brief_lower:
        industry_keywords.append("sustainable fashion")
    context["industry"] = " ".join(industry_keywords) if industry_keywords else "general"
    
    # Extract audience
    audience_keywords = []
    if "millennial" in brief_lower:
        audience_keywords.append("millennials")
    if "gen z" in brief_lower or "gen-z" in brief_lower:
        audience_keywords.append("gen z")
    if "environment" in brief_lower:
        audience_keywords.append("environmentally conscious")
    context["audience"] = " ".join(audience_keywords) if audience_keywords else "general audience"
    
    # Extract product
    if "sneaker" in brief_lower or "shoe" in brief_lower:
        context["product"] = "sustainable sneakers recycled materials"
    else:
        context["product"] = "consumer product"
    
    # Extract geography
    if "us" in brief_lower or "united states" in brief_lower or "america" in brief_lower:
        context["geography"] = "US"
        if "urban" in brief_lower:
            context["geography"] = "US urban"
    else:
        context["geography"] = "global"
    
    return context


# Optional: Add endpoint to query RAG directly (for debugging)
@app.post("/api/v1/query-knowledge")
async def query_knowledge(
    query: str,
    doc_type: str = "trends",
    n_results: int = 5
):
    """
    Direct access to the RAG knowledge base (for debugging/testing).
    
    Args:
        query: Search query
        doc_type: Type of documents to search (trends, case_studies, market_research)
        n_results: Number of results to return
    """
    try:
        from rag.knowledge_manager import get_knowledge_manager
        km = get_knowledge_manager()
        results = km.query(query, doc_type, n_results=n_results)
        
        return {
            "status": "success",
            "query": query,
            "doc_type": doc_type,
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Optional: Add endpoint to get knowledge base stats
@app.get("/api/v1/knowledge-stats")
async def knowledge_stats():
    """Get statistics about the knowledge base."""
    try:
        from rag.knowledge_manager import get_knowledge_manager
        km = get_knowledge_manager()
        stats = km.get_collection_stats()
        
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)