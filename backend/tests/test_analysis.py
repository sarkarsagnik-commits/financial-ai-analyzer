"""Tests for analysis and document management endpoints."""
import os


def test_list_documents_empty(client, auth_headers):
    """List documents when none uploaded."""
    resp = client.get("/api/analysis/documents", headers=auth_headers)
    assert resp.status_code == 200
    assert "documents" in resp.json()


def test_run_analysis_no_modules(client, auth_headers):
    """Running analysis with no modules returns 400."""
    resp = client.post(
        "/api/analysis/run",
        json={"document_id": "fake-id", "modules": []},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_run_analysis_missing_document(client, auth_headers):
    """Running analysis on a non-existent document returns error in results."""
    resp = client.post(
        "/api/analysis/run",
        json={"document_id": "nonexistent", "modules": ["Financial Changes"]},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "error" in data["results"]["Financial Changes"]


def test_semantic_query_missing_document(client, auth_headers):
    """Querying a non-existent document returns error."""
    resp = client.post(
        "/api/analysis/query",
        json={"document_id": "nonexistent", "query": "revenue", "top_k": 3},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0
    assert "error" in data["results"][0]


def test_rag_no_api_key(client, auth_headers):
    """RAG endpoint without OPENAI_API_KEY returns 500."""
    # Only run this test if OPENAI_API_KEY is not actually set
    if os.getenv("OPENAI_API_KEY"):
        return  # skip — key is set, endpoint would try to call OpenAI
    resp = client.post(
        "/api/analysis/rag",
        json={"query": "What is the revenue?", "document_id": "fake-id"},
        headers=auth_headers,
    )
    assert resp.status_code == 500
    assert "OPENAI_API_KEY" in resp.json()["detail"]


def test_rag_no_document_id(client, auth_headers):
    """RAG endpoint without document_id returns 400."""
    if not os.getenv("OPENAI_API_KEY"):
        return  # skip — this check runs after the API key check
    resp = client.post(
        "/api/analysis/rag",
        json={"query": "test"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_document_info_nonexistent(client, auth_headers):
    """Getting info for a non-existent document."""
    resp = client.get("/api/analysis/documents/nonexistent", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["exists"] is False
    assert data["chunk_count"] == 0
