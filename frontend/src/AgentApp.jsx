import { useState, useRef, useEffect } from "react";
import { Send, Database, Activity, Terminal, Bot, Search, BarChart3, AlertCircle, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent } from "./components/ui/card";
import clsx from "clsx";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

const API_URL = "https://indic-finsight-seaadeep-998877.loca.lt";

const AGENT_META = {
  filings: { label: "FilingsAgent", icon: Search, color: "text-amber-400", bg: "bg-amber-400/10 border-amber-400/20" },
  market:  { label: "MarketAgent",  icon: Activity, color: "text-emerald-400", bg: "bg-emerald-400/10 border-emerald-400/20" },
  chart:   { label: "ChartAgent",   icon: BarChart3, color: "text-blue-400", bg: "bg-blue-400/10 border-blue-400/20" },
};

function AgentApp() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("checking");
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isLoading]);

  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch(`${API_URL}/health`, { headers: { "Bypass-Tunnel-Reminder": "true" } });
        if (r.ok) setStatus("online");
        else setStatus("offline");
      } catch {
        setStatus("offline");
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  const parseResponse = (content) => {
    const steps = [];
    let finalAnswer = "";
    let chartData = null;
    let chartTitle = "";

    const lines = content.split("\n");
    let currentStep = { thought: "", action: "", input: "", observation: "" };
    let currentKey = null;

    for (const line of lines) {
      if (line.startsWith("Thought:")) {
        if (currentStep.thought || currentStep.action) steps.push({ ...currentStep });
        currentStep = { thought: line.slice(8).trim(), action: "", input: "", observation: "" };
        currentKey = "thought";
      } else if (line.startsWith("Action:")) {
        currentStep.action = line.slice(7).trim();
        currentKey = "action";
      } else if (line.startsWith("Action Input:")) {
        currentStep.input = line.slice(13).trim();
        currentKey = "input";
      } else if (line.startsWith("Observation:")) {
        currentStep.observation = line.slice(12).trim();
        currentKey = "observation";
      } else if (line.startsWith("Result:")) {
        currentStep.observation = line.slice(7).trim();
        currentKey = "observation";
      } else if (line.startsWith("Final Answer:")) {
        finalAnswer = line.slice(13).trim();
        currentKey = "final";
      } else {
        if (currentKey === "thought") currentStep.thought += " " + line.trim();
        else if (currentKey === "observation") currentStep.observation += " " + line.trim();
        else if (currentKey === "final") finalAnswer += " " + line.trim();
      }
    }
    if (currentStep.thought || currentStep.action) steps.push({ ...currentStep });

    // Extract chart data
    for (const step of steps) {
      if (step.action === "plot_bar_chart" && step.input) {
        try {
          const parts = step.input.split("|");
          if (parts.length === 2) {
            chartTitle = parts[0].trim();
            chartData = parts[1].split(",").map(pair => {
              const [k, v] = pair.split("=");
              return { name: k.trim(), value: parseFloat(v) || 0 };
            });
          }
        } catch (e) { /* ignore parse errors */ }
      }
    }

    return { steps, finalAnswer, chartData, chartTitle };
  };

  const handleSend = async () => {
    if (!query.trim() || status !== "online") return;
    const userMsg = { role: "user", content: query };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setQuery("");

    try {
      const r = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Bypass-Tunnel-Reminder": "true" },
        body: JSON.stringify({ text: userMsg.content, history: messages }),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      if (data.history?.length > 0) {
        const combined = data.history.map(m => m.content).join("\n");
        const agentsUsed = data.history[0]?.agents_used || [];
        setMessages(prev => [...prev, { role: "assistant", content: combined, agentsUsed }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        role: "assistant",
        error: true,
        content: `Connection failed: ${err.message}. Make sure the Kaggle notebook is running.`,
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const statusColor = status === "online" ? "bg-emerald-500" : status === "checking" ? "bg-amber-500" : "bg-red-500";
  const statusText = status === "online" ? "Connected" : status === "checking" ? "Connecting..." : "Offline";

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
                <span className="flex items-center gap-2 text-slate-400"><Terminal className="w-3.5 h-3.5" /> Compute</span>
                <span className="text-purple-400 text-[10px] font-medium">T4 GPU</span>
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
          <span className="text-xs text-slate-600 ml-auto font-mono">gemma-2-2b-it</span>
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
                    "Get RELIANCE.NS stock price",
                    "Show a chart of Reliance segment revenues",
                  ].map((q, i) => (
                    <button
                      key={i}
                      onClick={() => { setQuery(q); }}
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
                  <div className="w-full max-w-[90%] space-y-3">
                    {/* Agent badges */}
                    {msg.agentsUsed?.length > 0 && (
                      <div className="flex items-center gap-1.5">
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

                    {(() => {
                      const { steps, finalAnswer, chartData, chartTitle } = parseResponse(msg.content);
                      return (
                        <>
                          {/* Reasoning steps */}
                          {steps.length > 0 && (
                            <details className="group">
                              <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-300 transition-colors flex items-center gap-1.5">
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                {steps.length} reasoning step{steps.length !== 1 ? "s" : ""}
                              </summary>
                              <div className="mt-2 space-y-2 pl-1 border-l border-white/[0.06]">
                                {steps.map((step, idx) => (
                                  <div key={idx} className="pl-3 text-xs font-mono text-slate-500 space-y-1">
                                    {step.thought && <div><span className="text-purple-400">Thought:</span> {step.thought}</div>}
                                    {step.action && <div><span className="text-blue-400">Action:</span> {step.action}({step.input})</div>}
                                    {step.observation && <div><span className="text-emerald-400">Result:</span> {step.observation}</div>}
                                  </div>
                                ))}
                              </div>
                            </details>
                          )}

                          {/* Answer */}
                          <div className="bg-white/[0.03] border border-white/[0.06] px-5 py-4 rounded-lg text-sm leading-relaxed">
                            {finalAnswer || msg.content}
                          </div>

                          {/* Chart */}
                          {chartData?.length > 0 && (
                            <div className="bg-white/[0.03] border border-white/[0.06] p-5 rounded-lg">
                              <h4 className="text-xs font-medium text-slate-400 mb-4 text-center">{chartTitle}</h4>
                              <div className="h-56">
                                <ResponsiveContainer width="100%" height="100%">
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
                                </ResponsiveContainer>
                              </div>
                            </div>
                          )}
                        </>
                      );
                    })()}
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2.5 text-sm text-slate-500">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Agents working...</span>
              </div>
            )}
          </div>
        </div>

        <div className="p-4 border-t border-white/[0.06] bg-[#0d0d14]">
          <div className="max-w-2xl mx-auto flex gap-2">
            <Input
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleSend()}
              placeholder={status === "online" ? "Ask about Indian financial markets..." : "Waiting for backend..."}
              disabled={status !== "online" || isLoading}
              className="flex-1 bg-white/[0.03] border-white/[0.06] h-11 text-sm placeholder:text-slate-600 focus-visible:ring-1 focus-visible:ring-blue-500/30"
            />
            <Button
              onClick={handleSend}
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
