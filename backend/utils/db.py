"""
db.py — ChromaDB Manager for FinSight AI
=========================================
Central module for all ChromaDB operations:
  - Client initialization (PersistentClient)
  - Collection management (create / get / delete / list)
  - Document ingestion  (upsert chunks with rich metadata)
  - Semantic querying   (cosine similarity search with filters)
  - Document deletion   (remove all chunks for a document_id)
  - Health check        (verify DB is reachable)

All other services import from here — nothing touches chromadb directly.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import settings

logger = logging.getLogger(__name__)

# ── Singleton state ────────────────────────────────────────────────────────
_client: Optional[chromadb.PersistentClient] = None
_collections: Dict[str, chromadb.Collection] = {}  # cache by name


# ── Client ─────────────────────────────────────────────────────────────────

def get_client() -> chromadb.PersistentClient:
    """
    Return the singleton ChromaDB PersistentClient.
    Creates and persists to CHROMA_PERSIST_DIR on first call.
    """
    global _client
    if _client is None:
        persist_path = Path(settings.CHROMA_PERSIST_DIR)
        persist_path.mkdir(parents=True, exist_ok=True)

        _client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,          # enables reset_database() below
            ),
        )
        logger.info(f"ChromaDB client initialized at: {persist_path.resolve()}")
    return _client


# ── Collection helpers ─────────────────────────────────────────────────────

def get_collection(name: Optional[str] = None) -> chromadb.Collection:
    """
    Return (and cache) a ChromaDB collection by name.
    Defaults to CHROMA_COLLECTION_NAME from config.
    Creates the collection if it does not exist.

    Embedding function: ChromaDB's default (all-MiniLM-L6-v2 via sentence-transformers).
    This runs locally — no API key required.
    """
    collection_name = name or settings.CHROMA_COLLECTION_NAME

    if collection_name not in _collections:
        client = get_client()
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",          # cosine similarity for semantic search
                "hnsw:construction_ef": 200,     # build-time accuracy (higher = better index)
                "hnsw:search_ef": 100,           # query-time accuracy
                "description": "FinSight AI financial document chunks",
            },
        )
        _collections[collection_name] = collection
        logger.info(f"Collection '{collection_name}' ready ({collection.count()} chunks stored)")

    return _collections[collection_name]


def list_collections() -> List[str]:
    """Return names of all collections in this ChromaDB instance."""
    return [c.name for c in get_client().list_collections()]


def delete_collection(name: str) -> bool:
    """Delete an entire collection. Returns True if deleted."""
    try:
        get_client().delete_collection(name)
        _collections.pop(name, None)
        logger.info(f"Collection '{name}' deleted.")
        return True
    except Exception as e:
        logger.warning(f"Could not delete collection '{name}': {e}")
        return False


def reset_database() -> bool:
    """
    ⚠️  DANGER: Wipe the entire ChromaDB instance.
    Only usable when allow_reset=True in ChromaSettings.
    """
    global _client, _collections
    try:
        get_client().reset()
        _client = None
        _collections = {}
        logger.warning("ChromaDB has been fully reset.")
        return True
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        return False


# ── Ingestion ──────────────────────────────────────────────────────────────

def upsert_chunks(
    document_id: str,
    chunks: List[str],
    extra_metadata: Optional[Dict[str, Any]] = None,
    collection_name: Optional[str] = None,
) -> int:
    """
    Store (or overwrite) text chunks for a document in ChromaDB.

    Each chunk is stored with metadata:
      - document_id  : parent document UUID
      - chunk_index  : position in document
      - char_count   : length of chunk in characters
      - + any extra_metadata fields (e.g. filename, user_id, upload_date)

    Returns the number of chunks stored.
    """
    if not chunks:
        logger.warning(f"upsert_chunks called with 0 chunks for document {document_id}")
        return 0

    collection = get_collection(collection_name)

    ids = [f"{document_id}__chunk__{i}" for i in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "chunk_index": i,
            "char_count": len(chunk),
            **(extra_metadata or {}),
        }
        for i, chunk in enumerate(chunks)
    ]

    collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)
    logger.info(f"Upserted {len(chunks)} chunks for document '{document_id}'")
    return len(chunks)


# ── Querying ───────────────────────────────────────────────────────────────

def query_chunks(
    query: str,
    document_id: Optional[str] = None,
    top_k: int = 5,
    collection_name: Optional[str] = None,
    include_distances: bool = False,
) -> List[Dict[str, Any]]:
    """
    Semantic search over stored chunks.

    Args:
        query           : Natural language question or keyword string
        document_id     : Filter to a specific document (None = search all)
        top_k           : Number of results to return
        collection_name : Override default collection
        include_distances: Include cosine distance scores in output

    Returns:
        List of dicts: { "text": str, "metadata": dict, "distance"?: float }
    """
    collection = get_collection(collection_name)

    # Guard: ChromaDB errors if top_k > total stored chunks
    total = collection.count()
    if total == 0:
        logger.warning("query_chunks called on empty collection")
        return []
    top_k = min(top_k, total)

    where_filter = {"document_id": document_id} if document_id else None

    results = collection.query(
        query_texts=[query],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    output = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(docs, metas, dists):
        entry: Dict[str, Any] = {"text": doc, "metadata": meta}
        if include_distances:
            entry["distance"] = round(dist, 4)
            entry["similarity"] = round(1 - dist, 4)   # cosine similarity
        output.append(entry)

    return output


def query_chunks_text_only(
    query: str,
    document_id: Optional[str] = None,
    top_k: int = 5,
    collection_name: Optional[str] = None,
) -> List[str]:
    """
    Convenience wrapper — returns just the text strings (no metadata).
    Used by the analysis modules.
    """
    results = query_chunks(query, document_id, top_k, collection_name)
    return [r["text"] for r in results]


# ── Document management ────────────────────────────────────────────────────

def delete_document_chunks(
    document_id: str,
    collection_name: Optional[str] = None,
) -> int:
    """
    Delete all chunks belonging to a document_id.
    Returns number of chunks deleted.
    """
    collection = get_collection(collection_name)

    # Fetch all IDs for this document first
    results = collection.get(where={"document_id": document_id}, include=["metadatas"])
    ids_to_delete = results.get("ids", [])

    if ids_to_delete:
        collection.delete(ids=ids_to_delete)
        logger.info(f"Deleted {len(ids_to_delete)} chunks for document '{document_id}'")
    else:
        logger.info(f"No chunks found for document '{document_id}'")

    return len(ids_to_delete)


def document_exists(document_id: str, collection_name: Optional[str] = None) -> bool:
    """Return True if any chunks exist for this document_id."""
    collection = get_collection(collection_name)
    results = collection.get(
        where={"document_id": document_id},
        include=["metadatas"],
        limit=1,
    )
    return len(results.get("ids", [])) > 0


def get_document_chunk_count(document_id: str, collection_name: Optional[str] = None) -> int:
    """Return how many chunks are stored for a given document."""
    collection = get_collection(collection_name)
    results = collection.get(where={"document_id": document_id}, include=["metadatas"])
    return len(results.get("ids", []))


def list_documents(collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return a summary of all documents stored in the collection.
    Each entry: { document_id, filename, chunk_count, upload_date }
    """
    collection = get_collection(collection_name)
    all_items = collection.get(include=["metadatas"])
    metadatas = all_items.get("metadatas", [])

    # Aggregate by document_id
    doc_map: Dict[str, Dict] = {}
    for meta in metadatas:
        doc_id = meta.get("document_id", "unknown")
        if doc_id not in doc_map:
            doc_map[doc_id] = {
                "document_id": doc_id,
                "filename": meta.get("filename", "unknown"),
                "upload_date": meta.get("upload_date", "unknown"),
                "chunk_count": 0,
            }
        doc_map[doc_id]["chunk_count"] += 1

    return list(doc_map.values())


# ── Health check ───────────────────────────────────────────────────────────

def health_check() -> Dict[str, Any]:
    """
    Verify ChromaDB is reachable and return basic stats.
    Called by /health endpoint.
    """
    try:
        client = get_client()
        collections = client.list_collections()
        collection = get_collection()
        return {
            "status": "ok",
            "persist_dir": str(Path(settings.CHROMA_PERSIST_DIR).resolve()),
            "collections": [c.name for c in collections],
            "active_collection": settings.CHROMA_COLLECTION_NAME,
            "total_chunks": collection.count(),
        }
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
        return {"status": "error", "detail": str(e)}