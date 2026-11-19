
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma


def ingest_banking_policies():

    # 1. Load documents
    documents = [

        Document(
            page_content="""
            International Transfer Policy

            Retail customers can initiate outbound
            international transfers up to USD 10,000
            per transaction, subject to regulatory
            restrictions and account eligibility.

            Transfers above this limit require
            additional verification and approval.
            """,
            metadata={
                "source": "international_transfer_policy.md",
                "tenant_id": "retail",
                "version": "2026-01"
            }
        ),

        Document(
            page_content="""
            International Transfer Charges

            International transfers may involve
            currency conversion charges and
            intermediary bank fees.

            The final amount received depends on
            the applicable exchange rate and
            intermediary charges.
            """,
            metadata={
                "source": "transfer_charges.md",
                "tenant_id": "retail",
                "version": "2026-01"
            }
        ),

        Document(
            page_content="""
            Transfer Processing Time

            International transfers generally
            require one to five business days.

            Processing time depends on the
            destination country, intermediary banks
            and compliance verification.
            """,
            metadata={
                "source": "transfer_processing.md",
                "tenant_id": "retail",
                "version": "2026-01"
            }
        )
    ]

    # 2. Split documents into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=60
    )

    chunks = splitter.split_documents(documents)

    # 3. Create embedding model
    embeddings = OllamaEmbeddings(
        model="nomic-embed-text"
    )

    # 4. Create vector database
    vector_store = Chroma(
        collection_name="banking_policies",
        embedding_function=embeddings,
        persist_directory="./chroma_db"
    )

    # 5. Store chunks and metadata
    ids = [
        f"policy_chunk_{index}"
        for index in range(len(chunks))
    ]

    vector_store.add_documents(
        documents=chunks,
        ids=ids
    )

    print(f"Indexed {len(chunks)} chunks")


if __name__ == "__main__":
    ingest_banking_policies()
