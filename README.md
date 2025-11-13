<<<<<<< HEAD
# Badminton Agent

A full-stack solution for badminton-court booking & agent routing.

## Quick start
```bash
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && streamlit run streamlit_app.py
```
=======
# badmintion_stringing
>>>>>>> 74ce242e420197210ffef3ba1652a6104a026ce5



# 🏸 Badminton Racket Stringing RAG System

## Overview

A **Graph-RAG powered** intelligent customer support system for badminton racket stringing services. Built with **Neo4j**, **FastAPI**, **Streamlit**, and **Groq LLM** to provide context-aware responses based on historical customer queries and issues.

---

## 🎯 Key Features

### ✨ Graph-based RAG (Retrieval-Augmented Generation)
- **Neo4j Knowledge Graph**: Stores relationships between brands, issues, customers, and queries
- **Smart Context Retrieval**: Fetches relevant historical data for LLM enhancement
- **Multi-hop Reasoning**: Traverses Brand→Issue→Timeframe relationships
- **Incremental Learning**: System improves with every query automatically

### 🤖 AI-Powered Chat Support
- **Groq LLM Integration**: Fast responses using llama-3.3-70b-versatile
- **Contextual Answers**: Leverages historical patterns from Neo4j
- **Entity Extraction**: Detects brands, issues, timeframes from natural language
- **Frequency Tracking**: Identifies common problems across brands

### 📊 Analytics & Visualization
- Customer order tracking
- Brand issue frequency analysis
- Query pattern recognition
- Temporal pattern detection

***

## 🏗️ Architecture

``````
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (Streamlit)                │
│  - Chat Interface  - Customer Module  - Analytics Dashboard │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               LLM Agent (Groq API Client)                    │
│  - Query processing  - Context injection  - Response gen.   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│             Orchestrator (RAG Controller)                    │
│  - Entity extraction  - Context retrieval  - Graph updates  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Neo4j Knowledge Graph                           │
│  Nodes: Brand, Issue, QueryPattern, Timeframe, Order        │
│  Edges: HAS_ISSUE, ASKS_ABOUT, MENTIONS, OCCURS_WITHIN     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Neo4j Aura (or local Neo4j instance)
- Groq API Key

### Installation

``````bash
# Clone repository
git clone <your-repo-url>
cd badminton-stringing-rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create `.env` file in project root:

```env```
# Neo4j Configuration
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASS=your-password

# Groq API
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=llama-3.3-70b-versatile

# Backend
BACKEND_URL=http://127.0.0.1:8000
```

### Run Application

``````bash
# Terminal 1: Start FastAPI Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Start Streamlit Frontend
streamlit run frontend/streamlit_app.py
```

Access:
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

***

## 📂 Project Structure

``````
badminton-stringing-rag/
├── backend/
│   ├── routes/
│   │   ├── orchestrator.py      # RAG core logic
│   │   ├── orders.py             # Order management
│   │   └── agents.py             # Agent assignment
│   ├── services/
│   │   ├── neo4j_client.py       # Neo4j operations
│   │   ├── ml_predictor.py       # ETA prediction
│   │   └── geocode_client.py     # Address geocoding
│   └── main.py                   # FastAPI app
├── frontend/
│   ├── components/
│   │   ├── llm_agent.py          # Groq LLM client
│   │   ├── chat_interface.py     # Chat UI
│   │   └── customer_module.py    # Customer management
│   └── streamlit_app.py          # Main UI
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## 🧠 How RAG Works

### 1. Query Processing
``````python
User: "Why does Yonex string break?"
↓
Extract Entities: {brand: "Yonex", issue: "string_breakage"}
```

### 2. Knowledge Retrieval
```cy```
MATCH (b:Brand {name: "Yonex"})-[r:HAS_ISSUE]->(i:Issue)
RETURN i.type, r.frequency, r.last_reported
```

### 3. Context Injection
``````
System Prompt: "You are a stringing expert.
Historical Data: Yonex has 5 reports of string_breakage...
Use this to inform your answer."
```

### 4. Enhanced Response
``````
AI: "Based on previous reports, Yonex string breakage 
has been reported 5 times. Common causes include..."
```

---

## 🗄️ Neo4j Graph Schema

### Node Types
- **QueryPattern**: User questions and patterns
- **Brand**: Racket manufacturers (Yonex, Li-ning, Victor, etc.)
- **Issue**: Problem types (string_breakage, tension_loss, etc.)
- **Timeframe**: Temporal patterns (3 days, 2 weeks, etc.)
- **Order**: Customer orders
- **Customer**: Users

