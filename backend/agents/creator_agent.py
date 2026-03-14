# agents/creator_agent.py
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from agents.base_agent import CampaignMindAgent


class CreatorAgent(CampaignMindAgent):
    """
    Builds campaign concept outputs after strategic insights.
    """

    def __init__(self):
        super().__init__("creator_agent")

    async def generate_concepts(
        self,
        brief_analysis: str,
        trend_analysis: str,
        case_analysis: str,
        landscape_analysis: str,
        final_insights: str,
        original_brief: str,
        timing: str = "",
    ) -> str:
        timing_line = timing.strip() or "No timing metadata provided"
        prompt = f"""Generate FOUR distinct Big Campaign Ideas from the inputs below.

ORIGINAL BRIEF:
{original_brief}

TIMING METADATA:
{timing_line}

BRIEF ANALYSIS:
{brief_analysis}

TREND ANALYSIS:
{trend_analysis}

CASE INTELLIGENCE:
{case_analysis}

MARKET LANDSCAPE:
{landscape_analysis}

STRATEGIC INSIGHT SUMMARY:
{final_insights}

Return only markdown using your required format.
At the end include this exact instruction line:
"Reply with 1 (Tagline options), 2 (4-week content calendar), or 3 (Hero ad concepts)."
"""
        response = await self.agent.on_messages(
            [TextMessage(content=prompt, source="user")],
            CancellationToken(),
        )
        return response.chat_message.content

    async def generate_option_output(
        self,
        option: str,
        concepts_output: str,
        timing: str = "",
    ) -> str:
        prompt = f"""Using the campaign concepts below, generate option {option}.

CAMPAIGN CONCEPTS:
{concepts_output}

TIMING METADATA:
{timing or "No timing metadata provided"}

Rules:
- If option is 1: generate tagline options.
- If option is 2: generate a practical 4-week content calendar aligned to timing.
- If option is 3: generate hero ad concepts.
- Keep output markdown and execution-ready.
- Do not ask follow-up questions.
- Do not include any "next move" section.
"""
        response = await self.agent.on_messages(
            [TextMessage(content=prompt, source="user")],
            CancellationToken(),
        )
        return response.chat_message.content

