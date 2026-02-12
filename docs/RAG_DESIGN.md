# RAG Implementation - Design & Architecture

**Project:** Omni-Channel AI Servicing Platform  
**Feature:** Retrieval-Augmented Generation (RAG)  
**Status:** Design Phase  
**Target Completion:** February 14-16, 2026  

---

## Executive Summary

This document outlines the design and implementation strategy for adding Retrieval-Augmented Generation (RAG) capabilities to the existing LangGraph-based AI servicing platform. The RAG system will ground LLM responses in banking policy documents, reducing hallucinations and improving answer accuracy through evidence-based retrieval.

**Key Objectives:**
- Add policy document retrieval to existing workflow
- Achieve 0.75+ RAGAS composite score on 50+ Q&A pairs
- Maintain sub-500ms retrieval latency
- Preserve backward compatibility with existing system
- Enable measurable evaluation with RAGAS framework

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Design](#component-design)
3. [Knowledge Base Structure](#knowledge-base-structure)
4. [Vector Store Design](#vector-store-design)
5. [Retrieval Service](#retrieval-service)
6. [LangGraph Integration](#langgraph-integration)
7. [RAGAS Evaluation](#ragas-evaluation)
8. [Implementation Phases](#implementation-phases)
9. [Performance Targets](#performance-targets)
10. [Testing Strategy](#testing-strategy)

---

## Architecture Overview

### High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXISTING LANGGRAPH WORKFLOW                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  validate_input → classify_intent → extract_entities             │
│                                          ↓                        │
│                                   [NEW: retrieve_context]        │
│                                          ↓                        │
│                                   generate_response              │
│                                          ↓                        │
│                                   validate_output → respond      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      RAG COMPONENTS (NEW)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. Knowledge Base (Documents)                                   │
│     ├─ Banking Policies (address, disputes, payments, fraud)    │
│     ├─ FAQs and Procedures                                       │
│     └─ Regulatory Guidelines                                     │
│                                                                   │
│  2. Vector Store (FAISS)                                         │
│     ├─ Document Embeddings (OpenAI text-embedding-3-small)      │
│     ├─ Metadata (intent_type, policy_id, version)               │
│     └─ Local persistence (faiss_index/)                          │
│                                                                   │
│  3. Retrieval Service                                            │
│     ├─ Query embedding                                           │
│     ├─ Similarity search (top-k=3)                               │
│     ├─ Re-ranking by intent relevance                            │
│     └─ Context formatting for LLM                                │
│                                                                   │
│  4. RAGAS Evaluation                                             │
│     ├─ Test Dataset (50+ Q&A pairs)                              │
│     ├─ Metrics: faithfulness, relevancy, precision, recall       │
│     └─ Offline evaluation pipeline                               │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Integration Points

**State Flow (Updated):**
```python
State = {
    "messages": List[BaseMessage],
    "intent": str,                    # Existing
    "entities": Dict,                 # Existing
    "context": List[Document],        # NEW - Retrieved documents
    "context_metadata": Dict,         # NEW - Retrieval metadata
    "response": str,
    "guardrails": Dict,
    "metrics": Dict
}
```

---

## Component Design

### 1. Knowledge Base Structure

#### Directory Layout
```
knowledge_base/
├── policies/
│   ├── address_update_policy.md       # Address change procedures
│   ├── dispute_handling_policy.md     # Chargeback/dispute process
│   ├── payment_policy.md              # Payment methods, schedules
│   ├── fraud_reporting_policy.md      # Fraud detection, reporting
│   ├── card_services_policy.md        # Card activation, replacement
│   └── account_inquiry_policy.md      # Balance, statement requests
├── faqs/
│   ├── address_faqs.md                # Common address questions
│   ├── dispute_faqs.md                # Dispute Q&A
│   ├── payment_faqs.md                # Payment Q&A
│   └── general_faqs.md                # General banking Q&A
└── metadata.json                      # Document metadata (intent tags)
```

#### Document Format Example
```markdown
# Address Update Policy

## Policy ID: POL-ADDR-001
## Version: 2024-01
## Intent: ADDRESS_UPDATE
## Last Updated: January 15, 2024

## Overview
Customers can update their mailing address through multiple channels including 
online banking, mobile app, phone banking, or in-branch visits. This policy 
outlines the verification requirements and processing timelines.

## Requirements
- Valid customer authentication (verified account access)
- Proof of new address (one of the following):
  - Utility bill (water, electric, gas) dated within 60 days
  - Lease agreement or mortgage statement
  - Government-issued document showing new address
- Secondary ID verification for address changes to different state

## Processing Timeline
- Online/Mobile: 1-2 business days
- Phone/In-branch: 3-5 business days
- International address: 5-10 business days

## Procedures
1. Customer submits address update request via preferred channel
2. System validates current address on file for comparison
3. Agent or automated system verifies supporting documentation
4. System updates address in core banking system
5. Confirmation sent to both old and new addresses
6. Update propagated to card services, statement delivery, etc.

## Special Cases
### International Addresses
- Additional verification required
- Embassy or consulate documentation may be needed
- Extended processing time (5-10 business days)

### PO Box Addresses
- Accepted for mailing address only
- Physical address still required on file
- Cannot be used for card delivery

## Compliance Notes
- GDPR: Customer consent required for address data processing
- PATRIOT ACT: Address verification required for AML compliance
- State regulations: Some states require additional documentation
```

#### Metadata Schema
```json
{
  "documents": [
    {
      "file_path": "policies/address_update_policy.md",
      "policy_id": "POL-ADDR-001",
      "intent": "ADDRESS_UPDATE",
      "document_type": "policy",
      "version": "2024-01",
      "last_updated": "2024-01-15",
      "keywords": ["address", "update", "change", "relocation", "move"],
      "related_intents": ["ACCOUNT_INQUIRY"],
      "compliance_tags": ["GDPR", "PATRIOT_ACT"]
    },
    {
      "file_path": "policies/dispute_handling_policy.md",
      "policy_id": "POL-DISP-001",
      "intent": "DISPUTE",
      "document_type": "policy",
      "version": "2024-01",
      "last_updated": "2024-01-10",
      "keywords": ["dispute", "chargeback", "unauthorized", "transaction"],
      "related_intents": ["FRAUD_REPORT"],
      "compliance_tags": ["FCBA", "EFTA"]
    }
  ]
}
```

---

## Vector Store Design

### FAISS Implementation

**Why FAISS?**
- ✅ **Local deployment**: No cloud dependencies, faster prototyping
- ✅ **Performance**: Sub-10ms similarity search
- ✅ **Lightweight**: Fits in memory, minimal resource overhead
- ✅ **Production-ready**: Meta's library, battle-tested at scale
- ✅ **Free**: No licensing costs, open-source

**Alternative Considered:**
- Chroma: Good for prototyping, but FAISS is faster for <10k docs
- Pinecone: Cloud-based, adds latency and cost
- Weaviate: Overkill for prototype scale

### Storage Architecture

```python
# Document Structure in Vector Store
{
    "id": "policy_001_chunk_001",
    "content": "Address update procedures require...",
    "embedding": [0.123, -0.456, ...],  # 1536-dim vector (OpenAI)
    "metadata": {
        "policy_id": "POL-ADDR-001",
        "intent": "ADDRESS_UPDATE",
        "document_type": "policy",
        "chunk_index": 0,
        "source_file": "policies/address_update_policy.md",
        "version": "2024-01",
        "section": "Requirements"
    }
}
```

### Chunking Strategy

**Configuration:**
- **Chunk size**: 500 tokens (~2000 characters)
- **Overlap**: 50 tokens (10%)
- **Splitting**: Semantic boundaries (paragraphs, sections)

**Rationale:**
- 500 tokens: Balances context completeness vs. retrieval precision
- 10% overlap: Prevents context loss at chunk boundaries
- Semantic splitting: Preserves meaning, avoids mid-sentence cuts

**Example:**
```python
# Document: 2000 tokens
# Chunks:
#   Chunk 0: tokens 0-500
#   Chunk 1: tokens 450-950   (50 token overlap)
#   Chunk 2: tokens 900-1400  (50 token overlap)
#   Chunk 3: tokens 1350-1850
#   Chunk 4: tokens 1800-2000
```

### Index Structure

```
faiss_index/
├── index.faiss              # FAISS vector index (similarity search)
├── docstore.json            # Document content + metadata
├── index_metadata.json      # Index configuration
└── embeddings_cache.pkl     # Cached embeddings (optional)
```

**Index Configuration:**
```python
{
    "embedding_model": "text-embedding-3-small",
    "embedding_dimension": 1536,
    "index_type": "FlatIP",  # Inner Product (cosine similarity)
    "num_documents": 150,     # ~50 docs × 3 chunks avg
    "created_at": "2026-02-13T10:00:00Z",
    "last_updated": "2026-02-13T10:00:00Z"
}
```

---

## Retrieval Service

### Component Architecture

```
omni_channel_ai_servicing/
└── infrastructure/
    └── retrieval/
        ├── __init__.py
        ├── vector_store.py         # FAISS wrapper
        ├── embedding_service.py    # OpenAI embeddings
        ├── retriever.py            # Retrieval logic + re-ranking
        └── document_loader.py      # Load, chunk, embed documents
```

### Retrieval Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    RETRIEVAL PIPELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Input Processing                                         │
│     ├─ user_query: "How do I update my address?"            │
│     ├─ intent: CustomerIntent.ADDRESS_UPDATE                │
│     └─ entities: {address_type: "mailing"}                  │
│                                                               │
│  2. Query Enhancement                                        │
│     └─ enriched_query: "Update mailing address procedures"  │
│                                                               │
│  3. Embedding                                                │
│     └─ query_vector: [0.12, -0.45, ...] (1536-dim)         │
│                                                               │
│  4. Intent Filtering (Optional)                              │
│     └─ Filter: metadata["intent"] == "ADDRESS_UPDATE"       │
│                                                               │
│  5. Similarity Search                                        │
│     ├─ Algorithm: Cosine similarity (Inner Product)         │
│     ├─ Top-k: 5 candidates (before re-ranking)              │
│     └─ Scores: [0.92, 0.89, 0.85, 0.82, 0.79]              │
│                                                               │
│  6. Re-ranking                                               │
│     ├─ Intent match bonus: +0.1 if exact intent            │
│     ├─ Document type bonus: +0.05 for "policy" vs "faq"    │
│     └─ Top-k: 3 final documents                             │
│                                                               │
│  7. Context Formatting                                       │
│     └─ Formatted for LLM prompt injection                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Code Design

#### 1. Vector Store Interface
```python
# omni_channel_ai_servicing/infrastructure/retrieval/vector_store.py

from typing import List, Dict, Optional
import faiss
import numpy as np
from pathlib import Path

class FAISSVectorStore:
    """
    FAISS-based vector store for document retrieval.
    
    Features:
    - Local persistence (no cloud dependencies)
    - Fast similarity search (<10ms)
    - Metadata filtering
    """
    
    def __init__(self, index_path: Path, embedding_dim: int = 1536):
        self.index_path = index_path
        self.embedding_dim = embedding_dim
        self.index: Optional[faiss.Index] = None
        self.docstore: Dict[str, Dict] = {}
        
    async def initialize(self):
        """Load or create FAISS index."""
        pass
    
    async def add_documents(
        self, 
        documents: List[Dict],
        embeddings: np.ndarray
    ):
        """Add documents with embeddings to index."""
        pass
    
    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Similarity search with optional metadata filtering.
        
        Args:
            query_embedding: Query vector (1536-dim)
            top_k: Number of results
            filter_metadata: Filter by metadata (e.g., {"intent": "ADDRESS_UPDATE"})
            
        Returns:
            List of documents with scores
        """
        pass
    
    def save(self):
        """Persist index to disk."""
        pass
    
    def load(self):
        """Load index from disk."""
        pass
```

#### 2. Embedding Service
```python
# omni_channel_ai_servicing/infrastructure/retrieval/embedding_service.py

from typing import List
import openai
from tenacity import retry, stop_after_attempt, wait_exponential

class EmbeddingService:
    """
    OpenAI embedding service with caching and retry logic.
    
    Model: text-embedding-3-small (1536 dimensions)
    Cost: $0.00002 per 1K tokens
    """
    
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.cache: Dict[str, List[float]] = {}
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text.
        
        Args:
            text: Input text (max 8191 tokens)
            
        Returns:
            Embedding vector (1536-dim)
        """
        # Check cache
        if text in self.cache:
            return self.cache[text]
        
        # Generate embedding
        response = await openai.Embedding.acreate(
            model=self.model,
            input=text
        )
        
        embedding = response['data'][0]['embedding']
        
        # Cache result
        self.cache[text] = embedding
        
        return embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embedding generation (more efficient)."""
        pass
```

#### 3. Document Loader
```python
# omni_channel_ai_servicing/infrastructure/retrieval/document_loader.py

from typing import List, Dict
from pathlib import Path
import re

class DocumentLoader:
    """
    Load and chunk documents from knowledge base.
    
    Features:
    - Markdown parsing
    - Semantic chunking (paragraph-aware)
    - Metadata extraction
    """
    
    def __init__(
        self,
        knowledge_base_path: Path,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        self.knowledge_base_path = knowledge_base_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    async def load_all_documents(self) -> List[Dict]:
        """
        Load all documents from knowledge base.
        
        Returns:
            List of documents with content and metadata
        """
        pass
    
    def chunk_document(self, content: str, metadata: Dict) -> List[Dict]:
        """
        Split document into overlapping chunks.
        
        Strategy:
        1. Split on section boundaries (## headers)
        2. Further split long sections by paragraphs
        3. Add chunk_index to metadata
        
        Returns:
            List of chunks with metadata
        """
        pass
    
    def extract_metadata(self, content: str, file_path: Path) -> Dict:
        """
        Extract metadata from document frontmatter.
        
        Parses:
        - Policy ID
        - Intent tags
        - Version
        - Keywords
        """
        pass
```

#### 4. Retriever (Main Interface)
```python
# omni_channel_ai_servicing/infrastructure/retrieval/retriever.py

from typing import List, Optional
from omni_channel_ai_servicing.domain.models.intent import CustomerIntent

class Retriever:
    """
    High-level retrieval interface with re-ranking.
    
    Features:
    - Intent-aware filtering
    - Re-ranking by relevance
    - Context formatting
    """
    
    def __init__(
        self,
        vector_store: FAISSVectorStore,
        embedding_service: EmbeddingService
    ):
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        
    async def retrieve(
        self,
        query: str,
        intent: Optional[CustomerIntent] = None,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Retrieve relevant documents with re-ranking.
        
        Args:
            query: User query or enriched search query
            intent: Optional intent for filtering
            top_k: Number of final documents to return
            
        Returns:
            List of documents sorted by relevance
        """
        # 1. Embed query
        query_embedding = await self.embedding_service.embed_text(query)
        
        # 2. Retrieve candidates (top_k * 2 for re-ranking)
        filter_metadata = {"intent": intent.value} if intent else None
        candidates = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k * 2,
            filter_metadata=filter_metadata
        )
        
        # 3. Re-rank
        reranked = self._rerank(candidates, intent)
        
        # 4. Return top-k
        return reranked[:top_k]
    
    def _rerank(self, documents: List[Dict], intent: Optional[CustomerIntent]) -> List[Dict]:
        """
        Re-rank documents by relevance.
        
        Scoring:
        - Base score: cosine similarity
        - Intent match: +0.1 if exact intent
        - Document type: +0.05 for "policy" vs "faq"
        - Freshness: +0.02 for docs updated in last 90 days
        """
        pass
    
    def format_context(self, documents: List[Dict]) -> str:
        """
        Format retrieved documents for LLM prompt.
        
        Format:
        [Document 1 - address_update_policy.md]
        <content>
        ---
        [Document 2 - address_faqs.md]
        <content>
        """
        pass
```

---

## LangGraph Integration

### New Node: `retrieve_context`

```python
# omni_channel_ai_servicing/graph/nodes/retrieve_context.py

from typing import Any
from langgraph.graph import StateGraph
from omni_channel_ai_servicing.graph.state import State
from omni_channel_ai_servicing.domain.models.intent import CustomerIntent
from omni_channel_ai_servicing.infrastructure.retrieval.retriever import Retriever
from omni_channel_ai_servicing.services.metrics import metrics

async def retrieve_context(state: State) -> State:
    """
    Retrieve relevant policy documents based on intent and entities.
    
    Flow:
    1. Extract intent and entities from state
    2. Build enriched search query
    3. Retrieve top-k documents from vector store
    4. Add context to state
    5. Track retrieval metrics
    
    Args:
        state: LangGraph state with intent and entities
        
    Returns:
        Updated state with context and context_metadata
    """
    # Get intent
    intent_str = state.get("intent", "FALLBACK")
    intent = CustomerIntent(intent_str)
    
    # Get entities
    entities = state.get("entities", {})
    
    # Get user message
    user_message = state["messages"][-1].content
    
    # Build enriched query
    query = build_search_query(user_message, intent, entities)
    
    # Retrieve documents
    retriever = get_retriever()  # Singleton instance
    docs = await retriever.retrieve(
        query=query,
        intent=intent,
        top_k=3
    )
    
    # Format context
    formatted_context = retriever.format_context(docs)
    
    # Update state
    state["context"] = formatted_context
    state["context_metadata"] = {
        "num_docs_retrieved": len(docs),
        "sources": [d["metadata"]["source_file"] for d in docs],
        "intent_filter": intent.value,
        "query_used": query
    }
    
    # Track metrics
    metrics.increment("retrieval.total")
    metrics.histogram("retrieval.docs_retrieved", len(docs))
    if len(docs) == 0:
        metrics.increment("retrieval.no_results")
    
    return state


def build_search_query(
    user_message: str,
    intent: CustomerIntent,
    entities: dict
) -> str:
    """
    Build enriched search query from user message and extracted data.
    
    Examples:
    - Intent: ADDRESS_UPDATE, Entities: {address_type: "mailing"}
      Query: "Update mailing address procedures requirements"
      
    - Intent: DISPUTE, Entities: {transaction_id: "TXN123", amount: 50.00}
      Query: "Dispute unauthorized transaction chargeback procedures"
    """
    # Start with user message
    query_parts = [user_message]
    
    # Add intent context
    if intent != CustomerIntent.FALLBACK:
        intent_keywords = {
            CustomerIntent.ADDRESS_UPDATE: "update change address",
            CustomerIntent.DISPUTE: "dispute chargeback unauthorized",
            CustomerIntent.FRAUD_REPORT: "fraud report unauthorized",
            # ... more mappings
        }
        query_parts.append(intent_keywords.get(intent, ""))
    
    # Add entity context
    if entities:
        entity_str = " ".join(str(v) for v in entities.values() if v)
        query_parts.append(entity_str)
    
    return " ".join(query_parts)
```

### Updated Workflow

```python
# omni_channel_ai_servicing/graph/workflow.py

from langgraph.graph import StateGraph, END
from omni_channel_ai_servicing.graph.nodes import (
    validate_input,
    classify_intent,
    extract_entities,
    retrieve_context,  # NEW
    generate_response,
    validate_output,
    respond
)

def create_workflow() -> StateGraph:
    """Create LangGraph workflow with RAG."""
    
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("validate_input", validate_input)
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("extract_entities", extract_entities)
    workflow.add_node("retrieve_context", retrieve_context)  # NEW
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("validate_output", validate_output)
    workflow.add_node("respond", respond)
    
    # Define edges
    workflow.set_entry_point("validate_input")
    workflow.add_edge("validate_input", "classify_intent")
    workflow.add_edge("classify_intent", "extract_entities")
    workflow.add_edge("extract_entities", "retrieve_context")  # NEW
    workflow.add_edge("retrieve_context", "generate_response")  # NEW
    workflow.add_edge("generate_response", "validate_output")
    workflow.add_edge("validate_output", "respond")
    workflow.add_edge("respond", END)
    
    return workflow.compile()
```

### Updated Prompt (Context Injection)

```python
# omni_channel_ai_servicing/llm/prompts.py

def get_response_prompt_with_context(
    intent: str,
    entities: dict,
    context: str,
    user_message: str
) -> str:
    """
    Generate prompt with RAG context injection.
    
    Key elements:
    - Explicit instruction to use ONLY provided context
    - Source citation requirement
    - Fallback behavior if context insufficient
    """
    
    prompt = f"""You are a banking customer service assistant. Use ONLY the following 
policy documents to answer the customer's question. Do not use information from 
outside these documents.

POLICY DOCUMENTS:
{context}

CUSTOMER INTENT: {intent}
EXTRACTED ENTITIES: {entities}
CUSTOMER QUESTION: {user_message}

INSTRUCTIONS:
1. Answer the question using ONLY information from the policy documents above
2. Cite the source document for each piece of information (e.g., "According to the Address Update Policy...")
3. If the policy documents don't contain enough information, explicitly state: 
   "I don't have complete information in the available policies. Let me connect you with a specialist."
4. Maintain a helpful, professional tone
5. If multiple documents provide relevant information, synthesize them coherently

Provide your response:"""
    
    return prompt


# Fallback for when no context retrieved
def get_response_prompt_no_context(
    intent: str,
    entities: dict,
    user_message: str
) -> str:
    """Fallback prompt when retrieval returns no results."""
    
    prompt = f"""You are a banking customer service assistant. 

CUSTOMER INTENT: {intent}
EXTRACTED ENTITIES: {entities}
CUSTOMER QUESTION: {user_message}

Note: No specific policy documents were found for this query. Provide a general, 
helpful response and suggest the customer contact support for detailed information.

Provide your response:"""
    
    return prompt
```

---

## RAGAS Evaluation

### Evaluation Framework Design

#### Test Dataset Structure

```python
# evaluation/test_dataset.json

{
    "metadata": {
        "version": "1.0",
        "created_at": "2026-02-13",
        "num_test_cases": 50,
        "intents_covered": ["ADDRESS_UPDATE", "DISPUTE", "FRAUD_REPORT", ...]
    },
    "test_cases": [
        {
            "id": "test_001",
            "question": "How do I update my address?",
            "intent": "ADDRESS_UPDATE",
            "entities": {},
            "ground_truth": "To update your address, you need to provide valid ID verification and proof of new address such as a utility bill dated within 60 days. Online/mobile updates take 1-2 business days, while phone/in-branch updates take 3-5 business days.",
            "expected_sources": ["policies/address_update_policy.md"],
            "difficulty": "easy"
        },
        {
            "id": "test_002",
            "question": "I moved to a different state. What documents do I need to update my address?",
            "intent": "ADDRESS_UPDATE",
            "entities": {"address_type": "relocation", "cross_state": true},
            "ground_truth": "For address changes to a different state, you need secondary ID verification in addition to proof of new address. Required documents include utility bill or lease agreement dated within 60 days, plus government-issued ID showing new address. Processing takes 3-5 business days.",
            "expected_sources": ["policies/address_update_policy.md"],
            "difficulty": "medium"
        },
        {
            "id": "test_003",
            "question": "Can I use a PO Box as my primary address?",
            "intent": "ADDRESS_UPDATE",
            "entities": {"address_type": "po_box"},
            "ground_truth": "PO Box addresses are accepted for mailing address only. You must still maintain a physical address on file, and PO Boxes cannot be used for card delivery.",
            "expected_sources": ["policies/address_update_policy.md"],
            "difficulty": "medium"
        },
        {
            "id": "test_010",
            "question": "I see an unauthorized charge of $500 on my statement. What should I do?",
            "intent": "DISPUTE",
            "entities": {"amount": 500, "issue_type": "unauthorized"},
            "ground_truth": "File a dispute immediately by calling customer service or using the mobile app. You have 60 days from the statement date to dispute charges. The charge will be temporarily credited while we investigate. Investigation typically takes 10-30 business days.",
            "expected_sources": ["policies/dispute_handling_policy.md"],
            "difficulty": "easy"
        }
        // ... 46 more test cases
    ]
}
```

#### Evaluation Pipeline

```python
# evaluation/ragas_evaluation.py

import asyncio
from typing import List, Dict
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset

from omni_channel_ai_servicing.infrastructure.retrieval.retriever import Retriever
from omni_channel_ai_servicing.graph.workflow import create_workflow

class RAGASEvaluator:
    """
    RAGAS evaluation framework for RAG system.
    
    Metrics:
    - Faithfulness: Answer grounded in retrieved context?
    - Answer Relevancy: Answer addresses the question?
    - Context Precision: Relevant docs ranked high?
    - Context Recall: Ground truth in retrieved docs?
    """
    
    def __init__(
        self,
        test_dataset_path: str,
        workflow: StateGraph,
        retriever: Retriever
    ):
        self.test_dataset_path = test_dataset_path
        self.workflow = workflow
        self.retriever = retriever
        
    async def run_evaluation(self) -> Dict:
        """
        Run full RAGAS evaluation.
        
        Returns:
            {
                "composite_score": 0.78,
                "faithfulness": 0.82,
                "answer_relevancy": 0.79,
                "context_precision": 0.75,
                "context_recall": 0.92,
                "per_intent_scores": {...}
            }
        """
        # Load test dataset
        test_cases = self._load_test_dataset()
        
        # Run retrieval + generation for each test case
        results = []
        for test in test_cases:
            result = await self._evaluate_single(test)
            results.append(result)
        
        # Convert to RAGAS dataset format
        dataset = Dataset.from_list(results)
        
        # Run RAGAS evaluation
        scores = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall
            ]
        )
        
        # Aggregate results
        aggregated = self._aggregate_scores(scores, test_cases)
        
        # Save results
        self._save_results(aggregated)
        
        return aggregated
    
    async def _evaluate_single(self, test_case: Dict) -> Dict:
        """
        Evaluate single test case.
        
        Returns:
            {
                "question": "How do I update my address?",
                "contexts": ["Policy doc 1...", "Policy doc 2..."],
                "answer": "To update your address...",
                "ground_truth": "Expected answer..."
            }
        """
        question = test_case["question"]
        intent = test_case["intent"]
        
        # Retrieve context
        docs = await self.retriever.retrieve(
            query=question,
            intent=intent,
            top_k=3
        )
        contexts = [d["content"] for d in docs]
        
        # Generate answer
        state = {
            "messages": [{"role": "user", "content": question}],
            "intent": intent,
            "entities": test_case.get("entities", {})
        }
        result_state = await self.workflow.ainvoke(state)
        answer = result_state["response"]
        
        return {
            "question": question,
            "contexts": contexts,
            "answer": answer,
            "ground_truth": test_case["ground_truth"]
        }
    
    def _aggregate_scores(self, scores: Dict, test_cases: List[Dict]) -> Dict:
        """
        Aggregate scores with per-intent breakdown.
        
        Returns:
            {
                "composite_score": 0.78,
                "faithfulness": 0.82,
                "per_intent_scores": {
                    "ADDRESS_UPDATE": {"faithfulness": 0.85, ...},
                    "DISPUTE": {"faithfulness": 0.78, ...}
                }
            }
        """
        pass
```

### RAGAS Metrics Explained

#### 1. Faithfulness (Answer Grounding)
**Question:** Is the generated answer faithful to the retrieved context?

**Measurement:**
- Decomposes answer into statements
- Checks if each statement can be inferred from context
- Score = (verified statements) / (total statements)

**Example:**
```
Context: "Processing takes 3-5 business days for phone updates."
Answer: "Your address update will take 3-5 business days."
Faithfulness: 1.0 (fully grounded)

Answer: "Your address update will take 1-2 days."
Faithfulness: 0.0 (contradicts context)
```

#### 2. Answer Relevancy (Question Addressing)
**Question:** Does the answer address the user's question?

**Measurement:**
- Generates questions that the answer would address
- Compares to actual user question using embeddings
- Score = similarity(generated_questions, user_question)

**Example:**
```
Question: "How do I update my address?"
Answer: "Call customer service at 1-800-XXX-XXXX to update your address."
Relevancy: 1.0 (directly answers)

Answer: "We offer many services including loans and credit cards."
Relevancy: 0.2 (not relevant)
```

#### 3. Context Precision (Ranking Quality)
**Question:** Are relevant documents ranked higher than irrelevant ones?

**Measurement:**
- For each position k in retrieved docs
- Checks if doc at position k is relevant to answer
- Penalizes relevant docs at lower ranks

**Example:**
```
Retrieved (top-3):
1. Address Update Policy (relevant) ✓
2. General FAQ (not relevant) ✗
3. Address Change Form (relevant) ✓

Precision: 0.67 (2 relevant / 3 total, but #2 is noise)
```

#### 4. Context Recall (Coverage)
**Question:** Are all facts from ground truth present in retrieved context?

**Measurement:**
- Decomposes ground truth into statements
- Checks if each statement can be found in retrieved context
- Score = (found statements) / (total statements)

**Example:**
```
Ground Truth: "Need ID verification and proof of address. Takes 3-5 days."
Retrieved Context: "ID verification required. Processing time 3-5 days."
Recall: 0.67 (missing "proof of address")
```

### Target Scores

**Prototype Targets (Resume-Worthy):**
- **Composite Score**: 0.75+ (good)
- **Faithfulness**: 0.80+ (high priority - no hallucinations)
- **Answer Relevancy**: 0.75+ (answers match questions)
- **Context Precision**: 0.70+ (good retrieval ranking)
- **Context Recall**: 0.90+ (comprehensive context)

**Production Targets (Stretch Goals):**
- **Composite Score**: 0.85+
- **Faithfulness**: 0.90+
- **Answer Relevancy**: 0.85+
- **Context Precision**: 0.80+
- **Context Recall**: 0.95+

---

## Implementation Phases

### Phase 1: Foundation (Day 1 - February 13)

**Goal:** Set up infrastructure and create knowledge base

**Tasks:**
1. ✓ Create design document (this file)
2. ✓ Set up directory structure
3. ✓ Write 50+ banking policy documents
   - 6 main policies (one per intent)
   - 4 FAQ documents
   - Metadata configuration
4. ✓ Create test dataset (50 Q&A pairs with ground truth)
5. ✓ Install dependencies
   ```bash
   pip install faiss-cpu openai langchain ragas datasets
   ```

**Deliverables:**
- `docs/RAG_DESIGN.md`
- `knowledge_base/` with 10+ documents
- `evaluation/test_dataset.json` with 50 test cases
- Updated `requirements.txt`

---

### Phase 2: Vector Store (Day 2 - February 14)

**Goal:** Implement document loading, embedding, and vector store

**Tasks:**
1. ✓ Implement `DocumentLoader`
   - Markdown parsing
   - Chunking with overlap
   - Metadata extraction
2. ✓ Implement `EmbeddingService`
   - OpenAI integration
   - Caching
   - Batch processing
3. ✓ Implement `FAISSVectorStore`
   - Index creation
   - Document storage
   - Similarity search
4. ✓ Build initial index
   ```bash
   python scripts/build_index.py
   ```
5. ✓ Test retrieval in isolation
   ```bash
   python scripts/test_retrieval.py "How do I update my address?"
   ```

**Deliverables:**
- `omni_channel_ai_servicing/infrastructure/retrieval/` (4 files)
- `faiss_index/` with populated index
- Unit tests for retrieval components

---

### Phase 3: LangGraph Integration (Day 2-3)

**Goal:** Integrate retrieval into existing workflow

**Tasks:**
1. ✓ Create `retrieve_context` node
2. ✓ Update workflow graph (add edge)
3. ✓ Update `generate_response` prompt (context injection)
4. ✓ Update `State` type (add context fields)
5. ✓ Test end-to-end RAG workflow
   ```bash
   python app.py
   # Test: "How do I update my address?"
   ```

**Deliverables:**
- `omni_channel_ai_servicing/graph/nodes/retrieve_context.py`
- Updated `generate_response.py` with context prompt
- Integration tests

---

### Phase 4: RAGAS Evaluation (Day 3 - February 15)

**Goal:** Run evaluation and achieve target scores

**Tasks:**
1. ✓ Implement `RAGASEvaluator`
2. ✓ Run baseline evaluation
   ```bash
   python evaluation/ragas_evaluation.py
   ```
3. ✓ Analyze results (identify weak areas)
4. ✓ Iterate on retrieval/prompts
   - Adjust chunk size
   - Tune re-ranking weights
   - Refine prompts
5. ✓ Re-run evaluation until scores meet targets
6. ✓ Document final metrics

**Deliverables:**
- `evaluation/ragas_evaluation.py`
- `evaluation/results/` with score reports
- Updated README with metrics

---

### Phase 5: Testing & Documentation (Weekend - February 16-17)

**Goal:** Comprehensive testing and portfolio polish

**Tasks:**
1. ✓ Unit tests (retrieval components)
   - `test_document_loader.py`
   - `test_embedding_service.py`
   - `test_vector_store.py`
   - `test_retriever.py`
2. ✓ Integration tests (RAG workflow)
   - `test_rag_workflow.py`
   - `test_context_retrieval.py`
3. ✓ Performance benchmarking
   - Retrieval latency
   - End-to-end response time
4. ✓ Update documentation
   - README with RAG section
   - API docs
   - Architecture diagrams
5. ✓ Add metrics to MetricsCollector
   - `retrieval.latency`
   - `retrieval.docs_retrieved`
   - `retrieval.no_results`

**Deliverables:**
- 30+ new unit/integration tests
- Performance benchmark report
- Updated README and docs
- Metrics dashboard

---

## Performance Targets

### Latency Requirements

| Component | Target | Acceptable | Notes |
|-----------|--------|------------|-------|
| Embedding Generation | <100ms | <200ms | Single query (1536-dim) |
| Vector Search (FAISS) | <10ms | <20ms | Similarity search top-5 |
| Document Formatting | <5ms | <10ms | String concatenation |
| **Total Retrieval** | **<200ms** | **<300ms** | End-to-end retrieve_context |
| LLM Generation (GPT-4) | 1-3s | 1-5s | Depends on response length |
| **End-to-End Response** | **<4s** | **<6s** | Full RAG workflow |

### Accuracy Targets

| Metric | Target | Acceptable | Measurement |
|--------|--------|------------|-------------|
| RAGAS Faithfulness | >0.80 | >0.75 | Answer grounded in context |
| RAGAS Relevancy | >0.75 | >0.70 | Answer addresses question |
| RAGAS Precision | >0.70 | >0.65 | Relevant docs ranked high |
| RAGAS Recall | >0.90 | >0.85 | Ground truth in context |
| **Composite Score** | **>0.78** | **>0.73** | Average of 4 metrics |

### Resource Targets

| Resource | Target | Notes |
|----------|--------|-------|
| FAISS Index Size | <100MB | ~150 chunks × 1536-dim × 4 bytes |
| Memory Usage | <512MB | Index + Python runtime |
| Embedding API Cost | <$0.50 | ~25K tokens for initial indexing |
| LLM API Cost | <$0.10/query | GPT-4 with RAG context |

---

## Testing Strategy

### Unit Tests

**Document Loader Tests:**
```python
# tests/unit/test_document_loader.py

def test_load_document():
    """Test loading single markdown document."""
    pass

def test_chunk_document():
    """Test document chunking with overlap."""
    pass

def test_extract_metadata():
    """Test metadata extraction from frontmatter."""
    pass

def test_chunk_size_limits():
    """Test chunks respect size limits."""
    pass
```

**Embedding Service Tests:**
```python
# tests/unit/test_embedding_service.py

def test_embed_single_text():
    """Test embedding generation for single text."""
    pass

def test_embed_batch():
    """Test batch embedding generation."""
    pass

def test_caching():
    """Test embedding cache hits."""
    pass

def test_retry_on_failure():
    """Test retry logic on API failure."""
    pass
```

**Vector Store Tests:**
```python
# tests/unit/test_vector_store.py

def test_add_documents():
    """Test adding documents to index."""
    pass

def test_search():
    """Test similarity search."""
    pass

def test_metadata_filtering():
    """Test search with metadata filters."""
    pass

def test_persistence():
    """Test save/load index."""
    pass
```

**Retriever Tests:**
```python
# tests/unit/test_retriever.py

def test_retrieve_with_intent_filter():
    """Test retrieval with intent filtering."""
    pass

def test_reranking():
    """Test re-ranking by relevance."""
    pass

def test_context_formatting():
    """Test context formatting for prompts."""
    pass

def test_no_results_handling():
    """Test behavior when no documents match."""
    pass
```

### Integration Tests

```python
# tests/integration/test_rag_workflow.py

async def test_end_to_end_rag_workflow():
    """Test full RAG workflow from query to response."""
    pass

async def test_context_injection():
    """Test retrieved context appears in LLM prompt."""
    pass

async def test_fallback_no_context():
    """Test graceful fallback when retrieval fails."""
    pass

async def test_intent_specific_retrieval():
    """Test retrieval filters by intent correctly."""
    pass
```

### RAGAS Evaluation Tests

```python
# tests/integration/test_ragas_evaluation.py

async def test_ragas_evaluation_runs():
    """Test RAGAS evaluation completes successfully."""
    pass

async def test_per_intent_breakdown():
    """Test per-intent score aggregation."""
    pass

async def test_faithfulness_scoring():
    """Test faithfulness metric calculation."""
    pass
```

---

## Design Principles

### 1. Backward Compatibility
- **RAG is optional**: System works without retrieval
- **Graceful degradation**: Fallback to non-RAG prompt if retrieval fails
- **No breaking changes**: Existing API contracts unchanged

### 2. Metadata-Driven Architecture
- **Intent tags**: Documents tagged with relevant intents
- **Policy versions**: Track document versions for auditing
- **Source citations**: Preserve document provenance

### 3. Performance-First
- **Local FAISS**: No cloud round-trips, sub-10ms search
- **Async retrieval**: Non-blocking operations
- **Efficient chunking**: Balance context vs. speed (top-k=3)

### 4. Observability
- **Metrics**: Retrieval latency, docs retrieved, relevance scores
- **Tracing**: Track which documents used per response
- **RAGAS scores**: Continuous evaluation per intent type

### 5. Testability
- **Mock retriever**: Unit tests don't need real index
- **Test dataset**: Regression testing with 50+ Q&A pairs
- **Offline evaluation**: RAGAS runs without production traffic

---

## File Structure (Post-Implementation)

```
omni-channel-ai-servicing/
├── docs/
│   └── RAG_DESIGN.md                          # This document
├── knowledge_base/                             # NEW - Knowledge base
│   ├── policies/
│   │   ├── address_update_policy.md
│   │   ├── dispute_handling_policy.md
│   │   ├── payment_policy.md
│   │   ├── fraud_reporting_policy.md
│   │   ├── card_services_policy.md
│   │   └── account_inquiry_policy.md
│   ├── faqs/
│   │   ├── address_faqs.md
│   │   ├── dispute_faqs.md
│   │   ├── payment_faqs.md
│   │   └── general_faqs.md
│   └── metadata.json
├── omni_channel_ai_servicing/
│   ├── infrastructure/
│   │   └── retrieval/                         # NEW - Retrieval service
│   │       ├── __init__.py
│   │       ├── vector_store.py                # FAISS wrapper
│   │       ├── embedding_service.py           # OpenAI embeddings
│   │       ├── retriever.py                   # High-level retrieval
│   │       └── document_loader.py             # Document loading/chunking
│   └── graph/
│       └── nodes/
│           └── retrieve_context.py            # NEW - Retrieval node
├── evaluation/                                 # NEW - RAGAS evaluation
│   ├── test_dataset.json                      # 50+ Q&A test cases
│   ├── ragas_evaluation.py                    # Evaluation pipeline
│   └── results/
│       ├── baseline_scores.json
│       └── final_scores.json
├── faiss_index/                               # NEW - Vector index (gitignored)
│   ├── index.faiss
│   ├── docstore.json
│   └── index_metadata.json
├── scripts/                                    # NEW - Utility scripts
│   ├── build_index.py                         # Build FAISS index
│   ├── test_retrieval.py                      # Test retrieval
│   └── run_evaluation.py                      # Run RAGAS evaluation
└── tests/
    ├── unit/
    │   ├── test_document_loader.py            # NEW
    │   ├── test_embedding_service.py          # NEW
    │   ├── test_vector_store.py               # NEW
    │   └── test_retriever.py                  # NEW
    └── integration/
        ├── test_rag_workflow.py               # NEW
        └── test_ragas_evaluation.py           # NEW
```

---

## Dependencies

### New Requirements

```txt
# Vector Store
faiss-cpu==1.7.4              # FAISS for vector similarity search

# Embeddings (already have openai)
tiktoken==0.5.2               # Token counting for OpenAI

# Evaluation
ragas==0.1.7                  # RAG evaluation framework
datasets==2.16.1              # RAGAS dataset format

# Document Processing
markdown==3.5.1               # Markdown parsing
python-frontmatter==1.0.0     # Metadata extraction

# Utilities
tenacity==8.2.3               # Retry logic (might already have)
```

### Cost Estimation

**Initial Setup (One-Time):**
- Embedding 10 documents (~25K tokens): $0.50
- RAGAS evaluation (50 tests × 3 LLM calls): $5.00
- **Total**: ~$5.50

**Per Query (Production):**
- Query embedding (1K tokens): $0.00002
- LLM generation with context (2K tokens): $0.06
- **Total**: ~$0.06 per query

---

## Success Criteria

### Must-Have (Minimum Viable)
- ✓ FAISS index built with 50+ document chunks
- ✓ Retrieval working end-to-end (<500ms)
- ✓ Context injected into LLM prompts
- ✓ RAGAS composite score >0.73
- ✓ 30+ unit/integration tests passing

### Should-Have (Target)
- ✓ RAGAS composite score >0.78
- ✓ Per-intent score breakdown
- ✓ Retrieval latency <200ms
- ✓ Source citations in responses
- ✓ Comprehensive documentation

### Nice-to-Have (Stretch)
- ✓ RAGAS composite score >0.85
- ✓ Simple web UI showing retrieved docs
- ✓ A/B test framework (RAG vs. no-RAG)
- ✓ Automated index updates on doc changes

---

## Interview Talking Points

### Architecture Decision
> "I chose FAISS for the vector store because it's production-ready (Meta's library), has sub-10ms search latency, and runs locally without cloud dependencies. This keeps the prototype fast and cost-effective while maintaining patterns that scale to production."

### Evaluation Strategy
> "I used the RAGAS framework to evaluate RAG quality across four dimensions: faithfulness ensures no hallucinations, answer relevancy checks we're addressing the question, and precision/recall measure retrieval quality. I achieved 0.78+ composite score on 50 banking Q&A pairs."

### Prompt Engineering
> "I engineered the prompt to explicitly constrain the LLM to ONLY use retrieved context, require source citations, and provide a graceful fallback when context is insufficient. This reduces hallucinations and makes responses auditable."

### Production Thinking
> "Even in a prototype, I built with production patterns: metadata-driven document tagging, async retrieval for non-blocking operations, comprehensive metrics (latency, retrieval success rate), and backward compatibility so the system works with or without RAG."

---

## Next Steps After Implementation

### Immediate Enhancements
1. **Add more documents**: Expand knowledge base to 50+ policies
2. **Improve chunking**: Experiment with semantic splitting
3. **Add reranking model**: Use cross-encoder for better precision
4. **Cache embeddings**: Reduce API calls for repeated queries

### Medium-Term Features
1. **Human-in-the-Loop (HITL)**: Review low-confidence retrievals
2. **Feedback loop**: Track which responses get escalated
3. **A/B testing**: Compare RAG vs. non-RAG performance
4. **Query expansion**: Use LLM to enhance user queries

### Long-Term Vision
1. **Multi-modal RAG**: Add images (forms, diagrams)
2. **Agentic retrieval**: Let agent decide when to retrieve
3. **Distributed store**: Move to Pinecone/Weaviate for scale
4. **Fine-tuned embeddings**: Train custom embedding model

---

## Appendix: Alternative Approaches Considered

### Why Not Chroma?
- **Pro**: Good developer experience, built-in metadata filtering
- **Con**: Heavier than FAISS, more dependencies, slower for <10k docs
- **Decision**: FAISS sufficient for prototype scale

### Why Not Semantic Chunking (LangChain)?
- **Pro**: Better semantic boundaries
- **Con**: Slower, more complex, overkill for structured policies
- **Decision**: Fixed-size with overlap is simpler and effective

### Why Not Hybrid Search (BM25 + Vector)?
- **Pro**: Better for keyword-heavy queries
- **Con**: Added complexity, marginal gains for policy documents
- **Decision**: Pure vector search sufficient, can add BM25 later

### Why Not Fine-Tuned Embeddings?
- **Pro**: Domain-specific embeddings might improve retrieval
- **Con**: Requires training data, time investment, unclear ROI
- **Decision**: Use OpenAI embeddings (proven quality), fine-tune later if needed

---

**End of Design Document**

This design provides a comprehensive blueprint for RAG implementation. Ready to proceed with Phase 1 (knowledge base creation)?
