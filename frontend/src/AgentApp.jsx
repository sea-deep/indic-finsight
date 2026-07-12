import { useState, useRef, useEffect } from "react";
import { Send, Database, Activity, Terminal, Bot, Search, BarChart3, AlertCircle, Loader2, CheckCircle2, Globe, Calculator, FileText } from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent } from "./components/ui/card";
import clsx from "clsx";
import ReactMarkdown from 'react-markdown';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

const API_URL = "https://indic-finsight-seaadeep-998877.loca.lt";

const AGENT_META = {
  filings: { label: "FilingsAgent", icon: Search, color: "text-amber-400", bg: "bg-amber-400/10 border-amber-400/20" },
  market:  { label: "MarketAgent",  icon: Activity, color: "text-emerald-400", bg: "bg-emerald-400/10 border-emerald-400/20" },
  chart:   { label: "ChartAgent",   icon: BarChart3, color: "text-blue-400", bg: "bg-blue-400/10 border-blue-400/20" },
  web:     { label: "WebAgent",     icon: Globe, color: "text-purple-400", bg: "bg-purple-400/10 border-purple-400/20" },
  math:    { label: "MathAgent",    icon: Calculator, color: "text-pink-400", bg: "bg-pink-400/10 border-pink-400/20" },
  summary: { label: "SummaryAgent", icon: FileText, color: "text-indigo-400", bg: "bg-indigo-400/10 border-indigo-400/20" },
};

const CHART_COLORS = ["#60a5fa", "#34d399", "#fbbf24", "#f87171", "#c084fc", "#a78bfa"];

