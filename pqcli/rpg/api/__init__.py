"""Serializable API contracts for future HTTP/WebSocket adapters."""

from .contracts import API_VERSION, ErrorResponse, LoginRequest, LoginResponse

__all__ = ["API_VERSION", "ErrorResponse", "LoginRequest", "LoginResponse"]
