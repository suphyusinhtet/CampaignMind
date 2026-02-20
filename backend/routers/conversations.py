# routers/conversations.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from auth.dependencies import get_current_user
from db.supabase_client import get_supabase_admin
from agents.orchestrator import MasterOrchestrator
from agents.followup_agent import FollowUpAgent

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


# ── Request / Response Models ────────────────────────────────────────────────

class ConversationCreate(BaseModel):
    title: Optional[str] = None


class MessageCreate(BaseModel):
    content: str


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
    user_id: str
    title: str
    created_at: str
    updated_at: str
    messages: Optional[List[MessageOut]] = None


# ── Helpers ──────────────────────────────────────────────────────────────────

def _auto_title(content: str) -> str:
    """Generate a conversation title from the first 60 chars of the brief."""
    title = content.strip().replace("\n", " ")
    return (title[:57] + "...") if len(title) > 60 else title


def _is_first_message(conversation_id: str) -> bool:
    """Return True if the conversation has no messages yet."""
    db = get_supabase_admin()
    result = (
        db.table("messages")
        .select("id")
        .eq("conversation_id", conversation_id)
        .limit(1)
        .execute()
    )
    return len(result.data) == 0


def _verify_ownership(conversation_id: str, user_id: str) -> dict:
    """
    Fetch the conversation and verify it belongs to user_id.
    Raises HTTP 404 if not found or not owned by the user.
    """
    db = get_supabase_admin()
    result = (
        db.table("conversations")
        .select("*")
        .eq("id", conversation_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result.data


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.post("", response_model=ConversationOut, status_code=201)
async def create_conversation(
    body: ConversationCreate,
    user: dict = Depends(get_current_user),
):
    """Create a new empty conversation for the authenticated user."""
    db = get_supabase_admin()
    result = (
        db.table("conversations")
        .insert({"user_id": user["sub"], "title": body.title or "New Conversation"})
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create conversation")
    return result.data[0]


@router.get("", response_model=List[ConversationOut])
async def list_conversations(
    user: dict = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    """List the authenticated user's conversations, newest first."""
    db = get_supabase_admin()
    result = (
        db.table("conversations")
        .select("*")
        .eq("user_id", user["sub"])
        .order("updated_at", desc=True)
        .limit(limit)
        .offset(offset)
        .execute()
    )
    return result.data


@router.get("/{conversation_id}", response_model=ConversationOut)
async def get_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    """Get a conversation with all its messages."""
    conv = _verify_ownership(conversation_id, user["sub"])
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


@router.post("/{conversation_id}/messages", response_model=MessageOut)
async def send_message(
    conversation_id: str,
    body: MessageCreate,
    user: dict = Depends(get_current_user),
):
    """
    Send a user message to a conversation and receive an AI response.

    First message  → runs the full MasterOrchestrator pipeline (10–40 s).
    Follow-up      → lightweight FollowUpAgent with conversation history (2–5 s).

    The returned MessageOut is the *assistant* response message.
    The user message is also persisted but not returned (fetch via GET /{id}).
    """
    _verify_ownership(conversation_id, user["sub"])

    db = get_supabase_admin()
    is_first = _is_first_message(conversation_id)
    user_msg_type = "brief" if is_first else "followup"

    # Persist user message
    user_msg_result = (
        db.table("messages")
        .insert({
            "conversation_id": conversation_id,
            "role": "user",
            "content": body.content,
            "message_type": user_msg_type,
        })
        .execute()
    )
    if not user_msg_result.data:
        raise HTTPException(status_code=500, detail="Failed to save user message")

    # Auto-set conversation title from first message
    if is_first:
        db.table("conversations").update(
            {"title": _auto_title(body.content)}
        ).eq("id", conversation_id).execute()

    # Generate AI response
    start_time = datetime.now(timezone.utc)
    assistant_content: str
    assistant_metadata: Optional[dict] = None
    assistant_msg_type: str

    try:
        if is_first:
            # Full multi-agent pipeline
            orchestrator = MasterOrchestrator()
            results = await orchestrator.enhance_brief(brief=body.content)

            assistant_content = results["final_insights"]
            assistant_msg_type = "analysis"
            processing_time = (
                datetime.now(timezone.utc) - start_time
            ).total_seconds()

            # Store all sub-analyses in metadata for frontend expandable sections
            assistant_metadata = {
                "brief_analysis": results.get("brief_analysis"),
                "trend_analysis": results.get("trend_analysis"),
                "case_analysis": results.get("case_analysis"),
                "landscape_analysis": results.get("landscape_analysis"),
                "processing_time_seconds": round(processing_time, 2),
            }
        else:
            # Fetch last 20 messages for context window
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

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI pipeline failed: {str(e)}",
        )

    # Persist assistant message
    asst_result = (
        db.table("messages")
        .insert({
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": assistant_content,
            "message_type": assistant_msg_type,
            "metadata": assistant_metadata,
        })
        .execute()
    )
    if not asst_result.data:
        raise HTTPException(status_code=500, detail="Failed to save assistant message")

    # Touch conversation updated_at so sidebar ordering stays current
    db.table("conversations").update(
        {"updated_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", conversation_id).execute()

    return asst_result.data[0]


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
):
    """Delete a conversation and all its messages (cascaded by FK constraint)."""
    _verify_ownership(conversation_id, user["sub"])
    db = get_supabase_admin()
    db.table("conversations").delete().eq("id", conversation_id).execute()
