from fastapi import APIRouter, HTTPException, Body
from backend.services.neo4j_client import neo4j_client
import re
import json
from datetime import datetime


router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


# ==========================================
# 🔧 HELPER FUNCTIONS FOR RAG
# ==========================================


def extract_keywords(text: str) -> list:
    """Extract potential keywords from user query"""
    # Remove common words and extract meaningful terms
    stop_words = {'is', 'the', 'a', 'an', 'and', 'or', 'but', 'my', 'why', 'how', 'what', 'when', 'where'}
    words = re.findall(r'\b\w+\b', text.lower())
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords[:5]  # Return top 5 keywords


def extract_entities(text: str) -> dict:
    """Extract structured entities from user message (simple rule-based)"""
    entities = {
        "brand": None,
        "model": None,
        "issue_type": None,
        "timeframe": None,
        "query_type": "generic"  # ✅ ADD THIS LINE
    }
    
    # ✅ ADD THIS ENTIRE SECTION (Before brand detection)
    text_lower = text.lower()
    
    # Issue/Problem queries - SHOULD use RAG
    if any(word in text_lower for word in ['break', 'crack', 'damage', 'problem', 'issue', 'why', 'buzz', 'tension', 'frame']):
        entities["query_type"] = "issue_inquiry"
    
    # Service info queries - SHOULD NOT use RAG
    elif any(word in text_lower for word in ['cost', 'price', 'how much', 'how long', 'time', 'when', 'deliver', 'open', 'hours']):
        entities["query_type"] = "service_info"
    
    # Recommendation queries - SHOULD use RAG
    elif any(word in text_lower for word in ['which', 'best', 'recommend', 'should i', 'better', 'compare']):
        entities["query_type"] = "recommendation"
    
    # Greeting/casual - SHOULD NOT use RAG
    elif any(word in text_lower for word in ['hello', 'hi', 'thanks', 'thank you', 'bye']):
        entities["query_type"] = "casual"
    # ✅ END NEW SECTION
    
    # Common brands (KEEP EXISTING CODE)
    brands = ['yonex', 'li-ning', 'victor', 'apacs', 'fleet', 'carlton']
    for brand in brands:
        if brand in text.lower():
            entities["brand"] = brand.capitalize()
            break
    
    # Issue detection (KEEP EXISTING CODE)
    issues = {
        'string': 'string_damage',
        'break': 'string_breakage', 
        'buzz': 'string_buzzing',
        'tension': 'tension_loss',
        'frame': 'frame_damage',
        'crack': 'frame_crack'
    }
    for keyword, issue_type in issues.items():
        if keyword in text.lower():
            entities["issue_type"] = issue_type
            break
    
    # Timeframe extraction (KEEP EXISTING CODE)
    timeframe_patterns = [
        (r'(\d+)\s*day', 'days'),
        (r'(\d+)\s*week', 'weeks'),
        (r'(\d+)\s*month', 'months'),
        (r'(\d+)\s*session', 'sessions')
    ]
    for pattern, unit in timeframe_patterns:
        match = re.search(pattern, text.lower())
        if match:
            entities["timeframe"] = f"{match.group(1)} {unit}"
            break
    
    return entities


# ==========================================
# 🎯 RAG CONTEXT ENDPOINT
# ==========================================


