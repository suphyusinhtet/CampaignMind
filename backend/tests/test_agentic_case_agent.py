import asyncio
import sys
from pathlib import Path


# Robust import path handling whether pytest is run from repo root or backend/
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from agents.agentic_case_agent import AgenticCaseIntelligenceAgent


class _FakeTools:
    def __init__(self):
        self.web_calls = []

    def web_search(self, query, num_results=10, region="wt-wt"):
        self.web_calls.append(
            {"query": query, "num_results": num_results, "region": region}
        )
        return []

    def scrape_url(self, url):
        return {"url": url, "content": "", "source": "web_scrape"}


def _make_agent_without_init():
    # Avoid real model/tool initialization for unit tests.
    agent = AgenticCaseIntelligenceAgent.__new__(AgenticCaseIntelligenceAgent)
    agent.tools = _FakeTools()
    agent.quality_threshold = 0.6
    return agent


def test_resolve_region_mapping():
    agent = _make_agent_without_init()

    assert agent._resolve_region("Italy Europe") == "it-it"
    assert agent._resolve_region("United States") == "us-en"
    assert agent._resolve_region("UK") == "uk-en"
    assert agent._resolve_region("Europe") == "wt-wt"
    assert agent._resolve_region("") == "wt-wt"


def test_competitor_search_uses_geography_region():
    agent = _make_agent_without_init()
    brief_context = {"product": "car insurance", "industry": "insurance", "geography": "Italy"}
    context_keys = {"product": "car insurance", "industry": "insurance", "geography": "Italy"}

    agent._search_competitor_campaigns(brief_context, context_keys)

    assert agent.tools.web_calls, "Expected web_search to be called at least once"
    assert all(call["region"] == "it-it" for call in agent.tools.web_calls)


def test_retry_does_not_mutate_original_brief_context():
    agent = _make_agent_without_init()

    seen_contexts = []

    def _extract_campaign_context(ctx):
        seen_contexts.append(dict(ctx))
        return {}

    agent._extract_campaign_context = _extract_campaign_context
    agent._query_rag = lambda brief_context, filters, n_results: []
    agent._evaluate_case_quality = lambda results, context_keys: 1.0
    agent._search_competitor_campaigns = lambda brief_context, context_keys: []
    agent._extract_competitor_names = lambda competitor_results: []
    agent._scrape_competitor_campaigns = lambda competitors, brief_context: []
    agent._search_case_studies = lambda brief_context, context_keys: []
    agent._format_all_sources = lambda sources: ""

    async def _generate_response(brief_context, context, competitors_found):
        return "stub response"

    agent._generate_response = _generate_response

    # Force exactly one retry cycle.
    evaluate_calls = {"count": 0}

    def _evaluate_response(response, context_keys):
        evaluate_calls["count"] += 1
        if evaluate_calls["count"] == 1:
            return 0.0  # trigger retry
        return 1.0

    agent._evaluate_response = _evaluate_response

    original_context = {"objective": "awareness", "industry": "insurance"}
    asyncio.run(agent.analyze_cases(original_context, max_retries=1))

    assert "_refined_search" not in original_context
    assert len(seen_contexts) == 2
    assert "_refined_search" not in seen_contexts[0]
    assert seen_contexts[1].get("_refined_search") == "true"

