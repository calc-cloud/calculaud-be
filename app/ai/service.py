import json
import logging
from typing import Any

import openai
from fastapi import Request
from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from fastmcp.tools import Tool

from app.ai.exceptions import OpenAIError
from app.config import settings

logger = logging.getLogger(__name__)


def convert_mcp_tools_to_openai(mcp_tools: list[Tool]) -> list[dict[str, Any]]:
    """Convert MCP tools to OpenAI function calling format with simplified schema."""
    openai_tools = []

    for tool in mcp_tools:
        print(tool)
        # Create minimal, clean parameter schema
        parameters = {"type": "object", "properties": {}, "required": []}

        # Extract only essential parameters from MCP schema
        mcp_schema = getattr(tool, "inputSchema", {})
        if "properties" in mcp_schema:
            for prop_name, prop_def in mcp_schema["properties"].items():
                # Simplify parameter definitions
                if prop_name == "search":
                    parameters["properties"]["search"] = {
                        "type": "string",
                        "description": "Search term to filter suppliers by name (optional)",
                    }
                elif prop_name == "page":
                    parameters["properties"]["page"] = {
                        "type": "integer",
                        "description": "Page number for pagination (default: 1)",
                        "default": 1,
                    }
                elif prop_name == "limit":
                    parameters["properties"]["limit"] = {
                        "type": "integer",
                        "description": "Number of items per page (default: 100)",
                        "default": 100,
                    }

        # Convert MCP tool to OpenAI function format
        openai_tool = {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": parameters,
            },
        }
        openai_tools.append(openai_tool)
        logger.info(f"Converted MCP tool: {tool.name} with simplified schema")

    return openai_tools


async def ask_ai_with_mcp(question: str, request: Request) -> str:
    """Send question to any LLM with MCP tools using FastMCP client."""
    if not settings.llm_api_key:
        raise OpenAIError("LLM API key not configured")

    try:
        # Initialize universal LLM client
        client = openai.AsyncOpenAI(
            base_url=settings.llm_base_url, api_key=settings.llm_api_key
        )

        # Extract authorization token from request headers
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise OpenAIError("Authorization token required for MCP server access")

        # Extract the token (remove "Bearer " prefix)
        token = auth_header.split(" ", 1)[1]

        # Connect to MCP server using FastMCP client with authentication
        async with Client(
            settings.mcp_server_url, auth=BearerAuth(token=token)
        ) as mcp_client:
            # Get tools from MCP server
            mcp_tools = await mcp_client.list_tools()
            logger.info(f"Found {len(mcp_tools)} tools from MCP server")

            # Convert MCP tools to OpenAI function format
            openai_tools = convert_mcp_tools_to_openai(mcp_tools)

            # Prepare messages with directive system prompt
            system_prompt = (
                "You are a procurement system assistant. You MUST use the available tools "
                "to answer questions about procurement data. "
                "NEVER provide generic answers - ALWAYS call tools first to get real data.\n\n"
                "Examples:\n"
                "- User asks 'show me suppliers' → CALL get_suppliers tool immediately\n"
                "- User asks 'find Google suppliers' → CALL get_suppliers tool with search='Google'\n"
                "- User asks 'list all suppliers' → CALL get_suppliers tool with no search parameter\n\n"
                "Instructions:\n"
                "1. Identify if the question is about procurement data (suppliers, purposes, purchases, costs)\n"
                "2. If yes, immediately call the appropriate tool\n"
                "3. Use the tool results to provide a helpful answer\n"
                "4. If no relevant tool exists, say so clearly"
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ]

            # Determine tool choice strategy based on question content
            procurement_keywords = [
                "supplier",
                "suppliers",
                "vendor",
                "vendors",
                "purpose",
                "purposes",
                "purchase",
                "purchases",
                "cost",
                "costs",
                "hierarchy",
                "hierarchies",
            ]

            is_procurement_query = any(
                keyword in question.lower() for keyword in procurement_keywords
            )

            # Force tool usage for procurement queries
            tool_choice = (
                "required" if is_procurement_query and openai_tools else "auto"
            )

            # Debug: Log request details
            logger.info("Sending request to LLM:")
            logger.info(f"Model: {settings.model_name}")
            logger.info(f"Question: {question}")
            logger.info(f"Is procurement query: {is_procurement_query}")
            logger.info(f"Tools count: {len(openai_tools)}")
            logger.info(f"Tool choice: {tool_choice}")

            # Call LLM with tools
            response = await client.chat.completions.create(
                model=settings.model_name,
                messages=messages,
                tools=openai_tools if openai_tools else None,
                tool_choice=tool_choice,
            )

            # Debug: Log response details
            message = response.choices[0].message
            logger.info("LLM Response received:")
            logger.info(f"Message content: {message.content}")
            logger.info(f"Message role: {message.role}")
            logger.info(
                f"Tool calls count: {len(message.tool_calls) if message.tool_calls else 0}"
            )

            if message.tool_calls:
                for i, tc in enumerate(message.tool_calls):
                    logger.info(
                        f"Tool call {i}: {tc.function.name} with args: {tc.function.arguments}"
                    )
            else:
                logger.warning("NO TOOL CALLS MADE - LLM chose not to use tools!")
                logger.info(f"Full response object: {response}")
                logger.info(
                    f"Response usage: {getattr(response, 'usage', 'No usage info')}"
                )
                logger.info(
                    f"Response model: {getattr(response, 'model', 'No model info')}"
                )

            # Handle tool calls
            if message.tool_calls:
                # Add assistant message with tool calls
                messages.append(
                    {
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in message.tool_calls
                        ],
                    }
                )

                # Execute each tool call via FastMCP
                for tool_call in message.tool_calls:
                    try:
                        # Parse arguments
                        arguments = json.loads(tool_call.function.arguments)
                        logger.info(
                            f"Executing tool: {tool_call.function.name} with args: {arguments}"
                        )

                        # Execute tool via FastMCP client
                        result = await mcp_client.call_tool(
                            tool_call.function.name, arguments
                        )

                        # Extract result data from MCP response
                        if result.content and len(result.content) > 0:
                            tool_result = result.content[0].text
                        else:
                            tool_result = str(result)
                        logger.info(
                            f"Tool {tool_call.function.name} returned: {tool_result[:200]}..."
                        )

                        # Add tool result to messages
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": tool_result,
                            }
                        )

                    except Exception as e:
                        logger.error(
                            f"Error executing tool {tool_call.function.name}: {e}"
                        )
                        # Add error result
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": tool_call.function.name,
                                "content": f"Error: {str(e)}",
                            }
                        )

                # Get final response
                final_response = await client.chat.completions.create(
                    model=settings.model_name, messages=messages
                )

                return (
                    final_response.choices[0].message.content
                    or "I couldn't generate a response."
                )

            return message.content or "I couldn't generate a response."

    except openai.OpenAIError as e:
        logger.error(f"LLM API error: {e}")
        raise OpenAIError(str(e))
    except Exception as e:
        logger.error(f"Unexpected error in ask_ai_with_mcp: {e}")
        raise OpenAIError(f"Unexpected error: {str(e)}")
