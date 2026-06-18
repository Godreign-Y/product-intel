import React, { useState, useRef, useEffect } from 'react';
import { RefreshCw } from 'lucide-react';
import { renderMarkdown } from '../utils/mdRenderer';
import { useFilters } from '../components/FilterContext';
import { useWorkspace } from '../hooks/useWorkspace';
import { Message } from '../types';

export default function WorkspacePage() {
  const { selectedProduct, startDate, endDate } = useFilters();
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'assistant', text: "Hello! I am your AI Business Analyst. You can ask me to explain revenue drops, run simulations, or summarize historical reports." }
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [isStreaming, setIsStreaming] = useState(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isStreaming) return;

    const userMsg = chatInput;
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setChatInput('');
    setIsStreaming(true);

    // Add empty assistant message placeholder
    setMessages(prev => [...prev, { sender: 'assistant', text: '' }]);

    try {
      const response = await fetch('/api/v1/agent/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userMsg,
          context: {
            product_id: selectedProduct || null,
            start_date: startDate || null,
            end_date: endDate || null
          }
        })
      });

      if (!response.ok) throw new Error('Network error');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (reader) {
        let currentText = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6).trim();
              if (dataStr === '[DONE]') continue;
              if (!dataStr) continue;
              
              try {
                const data = JSON.parse(dataStr);
                if (data.type === 'metadata') {
                  setMessages(prev => {
                    const newMsgs = [...prev];
                    newMsgs[newMsgs.length - 1] = { ...newMsgs[newMsgs.length - 1], meta: { route: data.route_called } };
                    return newMsgs;
                  });
                } else if (data.type === 'text') {
                  currentText += data.content;
                  setMessages(prev => {
                    const newMsgs = [...prev];
                    newMsgs[newMsgs.length - 1] = { ...newMsgs[newMsgs.length - 1], text: currentText };
                    return newMsgs;
                  });
                }
              } catch (err) {
                // Ignore incomplete JSON chunks from stream buffering
              }
            }
          }
        }
      }
    } catch (error) {
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { sender: 'assistant', text: "Error: Could not connect to the Decision Intelligence Engine." };
        return newMsgs;
      });
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <>
      <div className="header">
        <div>
          <h1>AI Decision Workspace</h1>
          <p>Ask questions, analyze root causes, and run what-if simulations</p>
        </div>
      </div>

      <div className="chat-container animate-fade-in">
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`chat-bubble ${msg.sender}`}>
              {msg.sender === 'assistant' ? (
                <div dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }} />
              ) : (
                msg.text
              )}
              {msg.meta && (
                <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '6px' }}>
                  Routed to: <code>{msg.meta.route}</code>
                </div>
              )}
            </div>
          ))}
          {isStreaming && (
            <div className="chat-bubble assistant" style={{ display: 'flex', alignItems: 'center', gap: '8px', opacity: 0.7 }}>
              <RefreshCw size={14} className="spin" />
              Thinking...
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-container" onSubmit={handleSendMessage}>
          <input 
            type="text"
            className="chat-input"
            placeholder="Ask e.g.: 'Why did revenue drop for P001 on 2025-12-31?'"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            disabled={isStreaming}
          />
          <button 
            type="submit" 
            className="chat-send-btn"
            disabled={isStreaming || !chatInput.trim()}
          >
            Send
          </button>
        </form>
      </div>
    </>
  );
}
