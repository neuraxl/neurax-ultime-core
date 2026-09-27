from typing import Any

AGENTS={
    "health-finder":{"purpose":"Trouver des installations selon localisation et filtres"},
    "health-service":{"purpose":"Rechercher des services et capacités"},
    "health-emergency":{"purpose":"Analyser les données publiques des urgences"},
    "health-data":{"purpose":"Expliquer provenance, fraîcheur et changements"},
}

def route_health_query(intent:str)->dict[str,Any]:
    key=intent.strip().lower()
    if any(x in key for x in ("urgence","emergency","attente","civière")):
        name="health-emergency"
    elif any(x in key for x in ("service","capacité","soin","offre")):
        name="health-service"
    elif any(x in key for x in ("source","provenance","donnée","date","mise à jour")):
        name="health-data"
    else:
        name="health-finder"
    return {"agent":name,**AGENTS[name]}
