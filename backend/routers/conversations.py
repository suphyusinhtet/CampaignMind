# routers/conversations.py
import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents.brief_analyzer import BriefAnalyzerAgent
from agents.case_intelligence import CaseIntelligenceAgent
from agents.creator_agent import CreatorAgent
from agents.followup_agent import FollowUpAgent
from agents.insight_generator import InsightGeneratorAgent
from agents.market_landscape import MarketLandscapeAgent
from agents.orchestrator import MasterOrchestrator
from agents.trend_agent import TrendAgent
try:
    from agents.agentic_case_agent import AgenticCaseIntelligenceAgent
except Exception:
    AgenticCaseIntelligenceAgent = None
try:
    from agents.agentic_market_agent import AgenticMarketLandscapeAgent
except Exception:
    AgenticMarketLandscapeAgent = None
try:
    from agents.agentic_orchestrator import AgenticMasterOrchestrator
except Exception:
    AgenticMasterOrchestrator = None
try:
    from agents.agentic_trend_agent import AgenticTrendAgent
except Exception:
    AgenticTrendAgent = None
from auth.dependencies import get_current_or_guest_user
from db.supabase_client import get_supabase_admin

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])

CONTINUE_WORDS = {"continue", "next", "go", "run", "proceed"}
METADATA_CONFIRM_WORDS = {"confirm", "confirmed", "yes", "y", "ok", "okay", "continue", "proceed", "run"}
REQUIRED_METADATA_FIELDS = [
    "brand_name",
    "sector",
    "target_audience",
    "objectives_kpis",
    "competitors",
    "budget",
    "timing",
    "geography",
]
REQUIRED_METADATA_PROMPTS = {
    "brand_name": "Brand/Company name",
    "sector": "Sector/Industry (e.g., Korean supermarket, insurance, fintech)",
    "target_audience": "Target audience (demographic + psychographic details)",
    "objectives_kpis": "SMART objective and KPI targets (e.g., awareness + measurable KPI)",
    "competitors": "Top 3-5 competitors and any known positioning notes",
    "budget": "Campaign budget (or a realistic range) and any hard constraints",
    "timing": "Campaign timing/timeline (launch window + key phases/milestones)",
    "geography": "Geography/market scope (country/region/city focus)",
}
INTERACTIVE_STEPS = [
    "awaiting_user_metadata",
    "awaiting_user_metadata_confirmation",
    "awaiting_user_mode_selection",
    "awaiting_user_continue_trend",
    "awaiting_user_continue_case",
    "awaiting_user_continue_landscape",
    "awaiting_user_continue_insight",
    "awaiting_user_continue_creator",
]
MAX_CONVERSATION_TITLE_CHARS = 60
MAX_CONVERSATION_TITLE_WORDS = 10


class ConversationCreate(BaseModel):
    title: Optional[str] = None


class MessageCreate(BaseModel):
    content: str


class ConversationUpdate(BaseModel):
    title: str


