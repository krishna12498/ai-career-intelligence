from rag.documents import load_documents
from rag.vector_store import KnowledgeVectorStore


def test_vector_store_build_search_and_reload(tmp_path):
    index_path = tmp_path / "knowledge.faiss"
    metadata_path = tmp_path / "knowledge.json"
    documents = load_documents()
    store = KnowledgeVectorStore(index_path, metadata_path)

    store.build(documents)
    assert index_path.exists()
    assert metadata_path.exists()

    rag_results = store.search("retrieval augmented generation and vector embeddings", top_k=3)
    assert rag_results
    assert rag_results[0][0].skill in {"RAG", "Embeddings", "Vector Search"}
    assert rag_results[0][1] > 0

    docker_results = store.search("Docker container images deployment", top_k=3)
    assert docker_results
    assert docker_results[0][0].skill == "Docker"

    reloaded = KnowledgeVectorStore(index_path, metadata_path)
    reloaded.load()
    assert [document.skill for document in reloaded.documents] == [document.skill for document in documents]
    assert reloaded.search("Docker container images deployment", top_k=1)[0][0].skill == "Docker"


def test_vector_store_handles_empty_queries(tmp_path):
    store = KnowledgeVectorStore(tmp_path / "knowledge.faiss", tmp_path / "knowledge.json")
    store.build(load_documents())

    assert store.search("", top_k=5) == []
    assert store.search("unknown career technology", top_k=0) == []
    assert store.search("quantum computing", top_k=5) == []
