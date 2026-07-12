"use client";

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Mic, Send, Volume2, Square, Globe2 } from 'lucide-react';

interface Source {
  source: string;
  chapter: number;
  verse: number;
  sanskrit: string;
}

interface Message {
  role: string;
  content: string;
  sources?: Source[];
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState("English");
  const [isListening, setIsListening] = useState(false);
  const [isPlayingId, setIsPlayingId] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Handle Speech-to-Text
  const toggleListening = () => {
    if (isListening) {
      setIsListening(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Your browser does not support the Web Speech API for voice input.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = language === "English" ? "en-US" : (language === "Hindi" ? "hi-IN" : "en-US");
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    
    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
    };

    recognition.start();
  };

  // Handle Text-to-Speech
  const togglePlayback = (text: string, msgId: number) => {
    if (isPlayingId === msgId) {
      window.speechSynthesis.cancel();
      setIsPlayingId(null);
      return;
    }

    window.speechSynthesis.cancel(); // Stop any current speech
    setIsPlayingId(msgId);

    const utterance = new SpeechSynthesisUtterance(text);
    // Remove markdown asterisks before speaking
    utterance.text = text.replace(/\*/g, '');
    utterance.lang = language === "English" ? "en-US" : (language === "Hindi" ? "hi-IN" : "en-US");
    
    utterance.onend = () => setIsPlayingId(null);
    window.speechSynthesis.speak(utterance);
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    window.speechSynthesis.cancel();
    setIsPlayingId(null);

    const userMessage: Message = { role: "user", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message: userMessage.content, language }),
      });

      const data = await res.json();
      setMessages((prev) => [
        ...prev, 
        { role: "assistant", content: data.response, sources: data.sources }
      ]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev, 
        { role: "assistant", content: "Sorry, the Dharma-Compass server is unreachable." }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex flex-col h-screen text-neutral-200">
      <div className="fixed inset-0 z-[-1] bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-neutral-800 via-[#0a0a0a] to-[#0a0a0a]" />

      <header className="glass p-6 sticky top-0 z-10 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-white flex items-center gap-2">
            <Globe2 className="w-6 h-6 text-yellow-600" /> Dharma-Compass
          </h1>
          <p className="text-sm text-neutral-400 mt-1">IKS Philosophical Synthesis Engine</p>
        </div>
        
        <div className="flex items-center gap-2">
          <label className="text-xs text-neutral-400 uppercase tracking-wider font-semibold">Language</label>
          <select 
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-neutral-800 text-sm text-neutral-200 border border-neutral-700 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-yellow-600 transition-shadow"
          >
            <option value="English">English</option>
            <option value="Hindi">Hindi</option>
            <option value="Sanskrit">Sanskrit</option>
            <option value="Spanish">Spanish</option>
          </select>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-8">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-neutral-500 opacity-60">
            <Globe2 className="w-16 h-16 mb-4 text-neutral-600" />
            <p className="text-lg font-light tracking-wide">Seek ancient wisdom for modern dilemmas.</p>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex flex-col w-full ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className="flex gap-2 items-end group">
              {/* Play Button for Assistant */}
              {msg.role === 'assistant' && (
                <button 
                  onClick={() => togglePlayback(msg.content, idx)}
                  className="p-2 mb-2 rounded-full hover:bg-neutral-800 text-neutral-500 hover:text-yellow-600 transition-colors opacity-0 group-hover:opacity-100"
                  title="Read Aloud"
                >
                  {isPlayingId === idx ? <Square className="w-4 h-4 fill-current" /> : <Volume2 className="w-4 h-4" />}
                </button>
              )}

              {/* Chat Bubble */}
              <div 
                className={`max-w-3xl p-5 md:p-6 rounded-3xl shadow-xl leading-relaxed ${
                  msg.role === 'user' 
                    ? 'bg-neutral-800 text-white rounded-br-sm' 
                    : 'glass text-neutral-200 rounded-bl-sm prose prose-invert'
                }`}
              >
                {msg.role === 'user' ? (
                  msg.content
                ) : (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                )}
              </div>
            </div>
            
            {/* References Section */}
            {msg.sources && msg.sources.length > 0 && (
              <div className="mt-4 ml-10 space-y-3 max-w-3xl">
                <p className="text-xs font-bold text-yellow-600 uppercase tracking-widest">Foundational Scriptures</p>
                {msg.sources.map((src, sIdx) => (
                  <div key={sIdx} className="bg-neutral-900/50 border border-neutral-800 rounded-xl p-4 transition-colors hover:border-neutral-700">
                    <p className="text-sm font-medium text-neutral-300 mb-1">
                      {src.source} {src.philosophy && <span className="text-neutral-500 font-normal">— {src.philosophy}</span>}
                      {src.chapter !== undefined && src.verse !== undefined && ` — Chapter ${src.chapter}, Verse ${src.verse}`}
                    </p>
                    {src.sanskrit && (
                      <p className="text-sm text-neutral-500 font-serif leading-loose mt-2">
                        {src.sanskrit}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-start">
            <div className="max-w-3xl p-6 glass rounded-3xl rounded-bl-sm animate-pulse flex items-center gap-3">
              <div className="w-2 h-2 bg-yellow-600 rounded-full animate-bounce" style={{animationDelay: '0ms'}}/>
              <div className="w-2 h-2 bg-yellow-600 rounded-full animate-bounce" style={{animationDelay: '150ms'}}/>
              <div className="w-2 h-2 bg-yellow-600 rounded-full animate-bounce" style={{animationDelay: '300ms'}}/>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <footer className="p-4 md:p-6 glass border-t-0 mt-auto">
        <form onSubmit={sendMessage} className="max-w-4xl mx-auto flex gap-3 items-center">
          <button 
            type="button"
            onClick={toggleListening}
            className={`p-4 rounded-full transition-all duration-300 ${
              isListening 
                ? 'bg-red-500/20 text-red-500 animate-pulse shadow-[0_0_15px_rgba(239,68,68,0.5)]' 
                : 'bg-neutral-800 text-neutral-400 hover:bg-neutral-700 hover:text-white'
            }`}
            title="Voice Input"
          >
            <Mic className="w-5 h-5" />
          </button>
          
          <input
            type="text"
            className="flex-1 p-4 rounded-2xl bg-neutral-900/80 border border-neutral-800 text-white placeholder-neutral-500 focus:outline-none focus:border-yellow-600/50 focus:ring-1 focus:ring-yellow-600/50 transition-all shadow-inner"
            placeholder={isListening ? "Listening..." : "Seek guidance..."}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
          />
          
          <button 
            type="submit" 
            disabled={loading || !query.trim()}
            className="p-4 bg-yellow-600 text-white rounded-2xl font-medium hover:bg-yellow-500 disabled:opacity-50 disabled:hover:bg-yellow-600 transition-colors shadow-lg shadow-yellow-600/20"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </footer>
    </main>
  );
}
