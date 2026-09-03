from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from .adapters.local_mock import LocalMockAdapter
from .agents.graph import agent_graph
from .agents.state import AgentState
from typing import Optional
import pypdf
import io

app = FastAPI(title="ContentGuard AI Microservice")
ecm_adapter = LocalMockAdapter()

class AnalyzeRequest(BaseModel):
    doc_id: str

@app.get("/")
def read_root():
    return {"message": "ContentGuard AI Microservice is running!"}

# NEW: Endpoint to analyze uploaded files
@app.post("/api/v1/analyze-file")
async def analyze_uploaded_file(file: UploadFile = File(...)):
    try:
        # Safety check: Ensure filename exists
        if file.filename is None:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        filename = file.filename
        
        # Read the uploaded file
        contents = await file.read()
        
        # Extract text based on file type
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(contents)
        elif filename.endswith('.txt'):
            text = contents.decode('utf-8')
        elif filename.endswith('.docx'):
            text = extract_text_from_docx(contents)
        else:
            text = contents.decode('utf-8')  # Fallback
        
        # Initialize State with the actual document content
        initial_state = AgentState(
            doc_id=filename,
            document_content=text,
            metadata={"filename": filename, "source": "upload"}
        )
        
        # Invoke AI Graph
        final_state = agent_graph.invoke(initial_state)
        
        return {
            "status": "success",
            "doc_id": filename,
            "ai_extracted_data": final_state.get("extracted_data"),
            "compliance_audit": final_state.get("compliance_audit"),
            "source_citations": final_state.get("citations", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def extract_text_from_pdf(contents: bytes) -> str:
    """Extract text from PDF bytes"""
    pdf_reader = pypdf.PdfReader(io.BytesIO(contents))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(contents: bytes) -> str:
    """Extract text from DOCX bytes"""
    try:
        from docx import Document
        doc = Document(io.BytesIO(contents))
        return "\n".join([para.text for para in doc.paragraphs])
    except:
        return "Could not extract text from DOCX file"

# Keep the old endpoint for backward compatibility
@app.post("/api/v1/analyze")
def analyze_document(request: AnalyzeRequest):
    try:
        doc_data = ecm_adapter.fetch_document(request.doc_id)
        
        initial_state = AgentState(
            doc_id=doc_data.doc_id,
            document_content=doc_data.content,
            metadata=doc_data.metadata
        )
        
        final_state = agent_graph.invoke(initial_state)
        
        return {
            "status": "success",
            "doc_id": request.doc_id,
            "ai_extracted_data": final_state.get("extracted_data"),
            "compliance_audit": final_state.get("compliance_audit"),
            "source_citations": final_state.get("citations", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))