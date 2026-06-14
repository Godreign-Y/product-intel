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
  Pin,
  FlaskConical,
  Layers,
  TrendingUp,
} from 'lucide-react';
import { useAIWorkspace } from '../hooks/useAIWorkspace';
import { ChatMessage } from '../components/ChatMessage';
import { useDashboardData } from '../hooks/useDashboardData';

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
    sendMessage(inputVal.trim(), attachedFiles);
    setInputVal('');
    setAttachedFiles([]);
    // Reset file input so same file can be selected again
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
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
    <div className="flex gap-6 h-[calc(100vh-8rem)] overflow-hidden">
      {/* Column 1: History Panel (Width: 250px) */}
      <div className="w-[250px] flex flex-col justify-between bg-white border border-[#E5E7EB] rounded-[20px] shadow-sm overflow-hidden flex-shrink-0">
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {/* Previous Chats */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider">Previous Chats</span>
              <button
                onClick={createNewSession}
                className="p-1 hover:bg-[#F3E8FF] hover:text-[#7C3AED] border border-[#E5E7EB] text-[#7C3AED] rounded-[8px] cursor-pointer transition-colors"
                title="Start New Chat"
              >
                <Plus className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="space-y-1">
              {isLoading ? (
                <div className="space-y-2">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="h-9 bg-slate-50 rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : sessions.length === 0 ? (
                <div className="text-center py-4 text-[10px] text-[#9CA3AF]">
                  No previous sessions.
                </div>
              ) : (
                sessions.map((s) => {
                  const isActive = s.id === activeSessionId;
                  return (
                    <button
                      key={s.id}
                      onClick={() => setActiveSessionId(s.id)}
                      className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold flex items-center gap-2 cursor-pointer transition-all duration-150 ${
                        isActive
                          ? 'bg-[#7C3AED] text-white shadow-sm'
                          : 'text-[#111827] hover:bg-[#F3E8FF] hover:text-[#7C3AED]'
                      }`}
                    >
                      <MessageSquare className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-[#6B7280]'}`} />
                      <span className="truncate flex-1">{s.title}</span>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Pinned Analyses */}
          <div>
            <span className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block mb-3">Pinned Analyses</span>
            <div className="space-y-1.5">
              {[
                { title: 'Q2 Conversion Audit', date: '2 days ago' },
                { title: 'Revenue Leak Search', date: '1 week ago' },
              ].map((pa, i) => (
                <div key={i} className="p-2 border border-[#E5E7EB] hover:border-purple-200 rounded-lg flex items-center gap-2 cursor-pointer transition-colors">
                  <Pin className="w-3 h-3 text-amber-500 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-[11px] font-bold text-[#111827] truncate leading-tight">{pa.title}</p>
                    <span className="text-[9px] text-[#9CA3AF]">{pa.date}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Saved Experiments */}
          <div>
            <span className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block mb-3">Saved Experiments</span>
            <div className="space-y-1.5">
              {[
                { title: 'Checkout Step A/B', metric: '+6.2% Lift' },
                { title: 'Price elasticity simulation', metric: '+3.5% Profit' },
              ].map((se, i) => (
                <div key={i} className="p-2 border border-[#E5E7EB] hover:border-purple-200 rounded-lg flex items-center gap-2 cursor-pointer transition-colors">
                  <FlaskConical className="w-3.5 h-3.5 text-[#7C3AED] flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-[11px] font-bold text-[#111827] truncate leading-tight">{se.title}</p>
                    <span className="text-[9px] text-[#10B981] font-bold">{se.metric}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Column 2: Chat Area (Largest Section) */}
      <div className="flex-grow flex-1 flex flex-col justify-between bg-white border border-[#E5E7EB] rounded-[20px] shadow-sm overflow-hidden h-full">
        {/* Chat Pane */}
        <div className="flex-grow overflow-y-auto p-6 space-y-4">
          {!activeSession || activeSession.messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-lg mx-auto">
              <div className="bg-[#F3E8FF] text-[#7C3AED] w-12 h-12 rounded-2xl flex items-center justify-center shadow-lg shadow-purple-100 mb-6">
                <Brain className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-[#111827] mb-2">AI Product Intelligence Assistant</h3>
              <p className="text-xs text-[#6B7280] leading-relaxed">
                Ask business questions, analyze conversion anomalies, or simulate hypothetical product updates. Upload reports, PDFs, or CSV data for deep context-aware synthesis.
              </p>
              
              <div className="mt-8 grid grid-cols-2 gap-3 w-full">
                {suggestedQuestions.slice(0, 4).map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSuggestionClick(q)}
                    className="text-left p-3 border border-[#E5E7EB] rounded-xl text-xs text-[#6B7280] hover:border-purple-200 hover:bg-[#F3E8FF]/20 font-semibold transition-all duration-150 cursor-pointer leading-tight"
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
                  <div className="w-8 h-8 rounded-lg bg-[#7C3AED] text-white flex items-center justify-center shadow-sm">
                    <Sparkles className="w-4 h-4 animate-spin" />
                  </div>
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-semibold text-[#6B7280]">AI is analyzing metrics...</span>
                    <div className="flex gap-1">
                      <span className="w-1.5 h-1.5 bg-[#7C3AED] rounded-full animate-bounce delay-100" />
                      <span className="w-1.5 h-1.5 bg-[#7C3AED] rounded-full animate-bounce delay-200" />
                      <span className="w-1.5 h-1.5 bg-[#7C3AED] rounded-full animate-bounce delay-300" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Sticky Input Area */}
        <div className="p-4 border-t border-[#E5E7EB] bg-slate-50/50">
          <form onSubmit={handleSend} className="relative">
            {/* Display attached file chips inside the input area */}
            {attachedFiles.length > 0 && (
              <div className="flex flex-wrap gap-2 pb-3.5 mb-2.5 border-b border-[#E5E7EB]">
                {attachedFiles.map((file, idx) => (
                  <div key={idx} className="flex items-center gap-1.5 text-xs bg-[#F3E8FF] text-[#7C3AED] border border-purple-200 px-2.5 py-1 rounded-lg">
                    <FileText className="w-3.5 h-3.5" />
                    <span className="truncate max-w-[150px] font-semibold">{file.name}</span>
                    <button type="button" onClick={() => removeFile(idx)} className="text-purple-400 hover:text-purple-600 cursor-pointer">
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}

            <div className="flex items-center bg-white border border-[#E5E7EB] rounded-[12px] h-[44px] overflow-hidden shadow-sm focus-within:border-[#7C3AED] focus-within:ring-2 focus-within:ring-[#F3E8FF] transition-all">
              <input
                type="text"
                placeholder="Ask anything about your data... (Enter to send)"
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isSending}
                aria-label="Chat message input"
                className="flex-grow px-4 py-2 text-sm text-[#111827] placeholder-[#9CA3AF] focus:outline-none"
              />
              
              <div className="flex items-center gap-1.5 pr-2">
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
                  className="p-1.5 hover:bg-slate-50 text-[#6B7280] hover:text-[#111827] rounded-lg cursor-pointer transition-colors"
                  title="Attach Files"
                >
                  <Paperclip className="w-4 h-4" />
                </button>
                
                <button
                  type="submit"
                  disabled={isSending || (!inputVal.trim() && attachedFiles.length === 0)}
                  className="p-1.5 bg-[#7C3AED] hover:bg-[#6D28D9] disabled:bg-slate-100 text-white disabled:text-[#9CA3AF] rounded-lg cursor-pointer transition-colors shadow-sm flex items-center justify-center"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </form>
          
          {/* Suggested Questions below input */}
          {activeSession && activeSession.messages.length > 0 && suggestedQuestions.length > 0 && (
            <div className="flex items-center gap-2 overflow-x-auto py-2 mt-2 no-scrollbar">
              <span className="text-[10px] uppercase font-bold text-[#9CA3AF] tracking-wider whitespace-nowrap">Suggested:</span>
              <div className="flex gap-2">
                {suggestedQuestions.slice(0, 3).map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSuggestionClick(q)}
                    className="text-[11px] font-bold px-3 py-1 bg-white hover:bg-[#F3E8FF]/20 text-[#6B7280] hover:text-[#7C3AED] border border-[#E5E7EB] hover:border-purple-200 rounded-full transition-all duration-150 cursor-pointer whitespace-nowrap"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Column 3: Context Panel (Width: 350px) */}
      <div className="w-[350px] bg-white border border-[#E5E7EB] rounded-[20px] shadow-sm p-4 overflow-y-auto flex-shrink-0 flex flex-col gap-6">
        {/* KPI Panel */}
        <div>
          <span className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block mb-3">Current Stats</span>
          <div className="grid grid-cols-1 gap-3">
            {dashboardData?.kpis.filter(kpi => kpi.id !== 'aov').map((kpi) => (
              <div key={kpi.id} className="border border-[#E5E7EB] p-3 rounded-xl shadow-sm bg-slate-50/50 flex items-center justify-between">
                <div>
                  <span className="text-[11px] font-semibold text-[#6B7280]">{kpi.title}</span>
                  <p className="text-base font-extrabold text-[#111827] mt-0.5">{kpi.value}</p>
                </div>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${kpi.isPositive ? 'bg-emerald-50 text-[#10B981]' : 'bg-rose-50 text-[#EF4444]'}`}>
                  {kpi.isPositive ? '+' : ''}{kpi.changePercent}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Experiments */}
        <div>
          <span className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block mb-3">Recent Experiments</span>
          <div className="space-y-2">
            {dashboardData?.recentExperiments.slice(0, 3).map((exp) => (
              <div key={exp.id} className="border border-[#E5E7EB] p-2.5 rounded-xl text-xs hover:border-purple-200 transition-colors">
                <div className="flex justify-between items-center">
                  <span className="font-bold text-[#111827] truncate max-w-[160px]">{exp.name}</span>
                  <span className={`text-[9px] px-2 py-0.5 rounded-full font-bold ${
                    exp.status === 'Completed' ? 'bg-emerald-50 text-[#10B981]' : 'bg-amber-50 text-[#F59E0B]'
                  }`}>
                    {exp.status}
                  </span>
                </div>
                {exp.result && (
                  <p className="text-[10px] text-[#10B981] font-semibold mt-1">Result: {exp.result}</p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Uploaded Files */}
        <div>
          <span className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block mb-3 font-bold">Uploaded Files</span>
          <div className="space-y-2">
            {[
              { name: 'churn-analytics-q2.csv', size: '2.4 MB' },
              { name: 'checkout-flow-friction.pdf', size: '1.2 MB' },
            ].map((file, i) => (
              <div key={i} className="flex items-center justify-between p-2 border border-[#E5E7EB] rounded-xl text-xs bg-slate-50/50">
                <div className="flex items-center gap-2 truncate">
                  <FileText className="w-4 h-4 text-[#7C3AED] flex-shrink-0" />
                  <span className="font-semibold text-[#111827] truncate">{file.name}</span>
                </div>
                <span className="text-[10px] text-[#9CA3AF] font-bold whitespace-nowrap">{file.size}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Active Data Sources */}
        <div>
          <span className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block mb-3">Active Data Sources</span>
          <div className="space-y-2">
            {[
              { name: 'Shopify Connector', status: 'Connected', icon: Layers },
              { name: 'Google Analytics V4', status: 'Streaming', icon: TrendingUp },
            ].map((source, i) => (
              <div key={i} className="flex items-center justify-between p-2 border border-[#E5E7EB] rounded-xl text-xs bg-white hover:border-purple-200 transition-colors">
                <div className="flex items-center gap-2">
                  <source.icon className="w-3.5 h-3.5 text-[#7C3AED]" />
                  <span className="font-semibold text-[#111827]">{source.name}</span>
                </div>
                <span className="text-[9px] bg-emerald-50 text-[#10B981] font-bold px-2 py-0.5 rounded-full">{source.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
