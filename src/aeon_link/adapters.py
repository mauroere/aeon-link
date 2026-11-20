"""Transport payload MAPPINGS only — not A2A or MCP server/client implementations."""
from __future__ import annotations

from .core import ProtocolError, validate_envelope, VERSION


def as_a2a_data_part(envelope: dict) -> dict:
    """Place validated envelope in an A2A structured-data Part."""
    validate_envelope(envelope)
    return {"data": {"aeon_link": envelope}, "metadata": {"aeon_link_version": VERSION}}


def from_a2a_data_part(part: dict) -> dict:
    try:
        envelope = part["data"]["aeon_link"]
    except (KeyError, TypeError) as exc:
        raise ProtocolError("A2A Part lacks aeon_link data") from exc
    return validate_envelope(envelope)


def as_mcp_tool_result(envelope: dict) -> dict:
    """Example MCP structuredContent result body; not an MCP transport connection."""
    validate_envelope(envelope)
    return {"structuredContent": {"aeon_link": envelope}, "isError": False}


def from_mcp_tool_result(result: dict) -> dict:
    try:
        envelope = result["structuredContent"]["aeon_link"]
    except (KeyError, TypeError) as exc:
        raise ProtocolError("MCP result lacks aeon_link structuredContent") from exc
    return validate_envelope(envelope)
