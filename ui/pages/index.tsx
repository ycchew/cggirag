import React, { useState, useRef, useEffect } from 'react';
import Head from 'next/head';
import axios from 'axios';

// Define TypeScript interfaces
interface DocumentChunk {
  content: string;
  source: string;
  page_number?: number;
  metadata: Record<string, any>;
}

interface QueryResponse {
  query: string;
  answer: string;
  documents: DocumentChunk[];
  confidence_score: number;
}

const HomePage = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<{query: string, response: QueryResponse | null}[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) {
        throw new Error('NEXT_PUBLIC_API_URL environment variable is not set');
      }
      const apiResponse = await axios.post<QueryResponse>(apiUrl, {
        query: query,
        top_k: 3
      });

      const data = apiResponse.data;
      setResponse(data);
      
      // Add to chat history
      setChatHistory(prev => [...prev, { query, response: data }]);
      setQuery('');
    } catch (err) {
      console.error('Error:', err);
      setError('Failed to get response. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <Head>
        <title>CGGI RAG System</title>
        <meta name="description" content="Q&A system for Chandler Good Government Index" />
      </Head>

      <header className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-6 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">CGGI RAG System</h1>
          <nav>
            <ul className="flex space-x-6">
              <li><a href="#" className="text-blue-600 hover:text-blue-800">Home</a></li>
              <li><a href="#" className="text-gray-600 hover:text-gray-800">About CGGI</a></li>
              <li><a href="#" className="text-gray-600 hover:text-gray-800">Reports</a></li>
            </ul>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <section className="mb-12 text-center">
          <h2 className="text-3xl font-bold text-gray-800 mb-4">Ask Questions About CGGI</h2>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Get instant answers to your questions about the Chandler Good Government Index (CGGI) 
            using our AI-powered search engine.
          </p>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left column - Input */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <form onSubmit={handleSubmit} className="mb-6">
                <div className="relative">
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask a question about CGGI (e.g., 'What are the top 3 countries in CGGI 2025?')"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    disabled={loading}
                  />
                  <button
                    type="submit"
                    disabled={loading || !query.trim()}
                    className={`absolute right-2 top-1/2 transform -translate-y-1/2 px-4 py-1.5 rounded-md ${
                      loading || !query.trim()
                        ? 'bg-gray-300 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700 text-white'
                    }`}
                  >
                    {loading ? 'Searching...' : 'Ask'}
                  </button>
                </div>
              </form>

              {/* Chat history */}
              <div className="space-y-6 max-h-[60vh] overflow-y-auto pr-2">
                {chatHistory.map((item, index) => (
                  <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="font-medium text-gray-800">Q: {item.query}</div>
                    {item.response && (
                      <div className="mt-2">
                        <div className="text-gray-700 whitespace-pre-wrap">{item.response.answer}</div>
                        <div className="mt-2 text-sm text-gray-500">
                          Confidence: {(item.response.confidence_score * 100).toFixed(1)}%
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {loading && (
                  <div className="border-l-4 border-yellow-500 pl-4 py-2">
                    <div className="font-medium text-gray-800">Q: {query}</div>
                    <div className="mt-2 flex items-center text-gray-700">
                      <div className="animate-pulse">Generating response...</div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {error && (
                <div className="mt-4 p-3 bg-red-100 text-red-700 rounded-md">
                  {error}
                </div>
              )}
            </div>
          </div>

          {/* Right column - Information Panel */}
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="font-bold text-lg text-gray-800 mb-4">About CGGI</h3>
              <p className="text-gray-600 mb-4">
                The Chandler Good Government Index (CGGI) measures the effectiveness and capabilities 
                of governments around the world across seven pillars of good governance.
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">•</span>
                  <span>Launched in 2021 by the Chandler Institute of Governance</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">•</span>
                  <span>Covers 120 countries across 7 governance pillars</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">•</span>
                  <span>Updated annually with latest data and methodologies</span>
                </li>
              </ul>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="font-bold text-lg text-gray-800 mb-4">Recent Findings</h3>
              <div className="space-y-3">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-blue-800">2025 Top Performers</h4>
                  <p className="text-sm text-gray-600">Singapore, Denmark, Norway lead the rankings</p>
                </div>
                <div className="p-3 bg-purple-50 rounded-lg">
                  <h4 className="font-semibold text-purple-800">Key Pillars</h4>
                  <p className="text-sm text-gray-600">Leadership, Institutions, Financial Stewardship</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="bg-gray-800 text-white py-8 mt-12">
        <div className="container mx-auto px-4 text-center">
          <p>CGGI RAG System • Powered by Alibaba Cloud AI</p>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;