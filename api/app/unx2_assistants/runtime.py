"""Narrow OpenJarvis SDK adapter.

The factory requires a tenant- and instance-scoped config path. It never uses
process-wide defaults or another tenant's configuration.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from .contracts import AssistantInstance, AssistantRequest, AssistantResponse


class AssistantRuntime(Protocol):
    def ask(self, prompt: str) -> str: ...
    def close(self) -> None: ...


class OpenJarvisRuntime:
    def __init__(self, client: Any) -> None:
        self._client = client

    def ask(self, prompt: str) -> str:
        return str(self._client.ask(prompt))

    def close(self) -> None:
        close = getattr(self._client, "close", None)
        if callable(close):
            close()


class OpenJarvisRuntimeFactory:
    """Creates an OpenJarvis client from a server-provisioned instance config."""

    def __init__(self, config_root: str | Path) -> None:
        self._config_root = Path(config_root).expanduser().resolve()

    def _validate_instance(self, instance: AssistantInstance) -> Path:
        if not instance.tenant_id or not instance.instance_id:
            raise ValueError("tenant_id and instance_id are required")

        # Resolve the expected tenant/instance directory independently. This
        # prevents a valid path under the global root from pointing at a
        # different tenant's config.
        expected_dir = (
            self._config_root / instance.tenant_id / instance.instance_id
        ).resolve()
        try:
            expected_dir.relative_to(self._config_root)
        except ValueError as exc:
            raise ValueError("tenant and instance IDs must be safe path segments") from exc

        candidate = Path(instance.config_path).expanduser().resolve()
        if candidate.parent != expected_dir or candidate.name != "config.toml":
            raise ValueError(
                "assistant config must be config.toml inside its tenant/instance directory"
            )
        if not candidate.is_file():
            raise FileNotFoundError("assistant config has not been provisioned")
        return candidate

    def create(self, instance: AssistantInstance) -> AssistantRuntime:
        config_path = self._validate_instance(instance)
        try:
            from openjarvis import Jarvis
        except ImportError as exc:
            raise RuntimeError(
                "OpenJarvis is not installed. Install api/requirements-openjarvis.txt."
            ) from exc

        # Explicit config_path is mandatory: never fall back to a shared
        # ~/.openjarvis/config.toml or process-global OPENJARVIS_HOME.
        kwargs: dict[str, Any] = {"config_path": str(config_path)}
        if instance.engine_key:
            kwargs["engine_key"] = instance.engine_key
        if instance.model:
            kwargs["model"] = instance.model
        return OpenJarvisRuntime(Jarvis(**kwargs))

    def ask(
        self, instance: AssistantInstance, request: AssistantRequest
    ) -> AssistantResponse:
        if request.tenant_id != instance.tenant_id:
            raise PermissionError("assistant instance belongs to another tenant")
        if request.instance_id != instance.instance_id:
            raise PermissionError("request targets a different assistant instance")
        if not request.prompt.strip():
            raise ValueError("prompt must not be empty")
        runtime = self.create(instance)
        try:
            answer = runtime.ask(request.prompt)
        finally:
            runtime.close()
        return AssistantResponse(
            tenant_id=instance.tenant_id,
            instance_id=instance.instance_id,
            text=answer,
        )
