---
title: AI Banking Assistant Demo
emoji: 🏦
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.31.0
app_file: streamlit_app.py
pinned: false
license: mit
---

# AI Banking Assistant Demo

Real-time RAG-powered customer service platform for banking.

## Features

- 🧠 **Intent Classification**: Automatically routes queries to specialized workflows
- 📖 **Knowledge Base Retrieval**: 523 chunks from 24 policy documents
- 🔄 **Specialized Workflows**: Address updates, disputes, fraud reporting, etc.
- 📊 **Real-time Policy Enforcement**: Business rules applied automatically
- ✅ **RAGAS-Validated**: 0.68 faithfulness, 0.70 answer relevancy

## Tech Stack

- **LangGraph**: State machine workflows
- **FAISS**: Vector similarity search
- **OpenAI**: Embeddings (text-embedding-3-small) + Generation (GPT-4o-mini)
- **Streamlit**: Interactive UI
- **FastAPI**: Backend API

## Performance

- **Retrieval**: 208ms average
- **End-to-End**: 2.1s total
- **Cost**: $0.16 per 1,000 queries

## How It Works

1. User asks a banking question
2. System classifies intent (address update, dispute, fraud, etc.)
3. Retrieves relevant policy documents from vector store
4. Executes specialized workflow with business rules
5. Generates natural language response with citations

## Try It Out

Ask questions like:
- "How do I update my mailing address?"
- "I want to dispute a charge on my account"
- "Someone used my card without permission"
- "What are your hours of operation?"

## Development

Built as a portfolio project demonstrating enterprise RAG implementation for Vertex AI role.

**GitHub**: [Repository Link]
**Portfolio**: [PORTFOLIO_README.md](./PORTFOLIO_README.md)
