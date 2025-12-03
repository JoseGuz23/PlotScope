import React from 'react';
import { Link } from 'react-router-dom';

const Layout = ({ children }) => {
  return (
    <div className="flex flex-col min-h-screen bg-theme-bg text-theme-text font-sans antialiased selection:bg-theme-primary selection:text-white">
      
      {/* NAVBAR: Estilo Consola de Mando */}
      <nav className="bg-theme-header border-b-2 border-theme-text/10 fixed w-full z-50 h-16 shadow-sm backdrop-blur-sm bg-opacity-95">
        <div className="max-w-7xl mx-auto px-6 h-full flex justify-between items-center">
          
          {/* Identidad de la Herramienta */}
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <span className="text-2xl font-report-serif font-black tracking-tighter leading-none">LYA</span>
              <span className="text-[0.6rem] font-report-mono uppercase tracking-widest text-theme-subtle">Developmental Core</span>
            </div>
            <span className="h-8 w-px bg-theme-border/50 mx-2"></span>
            <div className="hidden md:flex gap-6">
                <Link to="/" className="text-xs font-bold font-report-mono uppercase tracking-widest text-theme-primary hover:text-theme-text transition-colors">Dashboard</Link>
                <Link to="/projects" className="text-xs font-bold font-report-mono uppercase tracking-widest text-theme-subtle hover:text-theme-text transition-colors">Manuscritos</Link>
                <Link to="/api" className="text-xs font-bold font-report-mono uppercase tracking-widest text-theme-subtle hover:text-theme-text transition-colors">API Logs</Link>
            </div>
          </div>

          {/* Indicador de Operación */}
          <button className="bg-theme-text text-white text-xs font-report-mono font-bold px-4 py-2 hover:bg-theme-primary transition-all shadow-sm flex items-center gap-2">
            <span>+ NUEVO PROYECTO</span>
          </button>
        </div>
      </nav>

      {/* CONTENIDO PRINCIPAL */}
      <main className="flex-grow pt-28 pb-16 max-w-7xl mx-auto w-full px-6">
        {children}
      </main>

      {/* FOOTER TÉCNICO (STATUS BAR) - Tipo VS Code */}
      <footer className="fixed bottom-0 w-full bg-theme-text text-theme-bg h-8 border-t border-theme-subtle flex items-center justify-between px-4 text-[10px] font-report-mono z-40">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-theme-primary animate-pulse"></span>
            ORCHESTRATOR: ONLINE
          </span>
          <span className="opacity-50">|</span>
          <span>AZURE REGION: US-EAST-2</span>
          <span className="opacity-50">|</span>
          <span>LATENCY: 45ms</span>
        </div>
        <div className="flex items-center gap-4 opacity-80">
          <span>MEM: 24%</span>
          <span>v4.1.2-stable</span>
        </div>
      </footer>
    </div>
  );
};

export default Layout;