@router.post("/agents/context")
async def get_rag_context(payload: dict = Body(...)):
    """
    Retrieve relevant context from Neo4j knowledge graph
    Based on user query for RAG-enhanced responses
    ✨ NOW WITH SMART CONTEXT FILTERING
    """
    user_query = payload.get("query", "")
    
    if not user_query:
        return {"context": "", "entities_detected": {}, "keywords": []}
    
    # Extract keywords and entities
    keywords = extract_keywords(user_query)
    entities = extract_entities(user_query)
    
    print(f"[DEBUG] 📥 Query: {user_query}")
    print(f"[DEBUG] 🔍 Entities: {entities}")
    print(f"[DEBUG] 🔑 Keywords: {keywords}")
    
    # ✅ NEW: Decide if we should use RAG context
    query_type = entities.get("query_type", "generic")
    use_rag = False
    
    # Use RAG for these types:
    if query_type in ["issue_inquiry", "recommendation"]:
        use_rag = True
        print(f"[DEBUG] ✅ Using RAG context (query type: {query_type})")
    
    # Also use RAG if brand or issue mentioned (even in other query types)
    elif entities.get("brand") or entities.get("issue_type"):
        use_rag = True
        print(f"[DEBUG] ✅ Using RAG context (brand/issue detected)")
    
    else:
        print(f"[DEBUG] ⏭️ Skipping RAG context (query type: {query_type})")
    
    context_string = ""
    
    try:
        if use_rag:
            # ✅ STEP 1: Store the query insight (for learning) - WITH RICH RELATIONSHIPS
            store_query_insight(user_query, entities)
            
            # ✅ STEP 2: Retrieve relevant context - WITH ENHANCED RELATIONSHIP TRAVERSAL
            context_string = get_relevant_context(entities)
            print(f"[DEBUG] 📚 Context retrieved: {context_string[:100]}..." if context_string else "[DEBUG] 📚 No context found")
            
            # ✅ STEP 3: Fallback - if no context from get_relevant_context, try legacy search
            context_results = []
            if not context_string:
                print("[DEBUG] No context from get_relevant_context, trying legacy search...")
                with neo4j_client.driver.session() as session:
                    
                    # Search for similar issues in past orders
                    if entities.get("issue_type"):
                        result = session.run("""
                            MATCH (o:Order)
                            WHERE toLower(o.issue) CONTAINS $issue_keyword
                            OPTIONAL MATCH (o)-[:RELATES_TO]->(r:Racket)
                            RETURN o.issue AS issue, 
                                   o.status AS status,
                                   r.brand AS brand,
                                   r.model AS model
                            LIMIT 3
                        """, issue_keyword=entities["issue_type"].replace('_', ' '))
                        
                        for record in result:
                            context_results.append(
                                f"Past case: {record['brand']} {record['model']} had {record['issue']} (Status: {record['status']})"
                            )
                    
                    # Search for brand-specific information
                    if entities.get("brand"):
                        result = session.run("""
                            MATCH (r:Racket {brand: $brand})
                            OPTIONAL MATCH (r)<-[:RELATES_TO]-(o:Order)
                            RETURN r.model AS model, 
                                   count(o) AS order_count,
                                   collect(DISTINCT o.issue)[..3] AS common_issues
                        """, brand=entities["brand"])
                        
                        for record in result:
                            if record['order_count'] > 0:
                                issues = ', '.join(record['common_issues'])
                                context_results.append(
                                    f"{entities['brand']} {record['model']}: {record['order_count']} orders, common issues: {issues}"
                                )
                
                # Combine legacy results if any
                if context_results:
                    context_string = "\n".join(context_results)
        else:
            # ✅ NEW: Don't store or retrieve for generic queries
            print(f"[INFO] 💤 RAG context disabled for this query type")
        
    except Exception as e:
        print(f"[ERROR] ❌ RAG context retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        context_string = ""
    
    return {
        "context": context_string,
        "entities_detected": entities,
        "keywords": keywords,
        "rag_used": use_rag  # ✅ NEW: Indicate if RAG was actually used
    }

# ==========================================
# 🧠 ENHANCED KNOWLEDGE STORAGE WITH RICH RELATIONSHIPS
# ==========================================


def store_query_insight(query: str, entities: dict):
    """
    ✨ ENHANCED: Store queries AND build rich relationship graph
    This makes your RAG knowledge graph grow smarter with each query!
    """
    print(f"[DEBUG] 🔥 store_query_insight CALLED (ENHANCED)")
    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] Entities: {entities}")
    
    try:
        with neo4j_client.driver.session() as session:
            
            # ✅ 1. Store the QueryPattern node
            session.run("""
                MERGE (q:QueryPattern {text: $query_text})
                ON CREATE SET q.count = 1, q.created_at = datetime()
                ON MATCH SET q.count = q.count + 1, q.last_asked = datetime()
            """, query_text=query[:200])
            print(f"[DEBUG] ✅ QueryPattern node created/updated")
            
            # ✅ 2. Create/Update Issue node
            if entities.get("issue_type"):
                session.run("""
                    MERGE (i:Issue {type: $issue_type})
                    ON CREATE SET i.first_seen = datetime(), i.frequency = 1
                    ON MATCH SET i.frequency = i.frequency + 1, i.last_seen = datetime()
                    SET i.sample_query = $query_text
                """, issue_type=entities["issue_type"], query_text=query)
                print(f"[DEBUG] ✅ Issue node created/updated: {entities['issue_type']}")
                
                # ✅ NEW: Link QueryPattern → Issue
                session.run("""
                    MATCH (q:QueryPattern {text: $query_text})
                    MATCH (i:Issue {type: $issue_type})
                    MERGE (q)-[r:ASKS_ABOUT]->(i)
                    ON CREATE SET r.count = 1, r.first_asked = datetime()
                    ON MATCH SET r.count = r.count + 1, r.last_asked = datetime()
                """, query_text=query[:200], issue_type=entities["issue_type"])
                print(f"[DEBUG] ✅ QueryPattern→Issue relationship created")
            
            # ✅ 3. Create/Update Brand node
            if entities.get("brand"):
                session.run("""
                    MERGE (b:Brand {name: $brand})
                    ON CREATE SET b.first_mentioned = datetime(), b.query_count = 1
                    ON MATCH SET b.query_count = b.query_count + 1, b.last_mentioned = datetime()
                """, brand=entities["brand"])
                print(f"[DEBUG] ✅ Brand node created/updated: {entities['brand']}")
                
                # ✅ NEW: Link QueryPattern → Brand
                session.run("""
                    MATCH (q:QueryPattern {text: $query_text})
                    MATCH (b:Brand {name: $brand})
                    MERGE (q)-[r:MENTIONS]->(b)
                    ON CREATE SET r.count = 1, r.first_mentioned = datetime()
                    ON MATCH SET r.count = r.count + 1, r.last_mentioned = datetime()
                """, query_text=query[:200], brand=entities["brand"])
                print(f"[DEBUG] ✅ QueryPattern→Brand relationship created")
            
            # ✅ 4. Create Brand → Issue relationship (MOST IMPORTANT FOR RAG)
            if entities.get("issue_type") and entities.get("brand"):
                session.run("""
                    MATCH (b:Brand {name: $brand})
                    MATCH (i:Issue {type: $issue_type})
                    MERGE (b)-[r:HAS_ISSUE]->(i)
                    ON CREATE SET r.frequency = 1, r.first_reported = datetime()
                    ON MATCH SET r.frequency = r.frequency + 1, r.last_reported = datetime()
                """, brand=entities["brand"], issue_type=entities["issue_type"])
                print(f"[DEBUG] ✅ Brand→Issue relationship created: {entities['brand']}→{entities['issue_type']}")
            
            # ✅ 5. NEW: Create Timeframe node and relationships
            if entities.get("timeframe"):
                session.run("""
                    MERGE (t:Timeframe {duration: $timeframe})
                    ON CREATE SET t.first_seen = datetime(), t.mention_count = 1
                    ON MATCH SET t.mention_count = t.mention_count + 1
                """, timeframe=entities["timeframe"])
                print(f"[DEBUG] ✅ Timeframe node created: {entities['timeframe']}")
                
                # Link Issue → Timeframe (when does this issue occur?)
                if entities.get("issue_type"):
                    session.run("""
                        MATCH (i:Issue {type: $issue_type})
                        MATCH (t:Timeframe {duration: $timeframe})
                        MERGE (i)-[r:OCCURS_WITHIN]->(t)
                        ON CREATE SET r.frequency = 1
                        ON MATCH SET r.frequency = r.frequency + 1
                    """, issue_type=entities["issue_type"], timeframe=entities["timeframe"])
                    print(f"[DEBUG] ✅ Issue→Timeframe relationship created")
            
            # ✅ 6. NEW: Store extracted entities metadata on QueryPattern
            session.run("""
                MATCH (q:QueryPattern {text: $query_text})
                SET q.brand_mentioned = $brand,
                    q.issue_mentioned = $issue_type,
                    q.timeframe_mentioned = $timeframe
            """, 
                query_text=query[:200],
                brand=entities.get("brand"),
                issue_type=entities.get("issue_type"),
                timeframe=entities.get("timeframe")
            )
            print(f"[DEBUG] ✅ Query metadata stored")
        
        print(f"[INFO] ✅ Stored query insight with RICH RELATIONSHIPS: {entities}")
    
    except Exception as e:
        print(f"[ERROR] ❌ Failed to store query insight: {e}")
        import traceback
        traceback.print_exc()


