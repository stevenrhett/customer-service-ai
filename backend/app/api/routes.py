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
    
    # Maximum file size: 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    try:
        # Validate filename exists
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")
        
        # Read file content with size limit
        content = b""
        total_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        
        while chunk := await file.read(chunk_size):
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024)}MB"
                )
            content += chunk
        
        # Extract text based on file type (case-insensitive)
        text = ""
        filename_lower = file.filename.lower()
        
        if filename_lower.endswith('.pdf'):
            pdf_reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() for page in pdf_reader.pages)
        elif filename_lower.endswith('.txt'):
            text = content.decode('utf-8')
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Only PDF and TXT files are supported."
            )
        
        # Validate text was extracted
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the file"
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
    
    except HTTPException:
        raise
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
