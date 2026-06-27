"""Quick tests: a fast citation check, and a smoke test of the full search pipeline."""
import pymupdf
from llama_index.core.schema import TextNode

from legendary_potato.search import citation, search


def test_citation_format():
    node = TextNode(text="x", metadata={"file_name": "a.pdf", "page_label": "41", "line": 7})
    assert citation(node) == "a.pdf  ›  p. 41  ›  line 7"


def test_search_finds_the_right_page(tmp_path):
    # Tiny 2-page PDF: page 1 irrelevant, page 2 holds the target text.
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "This page is about cats and gardening.")
    doc.new_page().insert_text(
        (72, 72),
        "A person who threatens another with a criminal act is guilty of making an unlawful threat.",
    )
    doc.save(str(tmp_path / "doc.pdf"))
    doc.close()

    results, n_chunks = search("unlawful threat", docs_dir=tmp_path, top_k=2)

    assert n_chunks >= 2
    assert results, "expected at least one hit"
    top = results[0].node
    assert "unlawful threat" in top.get_content().lower()
    assert top.metadata["page_label"] == "2"
