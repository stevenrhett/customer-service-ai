"""API routes for the customer service application."""
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import (
    ChatRequest, 
    ChatResponse, 
    DocumentUploadResponse,
    DocumentInfo
)
from typing import List
import uuid
from pypdf import PdfReader
import io

# Router will be initialized in main.py
router = APIRouter()

# Global variables for dependency injection (set in main.py)
orchestrator = None
vector_store = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle chat requests and route to appropriate agent.
    """
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    
    # Generate conversation ID if not provided
    conv_id = request.conversation_id or str(uuid.uuid4())
    
    # Route the query to the appropriate agent
    response, agent_name = orchestrator.route_query(
        query=request.message,
        conversation_id=conv_id
    )
    
    return ChatResponse(
        response=response,
        conversation_id=conv_id,
        agent_used=agent_name
    )


@router.post("/documents/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document to the vector store.
    Supports PDF files.
    """
    if not vector_store:
        raise HTTPException(status_code=500, detail="Vector store not initialized")
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract text based on file type
        text = ""
        if file.filename.endswith('.pdf'):
            pdf_reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() for page in pdf_reader.pages)
        elif file.filename.endswith('.txt'):
            text = content.decode('utf-8')
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Only PDF and TXT files are supported."
            )
        
        # Generate document ID
        doc_id = str(uuid.uuid4())
        
        # Add to vector store
        metadata = {
            "document_id": doc_id,
            "filename": file.filename
        }
        vector_store.add_document(text, metadata)
        
        return DocumentUploadResponse(
            success=True,
            message=f"Document '{file.filename}' uploaded successfully",
            document_id=doc_id
        )
    
    except Exception as e:
        return DocumentUploadResponse(
            success=False,
            message=f"Error uploading document: {str(e)}",
            document_id=None
        )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "customer-service-ai"
    }
