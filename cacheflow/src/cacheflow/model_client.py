"""Model client interface for AKV integration."""

import json
import time
from typing import Any, Dict, List, Optional, Callable, Literal
from abc import ABC, abstractmethod
import requests

from .errors import ModelClientError
from .state import RunState, ToolExecution, NodeOutput, NodeStatus, RunStatus
from .events import EventType, TraceLogger


class MockModelClient:
    """Mock model client for offline testing."""

    def __init__(self):
        """Initialize mock client."""
        self.request_history: List[Dict[str, Any]] = []
        self.response_history: List[Dict[str, Any]] = []
        self.tool_calls_seen: List[Dict[str, Any]] = []
        self.simulated_usage: Dict[str, float] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "cached_tokens": 0,
            "drop_skipped_tokens": 0,
            "repos_tokens": 0,
        }
        self.error_pattern: Optional[Callable[[], Exception]] = None
        self.timeouts: Optional[Callable[[float], None]] = None

    def send_request(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        stream: bool = False,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Simulate sending an LLM request and receiving a response."""
        try:
            if self.error_pattern and self.error_pattern():
                raise self.error_pattern()

            # Simulate network delay if configured
            if self.timeouts and self.timeouts(0.1):
                pass  # Handled by asyncio or timeout context

            # Generate mock response based on last tool call, else generic response
            content = ""
            if messages:
                last_user = messages[-1].get("role") == "user"
                if last_user:
                    content = f"Mock response to user message #{len(messages)}. Verdict: reachable."
                else:
                    content = "MOCK_ASSISTANT_RESPONSE"

            # Record requests
            full_payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "max_tokens": max_tokens,
                "usage": {"prompt_tokens": 100 + (len(messages) * 5), "completion_tokens": 20, "total_tokens": 120},
            }
            self.request_history.append(json.dumps(full_payload))

            # Generate mock tool calls
            tool_results = []
            for i in range(min(len(messages), 3)):
                msg = messages[i]
                if msg.get("role") == "assistant" and isinstance(msg.get("tool_calls"), list):
                    tc = msg["tool_calls"][0]
                    call_id = tc.get("id", "")
                    tool_name = tc.get("function", {}).get("name", "")
                    args = tc.get("function", {}).get("arguments", {})
                    self.tool_calls_seen.append({"call_id": call_id, "tool": tool_name, "args": args})
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": json.dumps({
                            "output": f"[mock output for {tool_name}]",
                            "truncated": False,
                            "metadata": {},
                        }),
                    })

            mock_response = {
                "id": "chatcmpl-mock-001",
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content,
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 100 + (len(messages) * 5),
                    "completion_tokens": 20,
                    "total_tokens": 120,
                },
            }

            # Inject tool results if any were requested
            if tool_results:
                full_response = {
                    "id": "chatcmpl-mock-001",
                    "object": "chat.completion",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": content,
                            },
                            "finish_reason": "tool_calls",
                        }
                    ],
                    "tool_calls": [],  # Actual tool results inserted separately
                    "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
                }

            # Simulated usage stats
            self.simulated_usage["prompt_tokens"] += len(messages)
            self.simulated_usage["completion_tokens"] += 20
            self.simulated_usage["cached_tokens"] += len(messages) // 2
            self.simulated_usage["drop_skipped_tokens"] += len(messages) - len(messages) // 2

            self.response_history.append(json.dumps(mock_response))

            return mock_response if not tool_results else full_response

        except requests.Timeout:
            raise ModelClientError("Request timed out")
        except requests.ConnectionError:
            raise ModelClientError("Cannot connect to model server")
        except requests.RequestException as e:
            raise ModelClientError(f"Request failed: {e}")
        except Exception as e:
            raise ModelClientError(f"Unexpected error in mock client: {e}")


class AKVModelClient:
    """AKV model client using official AKV integration."""

    def __init__(self, server_url: str, api_key: Optional[str] = None, model: str = "default"):
        """Initialize AKV model client."""
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}" if api_key else "", "Content-Type": "application/json"})
        self.endpoint = f"{self.server_url}/v1/chat/completions"

    def is_available(self) -> bool:
        """Check if AKV server is reachable."""
        try:
            resp = self.session.get(f"{self.server_url}/health", timeout=5)
            return resp.status_code < 500
        except requests.RequestException:
            return False

    def send_request(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        stream: bool = False,
        max_tokens: int = 1024,
        extra_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Send a chat completion request via AKV."""
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": stream,
            "max_tokens": max_tokens,
            **(extra_kwargs or {}),
        }

        try:
            resp = self.session.post(self.endpoint, json=payload, timeout=30)
            resp.raise_for_status()
        except requests.Timeout:
            raise ModelClientError("AKV request timed out")
        except requests.ConnectionError:
            raise ModelClientError("Cannot connect to AKV server")
        except requests.HTTPError as e:
            raise ModelClientError(f"HTTP error from AKV: {e}")
        except requests.RequestException as e:
            raise ModelClientError(f"AKV request failed: {e}")

        try:
            result = resp.json()
        except json.JSONDecodeError:
            raise ModelClientError("Invalid JSON response from AKV")

        # Extract usage if available
        if "usage" in result:
            result["usage_details"] = result["usage"]

        return result


