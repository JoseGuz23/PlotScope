import React from 'react';
import { ArrowRight, BrainCircuit, Globe, Zap, Layers, Scale, Users, ShieldCheck } from 'lucide-react';

function App() {
  return (
    <div className="min-h-screen bg-theme-bg text-theme-text font-sans selection:bg-theme-primary selection:text-white">
      {/* Corporate Navigation */}
      <nav className="bg-theme-bg/95 backdrop-blur-none border-b border-theme-border sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="flex justify-between h-20 items-center">
            {/* LOGO - LYA Style */}
            <div className="flex items-baseline gap-3 group select-none">
              <span className="font-serif text-3xl font-bold text-white tracking-tight group-hover:text-theme-primary transition-colors">
                PlotScope
              </span>
              <span className="hidden md:block w-px h-6 bg-theme-subtle mx-2"></span>
              <span className="hidden md:block font-mono text-xs text-theme-primary font-bold uppercase tracking-widest pt-1">
                Foundational AI Solutions
              </span>
            </div>

            <div className="hidden md:flex items-center space-x-12">
              <a href="#mission" className="text-xs font-bold uppercase tracking-widest text-theme-subtle hover:text-white transition-colors">Mission</a>
              <a href="#technology" className="text-xs font-bold uppercase tracking-widest text-theme-subtle hover:text-white transition-colors">Technology</a>
              <a href="#portfolio" className="text-xs font-bold uppercase tracking-widest text-theme-subtle hover:text-white transition-colors">Portfolio</a>
            </div>
            <div>
                <a href="https://lya.plotscope.net" className="text-sm font-bold text-theme-primary hover:text-white transition-colors flex items-center gap-2 uppercase tracking-wide">
                    Launch LYA <ArrowRight size={14} />
                </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section - The Problem: The Middle */}
      <section className="relative pt-32 pb-32 lg:pt-48 lg:pb-48 border-b border-theme-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
          <div className="max-w-4xl">
            <h1 className="font-editorial text-5xl md:text-7xl text-white mb-8 leading-tight">
              Solving the Context Gap.
            </h1>
            <p className="text-xl md:text-2xl text-theme-subtle font-light max-w-3xl leading-relaxed mb-12">
              We build robust AI infrastructures capable of processing massive information streams without loss. 
              Eliminating the "middle" where context disappears.
            </p>
            <div className="flex gap-6">
                <a href="#mission" className="bg-theme-text text-black px-8 py-4 font-bold uppercase tracking-wider text-sm hover:bg-theme-primary transition-colors">
                    Our Vision
                </a>
                <a href="#portfolio" className="border border-theme-subtle text-theme-text px-8 py-4 font-bold uppercase tracking-wider text-sm hover:bg-theme-subtle/10 transition-colors">
                    View Solutions
                </a>
            </div>
          </div>
        </div>
      </section>

      {/* Corporate Pillars (Mission) */}
      <section id="mission" className="py-24 bg-theme-paper border-b border-theme-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="mb-16">
                <h2 className="text-theme-primary font-mono text-xs font-bold uppercase tracking-widest mb-4">Core Philosophy</h2>
                <h3 className="font-editorial text-4xl text-white max-w-2xl">
                    Democratization, Ethics, and Performance.
                </h3>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
                {/* Pillar 1: Robustness */}
                <div className="p-8 border border-theme-border bg-theme-bg hover:border-theme-primary/50 transition-colors">
                    <Layers className="w-10 h-10 text-theme-primary mb-6" />
                    <h4 className="text-lg font-bold text-white mb-4 uppercase tracking-wide">Infinite Context</h4>
                    <p className="text-theme-subtle leading-relaxed">
                        The biggest challenge in AI is memory retention. Our solutions are engineered to maintain absolute context coherence across extensive datasets, ensuring no detail is lost in the "middle".
                    </p>
                </div>

                {/* Pillar 2: Democratization */}
                <div className="p-8 border border-theme-border bg-theme-bg hover:border-theme-primary/50 transition-colors">
                    <Users className="w-10 h-10 text-theme-primary mb-6" />
                    <h4 className="text-lg font-bold text-white mb-4 uppercase tracking-wide">Access for All</h4>
                    <p className="text-theme-subtle leading-relaxed">
                        Professional editing and development tools shouldn't be a luxury. We democratize access to advanced intelligence, empowering new writers and developers regardless of budget.
                    </p>
                </div>

                {/* Pillar 3: Ethical Model */}
                <div className="p-8 border border-theme-border bg-theme-bg hover:border-theme-primary/50 transition-colors">
                    <ShieldCheck className="w-10 h-10 text-theme-primary mb-6" />
                    <h4 className="text-lg font-bold text-white mb-4 uppercase tracking-wide">Client-Centric</h4>
                    <p className="text-theme-subtle leading-relaxed">
                        We reject predatory consumption models. Our profitability is strictly tied to user satisfaction and value generation, maximizing the product's utility, not the user's expense.
                    </p>
                </div>
            </div>
        </div>
      </section>

      {/* Technology Section */}
      <section id="technology" className="py-24 border-b border-theme-border">
         <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="grid md:grid-cols-2 gap-16 items-center">
                <div>
                    <h2 className="font-editorial text-4xl text-white mb-6">Cognitive Architecture</h2>
                    <p className="text-lg text-theme-subtle mb-6">
                        PlotScope does not simply wrap existing models. We build cognitive architectures that orchestrate multiple LLMs (Gemini, Claude) to verify, cross-reference, and synthesize information with human-like reasoning.
                    </p>
                    <ul className="space-y-4">
                        <li className="flex items-center gap-3 text-theme-text font-bold">
                            <BrainCircuit size={20} className="text-theme-primary" />
                            Multi-Model Synthesis
                        </li>
                        <li className="flex items-center gap-3 text-theme-text font-bold">
                            <Scale size={20} className="text-theme-primary" />
                            Contextual Integrity Verification
                        </li>
                        <li className="flex items-center gap-3 text-theme-text font-bold">
                            <Zap size={20} className="text-theme-primary" />
                            Low-Latency Inference
                        </li>
                    </ul>
                </div>
                <div className="bg-theme-paper p-1 border border-theme-border">
                    <div className="bg-theme-bg h-64 md:h-96 w-full flex items-center justify-center relative overflow-hidden">
                        <div className="absolute inset-0 grid grid-cols-6 grid-rows-6 gap-px opacity-20">
                            {Array.from({ length: 36 }).map((_, i) => (
                                <div key={i} className="bg-theme-subtle/30"></div>
                            ))}
                        </div>
                        <div className="relative z-10 text-center">
                             <span className="font-mono text-theme-primary text-xs uppercase tracking-[0.5em] block mb-2">SYSTEM STATUS</span>
                             <span className="font-editorial text-5xl text-white">OPERATIONAL</span>
                        </div>
                    </div>
                </div>
            </div>
         </div>
      </section>

      {/* Portfolio: LYA */}
      <section id="portfolio" className="py-24 bg-theme-paper">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="flex flex-col md:flex-row justify-between items-end mb-12">
                <div>
                    <h2 className="text-theme-primary font-mono text-xs font-bold uppercase tracking-widest mb-2">Flagship Product</h2>
                    <h3 className="font-editorial text-4xl text-white">LYA Platform</h3>
                </div>
                <div className="mt-4 md:mt-0">
                    <a href="https://lya.plotscope.net" className="text-white hover:text-theme-primary transition-colors flex items-center gap-2 font-bold uppercase tracking-wider text-sm">
                        Visit LYA Website <ArrowRight size={16} />
                    </a>
                </div>
            </div>

            <div className="border border-theme-border bg-theme-bg p-8 md:p-12">
                <div className="grid md:grid-cols-2 gap-12">
                    <div>
                        <h4 className="text-2xl font-bold text-white mb-4">The Logic Yield Assistant</h4>
                        <p className="text-theme-subtle mb-6 leading-relaxed">
                            LYA is the embodiment of our mission. A professional development editor that brings advanced analysis and structural guidance to writers. By utilizing our proprietary Context Preservation Engine, LYA remembers every detail of a manuscript, offering insights that traditional tools miss.
                        </p>
                        <div className="flex gap-4 mb-8">
                            <div className="px-3 py-1 border border-theme-border text-xs text-theme-subtle uppercase tracking-wider">Gemini Pro</div>
                            <div className="px-3 py-1 border border-theme-border text-xs text-theme-subtle uppercase tracking-wider">Claude 3.5</div>
                            <div className="px-3 py-1 border border-theme-border text-xs text-theme-subtle uppercase tracking-wider">PlotScope Core</div>
                        </div>
                        <a href="https://lya.plotscope.net" className="inline-block bg-theme-primary text-white px-6 py-3 font-bold uppercase tracking-wider text-xs hover:bg-theme-primary-hover transition-colors">
                            Start Editing with LYA
                        </a>
                    </div>
                    <div className="flex flex-col justify-center border-l border-theme-border pl-12">
                         <div className="space-y-6">
                            <div>
                                <h5 className="text-white font-bold mb-1">Advanced Development</h5>
                                <p className="text-xs text-theme-subtle uppercase tracking-wide">Code & Narrative Structure</p>
                            </div>
                            <div>
                                <h5 className="text-white font-bold mb-1">Accessible Pricing</h5>
                                <p className="text-xs text-theme-subtle uppercase tracking-wide">Professional tools for everyone</p>
                            </div>
                            <div>
                                <h5 className="text-white font-bold mb-1">Data Privacy</h5>
                                <p className="text-xs text-theme-subtle uppercase tracking-wide">Your IP remains yours</p>
                            </div>
                         </div>
                    </div>
                </div>
            </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-theme-bg border-t border-theme-border py-16">
        <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-8">
                <div>
                    <span className="font-serif text-2xl font-bold text-white block mb-2">PlotScope</span>
                    <p className="text-xs text-theme-subtle uppercase tracking-widest">Foundational AI Solutions</p>
                </div>
                <div className="flex gap-8 text-sm font-bold text-theme-subtle">
                    <a href="#" className="hover:text-white transition-colors">Legal</a>
                    <a href="#" className="hover:text-white transition-colors">Privacy</a>
                    <a href="#" className="hover:text-white transition-colors">Contact</a>
                </div>
                <div className="text-xs text-theme-subtle">
                    &copy; 2025 PlotScope Inc.
                </div>
            </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
