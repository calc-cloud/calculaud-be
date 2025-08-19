import logging

import openai
from agents import Agent, Runner, set_default_openai_client
from agents.mcp import MCPServerStreamableHttp
from fastapi import Request

from app.ai.exceptions import OpenAIError
from app.config import settings

logger = logging.getLogger(__name__)


def extract_bearer_token(request: Request) -> str:
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise OpenAIError("Authorization token required for MCP server access")

    # Extract the token (remove "Bearer " prefix)
    return auth_header.split(" ", 1)[1]


async def ask_ai_with_mcp(question: str, request: Request) -> str:
    """Send question to AI agent with MCP tools using OpenAI Agents SDK."""
    if not settings.llm_api_key:
        raise OpenAIError("LLM API key not configured")

    try:
        # Configure global OpenAI client for OpenAI-compatible APIs
        set_default_openai_client(
            openai.AsyncOpenAI(
                base_url=settings.llm_base_url, api_key=settings.llm_api_key
            )
        )

        # Use MCP server as async context manager for proper lifecycle management
        async with MCPServerStreamableHttp(
            params={
                "url": settings.mcp_server_url,
                "headers": {"Authorization": f"Bearer {extract_bearer_token(request)}"},
                "timeout": 60,
            },
            cache_tools_list=True,
            name="Calculaud MCP Server",
        ) as mcp_server:

            # Create agent with MCP server integration
            agent = Agent(
                name="Procurement Assistant",
                instructions=(
                    "You are a procurement system assistant. You MUST use the available tools "
                    "to answer questions about procurement data. "
                    "NEVER provide generic answers - ALWAYS call tools first to get real data."
                ),
                model=settings.model_name,
                mcp_servers=[mcp_server],
            )

            response = await Runner.run(agent, question)
            return response.final_output or "I couldn't generate a response."

    except openai.OpenAIError as e:
        logger.error(f"LLM API error: {e}")
        raise OpenAIError(str(e))
    except Exception as e:
        logger.error(f"Unexpected error in ask_ai_with_mcp: {e}")
        raise OpenAIError(f"Unexpected error: {str(e)}")
