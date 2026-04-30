import json
from pathlib import Path

import jsonschema
from jsonschema import RefResolver
import pytest


PROJECT_ROOT = Path(__file__).parent.parent.parent
SERVICE_CONTRACTS = PROJECT_ROOT / "contracts" / "service"
RELEASE_CONTRACTS = PROJECT_ROOT / "contracts" / "release"
FIXTURES = Path(__file__).parent / "fixtures" / "week08"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def validator(schema_name: str) -> jsonschema.Draft202012Validator:
    schema = load_json(SERVICE_CONTRACTS / schema_name)
    store = {
        "citation.schema.json": load_json(SERVICE_CONTRACTS / "citation.schema.json"),
        "retrieval_debug.schema.json": load_json(
            SERVICE_CONTRACTS / "retrieval_debug.schema.json"
        ),
    }
    return jsonschema.Draft202012Validator(
        schema,
        resolver=RefResolver.from_schema(schema, store=store),
    )


def test_rag_request_fixture_valid():
    validator("rag_request.schema.json").validate(load_json(FIXTURES / "rag_request.valid.json"))


@pytest.mark.parametrize(
    "fixture_name",
    ["rag_response.valid.json", "rag_response.no_answer.json"],
)
def test_rag_response_fixtures_valid(fixture_name: str):
    validator("rag_response.schema.json").validate(load_json(FIXTURES / fixture_name))


def test_rag_response_requires_citations_and_release_ids():
    payload = load_json(FIXTURES / "rag_response.valid.json")
    payload.pop("citations")
    with pytest.raises(jsonschema.ValidationError):
        validator("rag_response.schema.json").validate(payload)


def test_index_manifest_fixture_valid():
    schema = load_json(RELEASE_CONTRACTS / "index_manifest.schema.json")
    jsonschema.Draft202012Validator(schema).validate(
        load_json(FIXTURES / "index_manifest.valid.json")
    )


def test_no_answer_has_abstain_reason_and_no_evidence():
    payload = load_json(FIXTURES / "rag_response.no_answer.json")
    assert payload["abstain_reason"]
    assert payload["citations"] == []
    assert payload["evidence_ids"] == []
