import { useNavigate } from "react-router-dom";
import { Button } from "./components/ui/button";
import { ArrowRight, BarChart3, Database, Shield, Zap, Bot, GitBranch } from "lucide-react";

function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-slate-100 font-sans">
      <nav className="border-b border-white/[0.06] bg-[#0a0a0f]/95 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 flex h-14 items-center justify-between">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-400" />
            <span className="text-base font-semibold tracking-tight">Indic-FinSight</span>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              className="text-slate-400 hover:text-white text-xs"
              onClick={() => window.open("https://github.com/seaadeep/indic-finsight", "_blank")}
            >
              GitHub
            </Button>
            <Button size="sm" className="text-xs h-8" onClick={() => navigate("/app")}>
              Launch <ArrowRight className="ml-1.5 h-3 w-3" />
            </Button>
          </div>
        </div>
      </nav>

      <main>
        <section className="container mx-auto px-4 py-28 lg:py-36 flex flex-col items-center text-center gap-6">
          <div className="inline-flex items-center gap-1.5 text-[11px] px-3 py-1 rounded-full border border-white/[0.06] text-slate-500 mb-2">
            <Bot className="w-3 h-3" /> Powered by Gemma 2B on Kaggle T4 GPU
          </div>
          <h1 className="max-w-3xl text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1]">
            Multi-Agent Financial Intelligence
          </h1>
          <p className="max-w-xl text-sm md:text-base text-slate-500 leading-relaxed">
            Autonomous agents parse SEBI filings, fetch live NSE data, and generate
            visualizations — all running on free Kaggle GPUs.
          </p>
          <div className="flex gap-3 mt-3">
            <Button size="lg" className="text-sm h-10 px-6" onClick={() => navigate("/app")}>
              Start Analysis <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button size="lg" variant="outline" className="text-sm h-10 px-6 border-white/[0.06] text-slate-300 hover:text-white"
              onClick={() => window.open("https://github.com/seaadeep/indic-finsight", "_blank")}>
              View Source
            </Button>
          </div>
        </section>

        {/* Architecture */}
        <section className="border-t border-white/[0.06] py-20">
          <div className="container mx-auto px-4 text-center">
            <h2 className="text-lg font-semibold mb-2">How it works</h2>
            <p className="text-sm text-slate-500 mb-10 max-w-md mx-auto">
              Your query is classified, routed to specialized agents, and synthesized into a unified response.
            </p>
            <div className="flex flex-col md:flex-row items-center justify-center gap-3 text-xs">
              {[
                { label: "Your Query", sub: "Natural language" },
                { label: "Intent Router", sub: "Keyword classifier" },
                { label: "Sub-Agents", sub: "Filings · Market · Chart" },
                { label: "Orchestrator", sub: "Gemma 2B synthesis" },
                { label: "Response", sub: "Structured output" },
              ].map((step, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="px-4 py-3 rounded border border-white/[0.06] bg-white/[0.02] min-w-[140px]">
                    <div className="font-medium text-slate-200">{step.label}</div>
                    <div className="text-slate-600 text-[10px] mt-0.5">{step.sub}</div>
                  </div>
                  {i < 4 && <ArrowRight className="w-3.5 h-3.5 text-slate-700 hidden md:block" />}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="border-t border-white/[0.06] bg-white/[0.01] py-20">
          <div className="container mx-auto px-4 grid gap-8 md:grid-cols-3">
            {[
              { icon: Database, title: "RAG Retrieval", desc: "ChromaDB-powered semantic search over earnings transcripts and SEBI filings. Finds relevant context in milliseconds." },
              { icon: GitBranch, title: "Multi-Agent", desc: "Intent-based routing dispatches to FilingsAgent, MarketAgent, or ChartAgent. Each has a focused prompt and toolset." },
              { icon: Shield, title: "Local-First", desc: "All inference runs on Kaggle GPUs. No data leaves the compute environment. Designed for financial data sensitivity." },
            ].map(({ icon: Icon, title, desc }, i) => (
              <div key={i} className="space-y-3">
                <div className="h-9 w-9 rounded border border-white/[0.06] bg-white/[0.02] flex items-center justify-center">
                  <Icon className="h-4 w-4 text-slate-400" />
                </div>
                <h3 className="text-sm font-semibold">{title}</h3>
                <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-white/[0.06] py-6 text-center text-[11px] text-slate-600">
        Indic-FinSight · Kaggle Gemma Hackathon 2026
      </footer>
    </div>
  );
}

export default Landing;
