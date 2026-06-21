import React, { useState, useRef, useEffect } from 'react';
import { RefreshCw, ChevronDown } from 'lucide-react';
import { renderMarkdown } from '../utils/mdRenderer';
import { useFilters } from '../components/FilterContext';
import ChatVizPanel from '../components/ChatVizPanel';
import { ChatVisualization, Message } from '../types';

export default function WorkspacePage() {
  const { selectedProduct, startDate, endDate } = useFilters();
  const [chatInput, setChatInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'assistant', text: "Hello! I am your AI Business Analyst. You can ask me to explain revenue drops, run simulations, or summarize historical reports." }
  ]);
  
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentLogs, setCurrentLogs] = useState<string[]>([]);
  
  const chatMessagesRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [showScrollBtn, setShowScrollBtn] = useState(false);
  const isAutoScrolling = useRef(true);

  // Monitor scroll height changes to auto scroll or show scroll button
  const handleScroll = () => {
    const el = chatMessagesRef.current;
    if (!el) return;

    // Check if user is scrolled up from the bottom (80px threshold)
    const isAtBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 80;
    
    if (isAtBottom) {
      isAutoScrolling.current = true;
      setShowScrollBtn(false);
    } else {
      isAutoScrolling.current = false;
      setShowScrollBtn(true);
    }
  };

  const handleScrollToBottom = () => {
    isAutoScrolling.current = true;
    setShowScrollBtn(false);
    const el = chatMessagesRef.current;
    if (el) {
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  };

  // Scroll to bottom when message updates if auto scrolling is enabled
  useEffect(() => {
    if (isAutoScrolling.current && chatMessagesRef.current) {
      const el = chatMessagesRef.current;
      el.scrollTop = el.scrollHeight;
    }
  }, [messages, isStreaming, currentLogs]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isStreaming) return;

    const userMsg = chatInput;
    setMessages(prev => [...prev, { sender: 'user', text: userMsg }]);
    setChatInput('');
    setCurrentLogs([]);
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
                if (data.type === 'status') {
                  setCurrentLogs(prev => [...prev, data.content]);
                } else if (data.type === 'viz_planning') {
                  setCurrentLogs(prev => [...prev, data.content]);
                } else if (data.type === 'metadata') {
                  setMessages(prev => {
                    const newMsgs = [...prev];
                    newMsgs[newMsgs.length - 1] = { ...newMsgs[newMsgs.length - 1], meta: { route: data.route_called } };
                    return newMsgs;
                  });
                } else if (data.type === 'viz_plan') {
                  const placeholders: ChatVisualization[] = (data.visualizations || []).map((v: ChatVisualization) => ({
                    ...v,
                    status: 'loading',
                  }));
                  setMessages(prev => {
                    const newMsgs = [...prev];
                    newMsgs[newMsgs.length - 1] = {
                      ...newMsgs[newMsgs.length - 1],
                      visualizations: placeholders,
                    };
                    return newMsgs;
                  });
                } else if (data.type === 'viz_ready') {
                  const chart = data.chart;
                  setMessages(prev => {
                    const newMsgs = [...prev];
                    const last = newMsgs[newMsgs.length - 1];
                    const vizs = (last.visualizations || []).map(v =>
                      v.id === data.id
                        ? {
                            id: chart.id,
                            title: chart.title,
                            subtitle: chart.subtitle,
                            chart_type: chart.chart_type,
                            index_axis: chart.index_axis,
                            status: 'ready' as const,
                            data: chart.data,
                          }
                        : v
                    );
                    newMsgs[newMsgs.length - 1] = { ...last, visualizations: vizs };
                    return newMsgs;
                  });
                } else if (data.type === 'viz_error') {
                  setMessages(prev => {
                    const newMsgs = [...prev];
                    const last = newMsgs[newMsgs.length - 1];
                    const vizs = (last.visualizations || []).map(v =>
                      v.id === data.id ? { ...v, status: 'error' as const } : v
                    );
                    newMsgs[newMsgs.length - 1] = { ...last, visualizations: vizs };
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

      <div className="chat-container animate-fade-in" style={{ position: 'relative' }}>
        <div className="chat-messages" ref={chatMessagesRef} onScroll={handleScroll}>
          {messages.map((msg, index) => {
            // Render text if not empty
            const hasText = msg.text && msg.text.trim().length > 0;
            const hasViz = (msg.visualizations?.length ?? 0) > 0;
            if (!hasText && !hasViz && msg.sender === 'assistant' && isStreaming && index === messages.length - 1) {
              // Hide empty bubble while logs are running
              return null;
            }

            return (
              <div key={index} className={`chat-bubble ${msg.sender}`}>
                {msg.sender === 'assistant' ? (
                  <div dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }} />
                ) : (
                  msg.text
                )}
                {msg.visualizations && msg.visualizations.length > 0 && (
                  <ChatVizPanel visualizations={msg.visualizations} />
                )}
                {msg.meta && (
                  <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)', borderTop: '1px solid var(--border-subtle)', paddingTop: '6px' }}>
                    Routed to: <code>{msg.meta.route}</code>
                  </div>
                )}
              </div>
            );
          })}
          
          {isStreaming && (
            <div className="chat-bubble assistant">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: currentLogs.length > 0 ? '8px' : 0 }}>
                <RefreshCw size={14} className="spin" style={{ color: 'var(--calm-sienna)' }} />
                <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>Thinking...</span>
              </div>
              {currentLogs.length > 0 && (
                <div className="progress-logs">
                  {currentLogs.map((log, idx) => (
                    <div key={idx} className="progress-log-item">
                      <span className="log-check">✓</span>
                      <span className="log-text">{log}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {showScrollBtn && (
          <button 
            type="button" 
            className="scroll-bottom-btn animate-fade-in" 
            onClick={handleScrollToBottom}
            aria-label="Scroll to bottom"
          >
            <ChevronDown size={18} />
          </button>
        )}

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
