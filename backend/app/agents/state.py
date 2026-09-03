from typing import Any, Dict, List, Optional
#from langgraph.graph import MessageState
from pydantic import BaseModel, Field

class ExtractedMetadata(BaseModel):
    """Schema for the AI to fill out"""
    expiration_date: Optional[str] = Field(description="The expiration date of the contract, if mentioned.")
    risk_level: str = Field(description="Assess the risk level: 'Low', 'Medium', or ' High'.")
    missing_clauses: List[str] = Field(description="List any critical missing clauses, e.g., 'Liability', 'Termination'.")
    summary: str = Field(description="A brief 1-sentence summary of the document.")


class AgentState(BaseModel):
    """
    Represents the state of an agent in the system.
    """
    doc_id: str
    document_content: str
    metadata: dict
    extracted_data: Optional[ExtractedMetadata] = None
    compliance_audit: Optional[str] = None # NEW: Holds the RAG audit result
    compliance_issues: List[str] = []
    citations: List[str] = [] # NEW
    final_report: str = ""
    messages: List[Any] = []