import React from 'react';
import { User, Sparkles, Plus, Check, AlertTriangle, ShieldCheck, HelpCircle } from 'lucide-react';
import { ChatMessage as ChatMessageType, Hypothesis } from '../types/ai-workspace';

interface ChatMessageProps {
  message: ChatMessageType;
  onSuggestionClick?: (text: string) => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onSuggestionClick }) => {
  const { role, content, timestamp, suggestions, hypothesis, files } = message;
  const isUser = role === 'user';

  return (
    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} mb-6 max-w-4xl w-full`}>
      <div className={`flex items-start gap-3 w-full ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center shadow-sm ${
            isUser ? 'bg-[#F3E8FF] text-[#7C3AED]' : 'bg-[#7C3AED] text-white'
          }`}
        >
          {isUser ? <User className="w-4 h-4" /> : <Sparkles className="w-4 h-4" />}
        </div>

        {/* Message Bubble */}
        <div className="flex flex-col max-w-[85%]">
          <div className="flex items-center gap-2 mb-1 px-1">
            <span className="text-xs font-semibold text-slate-700">
              {isUser ? 'You' : 'AI Assistant'}
            </span>
            <span className="text-[10px] text-slate-400 font-medium">{timestamp}</span>
          </div>

          <div
            className={`rounded-2xl px-5 py-3.5 shadow-sm border text-sm leading-relaxed whitespace-pre-line ${
              isUser
                ? 'bg-[#7C3AED] text-white border-[#6D28D9] rounded-tr-none'
                : 'bg-white text-slate-800 border-slate-100 rounded-tl-none'
            }`}
          >
            {content}

            {/* Attached files rendering */}
            {files && files.length > 0 && (
              <div className="mt-3 pt-3 border-t border-purple-400/30 flex flex-wrap gap-2">
                {files.map((f, i) => (
                  <div key={i} className="flex items-center gap-1.5 text-xs bg-purple-800/40 text-purple-50 border border-purple-500/20 px-2 py-1 rounded-md">
                    <span className="truncate max-w-[150px] font-medium">{f.name}</span>
                    <span className="opacity-60 text-[10px]">({f.size})</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Hypothesis Visual Card */}
          {!isUser && hypothesis && (
            <div className="mt-4 bg-white border border-slate-100 rounded-xl shadow-md p-5 w-full">
              <div className="flex items-center justify-between border-b border-slate-50 pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <div className="bg-amber-50 text-amber-600 p-1.5 rounded-lg">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Generated Hypothesis</span>
                    <h4 className="text-sm font-bold text-slate-800">{hypothesis.title}</h4>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                    hypothesis.riskLevel === 'High' ? 'bg-rose-50 text-rose-600 border border-rose-100' :
                    hypothesis.riskLevel === 'Medium' ? 'bg-amber-50 text-amber-600 border border-amber-100' :
                    'bg-emerald-50 text-emerald-600 border border-emerald-100'
                  }`}>
                    {hypothesis.riskLevel} Risk
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-500 leading-relaxed mb-4">
                {hypothesis.description}
              </p>

              {/* Confidence Score bar */}
              <div className="mb-4">
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-semibold text-slate-500">Confidence Score</span>
                  <span className="font-bold text-indigo-600">{hypothesis.confidenceScore}%</span>
                </div>
                <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-[#7C3AED] h-full rounded-full transition-all duration-500"
                    style={{ width: `${hypothesis.confidenceScore}%` }}
                  />
                </div>
              </div>

              {/* Supporting vs Contradictory Evidence columns */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 bg-slate-50/50 p-3.5 rounded-xl border border-slate-100">
                <div>
                  <h5 className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider flex items-center gap-1 mb-2">
                    <Check className="w-3.5 h-3.5" />
                    Supporting Evidence
                  </h5>
                  <ul className="space-y-2">
                    {hypothesis.supportingEvidence.map((ev, i) => (
                      <li key={i} className="text-xs text-slate-600 leading-relaxed flex items-start gap-1">
                        <span className="text-emerald-500 mt-0.5">•</span>
                        <span>
                          {ev.text}{' '}
                          {ev.impact && (
                            <span className="text-[9px] font-semibold text-emerald-600 bg-emerald-50 px-1 py-0.2 rounded">
                              {ev.impact}
                            </span>
                          )}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <h5 className="text-[10px] font-bold text-rose-600 uppercase tracking-wider flex items-center gap-1 mb-2">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Contradictory / Nuance
                  </h5>
                  <ul className="space-y-2">
                    {hypothesis.contradictoryEvidence.map((ev, i) => (
                      <li key={i} className="text-xs text-slate-600 leading-relaxed flex items-start gap-1">
                        <span className="text-rose-400 mt-0.5">•</span>
                        <span>
                          {ev.text}{' '}
                          {ev.impact && (
                            <span className="text-[9px] font-semibold text-slate-600 bg-slate-100 px-1 py-0.2 rounded">
                              {ev.impact}
                            </span>
                          )}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Suggested Validation */}
              <div className="mt-4 pt-3 border-t border-slate-100">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Recommended Validation Approach</span>
                <p className="text-xs text-slate-600 font-medium mt-1 leading-relaxed bg-indigo-50/40 p-2.5 rounded border border-indigo-50/50">
                  {hypothesis.suggestedValidation}
                </p>
              </div>
            </div>
          )}

          {/* Suggestions prompt chips */}
          {!isUser && suggestions && suggestions.length > 0 && onSuggestionClick && (
            <div className="flex flex-wrap gap-2 mt-3 pl-1">
              {suggestions.map((s, index) => (
                <button
                  key={index}
                  onClick={() => onSuggestionClick(s)}
                  className="text-xs font-semibold px-3 py-1.5 bg-slate-50 text-[#7C3AED] border border-purple-100 hover:border-purple-200 hover:bg-[#F3E8FF]/40 rounded-full transition-all duration-150 cursor-pointer"
                >
                  {s}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
