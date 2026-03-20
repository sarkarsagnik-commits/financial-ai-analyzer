"""
analysis_service.py — Document ingestion + analysis modules + RAG pipeline
============================================================================
All ChromaDB operations are delegated to utils/db.py.
This module handles:
  - PDF text extraction + chunking
  - Document ingestion pipeline
  - Three analysis modules: Financial Changes, Risk Radar, Management Outlook
  - RAG pipeline (LangChain + FAISS): chunk → embed → query → LLM answer
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import pypdf

from utils.db import (
    upsert_chunks,
    query_chunks,
    query_chunks_text_only,
    delete_document_chunks,
    document_exists,
    get_document_chunk_count,
)
from config import settings

logger = logging.getLogger(__name__)


# ── PDF helpers ───────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> tuple[str, int]:
    """
    Extract all text from a PDF file.
    Returns (full_text, page_count).
    """
    reader = pypdf.PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text.strip())
    return "\n\n".join(pages), len(reader.pages)


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 150,
    min_chunk_len: int = 80,
) -> List[str]:
    """
    Split text into overlapping word-level chunks.

    Args:
        chunk_size    : target words per chunk
        overlap       : words shared between consecutive chunks
        min_chunk_len : discard chunks shorter than this (characters)
    """
    words = text.split()
    chunks, start = [], 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk.strip()) >= min_chunk_len:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


# ── Ingestion pipeline ────────────────────────────────────────────────────

def ingest_document(
    document_id: str,
    file_path: str,
    filename: str = "",
    user_id: str = "",
    force_reingest: bool = False,
) -> Dict[str, Any]:
    """
    Full ingestion pipeline:
      1. Check if already ingested (skip unless force_reingest=True)
      2. Extract text from PDF
      3. Chunk into overlapping windows
      4. Store in ChromaDB via db.upsert_chunks()

    Returns a summary dict with chunk_count, page_count, etc.
    """
    # Skip if already indexed
    if not force_reingest and document_exists(document_id):
        existing = get_document_chunk_count(document_id)
        logger.info(f"Document '{document_id}' already indexed ({existing} chunks). Skipping.")
        return {
            "document_id": document_id,
            "status": "already_indexed",
            "chunks_stored": existing,
            "page_count": 0,
        }

    # If re-ingesting, remove old chunks first
    if force_reingest:
        deleted = delete_document_chunks(document_id)
        logger.info(f"Removed {deleted} old chunks before re-ingestion.")

    # Extract
    logger.info(f"Extracting text from: {file_path}")
    full_text, page_count = extract_text_from_pdf(file_path)

    if not full_text.strip():
        logger.warning(f"No text extracted from {file_path} — may be a scanned PDF.")
        return {
            "document_id": document_id,
            "status": "no_text_extracted",
            "chunks_stored": 0,
            "page_count": page_count,
        }

    # Chunk
    chunks = chunk_text(full_text)
    logger.info(f"Created {len(chunks)} chunks from {page_count} pages")

    # Store with rich metadata
    extra_metadata = {
        "filename": filename or document_id,
        "page_count": page_count,
        "user_id": user_id,
        "upload_date": datetime.utcnow().isoformat(),
        "total_chars": len(full_text),
    }

    chunks_stored = upsert_chunks(document_id, chunks, extra_metadata=extra_metadata)

    return {
        "document_id": document_id,
        "status": "ingested",
        "chunks_stored": chunks_stored,
        "page_count": page_count,
        "total_chars": len(full_text),
        "filename": filename,
    }


# ── Analysis modules ──────────────────────────────────────────────────────

def run_financial_changes(document_id: str) -> Dict[str, Any]:
    """
    Extract key financial metrics and year-over-year changes.
    Uses semantic search to pull relevant chunks then applies regex extraction.
    """
    queries = [
        "revenue total revenue net revenue sales",
        "net income net profit loss earnings per share EPS",
        "total assets total liabilities stockholders equity",
        "operating income EBITDA gross profit margin",
        "cash flow from operations capital expenditure",
    ]

    # Pull 6 chunks per query → deduplicate
    seen, chunks = set(), []
    for q in queries:
        for chunk in query_chunks_text_only(q, document_id=document_id, top_k=6):
            if chunk not in seen:
                seen.add(chunk)
                chunks.append(chunk)

    context = "\n\n".join(chunks)

    # Regex patterns for common financial metrics
    metric_patterns = {
        "Revenue": r"(?:total\s+)?revenue[^$\d\n]*\$?\s*([\d,\.]+)\s*(billion|million|thousand)?",
        "Net Income": r"net\s+(?:income|profit|loss)[^$\d\n]*\$?\s*([\d,\.]+)\s*(billion|million|thousand)?",
        "EPS (Basic)": r"(?:basic\s+)?earnings\s+per\s+(?:common\s+)?share[^$\d\n]*\$?\s*([\d,\.]+)",
        "EPS (Diluted)": r"diluted\s+earnings\s+per\s+share[^$\d\n]*\$?\s*([\d,\.]+)",
        "Total Assets": r"total\s+assets[^$\d\n]*\$?\s*([\d,\.]+)\s*(billion|million|thousand)?",
        "Total Liabilities": r"total\s+liabilities[^$\d\n]*\$?\s*([\d,\.]+)\s*(billion|million|thousand)?",
        "Operating Income": r"(?:income|loss)\s+from\s+operations[^$\d\n]*\$?\s*([\d,\.]+)\s*(billion|million|thousand)?",
        "Gross Profit": r"gross\s+profit[^$\d\n]*\$?\s*([\d,\.]+)\s*(billion|million|thousand)?",
        "Cash & Equivalents": r"cash\s+and\s+(?:cash\s+)?equivalents[^$\d\n]*\$?\s*([\d,\.]+)\s*(billion|million|thousand)?",
    }

    metrics_found = {}
    for label, pattern in metric_patterns.items():
        match = re.search(pattern, context, re.IGNORECASE)
        if match:
            value = match.group(1).replace(",", "")
            unit = (match.group(2) or "").capitalize()
            metrics_found[label] = f"${value} {unit}".strip()

    # Try to find two-year comparison values (e.g. "2023: $X  2022: $Y")
    yoy_pattern = r"(20\d{2})[^\d]+([\d,\.]+)[^\d]+(20\d{2})[^\d]+([\d,\.]+)"
    yoy_matches = re.findall(yoy_pattern, context)
    yoy_changes = {}
    for m in yoy_matches[:5]:
        yr1, val1, yr2, val2 = m
        try:
            v1, v2 = float(val1.replace(",", "")), float(val2.replace(",", ""))
            pct = round((v1 - v2) / v2 * 100, 1) if v2 != 0 else 0
            yoy_changes[f"{yr2}→{yr1}"] = f"{'+' if pct >= 0 else ''}{pct}%"
        except ValueError:
            pass

    # LLM enrichment (graceful degradation without API key)
    ai_context = f"Metrics: {metrics_found}, YoY changes: {yoy_changes}"
    ai_explanation = enrich_with_llm(ai_context, "Financial Changes")

    return {
        "metrics": metrics_found if metrics_found else {"note": "No structured metrics found. Consider LLM enrichment."},
        "yoy_changes": yoy_changes if yoy_changes else {"note": "No year-over-year pairs detected in top chunks."},
        "chunks_analyzed": len(chunks),
        "summary": (
            f"Analyzed {len(chunks)} chunks. "
            f"Extracted {len(metrics_found)} financial metrics "
            f"and {len(yoy_changes)} year-over-year comparisons."
        ),
        "ai_explanation": ai_explanation,
        "context_preview": context[:600] + "…" if len(context) > 600 else context,
    }


def run_risk_radar(document_id: str) -> Dict[str, Any]:
    """
    Identify and categorize risk factors from the filing.
    Returns risks with type, severity estimate, and supporting excerpt.
    """
    risk_queries = [
        "risk factors uncertainty could adversely affect",
        "regulatory compliance legal proceedings litigation",
        "competition competitive market share pricing pressure",
        "operational supply chain disruption technology failure",
        "liquidity credit debt interest rate financial risk",
        "cybersecurity data breach information security",
        "macroeconomic inflation recession geopolitical",
        "climate environmental ESG sustainability risk",
    ]

    seen, chunks = set(), []
    for q in risk_queries:
        for chunk in query_chunks_text_only(q, document_id=document_id, top_k=5):
            if chunk not in seen:
                seen.add(chunk)
                chunks.append(chunk)

    RISK_TAXONOMY = {
        "Market Risk":        {"keywords": ["market", "volatility", "price fluctuation", "demand"], "weight": 1},
        "Regulatory Risk":    {"keywords": ["regulatory", "compliance", "legislation", "sec", "government", "law"], "weight": 1.5},
        "Competitive Risk":   {"keywords": ["competition", "competitor", "market share", "pricing pressure"], "weight": 1},
        "Operational Risk":   {"keywords": ["operational", "supply chain", "disruption", "failure", "outage"], "weight": 1.2},
        "Financial Risk":     {"keywords": ["liquidity", "credit", "debt", "interest rate", "leverage"], "weight": 1.3},
        "Cybersecurity Risk": {"keywords": ["cyber", "data breach", "security", "hacking", "ransomware"], "weight": 1.8},
        "Macro / Economic":   {"keywords": ["inflation", "recession", "geopolit", "macro", "economic downturn"], "weight": 1},
        "Climate / ESG":      {"keywords": ["climate", "environmental", "esg", "sustainability", "carbon"], "weight": 0.9},
        "Legal / Litigation": {"keywords": ["litigation", "lawsuit", "legal proceeding", "settlement", "judgment"], "weight": 1.4},
    }

    found_risks = []
    severity_breakdown: Dict[str, int] = {}

    for chunk in chunks:
        chunk_lower = chunk.lower()
        for risk_type, cfg in RISK_TAXONOMY.items():
            hit_count = sum(1 for kw in cfg["keywords"] if kw in chunk_lower)
            if hit_count > 0:
                score = hit_count * cfg["weight"]
                severity = "High" if score >= 3 else "Medium" if score >= 1.5 else "Low"

                if risk_type not in severity_breakdown:
                    severity_breakdown[risk_type] = 0
                    found_risks.append({
                        "type": risk_type,
                        "severity": severity,
                        "keyword_hits": hit_count,
                        "excerpt": chunk[:350].strip() + "…",
                    })
                severity_breakdown[risk_type] += hit_count

    # Sort by hit count descending
    found_risks.sort(key=lambda x: severity_breakdown.get(x["type"], 0), reverse=True)

    high_count = sum(1 for r in found_risks if r["severity"] == "High")
    med_count  = sum(1 for r in found_risks if r["severity"] == "Medium")

    # LLM enrichment
    risk_summary = "; ".join(f"{r['type']} ({r['severity']})" for r in found_risks[:5])
    ai_explanation = enrich_with_llm(risk_summary, "Risk Radar")

    return {
        "risk_factors": found_risks,
        "severity_breakdown": severity_breakdown,
        "risk_count": {"High": high_count, "Medium": med_count, "Low": len(found_risks) - high_count - med_count},
        "chunks_analyzed": len(chunks),
        "summary": (
            f"Identified {len(found_risks)} risk categories across {len(chunks)} chunks. "
            f"{high_count} High severity, {med_count} Medium severity risks detected."
        ),
        "ai_explanation": ai_explanation,
    }


def run_management_outlook(document_id: str) -> Dict[str, Any]:
    """
    Analyze management's tone and extract forward-looking guidance statements.
    """
    outlook_queries = [
        "management discussion analysis outlook strategy",
        "we expect anticipate forecast guidance target plan",
        "growth opportunity expand market future revenue",
        "challenge headwind uncertainty cautious conservative",
        "CEO letter to shareholders strategic priorities",
        "capital allocation dividend share repurchase investment",
    ]

    seen, chunks = set(), []
    for q in outlook_queries:
        for chunk in query_chunks_text_only(q, document_id=document_id, top_k=5):
            if chunk not in seen:
                seen.add(chunk)
                chunks.append(chunk)

    full_text = " ".join(chunks).lower()

    POSITIVE = ["growth", "increase", "expand", "strong", "opportunity", "improve",
                "gain", "positive", "confident", "exceed", "record", "momentum",
                "innovative", "leading", "accelerate", "outperform"]
    NEGATIVE = ["decline", "decrease", "challenge", "risk", "uncertain", "loss",
                "headwind", "concern", "difficult", "pressure", "slowdown",
                "disappoint", "miss", "below", "reduce", "restructure"]
    FORWARD_TRIGGERS = ["expect", "anticipate", "forecast", "guidance", "target",
                        "plan to", "intend to", "projected", "outlook", "we believe",
                        "on track", "will achieve"]

    pos_count = sum(full_text.count(w) for w in POSITIVE)
    neg_count = sum(full_text.count(w) for w in NEGATIVE)
    total = (pos_count + neg_count) or 1

    tone_score = round(pos_count / total, 3)
    tone = (
        "Strongly Positive" if tone_score > 0.70 else
        "Positive"          if tone_score > 0.55 else
        "Cautiously Optimistic" if tone_score > 0.45 else
        "Neutral / Mixed"   if tone_score > 0.35 else
        "Cautious"          if tone_score > 0.25 else
        "Negative"
    )

    # Extract forward-looking statements
    all_sentences = re.split(r"(?<=[.!?])\s+", " ".join(chunks))
    forward_statements = []
    for sentence in all_sentences:
        s_lower = sentence.lower()
        if (
            any(trigger in s_lower for trigger in FORWARD_TRIGGERS)
            and len(sentence.strip()) > 50
            and len(sentence.strip()) < 400
        ):
            forward_statements.append(sentence.strip())
    forward_statements = list(dict.fromkeys(forward_statements))[:8]  # dedupe + cap

    # Key themes: words that appear frequently
    key_themes = sorted(
        [(w, full_text.count(w)) for w in POSITIVE + NEGATIVE if full_text.count(w) > 1],
        key=lambda x: x[1], reverse=True
    )
    top_themes = [w for w, _ in key_themes[:10]]

    # LLM enrichment
    outlook_context = f"Tone: {tone} ({tone_score:.0%}), Top themes: {', '.join(top_themes)}, Forward statements: {len(forward_statements)}"
    ai_explanation = enrich_with_llm(outlook_context, "Management Outlook")

    return {
        "tone": tone,
        "tone_score": tone_score,
        "sentiment_counts": {"positive_signals": pos_count, "negative_signals": neg_count},
        "key_themes": top_themes,
        "forward_guidance": forward_statements,
        "chunks_analyzed": len(chunks),
        "summary": (
            f"Tone: {tone} (score {tone_score:.0%}). "
            f"{pos_count} positive vs {neg_count} negative signals. "
            f"Extracted {len(forward_statements)} forward-looking statements."
        ),
        "ai_explanation": ai_explanation,
    }


# ── LLM Enrichment ────────────────────────────────────────────────────────

def enrich_with_llm(extracted_data: str, module_name: str) -> str:
    """
    Generate an AI explanation of extracted analysis data.
    Returns a fallback message if OPENAI_API_KEY is not configured.
    """
    if not settings.OPENAI_API_KEY:
        return "AI explanation unavailable — set OPENAI_API_KEY in .env to enable."

    try:
        from langchain_openai import ChatOpenAI as _ChatOpenAI

        llm = _ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
        )

        prompts = {
            "Financial Changes": (
                "You are a financial analyst. Based on these extracted metrics "
                "from an SEC filing, write a 2-3 sentence explanation of the "
                "key financial changes and what they mean for the company:\n\n"
            ),
            "Risk Radar": (
                "You are a risk analyst. Based on these identified risk factors "
                "from an SEC filing, write a concise executive summary of the "
                "top risks and their potential impact:\n\n"
            ),
            "Management Outlook": (
                "You are an equity analyst. Based on this tone analysis and "
                "forward-looking statements from management, summarize the "
                "overall management sentiment and outlook in 2-3 sentences:\n\n"
            ),
        }

        prompt = prompts.get(module_name, "Analyze:\n\n") + extracted_data
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"LLM enrichment failed for {module_name}: {e}")
        return f"AI explanation failed: {str(e)}"


# ── Dispatcher ────────────────────────────────────────────────────────────

MODULE_MAP = {
    "Financial Changes": run_financial_changes,
    "Risk Radar":        run_risk_radar,
    "Management Outlook": run_management_outlook,
}


def run_analysis(document_id: str, modules: List[str]) -> Dict[str, Any]:
    """
    Run one or more analysis modules on an ingested document.
    Each module independently queries ChromaDB for relevant chunks.
    """
    if not document_exists(document_id):
        return {
            mod: {"error": f"Document '{document_id}' not found in ChromaDB. Please upload first."}
            for mod in modules
        }

    results = {}
    for module in modules:
        if module in MODULE_MAP:
            logger.info(f"Running module '{module}' on document '{document_id}'")
            try:
                results[module] = MODULE_MAP[module](document_id)
            except Exception as e:
                logger.error(f"Module '{module}' failed: {e}")
                results[module] = {"error": str(e)}
        else:
            results[module] = {"error": f"Unknown module: '{module}'"}

    return results


def query_document(
    document_id: str,
    query: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Semantic search over an ingested document's chunks.
    Returns list of matching chunks with metadata.
    """
    if not document_exists(document_id):
        return [{"error": f"Document '{document_id}' not found in ChromaDB."}]

    return query_chunks(
        query=query,
        document_id=document_id,
        top_k=top_k,
        include_distances=True,
    )


