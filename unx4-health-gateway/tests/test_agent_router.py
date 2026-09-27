from app.agent_router import route_health_query

def test_emergency_route():
    assert route_health_query("temps d'attente aux urgences")["agent"] == "health-emergency"

def test_service_route():
    assert route_health_query("quels services sont offerts")["agent"] == "health-service"

def test_data_route():
    assert route_health_query("quelle est la provenance de cette donnée")["agent"] == "health-data"