class MessageOut(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    message_type: str
    metadata: Optional[dict] = None
    created_at: str


class ConversationOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    guest_id: Optional[str] = None
    title: str
    created_at: str
    updated_at: str
    messages: Optional[List[MessageOut]] = None


class ConversationStateOut(BaseModel):
    conversation_id: str
    mode: Literal["interactive", "autonomous"]
    current_step: str
    pipeline_status: str
    pending_prompt: Optional[str] = None
    updated_at: str


class ConversationStateUpdate(BaseModel):
    mode: Optional[Literal["interactive", "autonomous"]] = None
    current_step: Optional[str] = None
    pipeline_status: Optional[str] = None
    pending_prompt: Optional[str] = None


class AgentEventOut(BaseModel):
    id: Optional[str] = None
    conversation_id: str
    agent_name: str
    status: str
    content: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: str


def _auto_title(content: str) -> str:
    title = content.strip().replace("\n", " ")
    return (title[:57] + "...") if len(title) > 60 else title


def _normalize_conversation_title(title: str) -> str:
    cleaned = re.sub(r"\s+", " ", title.strip())
    if not cleaned:
        raise HTTPException(status_code=400, detail="Conversation title cannot be empty")

    words = cleaned.split(" ")
    if len(words) > MAX_CONVERSATION_TITLE_WORDS:
        cleaned = " ".join(words[:MAX_CONVERSATION_TITLE_WORDS])

    if len(cleaned) > MAX_CONVERSATION_TITLE_CHARS:
        cleaned = cleaned[:MAX_CONVERSATION_TITLE_CHARS].rstrip()

    if not cleaned:
        raise HTTPException(status_code=400, detail="Conversation title is invalid")
    return cleaned


def _is_first_message(conversation_id: str) -> bool:
    db = get_supabase_admin()
    result = (
        db.table("messages")
        .select("id")
        .eq("conversation_id", conversation_id)
        .limit(1)
        .execute()
    )
    return len(result.data) == 0


def _verify_ownership(conversation_id: str, user: dict) -> dict:
    db = get_supabase_admin()
    query = db.table("conversations").select("*").eq("id", conversation_id)
    if user.get("is_guest"):
        query = query.eq("guest_id", user["sub"])
    else:
        query = query.eq("user_id", user["sub"])
    result = query.maybe_single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result.data


def _default_state(conversation_id: str) -> Dict[str, Any]:
    return {
        "conversation_id": conversation_id,
        "mode": "interactive",
        "current_step": "idle",
        "pipeline_status": "idle",
        "pending_prompt": None,
        "required_metadata": {},
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _get_or_create_state(conversation_id: str) -> Dict[str, Any]:
    db = get_supabase_admin()
    default_state = _default_state(conversation_id)

    try:
        result = (
            db.table("conversation_states")
            .select("*")
            .eq("conversation_id", conversation_id)
            .maybe_single()
            .execute()
        )
        if result.data:
            return result.data
    except Exception:
        return default_state

    try:
        created = (
            db.table("conversation_states")
            .upsert(default_state, on_conflict="conversation_id")
            .execute()
        )
        if created.data:
            return created.data[0]
    except Exception:
        pass

    return default_state


def _update_state(conversation_id: str, **patch: Any) -> Dict[str, Any]:
    db = get_supabase_admin()
    next_state = _default_state(conversation_id)
    next_state.update(_get_or_create_state(conversation_id))
    next_state.update({k: v for k, v in patch.items() if v is not None})
    next_state["updated_at"] = datetime.now(timezone.utc).isoformat()

    try:
        result = (
            db.table("conversation_states")
            .upsert(next_state, on_conflict="conversation_id")
            .execute()
        )
        if result.data:
            return result.data[0]
    except Exception:
        pass
    return next_state


def _insert_agent_event(
    conversation_id: str,
    agent_name: str,
    status_text: str,
    content: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Dict[str, Any]:
    db = get_supabase_admin()
    payload = {
        "conversation_id": conversation_id,
        "agent_name": agent_name,
        "status": status_text,
        "content": content,
        "metadata": metadata or {},
    }
    fallback = {
        **payload,
        "id": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        result = db.table("agent_events").insert(payload).execute()
        if result.data:
            return result.data[0]
    except Exception:
        pass
    return fallback


def _list_agent_events(
    conversation_id: str,
    limit: int = 200,
    after: Optional[str] = None,
) -> List[Dict[str, Any]]:
    db = get_supabase_admin()
    try:
        query = (
            db.table("agent_events")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .limit(limit)
        )
        if after:
            query = query.gt("created_at", after)
        result = query.execute()
        return result.data or []
    except Exception:
        return []


def _get_first_brief(conversation_id: str) -> Optional[str]:
    db = get_supabase_admin()
    result = (
        db.table("messages")
        .select("content, role, message_type")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )
    for msg in result.data or []:
        if msg.get("role") == "user" and msg.get("message_type") in {"brief", "interactive_brief"}:
            return msg.get("content")
    return None


def _get_latest_agent_output(conversation_id: str, agent_name: str) -> Optional[str]:
    db = get_supabase_admin()
    try:
        result = (
            db.table("agent_events")
            .select("content")
            .eq("conversation_id", conversation_id)
            .eq("agent_name", agent_name)
            .eq("status", "completed")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0].get("content")
    except Exception:
        return None
    return None


def _parse_enhancement_plan(brief_analysis: str) -> Dict[str, Any]:
    fallback = {
        "needs_trend_analysis": True,
        "needs_competitor_analysis": True,
        "needs_market_landscape": True,
    }
    if not brief_analysis:
        return fallback

    try:
        json_match = re.search(r"```json\s*(.*?)\s*```", brief_analysis, re.DOTALL)
        raw_json = json_match.group(1) if json_match else brief_analysis
        data = json.loads(raw_json)
        plan = data.get("enhancement_plan", {})
        return {
            "needs_trend_analysis": plan.get("needs_trend_analysis", True),
            "needs_competitor_analysis": plan.get("needs_competitor_analysis", True),
            "needs_market_landscape": plan.get("needs_market_landscape", True),
        }
    except Exception:
        return fallback


def _next_interactive_step(plan: Dict[str, Any], completed: set[str]) -> str:
    ordered = [
        ("trend", "awaiting_user_continue_trend", bool(plan.get("needs_trend_analysis", True))),
        ("case", "awaiting_user_continue_case", bool(plan.get("needs_competitor_analysis", True))),
        ("landscape", "awaiting_user_continue_landscape", bool(plan.get("needs_market_landscape", True))),
        ("insight", "awaiting_user_continue_insight", True),
        ("creator", "awaiting_user_continue_creator", True),
    ]
    for key, step, enabled in ordered:
        if not enabled:
            completed.add(key)
            continue
        if key not in completed:
            return step
    return "completed"


def _extract_metadata_from_text(text: str) -> Dict[str, str]:
    if not text:
        return {}
    content = text.strip()
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    joined = " ".join(lines)
    lower = joined.lower()

    metadata: Dict[str, str] = {}
    alias_map = {
        "brand_name": {"brand", "target brand", "brand name", "company", "company name"},
        "sector": {"sector", "industry", "category", "market type"},
        "target_audience": {"target audience", "audience", "segment"},
        "objectives_kpis": {"objective", "objectives", "goal", "goals", "kpi", "kpis", "success metric"},
        "competitors": {"competitor", "competitors", "competition"},
        "budget": {"budget", "spend", "investment", "timing & budget"},
        "timing": {"timing", "timeline", "launch", "go live", "schedule", "milestone"},
        "geography": {"geography", "market", "region", "country", "location"},
    }

    def normalize_value(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip(" -\t")

    # Parse key-value style lines first: "field: value"
    for i, line in enumerate(lines):
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key_l = key.strip().lower()
        value = normalize_value(value)
        # Support multiline value when user writes:
        # Geography:
        # United Kingdom
        if not value and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if ":" not in next_line:
                value = normalize_value(next_line)
        if not value:
            continue
        for field, aliases in alias_map.items():
            if any(alias in key_l for alias in aliases):
                metadata[field] = value
                break

    # Parse section-heading style blocks (heading line + content on next lines)
    heading_to_field = {
        "brand": "brand_name",
        "target brand": "brand_name",
        "brand name": "brand_name",
        "company": "brand_name",
        "company name": "brand_name",
        "sector": "sector",
        "industry": "sector",
        "target audience": "target_audience",
        "objectives / kpis": "objectives_kpis",
        "objectives/kpis": "objectives_kpis",
        "objectives": "objectives_kpis",
        "kpis": "objectives_kpis",
        "competitors": "competitors",
        "budget": "budget",
        "timing": "timing",
        "timeline": "timing",
        "geography": "geography",
    }
    i = 0
    while i < len(lines):
        line = lines[i].strip().lower().strip("- ")
        field = heading_to_field.get(line)
        if field and field not in metadata:
            block: List[str] = []
            j = i + 1
            while j < len(lines):
                candidate = lines[j].strip()
                candidate_l = candidate.lower().strip("- ")
                # stop at next known heading
                if candidate_l in heading_to_field:
                    break
                # if explicit key:value starts, likely next section
                if ":" in candidate and any(alias in candidate_l.split(":", 1)[0] for aliases in alias_map.values() for alias in aliases):
                    break
                block.append(candidate)
                j += 1
            value = normalize_value(" ".join(block))
            if value:
                metadata[field] = value
            i = j
            continue
        i += 1

    # Heuristic fallback from whole brief text
    if "target_audience" not in metadata:
        if any(k in lower for k in ("millennial", "gen z", "gen-z", "young driver", "family", "new driver")):
            metadata["target_audience"] = "Audience indicators detected in brief."
    if "objectives_kpis" not in metadata:
        if ("kpi" in lower or "%" in joined or re.search(r"\b\d+\b", joined)) and any(k in lower for k in ("goal", "objective", "awareness", "conversion")):
            metadata["objectives_kpis"] = "Objective/KPI indicators detected in brief."
    if "budget" not in metadata:
        budget_match = re.search(r"(\$|€|£)\s?\d[\d,]*(\.\d+)?", joined)
        if budget_match:
            metadata["budget"] = budget_match.group(0)
    if "timing" not in metadata:
        timing_match = re.search(
            r"(within\s+\d+\s*(day|days|week|weeks|month|months)|go live\s+[^.,;\n]+|launch\s+[^.,;\n]+)",
            lower,
        )
        if timing_match:
            metadata["timing"] = timing_match.group(0).strip()
    if "geography" not in metadata:
        geo_keywords = ["us", "usa", "united states", "uk", "italy", "europe", "global", "asia", "singapore", "australia"]
        for kw in geo_keywords:
            if kw in lower:
                metadata["geography"] = kw.upper() if kw in {"us", "uk"} else kw.title()
                break
    if "competitors" not in metadata and re.search(r"\bcompetitor", lower):
        metadata["competitors"] = "Competitor section mentioned but details may be incomplete."
    if "sector" not in metadata:
        sector_keywords = [
            "insurance",
            "supermarket",
            "grocery",
            "fintech",
            "banking",
            "retail",
            "ecommerce",
            "saas",
            "healthcare",
        ]
        for kw in sector_keywords:
            if kw in lower:
                metadata["sector"] = kw.title()
                break
    if "brand_name" not in metadata:
        first_line = lines[0] if lines else ""
        # "BRIEF - OSEYO ..."
        m = re.search(r"\bbrief\s*[-:\u2013\u2014]\s*([A-Za-z0-9&'().,\- ]{2,80})", first_line, re.IGNORECASE)
        if m:
            candidate = normalize_value(m.group(1))
            if candidate:
                metadata["brand_name"] = candidate

    # Filter placeholders and weak sentinel values.
    placeholders = {"...", "n/a", "na", "tbd", "to be decided", "to be confirmed", "unknown"}
    cleaned: Dict[str, str] = {}
    for key, value in metadata.items():
        val = str(value).strip()
        if not val:
            continue
        if val.lower() in placeholders:
            continue
        cleaned[key] = val
    return cleaned


def _merge_metadata(existing: Dict[str, str], incoming_text: str) -> Dict[str, str]:
    merged = dict(existing or {})
    extracted = _extract_metadata_from_text(incoming_text)
    for key, value in extracted.items():
        if value and str(value).strip():
            merged[key] = str(value).strip()
    return merged


def _missing_required_metadata(metadata: Dict[str, str]) -> List[str]:
    return [field for field in REQUIRED_METADATA_FIELDS if not str((metadata or {}).get(field, "")).strip()]


def _format_missing_metadata_prompt(missing_fields: List[str]) -> str:
    lines = [
        "## Required Metadata Before Specialist Agents",
        "Please provide the missing must-have brief data below so the next agents can run with higher-quality context:",
        "",
    ]
    for field in missing_fields:
        lines.append(f"- **{REQUIRED_METADATA_PROMPTS.get(field, field)}**")
    lines.extend(
        [
            "",
            "You can reply in this format:",
            "```",
            "Brand Name: ...",
            "Sector: ...",
            "Target Audience: ...",
            "Objectives/KPIs: ...",
            "Competitors: ...",
            "Budget: ...",
            "Timing: ...",
            "Geography: ...",
            "```",
        ]
    )
    return "\n".join(lines)


def _metadata_as_brief_block(metadata: Dict[str, str]) -> str:
    ordered = [
        ("brand_name", "Brand Name"),
        ("sector", "Sector"),
        ("target_audience", "Target Audience"),
        ("objectives_kpis", "Objectives/KPIs"),
        ("competitors", "Competitors"),
        ("budget", "Budget"),
        ("timing", "Timing"),
        ("geography", "Geography"),
    ]
    lines = []
    for key, label in ordered:
        value = (metadata or {}).get(key)
        if value:
            lines.append(f"- {label}: {value}")
    return "\n".join(lines)


def _format_metadata_confirmation_prompt(metadata: Dict[str, str]) -> str:
    lines = [
        "---",
        "",
        "**Extracted Metadata (Please Confirm/Edit)**",
        "Review the metadata below before running specialist agents:",
        "",
    ]
    block = _metadata_as_brief_block(metadata)
    lines.append(block if block else "- No metadata extracted.")
    lines.extend(
        [
            "",
            "If this metadata is correct, reply with **confirm**.",
            "If you want edits, provide corrected fields in this format:",
            "```",
            "Brand Name: ...",
            "Sector: ...",
            "Target Audience: ...",
            "Objectives/KPIs: ...",
            "Competitors: ...",
            "Budget: ...",
            "Timing: ...",
            "Geography: ...",
            "```",
        ]
    )
    return "\n".join(lines)


def _format_mode_selection_prompt() -> str:
    return "\n".join(
        [
            "## Choose Execution Mode",
            "Metadata is confirmed.",
            "",
            "**Interactive mode**",
            "- Runs agents step by step.",
            "- You control progress by replying `continue` each step.",
            "- Best when you want to review intermediate outputs.",
            "",
            "**Autonomous mode**",
            "- Runs all remaining agents automatically after this message.",
            "- Best when you want fastest end-to-end output.",
            "",
            "Reply with **interactive** or **autonomous**.",
        ]
    )


def _parse_execution_mode(text: str) -> Optional[str]:
    normalized = (text or "").strip().lower()
    if not normalized:
        return None

    interactive_markers = {"interactive", "interactively", "step by step", "manual"}
    autonomous_markers = {"autonomous", "auto", "automatically", "full run"}

    is_interactive = any(marker in normalized for marker in interactive_markers)
    is_autonomous = any(marker in normalized for marker in autonomous_markers)

    if is_interactive and not is_autonomous:
        return "interactive"
    if is_autonomous and not is_interactive:
        return "autonomous"
    return None


def _metadata_to_agent_context(metadata: Dict[str, str]) -> Dict[str, str]:
    """Map required-metadata schema to agent context keys."""
    if not metadata:
        return {}
    mapped = {
        "brand_name": metadata.get("brand_name", ""),
        "sector": metadata.get("sector", ""),
        "audience": metadata.get("target_audience", ""),
        "objective": metadata.get("objectives_kpis", ""),
        "competitors": metadata.get("competitors", ""),
        "budget": metadata.get("budget", ""),
        "timing": metadata.get("timing", ""),
        "geography": metadata.get("geography", ""),
        "industry": metadata.get("sector", ""),
    }
    return {k: v for k, v in mapped.items() if str(v).strip()}


def _step_to_agent_label(step: str) -> str:
    mapping = {
        "awaiting_user_metadata": "Required Brief Metadata",
        "awaiting_user_metadata_confirmation": "Metadata Confirmation",
        "awaiting_user_mode_selection": "Mode Selection",
        "awaiting_user_continue_trend": "Trend Agent",
        "awaiting_user_continue_case": "Case Intelligence Agent",
        "awaiting_user_continue_landscape": "Market Landscape Agent",
        "awaiting_user_continue_insight": "Insight Generator",
        "awaiting_user_continue_creator": "Creator Agent",
        "awaiting_user_creator_option": "Creator Output Selection (1/2/3)",
    }
    return mapping.get(step, "next step")


def _parse_creator_option(text: str) -> Optional[str]:
    normalized = (text or "").strip().lower()
    if not normalized:
        return None
    if re.search(r"\b1\b", normalized) or "tagline" in normalized:
        return "1"
    if re.search(r"\b2\b", normalized) or "content calendar" in normalized or "4-week" in normalized:
        return "2"
    if re.search(r"\b3\b", normalized) or "hero ad" in normalized:
        return "3"
    return None


def _extract_json_payload(raw: str) -> Optional[Dict[str, Any]]:
    if not raw:
        return None
    try:
        match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
        json_text = match.group(1) if match else raw
        parsed = json.loads(json_text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        return None
    return None


def _bullet_lines(items: Any) -> List[str]:
    if not isinstance(items, list):
        return []
    return [f"- {str(item)}" for item in items if str(item).strip()]


def _format_brief_analysis_output(raw: str, brief_text: Optional[str] = None) -> str:
    data = _extract_json_payload(raw)
    if not data:
        return raw

    missing_items = [str(x) for x in data.get("missing_elements", []) if str(x).strip()]
    vague_items = [str(x) for x in data.get("vague_elements", []) if str(x).strip()]
    questions = [str(x) for x in data.get("clarifying_questions", []) if str(x).strip()]
    plan = data.get("enhancement_plan", {}) if isinstance(data.get("enhancement_plan"), dict) else {}
    score = data.get("completeness_score", 0)

    def pick_items(keywords: List[str], limit: int = 3) -> List[str]:
        matched: List[str] = []
        pool = missing_items + vague_items
        for item in pool:
            lower = item.lower()
            if any(k in lower for k in keywords):
                matched.append(item)
        return matched[:limit]

    sections = [
        ("Background & Context", ["background", "context", "business", "market"]),
        ("Task & Deliverables", ["deliverable", "channel", "scope", "task", "asset"]),
        ("Marketing Objectives & KPIs", ["objective", "kpi", "metric", "awareness", "conversion", "success"]),
        ("Target Audience", ["audience", "demographic", "psychographic", "segment"]),
        ("Brand Information", ["brand", "position", "personality", "tone", "guideline"]),
        ("Product/Service Details", ["product", "service", "price", "coverage", "feature", "benefit"]),
        ("Competitors", ["competitor", "market landscape", "positioning", "benchmark"]),
        ("Timing & Budget", ["timing", "timeline", "launch", "milestone", "budget"]),
    ]

    brief_title = "Campaign Brief"
    if brief_text and brief_text.strip():
        first_line = brief_text.strip().splitlines()[0].strip()
        brief_title = first_line[:90]

    lines: List[str] = [
        f"# Brief Analysis Report - {brief_title}",
        "",
        f"**Completeness Score:** {score}/100",
        "",
    ]

    idx = 1
    for name, keywords in sections:
        section_missing = pick_items(keywords)
        section_questions = [q for q in questions if any(k in q.lower() for k in keywords)][:2]

        if len(section_missing) >= 2:
            status = "Missing"
        elif section_missing or section_questions:
            status = "Partial"
        else:
            status = "Complete"

        lines.append(f"## {idx}. {name}")
        lines.append(f"- **Classification:** {status}")

        if section_missing:
            lines.append("- **What's Missing:**")
            lines.extend([f"  - {item}" for item in section_missing[:3]])
        elif status == "Complete":
            lines.append("- **What's Missing:** No critical gap detected from the provided brief.")

        if section_questions:
            lines.append("- **What Would Make It Complete:**")
            lines.extend([f"  - {q}" for q in section_questions])
        elif status != "Complete":
            fallback_guidance = {
                "Target Audience": "Provide demographic and psychographic details, plus segmentation insights.",
                "Brand Information": "Add brand values, positioning, and tone-of-voice guidance.",
                "Product/Service Details": "Add pricing/coverage details and key proof points.",
                "Competitors": "List main competitors and summarize their positioning.",
                "Timing & Budget": "Add launch timing, phase milestones, and budget allocation constraints.",
            }
            guidance_text = fallback_guidance.get(name)
            if guidance_text:
                lines.append("- **What Would Make It Complete:**")
                lines.append(f"  - {guidance_text}")

        lines.append("")
        idx += 1

    guidance: List[str] = []
    if plan.get("needs_trend_analysis", True):
        guidance.append("- **Trend Agent:** Look for current digital/social trend shifts and consumer behavior changes.")
    if plan.get("needs_competitor_analysis", True):
        guidance.append("- **Case Agent:** Identify strong competitor campaigns and analogous executions.")
    if plan.get("needs_market_landscape", True):
        guidance.append("- **Market Agent:** Analyze positioning map, crowded claims, and whitespace opportunities.")

    if guidance:
        lines.append("## Guidance for Next Agents")
        lines.extend(guidance)
        lines.append("")

    lines.append("## ACTION REQUIRED")
    lines.append(
        "Please provide the missing information above so the next agent steps can produce stronger and more precise recommendations."
    )
    lines.append("")
    lines.append(
        "**Do you want to work INTERACTIVELY with AI AGENTS or have the AI AGENTS WORK AUTONOMOUSLY?**"
    )
    lines.append(
        "Please specify your preference. You can also switch mode from the right panel."
    )

    return "\n".join(lines).strip() or raw


def _format_specialist_output(raw: str, title: str) -> str:
    data = _extract_json_payload(raw)
    if not data:
        return raw

    lines: List[str] = [f"### {title} Summary", ""]

    for key in ("key_insights", "recommendations", "differentiation_opportunities", "whitespace_opportunities"):
        items = data.get(key)
        if isinstance(items, list) and items:
            heading = key.replace("_", " ").title()
            lines.append(f"**{heading}:**")
            for item in items[:6]:
                if isinstance(item, dict):
                    text = item.get("opportunity") or item.get("trend") or item.get("campaign") or json.dumps(item)
                    lines.append(f"- {text}")
                else:
                    lines.append(f"- {item}")
            lines.append("")

    if len(lines) <= 2:
        return raw
    return "\n".join(lines).strip()


@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    user: dict = Depends(get_current_or_guest_user),
):
    db = get_supabase_admin()
    title = _normalize_conversation_title(body.title) if body.title else "New Conversation"
    payload = {"title": title}
    if user.get("is_guest"):
        payload["guest_id"] = user["sub"]
    else:
        payload["user_id"] = user["sub"]
    result = db.table("conversations").insert(payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create conversation")
    return result.data[0]


@router.get("", response_model=List[ConversationOut])
async def list_conversations(
    user: dict = Depends(get_current_or_guest_user),
    limit: int = 50,
    offset: int = 0,
):
    db = get_supabase_admin()
    query = db.table("conversations").select("*")
    if user.get("is_guest"):
        query = query.eq("guest_id", user["sub"])
    else:
        query = query.eq("user_id", user["sub"])
    result = query.order("updated_at", desc=True).limit(limit).offset(offset).execute()
    return result.data


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_or_guest_user),
):
    conv = _verify_ownership(conversation_id, user)
    db = get_supabase_admin()
    msgs = (
        db.table("messages")
        .select("*")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )
    conv["messages"] = msgs.data
    return conv


@router.patch("/{conversation_id}", response_model=ConversationOut)
async def rename_conversation(
    conversation_id: str,
    body: ConversationUpdate,
    user: dict = Depends(get_current_or_guest_user),
):
    _verify_ownership(conversation_id, user)
    db = get_supabase_admin()
    next_title = _normalize_conversation_title(body.title)
    query = (
        db.table("conversations")
        .update(
            {
                "title": next_title,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        .eq("id", conversation_id)
    )
    if user.get("is_guest"):
        query = query.eq("guest_id", user["sub"])
    else:
        query = query.eq("user_id", user["sub"])
    result = query.execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to rename conversation")
    return result.data[0]


@router.get("/{conversation_id}/state", response_model=ConversationStateOut)
async def get_conversation_state(
    conversation_id: str,
    user: dict = Depends(get_current_or_guest_user),
):
    _verify_ownership(conversation_id, user)
    return _get_or_create_state(conversation_id)


@router.patch("/{conversation_id}/state", response_model=ConversationStateOut)
async def update_conversation_state(
    conversation_id: str,
    body: ConversationStateUpdate,
    user: dict = Depends(get_current_or_guest_user),
):
    _verify_ownership(conversation_id, user)
    return _update_state(
        conversation_id,
        mode=body.mode,
        current_step=body.current_step,
        pipeline_status=body.pipeline_status,
        pending_prompt=body.pending_prompt,
    )


@router.get("/{conversation_id}/events", response_model=List[AgentEventOut])
async def list_agent_events(
    conversation_id: str,
    user: dict = Depends(get_current_or_guest_user),
    limit: int = 200,
    after: Optional[str] = None,
):
    _verify_ownership(conversation_id, user)
    return _list_agent_events(conversation_id, limit=limit, after=after)


@router.get("/{conversation_id}/events/stream")
async def stream_agent_events(
    conversation_id: str,
    user: dict = Depends(get_current_or_guest_user),
    after: Optional[str] = Query(None, description="ISO timestamp to stream events after"),
):
    _verify_ownership(conversation_id, user)

    async def event_generator():
        cursor = after
        while True:
            rows = _list_agent_events(conversation_id, limit=100, after=cursor)
            for row in rows:
                cursor = row.get("created_at", cursor)
                payload = json.dumps(row, default=str)
                yield f"event: agent_event\ndata: {payload}\n\n"

            yield "event: heartbeat\ndata: {}\n\n"
            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/{conversation_id}/messages", response_model=MessageOut)
async def send_message(
    conversation_id: str,
    body: MessageCreate,
    user: dict = Depends(get_current_or_guest_user),
):
    _verify_ownership(conversation_id, user)

    db = get_supabase_admin()
    state = _get_or_create_state(conversation_id)
    mode = state.get("mode", "autonomous")
    is_first = _is_first_message(conversation_id)
    user_msg_type = "interactive_brief" if (is_first and mode == "interactive") else ("brief" if is_first else "followup")

    user_msg_result = (
        db.table("messages")
        .insert(
            {
                "conversation_id": conversation_id,
                "role": "user",
                "content": body.content,
                "message_type": user_msg_type,
            }
        )
        .execute()
    )
    if not user_msg_result.data:
        raise HTTPException(status_code=500, detail="Failed to save user message")

    if is_first:
        db.table("conversations").update(
            {"title": _auto_title(body.content)}
        ).eq("id", conversation_id).execute()

    start_time = datetime.now(timezone.utc)
    assistant_content: str
    assistant_metadata: Optional[dict] = None
    assistant_msg_type: str
    persisted_assistant_msg: Optional[dict] = None

    def _persist_assistant_message(
        content: str,
        message_type: str = "analysis",
        metadata: Optional[dict] = None,
    ) -> dict:
        nonlocal persisted_assistant_msg
        result = (
            db.table("messages")
            .insert(
                {
                    "conversation_id": conversation_id,
                    "role": "assistant",
                    "content": content,
                    "message_type": message_type,
                    "metadata": metadata,
                }
            )
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to save assistant message")
        persisted_assistant_msg = result.data[0]
        return result.data[0]

    try:
        if state.get("current_step") == "awaiting_user_metadata" and not is_first:
            existing_meta = state.get("required_metadata") if isinstance(state.get("required_metadata"), dict) else {}
            merged_meta = _merge_metadata(existing_meta, body.content)
            missing_fields = _missing_required_metadata(merged_meta)

            if missing_fields:
                assistant_msg_type = "analysis"
                assistant_content = (
                    "Metadata intake is still incomplete.\n\n"
                    f"{_format_missing_metadata_prompt(missing_fields)}"
                )
                assistant_metadata = {
                    "workflow_mode": mode,
                    "current_step": "awaiting_user_metadata",
                    "required_metadata": merged_meta,
                    "missing_required_metadata": missing_fields,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_metadata",
                    pipeline_status="waiting_user",
                    pending_prompt="Provide the required metadata fields listed above.",
                    required_metadata=merged_meta,
                )
            else:
                assistant_msg_type = "analysis"
                assistant_content = _format_metadata_confirmation_prompt(merged_meta)
                assistant_metadata = {
                    "workflow_mode": mode,
                    "current_step": "awaiting_user_metadata_confirmation",
                    "required_metadata": merged_meta,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_metadata_confirmation",
                    pipeline_status="waiting_user",
                    pending_prompt="Reply with 'confirm' to continue, or edit metadata fields.",
                    required_metadata=merged_meta,
                )

        elif state.get("current_step") == "awaiting_user_metadata_confirmation" and not is_first:
            existing_meta = state.get("required_metadata") if isinstance(state.get("required_metadata"), dict) else {}
            normalized = body.content.strip().lower()
            merged_meta = _merge_metadata(existing_meta, body.content)
            missing_fields = _missing_required_metadata(merged_meta)

            if missing_fields:
                assistant_msg_type = "analysis"
                assistant_content = (
                    "Metadata still has required gaps.\n\n"
                    f"{_format_missing_metadata_prompt(missing_fields)}"
                )
                assistant_metadata = {
                    "workflow_mode": mode,
                    "current_step": "awaiting_user_metadata",
                    "required_metadata": merged_meta,
                    "missing_required_metadata": missing_fields,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_metadata",
                    pipeline_status="waiting_user",
                    pending_prompt="Provide the missing required metadata fields.",
                    required_metadata=merged_meta,
                )
            elif normalized in METADATA_CONFIRM_WORDS:
                assistant_msg_type = "analysis"
                assistant_content = _format_mode_selection_prompt()
                assistant_metadata = {
                    "workflow_mode": mode,
                    "current_step": "awaiting_user_mode_selection",
                    "required_metadata": merged_meta,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_mode_selection",
                    pipeline_status="waiting_user",
                    pending_prompt="Choose mode: interactive or autonomous.",
                    required_metadata=merged_meta,
                )
            else:
                assistant_msg_type = "analysis"
                assistant_content = _format_metadata_confirmation_prompt(merged_meta)
                assistant_metadata = {
                    "workflow_mode": mode,
                    "current_step": "awaiting_user_metadata_confirmation",
                    "required_metadata": merged_meta,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_metadata_confirmation",
                    pipeline_status="waiting_user",
                    pending_prompt="Reply with 'confirm' to continue, or edit metadata fields.",
                    required_metadata=merged_meta,
                )

        elif state.get("current_step") == "awaiting_user_mode_selection" and not is_first:
            existing_meta = state.get("required_metadata") if isinstance(state.get("required_metadata"), dict) else {}
            merged_meta = _merge_metadata(existing_meta, body.content)
            missing_fields = _missing_required_metadata(merged_meta)
            selected_mode = _parse_execution_mode(body.content)
            extracted_updates = _extract_metadata_from_text(body.content)

            if missing_fields:
                assistant_msg_type = "analysis"
                assistant_content = (
                    "Metadata still has required gaps.\n\n"
                    f"{_format_missing_metadata_prompt(missing_fields)}"
                )
                assistant_metadata = {
                    "workflow_mode": mode,
                    "current_step": "awaiting_user_metadata",
                    "required_metadata": merged_meta,
                    "missing_required_metadata": missing_fields,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_metadata",
                    pipeline_status="waiting_user",
                    pending_prompt="Provide the missing required metadata fields.",
                    required_metadata=merged_meta,
                )
            elif selected_mode == "interactive":
                brief_analysis = _get_latest_agent_output(conversation_id, "brief_analyzer") or ""
                plan = _parse_enhancement_plan(brief_analysis)
                next_step = _next_interactive_step(plan, completed={"brief"})
                assistant_msg_type = "analysis"
                assistant_content = (
                    "Mode set to **interactive**.\n\n"
                    f"Reply with **continue** to run **{_step_to_agent_label(next_step)}**."
                )
                assistant_metadata = {
                    "workflow_mode": "interactive",
                    "current_step": next_step,
                    "required_metadata": merged_meta,
                }
                _update_state(
                    conversation_id,
                    mode="interactive",
                    current_step=next_step,
                    pipeline_status="waiting_user",
                    pending_prompt=f"Reply with 'continue' to run {_step_to_agent_label(next_step)}.",
                    required_metadata=merged_meta,
                )
            elif selected_mode == "autonomous":
                original_brief = _get_first_brief(conversation_id) or body.content
                brief_analysis = _get_latest_agent_output(conversation_id, "brief_analyzer") or ""
                if not brief_analysis:
                    _insert_agent_event(conversation_id, "brief_analyzer", "started", "Analyzing brief completeness")
                    brief_analysis = await BriefAnalyzerAgent().analyze_brief(original_brief)
                    _insert_agent_event(conversation_id, "brief_analyzer", "completed", brief_analysis)

                plan = _parse_enhancement_plan(brief_analysis)
                orchestrator = AgenticMasterOrchestrator() if AgenticMasterOrchestrator is not None else MasterOrchestrator()
                brief_context = orchestrator._extract_brief_context(original_brief)
                brief_context.update(_metadata_to_agent_context(merged_meta))

                _update_state(
                    conversation_id,
                    mode="autonomous",
                    current_step="running_pipeline",
                    pipeline_status="running",
                    pending_prompt=None,
                    required_metadata=merged_meta,
                )

                trend_analysis = "No trend analysis requested"
                case_analysis = "No case analysis requested"
                landscape_analysis = "No landscape analysis requested"

                if plan.get("needs_trend_analysis", True):
                    trend_agent = AgenticTrendAgent() if AgenticTrendAgent is not None else TrendAgent()
                    _insert_agent_event(conversation_id, "trend_agent", "started", "Running trend analysis")
                    trend_analysis = await trend_agent.analyze_trends(brief_context)
                    _insert_agent_event(conversation_id, "trend_agent", "completed", trend_analysis)
                    _persist_assistant_message(
                        "## Step 2 Complete: Trend Analysis\n\n"
                        f"{_format_specialist_output(trend_analysis, 'Trend Agent')}",
                        metadata={
                            "workflow_mode": "autonomous",
                            "current_step": "step_2_trend",
                        },
                    )
                else:
                    _insert_agent_event(conversation_id, "trend_agent", "completed", trend_analysis)
                    _persist_assistant_message(
                        "## Step 2 Skipped: Trend Analysis\n\nNo trend analysis required for this brief.",
                        metadata={
                            "workflow_mode": "autonomous",
                            "current_step": "step_2_trend",
                        },
                    )

                if plan.get("needs_competitor_analysis", True):
                    case_agent = AgenticCaseIntelligenceAgent() if AgenticCaseIntelligenceAgent is not None else CaseIntelligenceAgent()
                    _insert_agent_event(conversation_id, "case_intelligence", "started", "Running case intelligence analysis")
                    case_analysis = await case_agent.analyze_cases(brief_context)
                    _insert_agent_event(conversation_id, "case_intelligence", "completed", case_analysis)
                    _persist_assistant_message(
                        "## Step 3 Complete: Case Intelligence Analysis\n\n"
                        f"{_format_specialist_output(case_analysis, 'Case Intelligence')}",
                        metadata={
                            "workflow_mode": "autonomous",
                            "current_step": "step_3_case",
                        },
                    )
                else:
                    _insert_agent_event(conversation_id, "case_intelligence", "completed", case_analysis)
                    _persist_assistant_message(
                        "## Step 3 Skipped: Case Intelligence Analysis\n\nNo competitor/case analysis required for this brief.",
                        metadata={
                            "workflow_mode": "autonomous",
                            "current_step": "step_3_case",
                        },
                    )

                if plan.get("needs_market_landscape", True):
                    landscape_agent = AgenticMarketLandscapeAgent() if AgenticMarketLandscapeAgent is not None else MarketLandscapeAgent()
                    _insert_agent_event(conversation_id, "market_landscape", "started", "Running market landscape analysis")
                    landscape_analysis = await landscape_agent.analyze_landscape(brief_context)
                    _insert_agent_event(conversation_id, "market_landscape", "completed", landscape_analysis)
                    _persist_assistant_message(
                        "## Step 4 Complete: Market Landscape Analysis\n\n"
                        f"{_format_specialist_output(landscape_analysis, 'Market Landscape')}",
                        metadata={
                            "workflow_mode": "autonomous",
                            "current_step": "step_4_landscape",
                        },
                    )
                else:
                    _insert_agent_event(conversation_id, "market_landscape", "completed", landscape_analysis)
                    _persist_assistant_message(
                        "## Step 4 Skipped: Market Landscape Analysis\n\nNo market landscape analysis required for this brief.",
                        metadata={
                            "workflow_mode": "autonomous",
                            "current_step": "step_4_landscape",
                        },
                    )

                insight_agent = InsightGeneratorAgent()
                _insert_agent_event(conversation_id, "insight_generator", "started", "Synthesizing final recommendations")
                final_insights = await insight_agent.generate_insights(
                    brief_analysis=brief_analysis or "No brief analysis available",
                    trend_analysis=trend_analysis or "No trend analysis requested",
                    case_analysis=case_analysis or "No case analysis requested",
                    landscape_analysis=landscape_analysis or "No landscape analysis requested",
                    original_brief=original_brief,
                )
                _insert_agent_event(conversation_id, "insight_generator", "completed", final_insights)
                _persist_assistant_message(
                    "## Step 5 Complete: Insight Generation\n\n"
                    f"{final_insights}",
                    metadata={
                        "brief_analysis": brief_analysis,
                        "trend_analysis": trend_analysis,
                        "case_analysis": case_analysis,
                        "landscape_analysis": landscape_analysis,
                        "final_insights": final_insights,
                        "workflow_mode": "autonomous",
                        "current_step": "step_5_insight",
                    },
                )

                creator_agent = CreatorAgent()
                timing_value = merged_meta.get("timing", "")
                _insert_agent_event(conversation_id, "creator_agent", "started", "Generating four campaign concepts")
                creator_concepts = await creator_agent.generate_concepts(
                    brief_analysis=brief_analysis or "No brief analysis available",
                    trend_analysis=trend_analysis or "No trend analysis requested",
                    case_analysis=case_analysis or "No case analysis requested",
                    landscape_analysis=landscape_analysis or "No landscape analysis requested",
                    final_insights=final_insights,
                    original_brief=original_brief,
                    timing=timing_value,
                )
                _insert_agent_event(conversation_id, "creator_agent", "completed", creator_concepts)
                _persist_assistant_message(
                    "## Step 6 Complete: Creator Output\n\n"
                    f"{creator_concepts}",
                    metadata={
                        "brief_analysis": brief_analysis,
                        "trend_analysis": trend_analysis,
                        "case_analysis": case_analysis,
                        "landscape_analysis": landscape_analysis,
                        "final_insights": final_insights,
                        "creator_concepts": creator_concepts,
                        "workflow_mode": "autonomous",
                        "current_step": "completed",
                    },
                )

                assistant_content = creator_concepts
                assistant_msg_type = "analysis"
                processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                assistant_metadata = {
                    "brief_analysis": brief_analysis,
                    "trend_analysis": trend_analysis,
                    "case_analysis": case_analysis,
                    "landscape_analysis": landscape_analysis,
                    "final_insights": final_insights,
                    "creator_concepts": creator_concepts,
                    "processing_time_seconds": round(processing_time, 2),
                    "workflow_mode": "autonomous",
                    "current_step": "completed",
                    "required_metadata": merged_meta,
                }
                _update_state(
                    conversation_id,
                    mode="autonomous",
                    current_step="completed",
                    pipeline_status="idle",
                    pending_prompt=None,
                    required_metadata=merged_meta,
                )
            elif extracted_updates:
                assistant_msg_type = "analysis"
                assistant_content = (
                    "Metadata updated.\n\n"
                    f"{_format_metadata_confirmation_prompt(merged_meta)}"
                )
                assistant_metadata = {
                    "workflow_mode": mode,
                    "current_step": "awaiting_user_metadata_confirmation",
                    "required_metadata": merged_meta,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_metadata_confirmation",
                    pipeline_status="waiting_user",
                    pending_prompt="Review metadata and reply with 'confirm' or edit again.",
                    required_metadata=merged_meta,
                )
            else:
                assistant_msg_type = "analysis"
                assistant_content = _format_mode_selection_prompt()
                assistant_metadata = {
                    "workflow_mode": mode,
                    "current_step": "awaiting_user_mode_selection",
                    "required_metadata": merged_meta,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_mode_selection",
                    pipeline_status="waiting_user",
                    pending_prompt="Choose mode: interactive or autonomous.",
                    required_metadata=merged_meta,
                )

        elif mode == "interactive" and state.get("current_step") == "awaiting_user_creator_option" and not is_first:
            selected_option = _parse_creator_option(body.content)
            normalized = (body.content or "").strip().lower()
            if normalized in {"done", "finish", "complete", "completed"}:
                assistant_msg_type = "analysis"
                assistant_content = "Creator step completed. You can continue with normal chat."
                assistant_metadata = {
                    "workflow_mode": "interactive",
                    "current_step": "completed",
                }
                _update_state(
                    conversation_id,
                    current_step="completed",
                    pipeline_status="idle",
                    pending_prompt=None,
                )
            elif selected_option:
                creator = CreatorAgent()
                creator_concepts = _get_latest_agent_output(conversation_id, "creator_agent") or ""
                required_metadata = state.get("required_metadata") if isinstance(state.get("required_metadata"), dict) else {}
                timing_value = (required_metadata or {}).get("timing", "")

                _insert_agent_event(
                    conversation_id,
                    "creator_agent",
                    "started",
                    f"Generating creator option {selected_option}",
                )
                creator_output = await creator.generate_option_output(
                    option=selected_option,
                    concepts_output=creator_concepts,
                    timing=timing_value,
                )
                _insert_agent_event(conversation_id, "creator_agent", "completed", creator_output)

                assistant_msg_type = "analysis"
                assistant_content = (
                    f"{creator_output}\n\n"
                    "Reply with **1**, **2**, or **3** for another creator output, or **done** to finish creator step."
                )
                final_insights = _get_latest_agent_output(conversation_id, "insight_generator")
                assistant_metadata = {
                    "final_insights": final_insights,
                    "creator_concepts": creator_concepts,
                    "workflow_mode": "interactive",
                    "current_step": "awaiting_user_creator_option",
                    "selected_creator_option": selected_option,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_creator_option",
                    pipeline_status="waiting_user",
                    pending_prompt="Reply with 1 (Tagline options), 2 (4-week content calendar), or 3 (Hero ad concepts). Reply 'done' to finish.",
                )
            else:
                assistant_msg_type = "followup"
                assistant_content = (
                    "Creator step is waiting for your selection. "
                    "Reply with **1** (Tagline options), **2** (4-week content calendar), "
                    "**3** (Hero ad concepts), or **done**."
                )
                assistant_metadata = {
                    "final_insights": _get_latest_agent_output(conversation_id, "insight_generator"),
                    "creator_concepts": _get_latest_agent_output(conversation_id, "creator_agent"),
                    "workflow_mode": "interactive",
                    "current_step": "awaiting_user_creator_option",
                }

        elif mode == "interactive" and is_first:
            analyzer = BriefAnalyzerAgent()
            _insert_agent_event(conversation_id, "brief_analyzer", "started", "Interactive step 1 started")
            brief_analysis = await analyzer.analyze_brief(body.content)
            _insert_agent_event(conversation_id, "brief_analyzer", "completed", brief_analysis)

            plan = _parse_enhancement_plan(brief_analysis)
            required_metadata = _extract_metadata_from_text(body.content)
            missing_required = _missing_required_metadata(required_metadata)

            assistant_msg_type = "analysis"
            if missing_required:
                assistant_content = (
                    f"{_format_brief_analysis_output(brief_analysis, body.content)}\n\n"
                    f"{_format_missing_metadata_prompt(missing_required)}"
                )
                assistant_metadata = {
                    "brief_analysis": brief_analysis,
                    "workflow_mode": "interactive",
                    "current_step": "awaiting_user_metadata",
                    "required_metadata": required_metadata,
                    "missing_required_metadata": missing_required,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_metadata",
                    pipeline_status="waiting_user",
                    pending_prompt="Provide the required metadata fields before running specialist agents.",
                    required_metadata=required_metadata,
                )
            else:
                assistant_content = (
                    f"{_format_brief_analysis_output(brief_analysis, body.content)}\n\n"
                    f"{_format_metadata_confirmation_prompt(required_metadata)}"
                )
                assistant_metadata = {
                    "brief_analysis": brief_analysis,
                    "workflow_mode": "interactive",
                    "current_step": "awaiting_user_metadata_confirmation",
                    "required_metadata": required_metadata,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_metadata_confirmation",
                    pipeline_status="waiting_user",
                    pending_prompt="Reply with 'confirm' to continue, or edit metadata fields.",
                    required_metadata=required_metadata,
                )

        elif mode == "interactive" and state.get("current_step") in INTERACTIVE_STEPS:
            if body.content.strip().lower() not in CONTINUE_WORDS:
                current_step = state.get("current_step", "awaiting_user_continue_trend")
                assistant_msg_type = "followup"
                assistant_content = (
                    "Interactive mode is waiting for confirmation. "
                    f"Reply with **continue** to run **{_step_to_agent_label(current_step)}**."
                )
                assistant_metadata = {
                    "workflow_mode": "interactive",
                    "current_step": current_step,
                }
            else:
                original_brief = _get_first_brief(conversation_id) or body.content
                brief_analysis = _get_latest_agent_output(conversation_id, "brief_analyzer") or ""
                trend_analysis = _get_latest_agent_output(conversation_id, "trend_agent")
                case_analysis = _get_latest_agent_output(conversation_id, "case_intelligence")
                landscape_analysis = _get_latest_agent_output(conversation_id, "market_landscape")
                final_insights = _get_latest_agent_output(conversation_id, "insight_generator")
                creator_concepts = _get_latest_agent_output(conversation_id, "creator_agent")
                plan = _parse_enhancement_plan(brief_analysis)
                current_step = state.get("current_step")
                next_step = "completed"

                orchestrator = AgenticMasterOrchestrator() if AgenticMasterOrchestrator is not None else MasterOrchestrator()
                brief_context = orchestrator._extract_brief_context(original_brief)
                required_metadata = state.get("required_metadata") if isinstance(state.get("required_metadata"), dict) else {}
                brief_context.update(_metadata_to_agent_context(required_metadata))

                _update_state(
                    conversation_id,
                    current_step=current_step,
                    pipeline_status="running",
                    pending_prompt=None,
                )

                if current_step == "awaiting_user_continue_trend":
                    if plan.get("needs_trend_analysis", True):
                        agent = AgenticTrendAgent() if AgenticTrendAgent is not None else TrendAgent()
                        _insert_agent_event(conversation_id, "trend_agent", "started", "Running trend analysis")
                        trend_analysis = await agent.analyze_trends(brief_context)
                        _insert_agent_event(conversation_id, "trend_agent", "completed", trend_analysis)
                        assistant_content = (
                            "## Step 2 Complete: Trend Analysis\n\n"
                            f"{_format_specialist_output(trend_analysis, 'Trend Agent')}"
                        )
                    else:
                        trend_analysis = "No trend analysis requested"
                        _insert_agent_event(conversation_id, "trend_agent", "completed", trend_analysis)
                        assistant_content = "## Step 2 Skipped: Trend Analysis\n\nNo trend analysis required for this brief."
                    next_step = _next_interactive_step(plan, completed={"brief", "trend"})

                elif current_step == "awaiting_user_continue_case":
                    if plan.get("needs_competitor_analysis", True):
                        agent = AgenticCaseIntelligenceAgent() if AgenticCaseIntelligenceAgent is not None else CaseIntelligenceAgent()
                        _insert_agent_event(conversation_id, "case_intelligence", "started", "Running case intelligence analysis")
                        case_analysis = await agent.analyze_cases(brief_context)
                        _insert_agent_event(conversation_id, "case_intelligence", "completed", case_analysis)
                        assistant_content = (
                            "## Step 3 Complete: Case Intelligence Analysis\n\n"
                            f"{_format_specialist_output(case_analysis, 'Case Intelligence')}"
                        )
                    else:
                        case_analysis = "No case analysis requested"
                        _insert_agent_event(conversation_id, "case_intelligence", "completed", case_analysis)
                        assistant_content = "## Step 3 Skipped: Case Intelligence Analysis\n\nNo competitor/case analysis required for this brief."
                    completed = {"brief", "trend", "case"}
                    if plan.get("needs_trend_analysis", True) is False:
                        completed.add("trend")
                    next_step = _next_interactive_step(plan, completed=completed)

                elif current_step == "awaiting_user_continue_landscape":
                    if plan.get("needs_market_landscape", True):
                        agent = AgenticMarketLandscapeAgent() if AgenticMarketLandscapeAgent is not None else MarketLandscapeAgent()
                        _insert_agent_event(conversation_id, "market_landscape", "started", "Running market landscape analysis")
                        landscape_analysis = await agent.analyze_landscape(brief_context)
                        _insert_agent_event(conversation_id, "market_landscape", "completed", landscape_analysis)
                        assistant_content = (
                            "## Step 4 Complete: Market Landscape Analysis\n\n"
                            f"{_format_specialist_output(landscape_analysis, 'Market Landscape')}"
                        )
                    else:
                        landscape_analysis = "No landscape analysis requested"
                        _insert_agent_event(conversation_id, "market_landscape", "completed", landscape_analysis)
                        assistant_content = "## Step 4 Skipped: Market Landscape Analysis\n\nNo market landscape analysis required for this brief."
                    next_step = _next_interactive_step(plan, completed={"brief", "trend", "case", "landscape"})
                elif current_step == "awaiting_user_continue_insight":
                    agent = InsightGeneratorAgent()
                    _insert_agent_event(conversation_id, "insight_generator", "started", "Synthesizing final recommendations")
                    final_insights = await agent.generate_insights(
                        brief_analysis=brief_analysis or "No brief analysis available",
                        trend_analysis=trend_analysis or "No trend analysis requested",
                        case_analysis=case_analysis or "No case analysis requested",
                        landscape_analysis=landscape_analysis or "No landscape analysis requested",
                        original_brief=original_brief,
                    )
                    _insert_agent_event(conversation_id, "insight_generator", "completed", final_insights)
                    assistant_content = (
                        "## Step 5 Complete: Insight Generation\n\n"
                        f"{final_insights}"
                    )
                    next_step = "awaiting_user_continue_creator"
                elif current_step == "awaiting_user_continue_creator":
                    agent = CreatorAgent()
                    timing_value = (required_metadata or {}).get("timing", "")
                    _insert_agent_event(conversation_id, "creator_agent", "started", "Generating four campaign concepts")
                    creator_concepts = await agent.generate_concepts(
                        brief_analysis=brief_analysis or "No brief analysis available",
                        trend_analysis=trend_analysis or "No trend analysis requested",
                        case_analysis=case_analysis or "No case analysis requested",
                        landscape_analysis=landscape_analysis or "No landscape analysis requested",
                        final_insights=final_insights or "",
                        original_brief=original_brief,
                        timing=timing_value,
                    )
                    _insert_agent_event(conversation_id, "creator_agent", "completed", creator_concepts)
                    assistant_content = creator_concepts
                    next_step = "awaiting_user_creator_option"
                else:
                    # Any unexpected interactive step falls back to completed state.
                    assistant_content = "Interactive flow is complete."
                    next_step = "completed"

                if next_step == "completed":
                    assistant_metadata = {
                        "brief_analysis": brief_analysis,
                        "trend_analysis": trend_analysis,
                        "case_analysis": case_analysis,
                        "landscape_analysis": landscape_analysis,
                        "final_insights": final_insights,
                        "creator_concepts": creator_concepts,
                        "processing_time_seconds": round(
                            (datetime.now(timezone.utc) - start_time).total_seconds(),
                            2,
                        ),
                        "workflow_mode": "interactive",
                        "current_step": "completed",
                    }
                    assistant_msg_type = "analysis"
                    _update_state(
                        conversation_id,
                        current_step="completed",
                        pipeline_status="idle",
                        pending_prompt=None,
                    )
                elif next_step == "awaiting_user_creator_option":
                    assistant_msg_type = "analysis"
                    assistant_metadata = {
                        "brief_analysis": brief_analysis,
                        "trend_analysis": trend_analysis,
                        "case_analysis": case_analysis,
                        "landscape_analysis": landscape_analysis,
                        "final_insights": final_insights,
                        "creator_concepts": creator_concepts,
                        "workflow_mode": "interactive",
                        "current_step": "awaiting_user_creator_option",
                    }
                    _update_state(
                        conversation_id,
                        current_step="awaiting_user_creator_option",
                        pipeline_status="waiting_user",
                        pending_prompt="Reply with 1 (Tagline options), 2 (4-week content calendar), or 3 (Hero ad concepts).",
                    )
                else:
                    assistant_msg_type = "analysis"
                    assistant_content = (
                        f"{assistant_content}\n\nReply with **continue** to run **{_step_to_agent_label(next_step)}**."
                    )
                    assistant_metadata = {
                        "brief_analysis": brief_analysis,
                        "trend_analysis": trend_analysis,
                        "case_analysis": case_analysis,
                        "landscape_analysis": landscape_analysis,
                        "final_insights": final_insights,
                        "workflow_mode": "interactive",
                        "current_step": next_step,
                    }
                    _update_state(
                        conversation_id,
                        current_step=next_step,
                        pipeline_status="waiting_user",
                        pending_prompt=f"Reply with 'continue' to run {_step_to_agent_label(next_step)}.",
                    )
                if assistant_msg_type != "analysis":
                    assistant_msg_type = "analysis"
        elif is_first:
            _update_state(
                conversation_id,
                current_step="running_pipeline",
                pipeline_status="running",
                pending_prompt=None,
            )

            async def event_callback(event: Dict[str, Any]) -> None:
                _insert_agent_event(
                    conversation_id=conversation_id,
                    agent_name=event.get("agent_name", "unknown"),
                    status_text=event.get("status", "info"),
                    content=event.get("content"),
                    metadata=event.get("metadata") or {},
                )

            required_metadata = _extract_metadata_from_text(body.content)
            missing_required = _missing_required_metadata(required_metadata)
            if missing_required:
                brief_analysis = await BriefAnalyzerAgent().analyze_brief(body.content)
                _insert_agent_event(conversation_id, "brief_analyzer", "completed", brief_analysis)
                assistant_content = (
                    f"{_format_brief_analysis_output(brief_analysis, body.content)}\n\n"
                    f"{_format_missing_metadata_prompt(missing_required)}"
                )
                assistant_msg_type = "analysis"
                assistant_metadata = {
                    "brief_analysis": brief_analysis,
                    "workflow_mode": "autonomous",
                    "current_step": "awaiting_user_metadata",
                    "required_metadata": required_metadata,
                    "missing_required_metadata": missing_required,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_metadata",
                    pipeline_status="waiting_user",
                    pending_prompt="Provide the required metadata fields before running specialist agents.",
                    required_metadata=required_metadata,
                )
            else:
                assistant_msg_type = "analysis"
                assistant_content = (
                    f"{_format_metadata_confirmation_prompt(required_metadata)}"
                )
                assistant_metadata = {
                    "workflow_mode": "autonomous",
                    "current_step": "awaiting_user_metadata_confirmation",
                    "required_metadata": required_metadata,
                }
                _update_state(
                    conversation_id,
                    current_step="awaiting_user_metadata_confirmation",
                    pipeline_status="waiting_user",
                    pending_prompt="Reply with 'confirm' to continue, or edit metadata fields.",
                    required_metadata=required_metadata,
                )
        else:
            history_result = (
                db.table("messages")
                .select("role, content, message_type")
                .eq("conversation_id", conversation_id)
                .order("created_at", desc=False)
                .limit(20)
                .execute()
            )
            history = history_result.data or []

            followup_agent = FollowUpAgent()
            assistant_content = await followup_agent.chat(
                message=body.content,
                history=history,
            )
            assistant_msg_type = "followup"
            _insert_agent_event(
                conversation_id,
                "followup_agent",
                "completed",
                assistant_content,
            )

    except Exception as e:
        _update_state(
            conversation_id,
            current_step="error",
            pipeline_status="failed",
            pending_prompt="Fix error and retry.",
        )
        _insert_agent_event(
            conversation_id,
            "master_orchestrator",
            "failed",
            str(e),
        )
        raise HTTPException(
            status_code=500,
            detail=f"AI pipeline failed: {str(e)}",
        )

    if persisted_assistant_msg is not None:
        db.table("conversations").update(
            {"updated_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", conversation_id).execute()
        return persisted_assistant_msg

    asst_result = (
        db.table("messages")
        .insert(
            {
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": assistant_content,
                "message_type": assistant_msg_type,
                "metadata": assistant_metadata,
            }
        )
        .execute()
    )
    if not asst_result.data:
        raise HTTPException(status_code=500, detail="Failed to save assistant message")

    db.table("conversations").update(
        {"updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", conversation_id).execute()

    return asst_result.data[0]


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_or_guest_user),
):
    _verify_ownership(conversation_id, user)
    db = get_supabase_admin()
    db.table("conversations").delete().eq("id", conversation_id).execute()
