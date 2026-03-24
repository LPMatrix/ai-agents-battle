import json
from typing import Any

import httpx

BASE_URL = "https://battle-tank-arena.vercel.app/api/mcp"
TANK_NAME = "Matrix"

# Streamable HTTP transport (see mcp.client.streamable_http)
_ACCEPT = "application/json, text/event-stream"
_INIT_PROTOCOL_VERSION = "2025-03-26"


class MCPClient:
    """Minimal synchronous MCP Streamable HTTP client."""

    def __init__(self) -> None:
        self._http = httpx.Client(timeout=60.0)
        self._session_id: str | None = None
        self._protocol_version: str | None = None
        self._next_id = 0
        self._extra_headers = {"x-player-token": TANK_NAME}
        self._initialized = False

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "MCPClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {
            "Accept": _ACCEPT,
            "Content-Type": "application/json",
            **self._extra_headers,
        }
        if self._session_id:
            h["mcp-session-id"] = self._session_id
        if self._protocol_version:
            h["mcp-protocol-version"] = self._protocol_version
        return h

    def _rpc_id(self) -> int:
        self._next_id += 1
        return self._next_id

    @staticmethod
    def _parse_jsonrpc_response(response: httpx.Response) -> dict[str, Any]:
        if response.status_code == 202:
            return {}
        ct = (response.headers.get("content-type") or "").split(";")[0].strip().lower()
        raw = response.text
        if ct == "text/event-stream" or (
            ct != "application/json" and "event:" in raw[:200]
        ):
            last: dict[str, Any] | None = None
            for line in raw.splitlines():
                if line.startswith("data:"):
                    chunk = line[5:].strip()
                    if not chunk:
                        continue
                    try:
                        last = json.loads(chunk)
                    except json.JSONDecodeError:
                        continue
            if last is None:
                raise ValueError(
                    f"No JSON payload in SSE response (status {response.status_code})"
                )
            return last
        return response.json()

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        init = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": _INIT_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "battle-tank-client", "version": "1.0.0"},
            },
            "id": self._rpc_id(),
        }
        r = self._http.post(BASE_URL, json=init, headers=self._headers())
        r.raise_for_status()
        sid = r.headers.get("mcp-session-id")
        if sid:
            self._session_id = sid
        body = self._parse_jsonrpc_response(r)
        if body.get("error"):
            raise RuntimeError(body["error"])
        result = body.get("result") or {}
        self._protocol_version = result.get("protocolVersion") or _INIT_PROTOCOL_VERSION

        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        }
        r2 = self._http.post(BASE_URL, json=notif, headers=self._headers())
        if r2.status_code not in (200, 202):
            r2.raise_for_status()

        self._initialized = True

    def _parse(self, response: dict) -> dict:
        return json.loads(response["content"][0]["text"])

    def _call(self, tool: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._ensure_initialized()
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool,
                "arguments": params or {},
            },
            "id": self._rpc_id(),
        }
        response = self._http.post(BASE_URL, json=payload, headers=self._headers())
        response.raise_for_status()
        body = self._parse_jsonrpc_response(response)
        if body.get("error"):
            raise RuntimeError(body["error"])
        return body.get("result") or body

    def register(self) -> dict[str, Any]:
        return self._call("register", {"name": TANK_NAME})

    def get_valid_actions(self) -> dict[str, Any]:
        return self._call("get_valid_actions")

    def get_game_state(self) -> dict[str, Any]:
        return self._call("get_game_state")

    def rotate(self, direction: str) -> dict:
        return self._parse(self._call("rotate", {"direction": direction}))

    def move(self, die: int) -> dict:
        return self._parse(self._call("move", {"die": die}))

    def fire(self, die: int) -> dict:
        return self._parse(self._call("fire", {"die": die}))
