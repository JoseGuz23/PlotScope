import React from 'react';
import { ArrowRight, Globe, Layers, ShieldCheck, Cpu, Network, ArrowUpRight } from 'lucide-react';

function App() {
  return (
    <div className="min-h-screen bg-theme-bg text-theme-text font-sans selection:bg-theme-primary selection:text-white overflow-x-hidden">
      
      {/* --- CORPORATE NAVIGATION --- */}
      <nav className="border-b border-theme-border bg-theme-bg sticky top-0 z-50">
        <div className="max-w-screen-2xl mx-auto px-6 lg:px-12 h-24 flex justify-between items-center">
          {/* Logo */}
          <div className="flex flex-col">
            <span className="font-serif text-2xl font-bold tracking-tight text-white leading-none">PlotScope</span>
            <span className="text-[10px] uppercase tracking-[0.2em] text-theme-subtle mt-1 font-mono">Foundational Intelligence</span>
          </div>

          {/* Menu */}
          <div className="hidden md:flex items-center gap-12">
             {['Capabilities', 'Impact', 'Research', 'Company'].map((item) => (
               <a key={item} href={`#${item.toLowerCase()}`} className="text-sm font-medium text-theme-subtle hover:text-white transition-colors uppercase tracking-widest">
                 {item}
               </a>
             ))}
          </div>

          {/* Action */}
          <div>
            <a href="https://lya.plotscope.net" className="text-xs font-bold uppercase tracking-widest text-theme-primary hover:text-white transition-colors flex items-center gap-2 border border-theme-border px-6 py-3 hover:border-theme-primary">
               Portfolio Access <ArrowUpRight size={14} />
            </a>
          </div>
        </div>
      </nav>

      {/* --- HERO SECTION: ABSTRACT & VISIONARY --- */}
      <section className="relative min-h-[90vh] flex items-center justify-center border-b border-theme-border overflow-hidden">
        {/* Abstract Background Animation */}
        <div className="absolute inset-0 z-0 opacity-20">
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-theme-primary rounded-full blur-[128px] animate-pulse-slow"></div>
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-theme-secondary rounded-full blur-[128px] animate-pulse-slow" style={{animationDelay: '2s'}}></div>
        </div>
        
        <div className="relative z-10 max-w-screen-xl mx-auto px-6 text-center">
          <h1 className="font-editorial text-6xl md:text-8xl lg:text-9xl text-white mb-8 tracking-tight leading-[0.9]">
            The Architecture <br /> of <span className="text-theme-subtle">Reasoning.</span>
          </h1>
          <p className="font-sans text-xl md:text-2xl text-theme-subtle max-w-3xl mx-auto font-light leading-relaxed">
            PlotScope constructs the cognitive infrastructure required to bridge the gap between generative models and verifiable truth.
          </p>
        </div>
      </section>

      {/* --- STRATEGY / CAPABILITIES --- */}
      <section id="capabilities" className="py-32 border-b border-theme-border">
        <div className="max-w-screen-xl mx-auto px-6 grid md:grid-cols-12 gap-12">
           <div className="md:col-span-4">
              <span className="block font-mono text-xs text-theme-primary uppercase tracking-widest mb-4">Core Capabilities</span>
              <h2 className="font-editorial text-4xl text-white leading-tight">
                Solving the <br/> Context Gap.
              </h2>
           </div>
           <div className="md:col-span-8 grid md:grid-cols-2 gap-16">
              <div>
                 <Network className="w-8 h-8 text-white mb-6" />
                 <h3 className="text-lg font-bold uppercase tracking-wide text-white mb-4">Infinite Context Retention</h3>
                 <p className="text-theme-subtle">
                   We eliminate the "middle-loss" phenomenon in Large Language Models. Our proprietary vector orchestration ensures 99.9% fidelity across massive narrative datasets.
                 </p>
              </div>
              <div>
                 <Cpu className="w-8 h-8 text-white mb-6" />
                 <h3 className="text-lg font-bold uppercase tracking-wide text-white mb-4">Cognitive Synthesis</h3>
                 <p className="text-theme-subtle">
                   Beyond generation, our systems verify. We deploy multi-agent architectures (Gemini + Claude) to cross-reference logic and causality in real-time.
                 </p>
              </div>
           </div>
        </div>
      </section>

      {/* --- PORTFOLIO (LYA) --- */}
      <section id="impact" className="py-32 bg-theme-paper border-b border-theme-border">
         <div className="max-w-screen-xl mx-auto px-6">
            <div className="flex flex-col md:flex-row justify-between items-end mb-20">
               <div>
                 <span className="font-mono text-xs text-theme-primary uppercase tracking-widest mb-4 block">Deployed Solutions</span>
                 <h2 className="font-editorial text-5xl text-white">LYA Platform</h2>
               </div>
               <a href="https://lya.plotscope.net" className="group flex items-center gap-4 text-white mt-8 md:mt-0">
                  <span className="text-sm font-bold uppercase tracking-widest group-hover:text-theme-primary transition-colors">Explore Platform</span>
                  <div className="w-12 h-12 border border-theme-border flex items-center justify-center group-hover:border-theme-primary transition-colors">
                     <ArrowRight size={16} />
                  </div>
               </a>
            </div>

            <div className="grid md:grid-cols-2 gap-0 border border-theme-border">
               <div className="p-12 md:p-16 border-b md:border-b-0 md:border-r border-theme-border hover:bg-theme-bg transition-colors">
                  <h3 className="text-2xl font-bold text-white mb-6">Democratizing Professional Editing</h3>
                  <p className="text-theme-subtle mb-12">
                     LYA creates an accessible layer between complex foundational models and end-users, providing enterprise-grade narrative analysis to independent creators.
                  </p>
                  <ul className="space-y-4 font-mono text-xs uppercase tracking-wider text-theme-subtle">
                     <li className="flex justify-between border-b border-theme-border pb-2">
                        <span>Sector</span>
                        <span className="text-white">Creative Industries</span>
                     </li>
                     <li className="flex justify-between border-b border-theme-border pb-2">
                        <span>Status</span>
                        <span className="text-theme-primary">Active Deployment</span>
                     </li>
                  </ul>
               </div>
               <div className="p-12 md:p-16 flex items-center justify-center bg-black relative overflow-hidden group">
                  {/* Abstract Wireframe Background */}
                  <div className="absolute inset-0 opacity-20 pointer-events-none">
                     {/* Horizontal Lines simulating interface rows */}
                     <div className="absolute top-1/3 left-0 w-full h-px bg-theme-subtle"></div>
                     <div className="absolute top-2/3 left-0 w-full h-px bg-theme-subtle"></div>
                     <div className="absolute bottom-1/4 left-1/4 w-1/2 h-px bg-theme-subtle"></div>
                     
                     {/* Vertical Lines simulating columns */}
                     <div className="absolute top-0 left-1/4 h-full w-px bg-theme-subtle"></div>
                     <div className="absolute top-0 right-1/4 h-full w-px bg-theme-subtle"></div>
                     
                     {/* Code-like blocks */}
                     <div className="absolute top-[38%] left-[28%] w-[15%] h-2 bg-theme-subtle rounded-sm"></div>
                     <div className="absolute top-[42%] left-[28%] w-[25%] h-2 bg-theme-subtle rounded-sm"></div>
                     <div className="absolute top-[46%] left-[28%] w-[20%] h-2 bg-theme-subtle rounded-sm"></div>

                     <div className="absolute bottom-[20%] right-[28%] w-[10%] h-2 bg-theme-subtle rounded-sm opacity-50"></div>
                  </div>
                  
                  {/* Dynamic Glow */}
                  <div className="absolute inset-0 bg-gradient-to-tr from-theme-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>

                  <div className="relative z-10 text-center">
                     <span className="font-editorial text-6xl text-white block mb-2 tracking-tight">LYA</span>
                     <span className="font-mono text-xs text-theme-subtle uppercase tracking-[0.5em] border-t border-theme-subtle/30 pt-4 block">Logic Yield Assistant</span>
                  </div>
               </div>
            </div>
         </div>
      </section>

      {/* --- LEADERSHIP / COMPANY --- */}
      <section id="company" className="py-32 border-b border-theme-border bg-theme-bg">
         <div className="max-w-screen-xl mx-auto px-6">
            <div className="max-w-4xl mx-auto text-center">
                <span className="block font-mono text-xs text-theme-primary uppercase tracking-widest mb-12">Leadership</span>
                
                <div className="mb-12">
                     <h3 className="font-editorial text-5xl md:text-6xl text-white mb-8 leading-tight">
                        "Artificial Intelligence has taught us that elite capabilities must be universally accessible, not a privilege of the few."
                     </h3>
                     <div className="flex flex-col items-center">
                        <div className="w-16 h-1 bg-theme-primary mb-6"></div>
                        <h4 className="text-xl font-bold text-white uppercase tracking-wide">Jose Guzmán</h4>
                        <span className="text-sm text-theme-subtle font-mono">Founder & Executive Director</span>
                     </div>
                </div>

                <p className="text-theme-subtle max-w-2xl mx-auto leading-relaxed text-lg font-light">
                   Writer, Cloud Architect, and AI Enthusiast committed to dismantling the barriers between professional-grade tools and independent creators.
                </p>
            </div>
         </div>
      </section>

      {/* --- CONTACT SECTION --- */}
      <section id="contact" className="py-24 border-b border-theme-border bg-theme-paper">
          <div className="max-w-screen-xl mx-auto px-6 text-center">
              <h2 className="font-editorial text-3xl text-white mb-8">Get in Touch</h2>
              <a href="mailto:JoseA.Guzman@plotscope.net" className="text-2xl md:text-4xl font-bold text-white hover:text-theme-primary transition-colors border-b-2 border-theme-subtle/30 hover:border-theme-primary pb-2">
                  JoseA.Guzman@plotscope.net
              </a>
              <p className="text-theme-subtle mt-8">
                  For inquiries regarding partnerships, press, or portfolio technologies.
              </p>
          </div>
      </section>

      {/* --- INSIGHTS (Newsroom) --- */}
      <section id="research" className="py-32 bg-theme-paper border-b border-theme-border">
         <div className="max-w-screen-xl mx-auto px-6">
            <div className="flex justify-between items-baseline mb-16">
               <h2 className="font-editorial text-4xl text-white">Insights</h2>
               <a href="#" className="text-xs font-bold uppercase tracking-widest text-theme-subtle hover:text-white">View Archive</a>
            </div>
            <div className="grid md:grid-cols-3 gap-12 divide-y md:divide-y-0 md:divide-x divide-theme-border">
               <div className="pt-8 md:pt-0 md:pl-8 first:pl-0">
                  <span className="font-mono text-xs text-theme-primary mb-4 block">Ethics</span>
                  <h3 className="text-xl font-bold text-white mb-4 leading-normal hover:text-theme-subtle cursor-pointer transition-colors">
                     The Moral Imperative of Context Preservation in AI Models.
                  </h3>
                  <span className="text-sm text-theme-subtle">Oct 12, 2025</span>
               </div>
               <div className="pt-8 md:pt-0 md:pl-8">
                  <span className="font-mono text-xs text-theme-primary mb-4 block">Research</span>
                  <h3 className="text-xl font-bold text-white mb-4 leading-normal hover:text-theme-subtle cursor-pointer transition-colors">
                     Moving Beyond Token Limits: A New Approach to Memory.
                  </h3>
                  <span className="text-sm text-theme-subtle">Sep 28, 2025</span>
               </div>
               <div className="pt-8 md:pt-0 md:pl-8">
                  <span className="font-mono text-xs text-theme-primary mb-4 block">Company</span>
                  <h3 className="text-xl font-bold text-white mb-4 leading-normal hover:text-theme-subtle cursor-pointer transition-colors">
                     PlotScope commits to Client-Centric Pricing Models.
                  </h3>
                  <span className="text-sm text-theme-subtle">Aug 15, 2025</span>
               </div>
            </div>
         </div>
      </section>

      {/* --- ROBUST FOOTER --- */}
      <footer className="py-24 bg-theme-bg">
         <div className="max-w-screen-xl mx-auto px-6 grid md:grid-cols-4 gap-12 text-sm">
            <div>
               <span className="font-serif text-2xl font-bold text-white block mb-8">PlotScope</span>
               <address className="not-italic text-theme-subtle leading-loose">
                  Ciudad Juárez<br/>
                  Chihuahua, México<br/>
               </address>
            </div>
            <div>
               <h4 className="font-bold text-white uppercase tracking-widest mb-6">Company</h4>
               <ul className="space-y-4 text-theme-subtle">
                  <li><a href="#" className="hover:text-white transition-colors">About Us</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Press</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
               </ul>
            </div>
            <div>
               <h4 className="font-bold text-white uppercase tracking-widest mb-6">Resources</h4>
               <ul className="space-y-4 text-theme-subtle">
                  <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Research Papers</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Compliance</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
               </ul>
            </div>
            <div>
               <h4 className="font-bold text-white uppercase tracking-widest mb-6">Connect</h4>
               <ul className="space-y-4 text-theme-subtle">
                  <li><a href="#" className="hover:text-white transition-colors">LinkedIn</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">Twitter / X</a></li>
                  <li><a href="#" className="hover:text-white transition-colors">GitHub</a></li>
               </ul>
            </div>
         </div>
         <div className="max-w-screen-xl mx-auto px-6 mt-24 pt-8 border-t border-theme-border flex flex-col md:flex-row justify-between text-xs text-theme-subtle">
            <p>&copy; 2025 PlotScope Inc. All rights reserved.</p>
            <div className="flex gap-8 mt-4 md:mt-0">
               <a href="#" className="hover:text-white">Privacy Policy</a>
               <a href="#" className="hover:text-white">Terms of Service</a>
               <a href="#" className="hover:text-white">Cookie Settings</a>
            </div>
         </div>
      </footer>
    </div>
  );
}

export default App;