### Relationships
- `(QueryPattern)-[ASKS_ABOUT]->(Issue)`
- `(QueryPattern)-[MENTIONS]->(Brand)`
- `(Brand)-[HAS_ISSUE {frequency}]->(Issue)`
- `(Issue)-[OCCURS_WITHIN]->(Timeframe)`
- `(Customer)-[PLACED]->(Order)`
- `(Order)-[RELATES_TO]->(Racket)`

---

## 🔧 API Endpoints

### Orchestrator (RAG)
- `POST /orchestrator/agents/context` - Retrieve RAG context
- `POST /orchestrator/chat` - Process chat message
- `POST /orchestrator/assign_agent/{order_id}` - Assign agent

### Orders
- `POST /orders/create` - Create new order
- `GET /orders/customer/{customer_name}` - Get customer orders

### Debug
- `POST /orchestrator/debug/test-context` - Test context retrieval
- `GET /orchestrator/debug/graph-stats` - Get graph statistics

---

## 📊 Example Queries

### Neo4j Browser Queries

**View all brand issues:**
``````cypher
MATCH (b:Brand)-[r:HAS_ISSUE]->(i:Issue)
RETURN b.name as Brand, 
       i.type as Issue, 
       r.frequency as TimesReported
ORDER BY r.frequency DESC
```

**Visualize knowledge graph:**
```cypher```
MATCH path = (b:Brand)-[r:HAS_ISSUE]->(i:Issue)
RETURN path
LIMIT 50
```

**Check query patterns:**
``````cypher
MATCH (q:QueryPattern)-[:ASKS_ABOUT]->(i:Issue)
RETURN q.text as Query, 
       i.type as AboutIssue, 
       q.count as TimesAsked
ORDER BY q.count DESC
```

***

## 🎯 Usage Examples

### Chat Interface

**Query 1:**
``````
User: "Why does my Yonex string break after 3 days?"
AI: [First time - generic answer]
```

**Query 2:**
``````
User: "Yonex string problem again"
AI: "Based on previous reports, this issue has been 
reported 2 times with Yonex. Common timeframe is 3 days..."
[Uses RAG context!]
```

### Adding New Brands

Edit `backend/routes/orchestrator.py`:
```python```
brands = ['yonex', 'li-ning', 'victor', 'apacs', 'fleet', 
          'carlton', 'nivia']  # Add new brands here
```

---

## 🔍 System Capabilities

### Entity Detection
- **Brands**: Yonex, Li-ning, Victor, Apacs, Fleet, Carlton
- **Issues**: String breakage, tension loss, frame damage, buzzing
- **Timeframes**: Days, weeks, months, sessions
- **Query Types**: Issue inquiry, service info, recommendation, casual

### Relationship Building
- Automatically creates nodes for detected entities
- Builds relationships between related entities
- Tracks frequency of issue-brand combinations
- Records temporal patterns

### Context Retrieval
- Multi-hop graph traversal
- Frequency-based ranking
- Cross-brand pattern aggregation
- Similar query detection

---

## 📈 Performance

- **Query Processing**: ~50-200ms
- **Context Retrieval**: ~100ms (Neo4j)
- **LLM Response**: ~1-3s (Groq)
- **Total Latency**: ~1.5-3.5s per query

---

## 🛠️ Tech Stack

**Backend:**
- FastAPI - Web framework
- Neo4j - Graph database
- Groq API - LLM inference
- Python 3.9+ - Language

**Frontend:**
- Streamlit - UI framework
- Plotly - Visualizations
- Requests - HTTP client

**ML/AI:**
- Groq (llama-3.3-70b-versatile) - Language model
- Neo4j Graph Data Science - Pattern analysis

---

## 🚧 Future Enhancements

- [ ] Add NER model for automatic brand detection
- [ ] Implement solution tracking (Issue→Solution nodes)
- [ ] Add customer sentiment analysis
- [ ] Build recommendation engine
- [ ] Add multi-language support
- [ ] Implement vector embeddings for similarity search
- [ ] Add A/B testing framework
- [ ] Build admin dashboard

---

## 📝 License

MIT License - See LICENSE file for details

---

## 👨‍💻 Developer

Built by [Your Name] as a Graph-RAG demonstration project.

---

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

---

## 📞 Support

For issues or questions:
- Open a GitHub issue
- Contact: your-email@example.com

---

**Built with ❤️ using Neo4j, Groq, and Streamlit**