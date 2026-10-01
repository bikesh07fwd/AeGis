import pytest
from graph.workflow import route_after_supervisor, route_after_reflection

def test_route_after_supervisor():
    assert route_after_supervisor({"next_agent": "FINISH"}) == "reflection"
    assert route_after_supervisor({"next_agent": "research_agent"}) == "research_agent"

def test_route_after_reflection():
    assert route_after_reflection({"reflection_status": "NEEDS_REVISION", "revision_count": 0}) == "writing_agent"
    assert route_after_reflection({"reflection_status": "APPROVED", "revision_count": 0}) == "citation_checker"
    assert route_after_reflection({"reflection_status": "NEEDS_REVISION", "revision_count": 3}) == "citation_checker"
