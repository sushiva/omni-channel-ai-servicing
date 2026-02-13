# 🎯 Quick Demo Reference Card

## ✅ System Status
- **Backend API**: Running on port 8000 (PID: 18816)
- **Streamlit UI**: Running on port 8501 (PID: 19184)
- **Knowledge Base**: 523 chunks indexed in FAISS
- **RAG Performance**: 0.68 faithfulness, 0.70 relevancy

---

## 🌐 Access URLs
```
Streamlit UI:  http://localhost:8501
Backend API:   http://localhost:8000
API Docs:      http://localhost:8000/docs
Health Check:  http://localhost:8000/health
```

---

## 📧 Email Simulation Demo

### Support Email Address
```
support@demobank.ai
```

### Step-by-Step Demo
1. Open http://localhost:8501
2. Click "📧 Email Simulation" tab
3. Use pre-filled email or customize:
   - From: `jane.doe@example.com`
   - Subject: `Address Update Request`
   - Body: Include new address
   - Check: ✅ drivers_license.pdf, ✅ utility_bill.pdf
4. Click "📤 Send Email"
5. Watch real-time processing:
   - Intent classification
   - Entity extraction (address components)
   - RAG retrieval (3 documents)
   - Personalized response generation
6. See response in inbox

### Expected Output
```
Intent: address_update
Workflow: address_workflow
Retrieved Docs: 3
Entities Extracted: street, city, state, zip_code
Response: Confirms documents meet requirements
Processing Time: 2-4 seconds
```

---

## 💬 Chat Demo Queries

### ✅ Query 1: Address Update (Shows RAG)
```
How do I update my mailing address?
```
**Expected**: 3 docs retrieved, specific requirements listed

### ✅ Query 2: Fraud Report (Shows RAG)
```
Someone used my card without permission
```
**Expected**: Fraud policy docs, immediate action steps

### ✅ Query 3: Card Activation (Shows RAG)
```
How do I activate my new credit card?
```
**Expected**: Activation procedure from knowledge base

### ✅ Query 4: Greeting (Shows Fallback)
```
Hello
```
**Expected**: 0 docs retrieved, friendly greeting

---

## 🎤 Key Interview Points

### 30-Second Pitch
> "I built an enterprise-grade RAG system for banking customer service using LangGraph for workflow orchestration and FAISS for vector search. The system achieves 68% faithfulness on RAGAS evaluation and supports multi-channel interactions including a novel email simulation. It demonstrates intent classification, entity extraction, and human-in-the-loop design for sensitive operations."

### Technical Highlights
- **Architecture**: Clean hexagonal/ports-and-adapters
- **RAG**: FAISS with 523 chunks, OpenAI embeddings (1536-dim)
- **Workflows**: LangGraph state machines with 8+ nodes
- **Validation**: RAGAS metrics (faithfulness 0.68, relevancy 0.70)
- **Scalability**: Async/await, singleton patterns, ready for Redis/K8s

### Innovation: Email Channel
> "The email simulation shows omni-channel capability - same backend handles web chat and email. System extracts entities, retrieves policies, and generates context-aware responses. Designed with human-in-loop for document verification - AI triages, humans verify."

### Real-World Readiness
- ✅ Intent-based routing to specialized workflows
- ✅ Policy enforcement via RAG retrieval
- ✅ Entity extraction for structured data
- ✅ Error handling and fallback workflows
- ✅ Observability (trace IDs, logging)
- ✅ Type safety (Pydantic models throughout)

---

## 🐛 Quick Troubleshooting

### Backend Down
```bash
cd /home/bhargav/interview-Pocs/omni-channel-ai-servicing
source .venv/bin/activate
python -m uvicorn omni_channel_ai_servicing.app.main:app --host 0.0.0.0 --port 8000
```

### Streamlit Down
```bash
cd /home/bhargav/interview-Pocs/omni-channel-ai-servicing
source .venv/bin/activate
streamlit run streamlit_app.py --server.port 8501
```

### No RAG Results
- Symptom: "Retrieved Docs: 0"
- Solution: Use specific queries like "How do I update my address?"
- Avoid: Very short queries or greetings

---

## 📊 Demo Checklist

### Before Demo
- [ ] Backend running on port 8000
- [ ] Streamlit running on port 8501
- [ ] Both services responding (curl health check)
- [ ] Have DEMO_GUIDE.md open for reference

### During Demo - Chat
- [ ] Show clean UI
- [ ] Ask: "How do I update my mailing address?"
- [ ] Point out: Intent, Retrieved Docs (3), Processing Time
- [ ] Highlight: Specific policy details in response
- [ ] Show: "_Answer based on 3 relevant policy document(s)_"

### During Demo - Email
- [ ] Switch to "📧 Email Simulation" tab
- [ ] Show: Pre-filled email with address + attachments
- [ ] Click: "Send Email"
- [ ] Point out: Real-time processing, entity extraction
- [ ] Highlight: Response confirms documents meet requirements
- [ ] Explain: Human-in-loop design for production

### Wrap-Up Points
- [ ] Mention: 523-chunk knowledge base
- [ ] Mention: RAGAS validation (0.68/0.70)
- [ ] Mention: Clean architecture (hexagonal)
- [ ] Mention: Production-ready patterns
- [ ] Mention: Scalability considerations

---

## 🎬 1-Minute Speed Demo

1. **Open** → http://localhost:8501
2. **Say**: "This is a RAG-powered banking assistant with 523 policy documents"
3. **Ask**: "How do I update my mailing address?"
4. **Show**: 3 docs retrieved in 2-3 seconds
5. **Switch**: Email Simulation tab
6. **Send**: Pre-filled address update email
7. **Highlight**: System confirms documents meet requirements
8. **Explain**: "Production would add human verification step"
9. **Close**: "Built on LangGraph, FAISS, achieving 68% faithfulness"

---

## 📁 Key Files for Reference

- `DEMO_GUIDE.md` - Full user guide
- `README.md` - Project overview
- `RAGAS_EVALUATION.md` - Evaluation metrics
- `ROUTER_IMPLEMENTATION.md` - Architecture details
- `streamlit_app.py` - UI code
- `omni_channel_ai_servicing/` - Core implementation

---

**Status**: ✅ Demo Ready
**Last Updated**: 2026-02-13 11:55
**Backend PID**: 18816
**Streamlit PID**: 19184
