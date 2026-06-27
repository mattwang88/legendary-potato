"""Local hybrid search over PDFs: vector (embeddings) + BM25, fused. PyMuPDF for text."""
from __future__ import annotations

from pathlib import Path

try:
    import pymupdf
except ImportError:  # older PyMuPDF only exposes the `fitz` name
    import fitz as pymupdf

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.llms import MockLLM
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.retrievers.bm25 import BM25Retriever

# Small multilingual model — handles Swedish and English, no API key, runs locally.
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_META_KEYS = ["file_name", "page_label", "line"]


def _load_pdf(path: Path) -> list[Document]:
    """One Document per page; each text block (paragraph) becomes one line for fuller context."""
    docs: list[Document] = []
    pdf = pymupdf.open(str(path))
    try:
        for i in range(pdf.page_count):
            blocks = pdf[i].get_text("blocks", sort=True)
            paras = [" ".join(b[4].split()) for b in blocks if b[4].strip()]
            text = "\n".join(paras)
            if text:
                docs.append(Document(
                    text=text,
                    metadata={"file_name": path.name, "page_label": str(i + 1)},
                ))
    finally:
        pdf.close()
    return docs


def load_documents(docs_dir: str | Path) -> list[Document]:
    """Read every PDF under docs_dir into LlamaIndex Documents (one per page)."""
    documents: list[Document] = []
    for path in sorted(Path(docs_dir).rglob("*")):
        if path.suffix.lower() == ".pdf":
            documents.extend(_load_pdf(path))
    # Keep citation metadata out of the embedded/scored text.
    for d in documents:
        d.excluded_embed_metadata_keys = _META_KEYS
        d.excluded_llm_metadata_keys = _META_KEYS
    return documents


def build_retriever(docs_dir: str | Path, top_k: int = 5):
    documents = load_documents(docs_dir)
    if not documents:
        raise SystemExit(f"No PDFs found in '{docs_dir}'")
    nodes = SentenceSplitter(chunk_size=512, chunk_overlap=64).get_nodes_from_documents(documents)

    # Tag each chunk with the line of its source page where it starts (for citations).
    by_id = {d.id_: d for d in documents}
    for node in nodes:
        src = by_id.get(node.ref_doc_id)
        if src is not None and node.start_char_idx is not None:
            node.metadata["line"] = src.text.count("\n", 0, node.start_char_idx) + 1
        node.excluded_embed_metadata_keys = _META_KEYS
        node.excluded_llm_metadata_keys = _META_KEYS

    embed = HuggingFaceEmbedding(model_name=EMBED_MODEL)
    vector = VectorStoreIndex(nodes, embed_model=embed).as_retriever(similarity_top_k=top_k)
    bm25 = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=top_k)
    return QueryFusionRetriever(
        [vector, bm25],
        similarity_top_k=top_k,
        num_queries=1,              # no LLM query expansion
        mode="reciprocal_rerank",   # reciprocal rank fusion (of vector + BM25)
        use_async=False,
        llm=MockLLM(),              # never called (num_queries=1); just satisfies the constructor
    ), len(nodes)


def citation(node) -> str:
    """A human-readable source reference: file, page, and starting line."""
    md = node.metadata
    parts = [md.get("file_name", "?")]
    if md.get("page_label"):
        parts.append(f"p. {md['page_label']}")
    if md.get("line"):
        parts.append(f"line {md['line']}")
    return "  ›  ".join(parts)


def search(query: str, docs_dir: str | Path = "data", top_k: int = 5):
    retriever, n_nodes = build_retriever(docs_dir, top_k=top_k)
    return retriever.retrieve(query), n_nodes