def get_relevant_context(entities: dict) -> str:
    """
    ✨ ENHANCED: Retrieve context by traversing relationship graph
    Uses the rich relationships built from previous queries!
    """
    context_parts = []
    
    try:
        with neo4j_client.driver.session() as session:
            
            # ✅ 1. Get Issue information with ALL related data
            if entities.get("issue_type"):
                result = session.run("""
                    MATCH (i:Issue {type: $issue_type})
                    OPTIONAL MATCH (b:Brand)-[r:HAS_ISSUE]->(i)
                    OPTIONAL MATCH (i)-[t:OCCURS_WITHIN]->(tf:Timeframe)
                    OPTIONAL MATCH (q:QueryPattern)-[:ASKS_ABOUT]->(i)
                    WITH i, 
                         collect(DISTINCT b.name) as affected_brands,
                         collect(DISTINCT tf.duration) as timeframes,
                         sum(r.frequency) as total_brand_reports,
                         count(DISTINCT q) as times_asked
                    RETURN i.type as issue,
                           i.sample_query as sample_query,
                           i.frequency as times_asked_direct,
                           affected_brands,
                           timeframes,
                           total_brand_reports,
                           times_asked as total_queries
                    LIMIT 1
                """, issue_type=entities["issue_type"])
                
                record = result.single()
                if record:
                    brands = [b for b in record['affected_brands'] if b]
                    timeframes = [t for t in record['timeframes'] if t]
                    
                    # Build rich context string
                    context_parts.append(
                        f"Issue '{record['issue']}' has been asked about {record['total_queries']} times "
                        f"and reported {record['total_brand_reports'] or 0} times across {len(brands)} brands."
                    )
                    
                    if brands:
                        context_parts.append(
                            f"Brands commonly affected: {', '.join(brands[:5])}."
                        )
                    
                    if timeframes:
                        context_parts.append(
                            f"Typical occurrence timeframe: {', '.join(timeframes[:3])}."
                        )
            
            # ✅ 2. Get Brand-specific issue history with frequency
            if entities.get("brand"):
                result = session.run("""
                    MATCH (b:Brand {name: $brand})-[r:HAS_ISSUE]->(i:Issue)
                    RETURN i.type as issue, 
                           r.frequency as frequency,
                           r.first_reported as first_reported,
                           r.last_reported as last_reported
                    ORDER BY r.frequency DESC
                    LIMIT 5
                """, brand=entities["brand"])
                
                issues = []
                for rec in result:
                    issues.append(f"{rec['issue']} ({rec['frequency']}x)")
                
                if issues:
                    context_parts.append(
                        f"Known issues with {entities['brand']}: {', '.join(issues)}"
                    )
                else:
                    context_parts.append(
                        f"No historical issues recorded for {entities['brand']} yet."
                    )
            
            # ✅ 3. NEW: Find similar past queries
            if entities.get("issue_type"):
                result = session.run("""
                    MATCH (q:QueryPattern)-[:ASKS_ABOUT]->(i:Issue {type: $issue_type})
                    RETURN q.text as similar_query, 
                           q.count as asked_times,
                           q.last_asked as last_asked
                    ORDER BY q.count DESC
                    LIMIT 3
                """, issue_type=entities.get("issue_type"))
                
                similar_queries = []
                for rec in result:
                    similar_queries.append(f"'{rec['similar_query']}' (asked {rec['asked_times']}x)")
                
                if similar_queries:
                    context_parts.append(
                        f"Similar questions: {', '.join(similar_queries[:2])}"
                    )
            
            # ✅ 4. NEW: Check Brand + Issue combination severity
            if entities.get("brand") and entities.get("issue_type"):
                result = session.run("""
                    MATCH (b:Brand {name: $brand})-[r:HAS_ISSUE]->(i:Issue {type: $issue_type})
                    RETURN r.frequency as times_reported,
                           r.first_reported as first_seen,
                           r.last_reported as last_seen
                """, brand=entities["brand"], issue_type=entities["issue_type"])
                
                record = result.single()
                if record:
                    context_parts.append(
                        f"This specific combination ({entities['brand']} + {entities['issue_type']}) "
                        f"has been reported {record['times_reported']} times."
                    )
            
            # ✅ 5. NEW: Check timeframe patterns
            if entities.get("timeframe") and entities.get("issue_type"):
                result = session.run("""
                    MATCH (i:Issue {type: $issue_type})-[r:OCCURS_WITHIN]->(t:Timeframe {duration: $timeframe})
                    RETURN r.frequency as occurrences
                """, issue_type=entities["issue_type"], timeframe=entities["timeframe"])
                
                record = result.single()
                if record:
                    context_parts.append(
                        f"This issue commonly occurs within {entities['timeframe']} timeframe "
                        f"({record['occurrences']} similar cases)."
                    )
    
    except Exception as e:
        print(f"[ERROR] Failed to retrieve context: {e}")
        import traceback
        traceback.print_exc()
    
    return "\n".join(context_parts) if context_parts else ""