function AgentApp() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("checking");
  const [modelName, setModelName] = useState("Waiting for Kernel...");
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isLoading]);

  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch(`${API_URL}/health`, { headers: { "Bypass-Tunnel-Reminder": "true" } });
        if (r.ok) {
          setStatus("online");
          const data = await r.json();
          if (data.model) setModelName(data.model);
        }
        else setStatus("offline");
      } catch {
        setStatus("offline");
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  const sendMessage = async (text) => {
    if (!text.trim() || status !== "online") return;
    const userMsg = { role: "user", content: text };
    
    // Create placeholder for assistant response
    const assistantMsg = { 
        role: "assistant", 
        content: "", 
        steps: [], 
        agentsUsed: [], 
        options: [],
        isStreaming: true
    };
    
    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);
    if (text === query) setQuery("");

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Bypass-Tunnel-Reminder": "true" },
        body: JSON.stringify({ text: userMsg.content, history: messages }), // history doesn't include the current query
      });
      
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let currentAssistantMsg = { ...assistantMsg };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunkStr = decoder.decode(value, { stream: true });
        const lines = chunkStr.split("\n");
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === "step") {
                currentAssistantMsg.steps.push({
                    agent: data.agent,
                    thought: data.thought,
                    action: data.tool,
                    input: data.arguments ? JSON.stringify(data.arguments) : "",
                    observation: ""
                });
              } else if (data.type === "info") {
                  currentAssistantMsg.steps.push({
                      thought: data.message,
                      isInfo: true
                  });
              } else if (data.type === "observation") {
                if (currentAssistantMsg.steps.length > 0) {
                    currentAssistantMsg.steps[currentAssistantMsg.steps.length - 1].observation = data.observation;
                }
              } else if (data.type === "result") {
                  if (!currentAssistantMsg.steps.length || currentAssistantMsg.steps[currentAssistantMsg.steps.length - 1].observation) {
                      currentAssistantMsg.steps.push({
                          agent: data.agent,
                          thought: "Finished task.",
                          observation: data.result
                      });
                  } else {
                      currentAssistantMsg.steps[currentAssistantMsg.steps.length - 1].observation = data.result;
                  }
              } else if (data.type === "error") {
                  if (currentAssistantMsg.steps.length > 0) {
                    currentAssistantMsg.steps[currentAssistantMsg.steps.length - 1].observation = "Error: " + data.error;
                  } else {
                    currentAssistantMsg.content = "Server Error: " + data.error;
                    currentAssistantMsg.error = true;
                    currentAssistantMsg.isStreaming = false;
                  }
              } else if (data.type === "final_answer") {
                  currentAssistantMsg.content = data.content;
                  currentAssistantMsg.options = data.options || [];
                  currentAssistantMsg.agentsUsed = data.agents_used || [];
                  currentAssistantMsg.isStreaming = false;
              }
              
              setMessages(prev => {
                  const newMsgs = [...prev];
                  newMsgs[newMsgs.length - 1] = { ...currentAssistantMsg };
                  return newMsgs;
              });
              
            } catch (e) {
                console.error("Error parsing SSE JSON:", e);
            }
          }
        }
      }
      
      currentAssistantMsg.isStreaming = false;
      setMessages(prev => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1] = { ...currentAssistantMsg };
          return newMsgs;
      });
      
    } catch (err) {
      setMessages(prev => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1] = {
              role: "assistant",
              error: true,
              content: `Connection failed: ${err.message}. Make sure the Kaggle notebook is running.`
          };
          return newMsgs;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const statusColor = status === "online" ? "bg-emerald-500" : status === "checking" ? "bg-amber-500" : "bg-red-500";
  const statusText = status === "online" ? "Connected" : status === "checking" ? "Connecting..." : "Offline";

  const renderChart = (steps) => {
    let chartData = null;
    let chartTitle = "";
    let chartType = "bar";
    
    for (const step of steps || []) {
      if (step.action === "plot_chart" && step.input) {
        try {
          const parsedArgs = JSON.parse(step.input);
          const typeTitleData = parsedArgs.type_title_data || "";
          const parts = typeTitleData.split("|");
          if (parts.length === 3) {
            chartType = parts[0].trim().toLowerCase();
            chartTitle = parts[1].trim();
            chartData = parts[2].split(",").map(pair => {
              const [k, v] = pair.split("=");
              return { 
                name: k ? k.trim() : "", 
                value: v ? parseFloat(v.replace(/[^0-9.-]+/g, '')) || 0 : 0 
              };
            });
          }
        } catch (e) { /* ignore parse errors */ }
      }
    }
    
    if (!chartData || chartData.length === 0) return null;
    
    return (
        <div className="bg-white/[0.03] border border-white/[0.06] p-5 rounded-lg mt-3">
          <h4 className="text-xs font-medium text-slate-300 mb-4 text-center">{chartTitle}</h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              {chartType === "pie" ? (
                <PieChart>
                  <Pie 
                    data={chartData} 
                    dataKey="value" 
                    nameKey="name" 
                    cx="50%" cy="50%" 
                    innerRadius={60}
                    outerRadius={90} 
                    fill="#60a5fa" 
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: "#141420", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "6px", fontSize: "12px" }}
                    itemStyle={{ color: "#fff" }}
                  />
                </PieChart>
              ) : chartType === "line" ? (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="name" stroke="#525252" fontSize={11} tickLine={false} />
                  <YAxis stroke="#525252" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#141420", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "6px", fontSize: "12px" }}
                  />
                  <Line type="monotone" dataKey="value" stroke="#34d399" strokeWidth={2} dot={{ fill: "#34d399", r: 4 }} />
                </LineChart>
              ) : (
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="name" stroke="#525252" fontSize={11} tickLine={false} />
                  <YAxis stroke="#525252" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#141420", border: "1px solid rgba(255,255,255,0.06)", borderRadius: "6px", fontSize: "12px" }}
                    cursor={{ fill: "rgba(255,255,255,0.02)" }}
                  />
                  <Bar dataKey="value" fill="#60a5fa" radius={[3, 3, 0, 0]} />
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
        </div>
    );
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-100 flex font-sans">
      {/* Sidebar */}
      <aside className="w-72 border-r border-white/[0.06] p-5 flex-col gap-6 hidden md:flex bg-[#0d0d14]">
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-white">Indic-FinSight</h1>
          <p className="text-xs text-slate-500 mt-1">Multi-Agent Financial Analyst</p>
        </div>

        <div className="space-y-3">
          <h2 className="text-[11px] font-medium text-slate-500 uppercase tracking-widest">System</h2>
          <Card className="bg-white/[0.02] border-white/[0.06]">
            <CardContent className="p-3 space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-slate-400"><Database className="w-3.5 h-3.5" /> Vector DB</span>
                <span className="text-emerald-400 text-[10px] font-medium">Ready</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-slate-400"><Activity className="w-3.5 h-3.5" /> Market Feed</span>
                <span className="text-emerald-400 text-[10px] font-medium">Live</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-slate-400"><Globe className="w-3.5 h-3.5" /> Web Search</span>
                <span className="text-blue-400 text-[10px] font-medium">Enabled</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 text-slate-400"><Terminal className="w-3.5 h-3.5" /> Compute</span>
                <span className="text-purple-400 text-[10px] font-medium">T4 GPU x2</span>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-3">
          <h2 className="text-[11px] font-medium text-slate-500 uppercase tracking-widest">Agents</h2>
          <div className="space-y-1.5">
            {Object.entries(AGENT_META).map(([key, meta]) => (
              <div key={key} className={`flex items-center gap-2 text-xs px-3 py-2 rounded border ${meta.bg}`}>
                <meta.icon className={`w-3.5 h-3.5 ${meta.color}`} />
                <span className={meta.color}>{meta.label}</span>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col h-screen">
        <header className="h-12 border-b border-white/[0.06] flex items-center px-5 gap-3 bg-[#0d0d14]">
          <div className={`w-2 h-2 rounded-full ${statusColor} animate-pulse`} />
          <span className="text-xs text-slate-500">{statusText}</span>
          <span className="text-xs text-slate-600 ml-auto font-mono">{modelName}</span>
        </header>

        <div className="flex-1 overflow-y-auto p-5" ref={scrollRef}>
          <div className="max-w-2xl mx-auto space-y-6">
            {messages.length === 0 && (
              <div className="text-center mt-24 space-y-3">
                <Bot className="w-10 h-10 mx-auto text-slate-700" />
                <p className="text-sm text-slate-600">Ask a question about Indian financial markets.</p>
                <div className="flex flex-wrap justify-center gap-2 mt-4">
                  {[
                    "What are the supply chain risks for Reliance?",
                    "Search the web for latest Tata Motors news",
                    "Show a pie chart of Reliance segment revenues",
                  ].map((q, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(q)}
                      className="text-xs px-3 py-1.5 rounded border border-white/[0.06] text-slate-400 hover:text-white hover:border-white/[0.12] transition-colors"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={clsx("flex flex-col", msg.role === "user" ? "items-end" : "items-start")}>
                {msg.role === "user" ? (
                  <div className="bg-white/[0.05] border border-white/[0.06] px-4 py-2.5 rounded-lg text-sm max-w-[80%]">
                    {msg.content}
                  </div>
                ) : msg.error ? (
                  <div className="flex items-start gap-2.5 bg-red-500/5 border border-red-500/10 px-4 py-3 rounded-lg text-sm text-red-400 max-w-[90%]">
                    <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                    <span>{msg.content}</span>
                  </div>
                ) : (
                  <div className="w-full max-w-[90%] space-y-3 animate-fade-in">
                    {/* Agent badges */}
                    {msg.agentsUsed?.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {msg.agentsUsed.map(a => {
                          const meta = AGENT_META[a];
                          return meta ? (
                            <span key={a} className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded border ${meta.bg} ${meta.color}`}>
                              <meta.icon className="w-3 h-3" />{meta.label}
                            </span>
                          ) : null;
                        })}
                      </div>
                    )}

                    {/* Reasoning steps */}
                    {msg.steps?.length > 0 && (
                    <details className="group" open={msg.isStreaming}>
                        <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-300 transition-colors flex items-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        {msg.steps.length} agent event{msg.steps.length !== 1 ? "s" : ""} {msg.isStreaming && <Loader2 className="w-3 h-3 animate-spin inline ml-1" />}
                        </summary>
                        <div className="mt-2 space-y-2 pl-1 border-l border-white/[0.06]">
                        {msg.steps.map((step, idx) => {
                            const meta = AGENT_META[step.agent] || {};
                            return (
                                <div key={idx} className="pl-3 text-xs font-mono text-slate-500 space-y-1">
                                    {step.isInfo ? (
                                        <div className="font-semibold text-purple-400 italic">{step.thought}</div>
                                    ) : (
                                        <>
                                            <div className={`font-semibold ${meta.color || 'text-slate-400'}`}>[{step.agent?.toUpperCase()}]</div>
                                            {step.thought && <div><span className="text-purple-400">Thought:</span> {step.thought}</div>}
                                            {step.action && <div><span className="text-blue-400">Tool:</span> {step.action}({step.input})</div>}
                                            {step.observation && <div><span className="text-emerald-400">Result:</span> {step.observation.length > 300 ? step.observation.substring(0, 300) + '...' : step.observation}</div>}
                                        </>
                                    )}
                                </div>
                            );
                        })}
                        </div>
                    </details>
                    )}

                    {/* Answer */}
                    {msg.content && (
                        <div className="bg-white/[0.03] border border-white/[0.06] px-5 py-4 rounded-lg text-sm leading-relaxed prose prose-invert prose-p:my-2 prose-ul:my-2 prose-li:my-0 max-w-none">
                        <ReactMarkdown>{msg.content.replace(/\\n/g, '\n')}</ReactMarkdown>
                        </div>
                    )}

                    {/* Chart */}
                    {renderChart(msg.steps)}

                    {/* Options */}
                    {msg.options?.length > 0 && (
                    <div className="mt-4 flex flex-col gap-2">
                        <p className="text-[11px] font-medium text-slate-500 uppercase tracking-widest">Suggested Follow-ups</p>
                        <div className="flex flex-col gap-2">
                        {msg.options.map((opt, idx) => (
                            <button
                            key={idx}
                            onClick={() => sendMessage(opt)}
                            className="text-left text-sm px-4 py-2.5 rounded-lg border border-blue-500/20 bg-blue-500/5 text-blue-300 hover:bg-blue-500/10 hover:border-blue-500/30 transition-all"
                            >
                            {opt}
                            </button>
                        ))}
                        </div>
                    </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="p-4 border-t border-white/[0.06] bg-[#0d0d14]">
          <div className="max-w-2xl mx-auto flex gap-2">
            <Input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && sendMessage(query)}
              placeholder={status === "online" ? "Ask about Indian financial markets..." : "Waiting for backend..."}
              disabled={status !== "online" || isLoading}
              className="flex-1 bg-white/[0.03] border-white/[0.06] h-11 text-sm placeholder:text-slate-600 focus-visible:ring-1 focus-visible:ring-blue-500/30"
            />
            <Button
              onClick={() => sendMessage(query)}
              disabled={status !== "online" || isLoading || !query.trim()}
              className="h-11 w-11 p-0 bg-white/[0.05] border border-white/[0.06] hover:bg-white/[0.08]"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AgentApp;
