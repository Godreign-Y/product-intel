'use client';

import React, { useState, useRef, useEffect } from 'react';
import {
  Plus,
  Send,
  Paperclip,
  Brain,
  MessageSquare,
  Sparkles,
  FileText,
  X,
} from 'lucide-react';
import { useAIWorkspace } from '../../hooks/useAIWorkspace';
import { ChatMessage } from '../../components/ChatMessage';
import { useDashboardData } from '../../hooks/useDashboardData';


export default function AIWorkspacePage() {
  const {
    sessions,
    activeSession,
    activeSessionId,
    setActiveSessionId,
    suggestedQuestions,
    isLoading,
    isSending,
    sendMessage,
    createNewSession,
  } = useAIWorkspace();

  const { data: dashboardData } = useDashboardData();

  const [inputVal, setInputVal] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<{ name: string; size: string; type: string }[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll chat to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activeSession?.messages, isSending]);

  const handleSend = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputVal.trim() && attachedFiles.length === 0) return;

    sendMessage(inputVal, attachedFiles);
    setInputVal('');
    setAttachedFiles([]);
  };

  const handleSuggestionClick = (question: string) => {
    sendMessage(question);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    const newFiles = Array.from(files).map((f) => {
      const sizeKB = (f.size / 1024).toFixed(0);
      return {
        name: f.name,
        size: `${sizeKB} KB`,
        type: f.type,
      };
    });

    setAttachedFiles((prev) => [...prev, ...newFiles]);
  };

  const removeFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="flex gap-6 h-[calc(100vh-8.5rem)] pb-4 overflow-hidden">
      {/* 1. Chat Sessions Sidebar */}
      <div className="w-64 flex flex-col justify-between bg-white border border-slate-100 rounded-xl shadow-sm overflow-hidden flex-shrink-0">
        <div className="p-4 border-b border-slate-50 flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Chat History</span>
          <button
            onClick={createNewSession}
            className="p-1.5 hover:bg-slate-50 border border-slate-200 text-indigo-600 rounded-lg cursor-pointer transition-colors"
            title="Start New Chat"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        {/* Sessions list */}
        <div className="flex-1 overflow-y-auto p-2.5 space-y-1">
          {isLoading ? (
            <div className="space-y-2 p-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-10 bg-slate-50 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-400">
              No conversations. Click &quot;+&quot; to start.
            </div>
          ) : (
            sessions.map((s) => {
              const isActive = s.id === activeSessionId;
              return (
                <button
                  key={s.id}
                  onClick={() => setActiveSessionId(s.id)}
                  className={`w-full text-left px-3.5 py-2.5 rounded-lg text-xs font-semibold flex items-center gap-2.5 cursor-pointer transition-all duration-150 ${
                    isActive
                      ? 'bg-indigo-50 text-indigo-700 border border-indigo-100/50'
                      : 'text-slate-600 hover:bg-slate-50/60 border border-transparent'
                  }`}
                >
                  <MessageSquare className={`w-3.5 h-3.5 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                  <span className="truncate flex-1">{s.title}</span>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* 2. Chat Workspace (Middle) */}
      <div className="flex-1 flex flex-col justify-between bg-white border border-slate-100 rounded-xl shadow-sm overflow-hidden">
        {/* Chat Pane */}
        <div className="flex-grow overflow-y-auto p-6 space-y-4">
          {!activeSession || activeSession.messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto">
              <div className="bg-gradient-to-tr from-violet-600 to-indigo-600 text-white w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg shadow-indigo-200 mb-6">
                <Brain className="w-6 h-6 animate-pulse" />
              </div>
              <h3 className="text-base font-bold text-slate-800 mb-2">AI Product Intelligence Assistant</h3>
              <p className="text-xs text-slate-500 leading-relaxed">
                Ask business questions, analyze conversion anomalies, or simulate hypothetical product updates. Upload reports, PDFs, or CSV data for deep context-aware synthesis.
              </p>
              
              <div className="mt-8 grid grid-cols-2 gap-3 w-full">
                {suggestedQuestions.slice(0, 4).map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSuggestionClick(q)}
                    className="text-left p-3 border border-slate-100 rounded-xl text-xs text-slate-600 hover:border-indigo-100 hover:bg-indigo-50/20 font-medium transition-all duration-150 cursor-pointer"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {activeSession.messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={msg}
                  onSuggestionClick={handleSuggestionClick}
                />
              ))}
              {isSending && (
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-600 text-white flex items-center justify-center shadow-sm">
                    <Sparkles className="w-4 h-4 animate-spin" />
                  </div>
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-semibold text-slate-400">AI is analyzing metrics...</span>
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce delay-100" />
                      <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce delay-200" />
                      <span className="w-1.5 h-1.5 bg-slate-300 rounded-full animate-bounce delay-300" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input box */}
        <div className="p-4 border-t border-slate-50 bg-slate-50/50">
          <form onSubmit={handleSend} className="relative">
            {/* Display attached file chips inside the input area */}
            {attachedFiles.length > 0 && (
              <div className="flex flex-wrap gap-2 pb-3.5 mb-2.5 border-b border-slate-100">
                {attachedFiles.map((file, idx) => (
                  <div key={idx} className="flex items-center gap-1.5 text-xs bg-indigo-50 text-indigo-700 border border-indigo-100 px-2.5 py-1 rounded-lg">
                    <FileText className="w-3.5 h-3.5" />
                    <span className="truncate max-w-[150px] font-semibold">{file.name}</span>
                    <button type="button" onClick={() => removeFile(idx)} className="text-indigo-400 hover:text-indigo-600 cursor-pointer">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="flex items-center bg-white border border-slate-200 rounded-xl overflow-hidden shadow-sm focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-100 transition-all">
              <input
                type="text"
                placeholder="Ask anything about your data..."
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                disabled={isSending}
                className="flex-grow px-4 py-3.5 text-sm text-slate-800 placeholder-slate-400 focus:outline-none"
              />
              
              <div className="flex items-center gap-1.5 pr-3">
                {/* Hidden input for files */}
                <input
                  type="file"
                  multiple
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  className="hidden"
                />
                
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isSending}
                  className="p-2 hover:bg-slate-50 text-slate-400 hover:text-slate-600 rounded-lg cursor-pointer transition-colors"
                  title="Attach Files"
                >
                  <Paperclip className="w-4 h-4" />
                </button>
                
                <button
                  type="submit"
                  disabled={isSending || (!inputVal.trim() && attachedFiles.length === 0)}
                  className="p-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-100 text-white disabled:text-slate-400 rounded-lg cursor-pointer transition-colors shadow-sm"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </form>
          
          {/* Suggested Questions below input */}
          {activeSession && activeSession.messages.length > 0 && suggestedQuestions.length > 0 && (
            <div className="flex items-center gap-2 overflow-x-auto py-2.5 mt-2 no-scrollbar">
              <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider whitespace-nowrap">Suggested:</span>
              <div className="flex gap-2">
                {suggestedQuestions.slice(0, 3).map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSuggestionClick(q)}
                    className="text-xs font-semibold px-3 py-1 bg-white hover:bg-indigo-50/20 text-slate-600 hover:text-indigo-600 border border-slate-200 hover:border-indigo-100 rounded-full transition-all duration-150 cursor-pointer whitespace-nowrap"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 3. Live Metrics Panel (Right) */}
      <div className="w-80 bg-white border border-slate-100 rounded-xl shadow-sm p-4 overflow-y-auto flex-shrink-0 flex flex-col gap-4">
        <div>
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">Live Metrics</span>
          <p className="text-[10px] text-slate-400 mt-0.5">Real-time performance metrics stream</p>
        </div>

        <div className="space-y-4">
          {dashboardData?.kpis.map((kpi) => (
            <div key={kpi.id} className="border border-slate-50 p-3 rounded-lg shadow-sm">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-medium text-slate-500">{kpi.title}</span>
                <span className={`text-[10px] font-bold ${kpi.isPositive ? 'text-emerald-600' : 'text-rose-600'}`}>
                  {kpi.isPositive ? '+' : ''}{kpi.changePercent}%
                </span>
              </div>
              <span className="text-lg font-bold text-slate-900 leading-tight">{kpi.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
