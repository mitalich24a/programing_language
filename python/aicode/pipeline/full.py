
import os
from typing import Optional

from openai import OpenAI
from opensearchpy import OpenSearch, helpers
from sentence_transformers import SentenceTransformer, CrossEncoder


# ============================================================
# CONFIGURATION
# ============================================================

INDEX_NAME = "enterprise_documents"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

EMBEDDING_DIM = 384

TOP_K_RETRIEVAL = 20
TOP_K_FINAL = 5

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

os_client = OpenSearch(
    hosts=[{
        "host": "localhost",
        "port": 9200
    }],
    http_auth=(
        os.getenv("OPENSEARCH_USER", "admin"),
        os.getenv("OPENSEARCH_PASSWORD", "admin")
    ),
    use_ssl=False,
    verify_certs=False
)

embedding_model = SentenceTransformer(EMBEDDING_MODEL)
reranker = CrossEncoder(RERANKER_MODEL)


# ============================================================
# 1. CREATE OPENSEARCH INDEX
# ============================================================

def create_index():

    if os_client.indices.exists(index=INDEX_NAME):
        return

    mapping = {
        "settings": {
            "index": {
                "knn": True
            }
        },

        "mappings": {
            "properties": {

                "content": {
                    "type": "text"
                },

                "embedding": {
                    "type": "knn_vector",
                    "dimension": EMBEDDING_DIM,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "lucene"
                    }
                },

                "department": {
                    "type": "keyword"
                },

                "document_type": {
                    "type": "keyword"
                },

                "year": {
                    "type": "integer"
                },

                "allowed_roles": {
                    "type": "keyword"
                },

                "allowed_users": {
                    "type": "keyword"
                }
            }
        }
    }

    os_client.indices.create(
        index=INDEX_NAME,
        body=mapping
    )


# ============================================================
# 2. DOCUMENT EMBEDDING
# ============================================================

def embed_text(text):

    return embedding_model.encode(
        text,
        normalize_embeddings=True
    ).tolist()


# ============================================================
# 3. DOCUMENT INDEXING
# ============================================================

def index_documents(documents):

    actions = []

    for doc in documents:

        embedding = embed_text(doc["content"])

        actions.append({
            "_index": INDEX_NAME,
            "_id": doc["id"],
            "_source": {
                "content": doc["content"],
                "embedding": embedding,

                "department": doc["department"],
                "document_type": doc["document_type"],
                "year": doc["year"],

                "allowed_roles": doc["allowed_roles"],
                "allowed_users": doc["allowed_users"]
            }
        })

    helpers.bulk(os_client, actions)

    os_client.indices.refresh(index=INDEX_NAME)


# ============================================================
# 4. QUERY REWRITING
# ============================================================

def rewrite_query(user_query, conversation_context=None):

    prompt = f"""
    Rewrite the user question for enterprise document retrieval.

    Preserve the original intent.
    Resolve references using conversation context.
    Expand abbreviations where useful.
    Do not invent facts or assumptions.

    Context: {conversation_context or "None"}

    Question: {user_query}

    Return only the rewritten search query.
    """

    try:

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        rewritten = response.choices[0].message.content

        return rewritten.strip() if rewritten else user_query

    except Exception:
        return user_query


# ============================================================
# 5. ACCESS CONTROL + METADATA FILTERING
# ============================================================

def build_filters(user, metadata=None):

    metadata = metadata or {}

    filters = [

        # Authorization:
        # User can access documents matching their role
        # OR documents explicitly assigned to them.

        {
            "bool": {
                "should": [
                    {
                        "terms": {
                            "allowed_roles": user["roles"]
                        }
                    },
                    {
                        "terms": {
                            "allowed_users": [
                                user["id"],
                                "PUBLIC"
                            ]
                        }
                    }
                ],
                "minimum_should_match": 1
            }
        }
    ]

    # Metadata filters

    if metadata.get("department"):

        filters.append({
            "term": {
                "department": metadata["department"]
            }
        })

    if metadata.get("document_type"):

        filters.append({
            "term": {
                "document_type": metadata["document_type"]
            }
        })

    if metadata.get("year"):

        filters.append({
            "term": {
                "year": metadata["year"]
            }
        })

    return filters


# ============================================================
# 6. BM25 KEYWORD SEARCH
# ============================================================