# ── RAG Pipeline (from feature/RAG) ──────────────────────────────────────
#
# Uses LangChain + FAISS for a self-contained RAG flow:
#   1. chunk_document()   → split text with RecursiveCharacterTextSplitter
#   2. build_vector_store → embed with OpenAI and store in FAISS
#   3. generate_analysis  → RetrievalQA chain with GPT prompt
#   4. analyze_financial_report → end-to-end pipeline
#
# NOTE: This uses FAISS (separate from ChromaDB) and requires OPENAI_API_KEY.

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import PromptTemplate

_rag_vector_stores: dict = {}  # keyed by document_id


def chunk_document(text: str) -> List[str]:
    """Split text using LangChain's RecursiveCharacterTextSplitter."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    return splitter.split_text(text)


def build_rag_vector_store(chunks: List[str], document_id: str = "default"):
    """Embed chunks with OpenAI and store in FAISS."""
    global _rag_vector_stores

    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
    )

    _rag_vector_stores[document_id] = FAISS.from_texts(
        chunks,
        embedding=embeddings,
    )


def load_rag_vector_store(document_id: str = "default"):
    """Load a previously saved FAISS vector store."""
    global _rag_vector_stores

    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
    )

    _rag_vector_stores[document_id] = FAISS.load_local(
        settings.VECTOR_DB_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )


def generate_rag_analysis(query: str, document_id: str = "default") -> str:
    """Retrieve relevant chunks from FAISS and generate analysis via LLM."""
    store = _rag_vector_stores.get(document_id)
    if store is None:
        raise RuntimeError("RAG vector store not initialized. Call build_rag_vector_store first.")

    # Retrieve relevant chunks
    retriever = store.as_retriever()
    docs = retriever.invoke(query)
    context = "\n\n".join(doc.page_content for doc in docs)

    # Build prompt
    prompt = PromptTemplate(
        template="""
You are a financial analyst.

Using the financial report context below, provide:

1. A summary of the company's financial health
2. Key insights
3. Investment advice

Context:
{context}

Question:
{question}
""",
        input_variables=["context", "question"],
    )

    # Generate via LLM
    llm = ChatOpenAI(
        model=settings.LLM_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
    )

    formatted_prompt = prompt.format(context=context, question=query)
    response = llm.invoke(formatted_prompt)
    return response.content


def analyze_financial_report(parsed_text: str, query: str, document_id: str = "default") -> str:
    """
    Full RAG pipeline:
      1. Chunk the parsed text
      2. Build FAISS vector store
      3. Generate analysis via LLM
    """
    chunks = chunk_document(parsed_text)
    build_rag_vector_store(chunks, document_id)
    result = generate_rag_analysis(query, document_id)
    return result
