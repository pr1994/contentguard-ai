import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, START, END
from langfuse.langchain import CallbackHandler
from .state import AgentState, ExtractedMetadata
from .rag_setup import vector_store

load_dotenv()

# Initialize Langfuse Handler
langfuse_handler = CallbackHandler()

# Initialize Groq LLM with Langfuse tracing explicitly attached
llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    callbacks=[langfuse_handler] # <--- THIS IS THE MAGIC
)

structured_llm = llm.with_structured_output(ExtractedMetadata)

# --- Node 1: Extract Metadata ---
def extract_metadata_node(state: AgentState):
    print(f"--- Agent 1: Extracting metadata from {state.doc_id} ---")
    system_prompt = """You are an expert Legal Document Analyst. 
    Analyze the provided document content and extract the requested metadata."""
    
    result = structured_llm.invoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Document Content:\n{state.document_content}"}
    ], config={"callbacks": [langfuse_handler]}) # Pass handler to invoke
    
    return {"extracted_data": result}

# --- Node 2: RAG Compliance Auditor ---
def audit_compliance_node(state: AgentState):
    print(f"--- Agent 2: Auditing compliance for {state.doc_id} ---")
    
    if state.extracted_data is None:
        return {"compliance_audit": "Cannot perform compliance audit: metadata extraction failed.", "citations": []}
    
    # 1. Retrieve relevant policies from Qdrant
    query_text = f"Document risk: {state.extracted_data.risk_level}. Missing clauses: {state.extracted_data.missing_clauses}"
    retrieved_docs = vector_store.similarity_search(query_text, k=2)
    
    # Extract the text and format as citations (DEDUPLICATED)
    context = "\n".join([doc.page_content for doc in retrieved_docs])
    citations = list(set([doc.page_content for doc in retrieved_docs]))
    
    print(f"--- Retrieved Policies from Qdrant: {citations} ---")
    
    # 2. Ask the LLM to audit
    audit_prompt = f"""You are a Compliance Officer. 
    Review the document's extracted metadata against the Company Policies below.
    
    CRITICAL INSTRUCTIONS:
    1. State clearly if the document is COMPLIANT or NON-COMPLIANT in the first sentence.
    2. Keep your entire response strictly under 150 words.
    3. Do not use fluff. Focus only on the specific policy violated or met.
    
    Company Policies:
    {context}
    
    Extracted Metadata:
    {state.extracted_data.model_dump_json()}
    """
    
    response = llm.invoke(audit_prompt, config={"callbacks": [langfuse_handler]}) # Pass handler to invoke
    
    return {
        "compliance_audit": response.content,
        "citations": citations
    }

# --- Build the Graph ---
def build_graph():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("extract_metadata", extract_metadata_node)
    workflow.add_node("audit_compliance", audit_compliance_node)
    
    workflow.add_edge(START, "extract_metadata")
    workflow.add_edge("extract_metadata", "audit_compliance")
    workflow.add_edge("audit_compliance", END)
    
    return workflow.compile()

agent_graph = build_graph()