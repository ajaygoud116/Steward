"""
Lyzr Full Lifecycle Demo
========================
Covers: BUILD -> EVALUATE -> DEPLOY -> GOVERN
"""

# ============================================================
# STEP 0: Prerequisites
# ============================================================
# 1. Sign up at https://studio.lyzr.ai (Google/GitHub/email)
# 2. Get your API key from Account > API Keys
# 3. Install: pip install lyzr-adk

from lyzr import Studio
from lyzr import PIIType, PIIAction, SecretsAction


# ============================================================
# STEP 1: BUILD the Agent
# ============================================================
print("=" * 60)
print("STEP 1: BUILDING THE AGENT")
print("=" * 60)

# Initialize the SDK (reads LYZR_API_KEY from env or pass directly)
studio = Studio(api_key="<YOUR_API_KEY>")  # Replace with your key or set env var

# --- 1a. Basic Agent ---
support_agent = studio.create_agent(
    name="SupportBot",
    provider="gpt-4o",           # LLM model
    role="Customer support agent",
    goal="Resolve customer inquiries about billing and account issues",
    instructions="Be concise. Always ask for the account ID before looking up details.",
    temperature=0.3,              # Lower = more deterministic answers
)

# --- 1b. Add memory (remembers conversation context) ---
support_agent = studio.create_agent(
    name="SupportBot",
    provider="gpt-4o",
    role="Customer support agent",
    goal="Resolve customer inquiries about billing and account issues",
    instructions="Be concise. Always ask for the account ID before looking up details.",
    memory=30,                    # Remember last 30 messages
)

# --- 1c. Agent with a Tool (Python function) ---
def get_order_status(order_id: str) -> str:
    """Get the status of a customer order by order ID."""
    # In real code, you'd query your database/API
    db = {"ORD-1001": "Shipped", "ORD-1002": "Processing", "ORD-1003": "Delivered"}
    return db.get(order_id, "Order not found")

support_agent.add_tool(get_order_status)

# --- 1d. Agent with Knowledge Base (RAG) ---
kb = studio.create_knowledge_base(
    name="ProductDocs",
    vector_store="qdrant",
    embedding_model="text-embedding-3-large",
)

# Upload documents (PDF, website, etc.)
kb.add_pdf("product_manual.pdf")                        # Local file
kb.add_website("https://docs.example.com", max_pages=5)  # Web pages
kb.add_text("Our return policy allows 30-day returns for all unused items.")

# --- 1e. Agent with Context (background info) ---
company_ctx = studio.create_context(
    name="company_info",
    value="Acme Corp — Founded 2020, 50,000 customers, SaaS platform. Pricing: Basic $10/mo, Pro $50/mo."
)

support_agent = studio.create_agent(
    name="SupportBot",
    provider="gpt-4o",
    role="Customer support agent",
    goal="Resolve customer inquiries about billing and account issues",
    instructions="Be concise and always ask for the account ID.",
    memory=30,
    contexts=[company_ctx],
)


# ============================================================
# STEP 2: RUN / TEST the Agent (local evaluation)
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: RUNNING & TESTING THE AGENT")
print("=" * 60)

# --- 2a. Simple run ---
response = support_agent.run("What is your return policy?")
print(f"Agent: {response.response}")

# --- 2b. Multi-turn conversation with session ---
session = "customer_abc_123"
response1 = support_agent.run("My name is Ajay", session_id=session)
response2 = support_agent.run("What's my name?", session_id=session)
print(f"Session test — {response2.response}")  # Should remember "Ajay"

# --- 2c. Query with Knowledge Base at runtime ---
response = support_agent.run(
    "What are your shipping times?",
    knowledge_bases=[kb],           # KB injected at runtime
)
print(f"KB-backed answer: {response.response}")

# --- 2d. Structured output (typed response) ---
from pydantic import BaseModel
from typing import List

class Ticket(BaseModel):
    category: str
    urgency: str            # "low", "medium", "high"
    summary: str
    suggested_action: str

triage_agent = studio.create_agent(
    name="TicketTriage",
    provider="gpt-4o",
    role="Support ticket triage agent",
    goal="Categorize and prioritize support tickets",
    instructions="Analyze the ticket and return structured output",
    response_model=Ticket,
)

