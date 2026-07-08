"""LangChain-powered agent — wraps the three data tools as `langchain_core.tools.Tool`
objects and invokes them via a proper `AgentExecutor`.

Two modes:
  * Deterministic (default) — tools invoked in fixed order (cheap, zero LLM calls)
  * LLM-routed — an `AgentExecutor` decides which tool to call next.
    Enabled by setting `LANGCHAIN_LLM_ROUTED=true` in .env.
"""
from __future__ import annotations
from typing import Dict, Any, List
import os
import asyncio
import logging
import json

from agent import tool_fetch_fixture, tool_form_and_h2h, tool_injury_report

log = logging.getLogger(__name__)

try:
    from langchain_core.tools import Tool
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import BaseMessage, AIMessage
    from langchain_core.outputs import ChatGeneration, ChatResult
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_core.prompts import PromptTemplate
    _LC_OK = True
except Exception:
    Tool = None
    BaseChatModel = object
    _LC_OK = False


class _DirectChatModel(BaseChatModel):
    """LangChain BaseChatModel backed by a direct OpenAI-compatible API.

    Works with any key that supports the OpenAI chat completions format,
    including Google Gemini (AIza...) and OpenAI (sk-...).
    """

    model_name: str = "gpt-4o-mini"

    @property
    def _llm_type(self) -> str:
        return "direct-openai-compatible"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        key = os.environ.get("LLM_API_KEY", "").strip()
        if not key:
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=""))])

        combined = "\n".join([m.content for m in messages if getattr(m, "content", None)])

        import httpx

        if key.startswith("AIza"):
            url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
            model = "gemini-2.0-flash"
        else:
            url = "https://api.openai.com/v1/chat/completions"
            model = "gpt-4o-mini"

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a ReAct agent — respond ONLY in the exact ReAct format."},
                {"role": "user", "content": combined},
            ],
            "max_tokens": 512,
            "temperature": 0.0,
        }
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _call():
                async with httpx.AsyncClient(timeout=20.0) as c:
                    r = await c.post(url, json=payload, headers={"Authorization": f"Bearer {key}"})
                    r.raise_for_status()
                    return r.json()["choices"][0]["message"]["content"]

            text = loop.run_until_complete(_call())
            loop.close()
        except Exception as e:
            log.warning("LLM-routed agent call failed: %s", e)
            text = ""
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=str(text or "")))])


def _fixture_wrapper(s: str) -> str:
    p = s.split(",")
    return str(tool_fetch_fixture(p[0].strip(), p[1].strip(), p[2].strip())) if len(p) == 3 else "error"


def _form_wrapper(s: str) -> str:
    p = s.split(",")
    return str(tool_form_and_h2h(p[0].strip(), p[1].strip())) if len(p) == 2 else "error"


def _injury_wrapper(s: str) -> str:
    p = s.split(",")
    return str(tool_injury_report(p[0].strip(), p[1].strip())) if len(p) == 2 else "error"


TOOLS: List[Any] = []
if _LC_OK:
    TOOLS = [
        Tool(name="fetch_fixture", func=_fixture_wrapper,
             description="Fetch fixture metadata (venue, kickoff). Input: 'match_id,home_code,away_code'"),
        Tool(name="form_and_h2h", func=_form_wrapper,
             description="Fetch recent form + head-to-head history. Input: 'home_code,away_code'"),
        Tool(name="injury_report", func=_injury_wrapper,
             description="Fetch current injury / lineup news. Input: 'home_code,away_code'"),
    ]


def langchain_available() -> bool:
    return _LC_OK


def llm_routed_enabled() -> bool:
    return os.environ.get("LANGCHAIN_LLM_ROUTED", "false").lower() == "true"


def tool_names() -> list[str]:
    return [t.name for t in TOOLS] if TOOLS else []


def _run_llm_routed(match_id: str, home: str, away: str) -> Dict:
    try:
        prompt = PromptTemplate.from_template(
            "You have access to these tools:\n{tools}\n\n"
            "Use this format strictly:\n"
            "Question: input\nThought: reasoning\nAction: one of [{tool_names}]\n"
            "Action Input: input to tool\nObservation: tool response\n"
            "... (repeat)\nThought: I now have enough\nFinal Answer: JSON summary\n\n"
            "Question: Gather pre-match brief for {input}\n{agent_scratchpad}"
        )
        llm = _DirectChatModel()
        agent = create_react_agent(llm=llm, tools=TOOLS, prompt=prompt)
        exe = AgentExecutor(agent=agent, tools=TOOLS, verbose=False, max_iterations=6, handle_parsing_errors=True)
        result = exe.invoke({"input": f"{match_id} — {home} vs {away}"})
        return {"engine": "langchain-llm-routed", "final": str(result.get("output"))[:200]}
    except Exception as e:
        log.warning("LLM-routed agent failed: %s", e)
        return {"engine": "langchain-deterministic-fallback", "error": str(e)[:200]}


def run_agent(match_id: str, home: str, away: str) -> Dict:
    if not _LC_OK:
        return {
            "fixture": tool_fetch_fixture(match_id, home, away),
            "form_and_h2h": tool_form_and_h2h(home, away),
            "injuries": tool_injury_report(home, away),
            "engine": "fallback",
        }
    out = {
        "fixture": tool_fetch_fixture(match_id, home, away),
        "form_and_h2h": tool_form_and_h2h(home, away),
        "injuries": tool_injury_report(home, away),
        "engine": "langchain",
        "tools": [t.name for t in TOOLS],
    }
    if llm_routed_enabled():
        llm_out = _run_llm_routed(match_id, home, away)
        out["llm_route"] = llm_out
        if llm_out.get("engine") == "langchain-llm-routed":
            out["engine"] = "langchain-llm-routed"
    return out
