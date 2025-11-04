import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface ChatMessage {
  role: string;
  content: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  agent_used: string;
}

export interface DocumentUploadResponse {
  success: boolean;
  message: string;
  document_id?: string;
}

export const chatAPI = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await axios.post(`${API_URL}/chat`, request);
    return response.data;
  },

  uploadDocument: async (file: File): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${API_URL}/documents/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  healthCheck: async (): Promise<any> => {
    const response = await axios.get(`${API_URL}/health`);
    return response.data;
  },
};