# ==========================================
# 🤖 EXISTING ENDPOINTS
# ==========================================


@router.post("/assign_agent/{order_id}")
async def assign_agent(order_id: str):
    """Assign an agent to an order using AI logic"""
    # Fetch order details
    order = neo4j_client.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Simple agent assignment logic (you can enhance with LLM later)
    try:
        with neo4j_client.driver.session() as session:
            # Find available agent closest to order location
            result = session.run("""
                MATCH (a:Agent {status: 'available'})
                MATCH (o:Order {order_id: $order_id})-[:DELIVERED_TO]->(l:Location)
                RETURN a.agent_id AS agent_id, a.name AS name
                LIMIT 1
            """, order_id=order_id)
            
            agent = result.single()
            if not agent:
                raise HTTPException(status_code=404, detail="No available agents")
            
            agent_id = agent["agent_id"]
            
            # Assign agent
            session.run("""
                MATCH (a:Agent {agent_id: $agent_id})
                MATCH (o:Order {order_id: $order_id})
                MERGE (a)-[:ASSIGNED_TO]->(o)
                SET o.status = 'assigned'
            """, agent_id=agent_id, order_id=order_id)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assignment failed: {e}")
    
    return {
        "message": f"Order {order_id} assigned to agent {agent_id}",
        "agent_name": agent["name"]
    }


@router.post("/chat")
async def chat_with_ai(payload: dict = Body(...)):
    """
    Chat endpoint (frontend Groq client handles actual AI response)
    This endpoint can be used for logging or backend processing
    """
    user_message = payload.get("message")
    if not user_message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    # Extract and store entities for knowledge building
    entities = extract_entities(user_message)
    store_query_insight(user_message, entities)
    
    return {
        "response": f"Message received and processed",
        "entities_detected": entities
    }

@router.post("/debug/test-context")
async def debug_context(payload: dict = Body(...)):
    """
    Debug endpoint to see exactly what context is retrieved
    """
    query = payload.get("query", "")
    entities = extract_entities(query)
    
    # Get context
    context = get_relevant_context(entities)
    
    return {
        "query": query,
        "entities_extracted": entities,
        "context_retrieved": context,
        "context_length": len(context),
        "has_context": bool(context.strip())
    }
