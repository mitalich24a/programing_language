
from langchain_core.tools import tool
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma


embeddings = OllamaEmbeddings(
    model="nomic-embed-text"
)

vector_store = Chroma(
    collection_name="banking_policies",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)


@tool
def search_banking_policy(query: str) -> str:
    """
    Search internal banking policy documents.

    Use this tool for questions about:
    international transfers, fees, limits,
    processing times and banking procedures.
    """

    # Search relevant chunks
    documents = vector_store.similarity_search(
        query=query,
        k=4,
        filter={
            "tenant_id": "retail"
        }
    )

    if not documents:
        return "No relevant policy documents found."

    # Prepare retrieved context
    results = []

    for document in documents:

        source = document.metadata.get(
            "source",
            "Unknown"
        )

        version = document.metadata.get(
            "version",
            "Unknown"
        )

        results.append(
            f"""
            Source: {source}
            Version: {version}

            Content:
            {document.page_content}
            """
        )

    return "\n\n".join(results)
