# 🏦 Omni-Channel AI Banking Demo - User Guide

## 🚀 Quick Start

### Access the Demo
- **Streamlit UI**: http://localhost:8501
- **API Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 📧 Email Simulation Feature

### How It Works
The demo includes a realistic email simulation showing how customers can interact with your support system via email.

### Email Address
**Support Email**: `support@demobank.ai`

### Try It Out

1. **Go to the "📧 Email Simulation" Tab**

2. **Compose Your Email**:
   - From: `customer@example.com` (or any email)
   - Subject: `Address Update Request`
   - Attachments: Check the boxes for ID and utility bill

3. **Sample Email Body**:
   ```
   Hi,
   
   I recently moved and need to update my mailing address.
   
   My new address is:
   456 Oak Avenue, Apt 2B
   Austin, TX 78701
   
   I have attached my driver's license and a recent utility bill.
   
   Thank you,
   Jane Doe
   ```

4. **Click "📤 Send Email"**

5. **See the Magic**:
   - ✅ System processes the email in real-time
   - 🧠 Extracts address details automatically
   - 📚 Retrieves relevant policy documentation (3 docs)
   - 💬 Generates personalized response confirming documents
   - ⏱️ Shows processing time (~2-5 seconds)

---

## 💬 Chat Interface

### Example Queries to Try

1. **Address Update** (RAG-enabled):
   ```
   How do I update my mailing address?
   ```
   Expected: Retrieves 3 policy documents, explains document requirements

2. **Fraud Report** (RAG-enabled):
   ```
   Someone used my card without permission
   ```
   Expected: Retrieves fraud policies, provides immediate steps

3. **Card Activation** (RAG-enabled):
   ```
   How do I activate my new credit card?
   ```
   Expected: Retrieves activation procedures

4. **General Greeting** (Fallback):
   ```
   Hello
   ```
   Expected: Friendly greeting without RAG retrieval

---

## 🎯 Key Features Demonstrated

### 1. Intent Classification
- Automatically detects customer intent from natural language
- Maps to specialized workflows (address_update, fraud_report, etc.)

### 2. RAG (Retrieval Augmented Generation)
- **Knowledge Base**: 523 document chunks indexed in FAISS
- **Retrieval**: Top-3 most relevant documents per query
- **Accuracy**: RAGAS-validated (0.68 faithfulness, 0.70 relevancy)

### 3. Entity Extraction
- Extracts structured data from unstructured text
- Example: "123 Main St, Austin, TX 78701" → 
  - street: "123 Main St"
  - city: "Austin"
  - state: "TX"
  - zip_code: "78701"

### 4. Multi-Channel Support
- Web, Chat, Mobile, **Email**
- Same backend, different input methods

### 5. Document Verification Flow
- Customer mentions attached documents
- System validates against policy requirements
- Confirms documentation meets standards
- (In production: would create case for human verification)

---

## 🔍 What to Look For

### Response Quality Indicators
- ✅ **"_(Answer based on X relevant policy document(s))_"** - RAG working
- ✅ **Retrieved Docs: 3** - Successfully found relevant content
- ✅ **Processing Time: 2-4s** - Reasonable performance
- ✅ **Specific policy details** - Not generic, uses actual knowledge

### Workflow Execution
- **Intent**: Should match your query type
- **Workflow**: address_workflow, fraud_workflow, etc.
- **Status**: Shows workflow completion
- **Context**: Displays retrieved documents with sources

---

## 🎤 Interview Talking Points

### Technical Architecture
> "This demo showcases an **enterprise-grade RAG system** built with LangGraph for orchestration, FAISS for vector search, and OpenAI for embeddings and generation. The system demonstrates **intent-driven routing**, **knowledge retrieval with 0.68 faithfulness**, and **multi-channel support** - all running on a clean hexagonal architecture."

### Email Channel Innovation
> "The email simulation demonstrates **omni-channel capability** - the same backend workflow processes web chats and email requests. When a customer emails about address updates, the system **extracts entities**, **retrieves relevant policies**, and provides **context-aware responses**. In production, this would integrate with actual IMAP/SMTP for real email processing."

### Human-in-the-Loop Design
> "Notice the system **acknowledges documents but doesn't auto-approve** - this is intentional. For sensitive operations like address changes, the AI **triages and validates against policy**, but a human agent would verify the actual document images. This demonstrates **responsible AI design** where automation augments rather than replaces human judgment."

### RAG Performance
> "The knowledge base contains **523 chunks** across 10 documents. RAGAS evaluation shows **68% faithfulness** and **70% answer relevancy** - production-grade metrics. The system retrieves **top-3 documents per query** using cosine similarity, with intent-based filtering for precision."

### Scalability
> "Built on **LangGraph's state machine architecture** with async/await throughout. The FAISS index loads once as a singleton, supporting concurrent requests. In production, this would scale horizontally with Redis for state management and Kubernetes for orchestration."

---

## 🐛 Troubleshooting

### Backend Not Responding
```bash
# Check if backend is running
curl http://localhost:8000/health

# Restart if needed
cd /home/bhargav/interview-Pocs/omni-channel-ai-servicing
source .venv/bin/activate
python -m uvicorn omni_channel_ai_servicing.app.main:app --host 0.0.0.0 --port 8000
```

### Streamlit Not Loading
```bash
# Restart Streamlit
cd /home/bhargav/interview-Pocs/omni-channel-ai-servicing
source .venv/bin/activate
streamlit run streamlit_app.py --server.port 8501
```

### No Documents Retrieved
- Symptom: "Retrieved Docs: 0"
- Cause: Usually short queries or greetings
- Solution: Ask specific policy questions like "How do I update my address?"

---

## 📊 Success Metrics

### What "Good" Looks Like
- ✅ Intent classification: 95%+ accuracy (address_update for address queries)
- ✅ Document retrieval: 2-3 relevant documents per query
- ✅ Response time: 2-5 seconds end-to-end
- ✅ Response quality: Specific policy details, not generic
- ✅ Entity extraction: All address components captured

### Current Performance
- **RAGAS Faithfulness**: 0.68 (68% - answer grounded in context)
- **RAGAS Relevancy**: 0.70 (70% - retrieved docs relevant to query)
- **Knowledge Base**: 523 chunks, 1536-dim embeddings
- **Response Time**: ~3s average

---

## 🎬 Demo Script

### 1-Minute Demo Flow
1. **Open Streamlit** → Show clean interface
2. **Ask**: "How do I update my mailing address?"
3. **Point out**:
   - Intent: address_update ✓
   - Retrieved Docs: 3 ✓
   - Specific requirements listed
4. **Switch to Email tab**
5. **Show**: Pre-filled email with address + attachments
6. **Send**: Click "Send Email"
7. **Highlight**: System confirms documents meet requirements
8. **Explain**: "In production, this creates a case for human verification"

---

## 🔐 Important Notes

- **Demo Mode**: No real transactions, no real email sending
- **API Key**: Uses OpenAI API (requires valid key in .env)
- **Data**: All policy documents are sample/mock data
- **Human-in-Loop**: Designed for human oversight on sensitive operations

---

## 📚 Additional Resources

- **Architecture**: See `ROUTER_IMPLEMENTATION.md`
- **RAG Evaluation**: See `RAGAS_EVALUATION.md`
- **API Docs**: http://localhost:8000/docs
- **Code Structure**: Clean hexagonal architecture in `omni_channel_ai_servicing/`

---

**Built with**: LangGraph • FAISS • OpenAI • Streamlit • FastAPI

**Purpose**: Interview demo showcasing production-ready RAG system design
