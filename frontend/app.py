import streamlit as st
import requests
import json
from datetime import datetime

# Configuration
API_URL = "http://127.0.0.1:8000/api/v1/analyze"
API_UPLOAD_URL = "http://127.0.0.1:8000/api/v1/analyze-file"

st.set_page_config(
    page_title="ContentGuard AI", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better look
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .stAlert { border-radius: 10px; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ ContentGuard AI")
st.markdown("### Enterprise Document Compliance & Risk Analysis")
st.markdown("Powered by Multi-Agent RAG Pipeline with LangGraph & Groq")

# Sidebar
with st.sidebar:
    st.header("📂 Document Source")
    st.markdown("Upload a document or enter a Document ID from your ECM system.")
    
    # File Upload Option
    uploaded_file = st.file_uploader("Upload PDF/TXT", type=["pdf", "txt", "docx"])
    
    st.divider()
    
    # Manual ID Option (for WebCenter integration demo)
    st.markdown("**Or use existing Document ID:**")
    doc_id = st.text_input("Document ID", value="DOC-001")
    
    analyze_btn = st.button(" Analyze Document", type="primary", use_container_width=True)
    
    st.divider()
    st.markdown("### ℹ️ System Info")
    st.markdown("- **LLM:** Groq (Llama3/Qwen)")
    st.markdown("- **Vector DB:** Qdrant Cloud")
    st.markdown("- **Tracing:** Langfuse")
    st.markdown("- **Backend:** FastAPI + LangGraph")

# Main Content
if analyze_btn:
    with st.spinner(" AI Agents are analyzing the document... This may take a few seconds."):
        try:
            data = None
            
            # Check if a file was uploaded
            if uploaded_file is not None:
                st.info(f"📄 Analyzing uploaded file: **{uploaded_file.name}**")
                # Send file to the upload endpoint
                files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                response = requests.post(API_UPLOAD_URL, files=files, timeout=120)
            else:
                st.info(f"📄 Analyzing document ID: **{doc_id}**")
                # Use the existing document ID endpoint
                response = requests.post(API_URL, json={"doc_id": doc_id}, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                
                st.success("✅ Analysis Complete!")
                st.divider()
                
                # Top Metrics Row
                m1, m2, m3 = st.columns(3)
                meta = data.get("ai_extracted_data", {})
                
                with m1:
                    risk = meta.get("risk_level", "Unknown")
                    risk_color = "" if risk.lower() == "high" else "🟡" if risk.lower() == "medium" else "🟢"
                    st.metric("Risk Level", f"{risk} {risk_color}")
                
                with m2:
                    st.metric("Expiration Date", meta.get("expiration_date", "N/A"))
                
                with m3:
                    missing = len(meta.get("missing_clauses", []))
                    st.metric("Missing Clauses", f"⚠️ {missing}")
                
                st.divider()
                
                # Two Column Layout
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("📊 Extracted Metadata")
                    with st.expander("View Full Metadata", expanded=True):
                        st.write(f"**Summary:** {meta.get('summary', 'N/A')}")
                        st.write(f"**Missing Clauses:** {', '.join(meta.get('missing_clauses', []))}")
                        st.json(meta)
                    
                    st.subheader("📚 Source Citations (RAG)")
                    citations = data.get("source_citations", [])
                    if citations:
                        for i, citation in enumerate(citations, 1):
                            st.info(f"**Policy {i}:** {citation}")
                    else:
                        st.warning("No policies cited.")
                
                with col2:
                    st.subheader("⚖️ Compliance Audit Report")
                    audit = data.get("compliance_audit", "No audit available.")
                    st.markdown(audit)
                    
                    # Langfuse Link
                    st.divider()
                    st.caption("🔍 **Traceability:** This analysis was traced via Langfuse for full auditability.")
                    
            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.json(response.json())
                
        except requests.exceptions.ConnectionError:
            st.error("❌ **Connection Error:** Could not connect to the backend API.")
            st.info("💡 Make sure your FastAPI server is running on `http://127.0.0.1:8000`")
        except requests.exceptions.Timeout:
            st.warning(" The request timed out. The AI agents might be taking longer than expected.")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>Built with LangGraph, Groq, Qdrant, and FastAPI | Traced via Langfuse</p>
    <p>© 2026 ContentGuard AI - Enterprise Agentic AI Solution</p>
</div>
""", unsafe_allow_html=True)