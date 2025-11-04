'use client';

import ChatInterface from '@/components/ChatInterface';
import DocumentUpload from '@/components/DocumentUpload';

export default function Home() {
  return (
    <main className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-blue-600 text-white p-4 shadow-lg">
        <div className="container mx-auto">
          <h1 className="text-2xl font-bold">Customer Service AI</h1>
          <p className="text-sm text-blue-100">Multi-agent intelligent support system</p>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 container mx-auto p-4 flex gap-4 overflow-hidden">
        {/* Sidebar with document upload */}
        <aside className="w-80 flex-shrink-0">
          <DocumentUpload />
          
          <div className="mt-4 bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-semibold mb-3">Available Agents</h3>
            <ul className="space-y-3 text-sm">
              <li className="flex items-start">
                <span className="inline-block w-2 h-2 bg-green-500 rounded-full mt-1.5 mr-2"></span>
                <div>
                  <div className="font-medium">Document Retrieval Agent</div>
                  <div className="text-gray-600">Answers from documentation</div>
                </div>
              </li>
              <li className="flex items-start">
                <span className="inline-block w-2 h-2 bg-blue-500 rounded-full mt-1.5 mr-2"></span>
                <div>
                  <div className="font-medium">Technical Support Agent</div>
                  <div className="text-gray-600">Troubleshooting & issues</div>
                </div>
              </li>
              <li className="flex items-start">
                <span className="inline-block w-2 h-2 bg-purple-500 rounded-full mt-1.5 mr-2"></span>
                <div>
                  <div className="font-medium">General Inquiry Agent</div>
                  <div className="text-gray-600">General questions</div>
                </div>
              </li>
            </ul>
          </div>
        </aside>

        {/* Chat interface */}
        <div className="flex-1 bg-white rounded-lg shadow overflow-hidden">
          <ChatInterface />
        </div>
      </div>
    </main>
  );
}