ticket: Ticket = triage_agent.run("I was charged twice for my subscription this month!")
print(f"Category: {ticket.category}, Urgency: {ticket.urgency}")
print(f"Action: {ticket.suggested_action}")

# --- 2e. Streaming ---
print("\nStreaming response:")
for chunk in support_agent.run("Explain our pricing plans", stream=True):
    if chunk.delta:
        print(chunk.delta, end="", flush=True)
    if chunk.done:
        print("\n[Stream complete]")

# --- 2f. Call a Tool ---
response = support_agent.run("What's the status of order ORD-1001?")
print(f"\nTool call result: {response.response}")


# ============================================================
# STEP 3: GOVERNANCE (Responsible AI Guardrails)
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: GOVERNANCE — SAFETY GUARDRAILS")
print("=" * 60)

# Create a safety policy
safety_policy = studio.create_rai_policy(
    name="StrictPolicy",
    description="Production safety guardrails",
    toxicity_threshold=0.3,                        # Block toxic content
    secrets_detection=SecretsAction.MASK,          # Mask API keys, tokens
    pii_detection={
        PIIType.CREDIT_CARD: PIIAction.BLOCK,      # Block credit card numbers
        PIIType.EMAIL: PIIAction.REDACT,            # Redact emails
        PIIType.SSN: PIIAction.BLOCK,              # Block SSNs
        PIIType.PHONE: PIIAction.REDACT,           # Redact phone numbers
    },
)

# Attach the policy to the agent
support_agent = studio.create_agent(
    name="SupportBot",
    provider="gpt-4o",
    role="Customer support agent",
    goal="Resolve customer inquiries",
    instructions="Be concise and helpful.",
    memory=30,
    contexts=[company_ctx],
    rai_policy=safety_policy,                       # <-- Guardrails active
    reflection=True,                               # Self-check for accuracy
    bias_check=True,                               # Check for biased responses
)

# Try sending sensitive data — guardrails will block/redact it
response = support_agent.run("My card number is 4111-1111-1111-1111, please refund me")
print(f"With guardrails: {response.response}")
# The credit card should be blocked/redacted in the agent's processing


# ============================================================
# STEP 4: EVALUATION (Automated Testing)
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: EVALUATION — AUTOMATED TESTING")
print("=" * 60)

# Create an evaluation environment (auto-generates test scenarios)
eval_env = studio.create_evaluation_environment(
    agent_id=support_agent.id,
    name="Pre-Production",
    description="Tests before deploying to production",
)

# Metrics evaluated automatically:
# - Task Completion: Did the agent solve the user's problem?
# - Hallucination: Did the agent make up facts?
# - Toxicity: Was the response safe?
# - Bias: Was the response fair?
# - Faithfulness: Did the agent stay grounded in provided knowledge?

# Method A: Run auto-generated test cases
print("Running auto-generated test cases...")
eval_results = eval_env.run()

# Method B: Add custom test cases
eval_env.add_test_case(
    input="What is your refund policy?",
    expected_output="We offer 30-day returns for unused items.",
)

eval_env.add_test_case(
    input="I want to speak to a human",
    expected_output=None,  # Just check for safe/appropriate response
)

# Run evaluation
print("Evaluating agent...")
results = eval_env.run()

# Check results
for test in results.test_cases:
    print(f"  Test: {test.input[:50]}... → Score: {test.score}/1.0 {'PASS' if test.passed else 'FAIL'}")

# Agent Hardening: auto-fix failed tests
# (Analyzes failures and recommends config changes)
if results.failed_count > 0:
    print(f"\n{results.failed_count} tests failed. Running Agent Hardening...")
    improvements = eval_env.harden(failed_tests=results.failed[:5])
    print(f"Recommended changes: {improvements.recommendations}")


# ============================================================
# STEP 5: DEPLOY — Integrate into Your Project Code
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: DEPLOY — INTEGRATE INTO YOUR PROJECT")
print("=" * 60)

# --- Option A: Use Lyzr ADK directly in your app ---
def support_chatbot(user_message: str, session_id: str) -> str:
    """Your app calls this function whenever a user sends a message."""
    response = support_agent.run(user_message, session_id=session_id)
    return response.response

# Example usage in your FastAPI/Flask/Django app:
# @app.post("/chat")
# def chat_endpoint(request: Request):
#     data = await request.json()
#     reply = support_chatbot(data["message"], data["session_id"])
#     return {"reply": reply}

