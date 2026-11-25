from pathlib import Path

import pytest

from app.unx2_assistants.contracts import AssistantInstance, AssistantRequest
from app.unx2_assistants.runtime import OpenJarvisRuntimeFactory


def _instance(root: Path, tenant: str = "tenant-a", name: str = "assistant-a"):
    config = root / tenant / name / "config.toml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text("[intelligence]\n", encoding="utf-8")
    return AssistantInstance(
        instance_id=name,
        tenant_id=tenant,
        display_name="Test assistant",
        config_path=str(config),
    )


def test_rejects_config_outside_managed_root(tmp_path):
    root = tmp_path / "managed"
    root.mkdir()
    outside = tmp_path / "outside.toml"
    outside.write_text("[intelligence]\n", encoding="utf-8")
    instance = AssistantInstance("a1", "t1", "A1", str(outside))

    with pytest.raises(ValueError, match="inside UNX2 config root"):
        OpenJarvisRuntimeFactory(root)._validate_instance(instance)


def test_rejects_missing_config(tmp_path):
    root = tmp_path / "managed"
    root.mkdir()
    instance = AssistantInstance("a1", "t1", "A1", str(root / "missing.toml"))

    with pytest.raises(FileNotFoundError):
        OpenJarvisRuntimeFactory(root).create(instance)


def test_rejects_cross_tenant_request_before_runtime_creation(tmp_path):
    root = tmp_path / "managed"
    root.mkdir()
    instance = _instance(root)
    factory = OpenJarvisRuntimeFactory(root)
    request = AssistantRequest("tenant-b", "assistant-a", "Hello")

    with pytest.raises(PermissionError, match="another tenant"):
        factory.ask(instance, request)


def test_rejects_empty_prompt(tmp_path):
    root = tmp_path / "managed"
    root.mkdir()
    instance = _instance(root)
    factory = OpenJarvisRuntimeFactory(root)
    request = AssistantRequest("tenant-a", "assistant-a", "  ")

    with pytest.raises(ValueError, match="prompt"):
        factory.ask(instance, request)
