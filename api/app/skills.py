"""LÉVIATHAN Skill Runtime for UNX2.

This module provides a read-only skill registry and safe mission routing.
It deliberately does not execute agents or external tools until server-side
identity, authorization, tenant isolation and audit controls are implemented.
"""
from __future__ import annotations

import json
import re
from uuid import uuid4
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])

SKILLS: list[dict[str, str]] = [
    {"id": "leviathan-universe-orchestrator", "name": "LÉVIATHAN Orchestrator", "space": "Orchestration", "description": "Coordonne les espaces et route les missions."},
    {"id": "horus-security", "name": "HORUS Security", "space": "Transversal", "description": "Évalue permissions, risques, configurations et preuves."},
    {"id": "command-center", "name": "Command Center", "space": "01 · Pilotage", "description": "Pilotage et santé des services."},
    {"id": "universe-explorer", "name": "Universe Explorer", "space": "02 · Exploration", "description": "Recherche des ressources et projets."},
    {"id": "agent-society", "name": "Agent Society", "space": "03 · Agents", "description": "Coordination des agents et des Titans."},
    {"id": "memory-fabric", "name": "Memory Fabric", "space": "04 · Mémoire", "description": "Mémoire, provenance et recherche sémantique."},
    {"id": "knowledge-graph", "name": "Knowledge Graph", "space": "05 · Connaissances", "description": "Entités, relations et provenance."},
    {"id": "workflow-builder", "name": "Workflow Builder", "space": "06 · Automatisation", "description": "Conception et validation des workflows."},
    {"id": "neural-telemetry", "name": "Neural Telemetry", "space": "07 · Observabilité", "description": "Métriques, traces, journaux et anomalies."},
    {"id": "digital-twin", "name": "Digital Twin", "space": "08 · Simulation", "description": "Modèles numériques et scénarios simulés."},
    {"id": "shield-governance", "name": "Shield & Governance", "space": "09 · Gouvernance", "description": "Politiques, rôles, approbations et audit."},
    {"id": "open-source-registry", "name": "Open Source Registry", "space": "10 · Open source", "description": "Évaluation des licences et dépendances."},
    {"id": "value-layer-nxus", "name": "Value Layer / NXU$", "space": "11 · Valeur", "description": "Suivi des coûts, budgets et opérations de valeur."},
    {"id": "api-gateway-settings", "name": "API Gateway Settings", "space": "12 · API", "description": "Contrats API et intégrations."},
]

SKILL_IDS = {item["id"] for item in SKILLS}
RULES: list[tuple[str, re.Pattern[str]]] = [
    ("horus-security", re.compile(r"sécur|horus|vulnér|scan|tls|permission|attaque|risque", re.I)),
    ("api-gateway-settings", re.compile(r"api|passerelle|endpoint|connecteur|route|authentification", re.I)),
    ("workflow-builder", re.compile(r"workflow|automatis|processus|déclencheur", re.I)),
    ("agent-society", re.compile(r"agent|titan|modèle|llm|ia|intelligence artificielle", re.I)),
    ("memory-fabric", re.compile(r"mémoire|souvenir|embedding|vector|recherche sémantique", re.I)),
    ("knowledge-graph", re.compile(r"graphe|relation|entité|connaissance", re.I)),
    ("neural-telemetry", re.compile(r"métrique|télémétr|journal|latence|cpu|ram|supervision", re.I)),
    ("digital-twin", re.compile(r"simulation|jumeau|scénario|modélis", re.I)),
    ("shield-governance", re.compile(r"gouvernance|rôle|rbac|rls|politique|audit", re.I)),
    ("open-source-registry", re.compile(r"open.?source|licence|dépendance|github|logiciel", re.I)),
    ("value-layer-nxus", re.compile(r"nxu\$|paiement|facture|revenu|budget|transaction|valeur", re.I)),
    ("universe-explorer", re.compile(r"explor|recherche|ressource|inventaire|catalogue", re.I)),
    ("command-center", re.compile(r"état global|pilotage|tableau de bord|santé système", re.I)),
]


class RouteRequest(BaseModel):
    request: str = Field(min_length=1, max_length=4000)
    selected_skill: str | None = None


def choose_skill(message: str) -> str:
    for skill_id, pattern in RULES:
        if pattern.search(message):
            return skill_id
    return "leviathan-universe-orchestrator"


@router.get("")
async def list_skills() -> dict[str, Any]:
    return {
        "platform": "UNX2",
        "runtime": "planning_only",
        "execution_enabled": False,
        "count": len(SKILLS),
        "skills": SKILLS,
    }


@router.post("/route")
async def route_mission(payload: RouteRequest, request: Request) -> dict[str, Any]:
    skill_id = payload.selected_skill or choose_skill(payload.request)
    if skill_id not in SKILL_IDS:
        raise HTTPException(status_code=422, detail="Unknown skill_id")

    skill = next(item for item in SKILLS if item["id"] == skill_id)
    mission_id = str(uuid4())
    event = {
        "event": "skill.mission.routed",
        "mission_id": mission_id,
        "skill_id": skill_id,
        "status": "PROPOSED",
    }

    # Publish metadata only. Do not store the user's prompt or secrets in Redis.
    redis_status = "unavailable"
    redis_client = getattr(request.app.state, "redis", None)
    if redis_client is not None:
        try:
            await redis_client.publish("unx2:events:skills", json.dumps(event))
            redis_status = "published"
        except Exception:
            redis_status = "publish_failed"

    return {
        "mission_id": mission_id,
        "routed_skill": skill,
        "orchestrator": "leviathan-universe-orchestrator",
        "horus_preflight": {
            "status": "WARN",
            "scope": "routing_metadata_only",
            "checks": [
                {"name": "request_validation", "status": "PASS"},
                {"name": "server_side_authorization", "status": "NOT_TESTED"},
                {"name": "tenant_isolation", "status": "NOT_TESTED"},
                {"name": "tool_permissions", "status": "NOT_TESTED"},
            ],
        },
        "execution_status": "PROPOSED",
        "execution_enabled": False,
        "event_bus": redis_status,
        "message": "Mission routée et préparée. Aucun agent ni outil externe n'a été exécuté.",
    }