print("Deploy Option A: ADK in your app → call support_agent.run()")

# --- Option B: REST API (for any language: JS, Java, Go, etc.) ---
print("""
Deploy Option B: REST API (use from any language)
  POST https://agent-prod.studio.lyzr.ai/v3/agent/{agent_id}/chat
  Headers: x-api-key: YOUR_KEY, Content-Type: application/json
  Body: {"message": "hello", "session_id": "user-123"}
""")

# --- Option C: Export agent config & deploy independently ---
# Export the agent as a portable config
config = support_agent.export_config()
print(f"Agent config exported. Import it anywhere with Studio.import_agent(config)")

# --- Option D: Deploy via Agent Studio UI ---
# 1. Go to studio.lyzr.ai
# 2. Select your agent
# 3. Click "Deploy"
# 4. Choose visibility (Private/Public/Organization)
# 5. Find the REST endpoint in Agent > API tab
print("Deploy Option D: Agent Studio UI → click Deploy → get REST endpoint")


# ============================================================
# STEP 6: MONITORING & OBSERVABILITY
# ============================================================
print("\n" + "=" * 60)
print("STEP 6: MONITORING (built-in)")
print("=" * 60)

# Every agent run is automatically traced.
# View in Studio: Agent > Traces
# You get:
#   - Step-by-step trace of every agent run
#   - Latency per step (LLM call, tool call, retrieval)
#   - Token usage
#   - Cost tracking
print("All runs are automatically logged. View traces at studio.lyzr.ai")


# ============================================================
# FULL PRODUCTION READY EXAMPLE
# ============================================================
print("\n" + "=" * 60)
print("FULL PRODUCTION EXAMPLE")
print("=" * 60)

def create_production_agent(api_key: str):
    """One function to build a fully production-ready agent."""

    studio = Studio(api_key=api_key)

    # 1. Build
    agent = studio.create_agent(
        name="ProdSupportBot",
        provider="gpt-4o",
        role="Enterprise customer support agent",
        goal="Resolve customer issues quickly and accurately",
        instructions="1. Always greet the customer. 2. Ask for account ID first. 3. Use knowledge base for answers. 4. Never make up information. 5. Escalate if you cannot resolve.",
        memory=30,
        temperature=0.3,
        reflection=True,
        bias_check=True,
        groundedness_facts=[
            "Acme Corp was founded in 2020",
            "HQ in San Francisco",
            "CEO is John Smith",
            "30-day return policy for unused items",
        ],
    )

    # 2. Attach guardrails
    policy = studio.create_rai_policy(
        name="ProductionGuardrails",
        description="Production safety policies",
        toxicity_threshold=0.3,
        pii_detection={
            PIIType.CREDIT_CARD: PIIAction.BLOCK,
            PIIType.SSN: PIIAction.BLOCK,
            PIIType.EMAIL: PIIAction.REDACT,
        },
        secrets_detection=SecretsAction.MASK,
    )
    agent.add_rai_policy(policy)

    # 3. Add knowledge
    kb = studio.create_knowledge_base(name="ProdKB")
    kb.add_pdf("company_policies.pdf")
    kb.add_website("https://help.acmecorp.com")
    agent.add_knowledge_base(kb)

    # 4. Add tools
    def lookup_account(email: str) -> dict:
        """Look up customer account by email."""
        return {"name": "Ajay", "plan": "Pro", "status": "active"}

    def create_refund(account_id: str, amount: float) -> str:
        """Process a refund for a customer."""
        return f"Refund of ${amount} processed for account {account_id}"

    agent.add_tool(lookup_account)
    agent.add_tool(create_refund)

    return agent


# To use in production:
# agent = create_production_agent("your-api-key")
# response = agent.run("I need a refund", session_id="session_001")
# print(response.response)

print("""
=== DEPLOYMENT CHECKLIST ===
[ ] Sign up at studio.lyzr.ai
[ ] Get API key from Account > API Keys
[ ] pip install lyzr-adk
[ ] Set LYZR_API_KEY in your environment
[ ] Build and test your agent (see above)
[ ] Run evaluation (auto-test cases)
[ ] Add guardrails (RAI policy)
[ ] Deploy via ADK, REST API, or Studio UI
[ ] Monitor traces in Studio
""")