def bm25_search(query, filters, top_k=TOP_K_RETRIEVAL):

    response = os_client.search(
        index=INDEX_NAME,
        body={
            "size": top_k,

            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "content": query
                            }
                        }
                    ],

                    "filter": filters
                }
            }
        }
    )

    return response["hits"]["hits"]


# ============================================================
# 7. VECTOR SEARCH
# ============================================================

def vector_search(query, filters, top_k=TOP_K_RETRIEVAL):

    vector = embed_text(query)

    response = os_client.search(
        index=INDEX_NAME,
        body={
            "size": top_k,

            "query": {
                "knn": {
                    "embedding": {
                        "vector": vector,
                        "k": top_k,
                        "filter": {
                            "bool": {
                                "filter": filters
                            }
                        }
                    }
                }
            }
        }
    )

    return response["hits"]["hits"]


# ============================================================
# 8. RECIPROCAL RANK FUSION
# ============================================================

def reciprocal_rank_fusion(
    result_lists,
    k=60,
    top_k=TOP_K_RETRIEVAL
):

    scores = {}
    documents = {}

    for results in result_lists:

        for rank, hit in enumerate(results, start=1):

            doc_id = hit["_id"]

            scores[doc_id] = (
                scores.get(doc_id, 0)
                + 1 / (k + rank)
            )

            documents[doc_id] = hit

    ranked_ids = sorted(
        scores,
        key=scores.get,
        reverse=True
    )

    return [
        documents[doc_id]
        for doc_id in ranked_ids[:top_k]
    ]


# ============================================================
# 9. CROSS-ENCODER RERANKING
# ============================================================

def rerank_documents(
    query,
    documents,
    top_k=TOP_K_FINAL
):

    if not documents:
        return []

    pairs = [
        (
            query,
            doc["_source"]["content"]
        )
        for doc in documents
    ]

    scores = reranker.predict(pairs)

    ranked = sorted(
        zip(documents, scores),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        {
            "id": doc["_id"],
            "content": doc["_source"]["content"],
            "score": float(score)
        }
        for doc, score in ranked[:top_k]
    ]


# ============================================================
# 10. COMPLETE RETRIEVAL PIPELINE
# ============================================================

def retrieve(
    user_query,
    user,
    metadata=None,
    conversation_context=None
):

    # A. Rewrite query

    rewritten_query = rewrite_query(
        user_query,
        conversation_context
    )

    # B. Apply access control and metadata filters

    filters = build_filters(
        user,
        metadata
    )

    # C. Run hybrid retrieval

    keyword_results = bm25_search(
        rewritten_query,
        filters
    )

    semantic_results = vector_search(
        rewritten_query,
        filters
    )

    # D. Combine results

    hybrid_results = reciprocal_rank_fusion(
        [
            keyword_results,
            semantic_results
        ]
    )

    # E. Rerank

    final_results = rerank_documents(
        rewritten_query,
        hybrid_results
    )

    return {
        "original_query": user_query,
        "rewritten_query": rewritten_query,
        "documents": final_results
    }


# ============================================================
# 11. EXECUTION
# ============================================================

if __name__ == "__main__":

    create_index()

    documents = [
        {
            "id": "doc1",
            "content": (
                "Employees can carry forward "
                "up to 5 days of annual leave."
            ),
            "department": "finance",
            "document_type": "policy",
            "year": 2026,
            "allowed_roles": ["employee", "manager"],
            "allowed_users": []
        },
        {
            "id": "doc2",
            "content": (
                "Managers must approve leave requests "
                "before employees take leave."
            ),
            "department": "finance",
            "document_type": "policy",
            "year": 2026,
            "allowed_roles": ["manager"],
            "allowed_users": []
        }
    ]

    index_documents(documents)

    user = {
        "id": "user123",
        "roles": ["employee"]
    }

    metadata = {
        "department": "finance",
        "document_type": "policy",
        "year": 2026
    }

    result = retrieve(
        user_query="How much leave can I carry forward?",
        user=user,
        metadata=metadata
    )

    print("Original:", result["original_query"])
    print("Rewritten:", result["rewritten_query"])

    for doc in result["documents"]:

        print("\nDocument:", doc["id"])
        print("Content:", doc["content"])
        print("Score:", doc["score"])