class RunController:
    """Coordinates model client, tools, cache controller, and DAG execution."""

    def __init__(
        self,
        run_state: RunState,
        dag: Any,
        model_client: AKVModelClient,
        trace_logger: TraceLogger,
        cache_controller: Optional[Any] = None,
        tool_registry: Optional[Any] = None,
    ):
        """Initialize the run controller."""
        self.run_state = run_state
        self.dag = dag
        self.model_client = model_client
        self.trace = trace_logger
        self.cache_controller = cache_controller
        self.tools = tool_registry

    def submit_model_request(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Submit a model request with trace logging."""
        self.trace.log(EventType.MODEL_REQUEST_SENT, model="unknown", message_count=len(messages))

        response = self.model_client.send_request(messages, self.model_client.model)

        self.trace.log(EventType.MODEL_RESPONSE_RECEIVED, model=self.model_client.model, status="ok")
        return response

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: RunState = None) -> Any:
        """Execute a tool with trace logging and validation."""
        if state is None:
            state = self.run_state

        if not self.tools:
            raise RuntimeError("Tool registry not initialized")

        tool_fn = getattr(self.tools, tool_name, None)
        if tool_fn is None:
            raise ToolExecutionError(f"Unknown tool: {tool_name}")

        # Validate tool exists
        if not hasattr(tool_fn, '__call__'):
            raise ToolExecutionError(f"Tool '{tool_name}' has no callable implementation")

        execution_id = str(hash(f"{tool_name}:{canonicalize(arguments)}"))
        start_time = time.time()

        try:
            result = tool_fn(**arguments)

            # Track execution
            end_time = time.time()
            state.add_tool_execution(ToolExecution(
                execution_id=execution_id,
                tool_name=tool_name,
                arguments=arguments,
                output=result,
                status="success",
                timestamp=datetime.utcnow(),
            ))

            self.trace.log(EventType.TOOL_EXECUTED,
                          tool=tool_name, status="success", latency_ms=round((end_time - start_time) * 1000, 3))

            return result

        except Exception as e:
            duration = round((end_time - start_time) * 1000, 3)
            state.add_tool_execution(ToolExecution(
                execution_id=execution_id,
                tool_name=tool_name,
                arguments=arguments,
                output={"error": str(e)},
                status="failed",
                timestamp=datetime.utcnow(),
            ))

            self.trace.log(EventType.TOOL_EXECUTED,
                          tool=tool_name, status="failed", latency_ms=duration, error=str(e))
            raise ToolExecutionError(f"Tool '{tool_name}' failed: {e}") from e


def canonicalize(value: Any) -> Any:
    """Canonicalize arbitrary value for deterministic comparison."""
    if isinstance(value, dict):
        return {k: canonicalize(v) for k, v in sorted(value.items())}
    elif isinstance(value, list):
        return [canonicalize(item) for item in value]
    return value