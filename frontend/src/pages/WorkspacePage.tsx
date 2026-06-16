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

  const { mutate, isPending } = useWorkspace();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isPending]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isPending) return;

    const userMsg = chatInput;
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setChatInput('');

    mutate({
      query: userMsg,
      context: {
        product_id: selectedProduct || null,
        start_date: startDate || null,
        end_date: endDate || null
      }
    }, {
      onSuccess: (data) => {
        setMessages(prev => [...prev, { 
          sender: 'assistant', 
          text: data.response,
          meta: { route: data.routed_to }
        }]);
      },
      onError: () => {
        setMessages(prev => [...prev, { sender: 'assistant', text: "Error: Could not connect to the Decision Intelligence Engine." }]);
      }
    });
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
          {isPending && (
            <div className="chat-bubble assistant" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <RefreshCw size={14} className="spin" />
              Generating executive summaries and evaluating calculations...
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
            disabled={isPending}
          />
          <button 
            type="submit" 
            className="chat-send-btn"
            disabled={isPending || !chatInput.trim()}
          >
            Send
          </button>
        </form>
      </div>
    </>
  );
}
