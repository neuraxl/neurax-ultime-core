"""Provider-neutral contracts for tenant-scoped assistant instances."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AssistantInstance:
    """An assistant instance owned by exactly one UNX2 tenant."""

    instance_id: str
    tenant_id: str
    display_name: str
    config_path: str
    engine_key: str | None = None
    model: str | None = None


@dataclass(frozen=True, slots=True)
class AssistantRequest:
    tenant_id: str
    instance_id: str
    prompt: str


@dataclass(frozen=True, slots=True)
class AssistantResponse:
    tenant_id: str
    instance_id: str
    text: str
    runtime: str = "openjarvis"
    metadata: dict[str, Any] | None = None
