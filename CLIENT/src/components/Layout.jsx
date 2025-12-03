import React from 'react';
import { Link } from 'react-router-dom';

const Layout = ({ children }) => {
  return (
    // No necesitamos bg-theme-bg aquí porque ya está en el body via index.css
    <div className="min-h-screen"> 
      
      {/* NAVBAR: Réplica exacta de syltest.html */}
      <nav className="bg-theme-header shadow-md border-b-2 border-theme-border/50 fixed w-full z-10">
        <div className="max-w-7xl mx-auto px-8">
            <div className="flex justify-between h-16 items-center">
                
                {/* Logo e Identidad */}
                <div className="flex items-center space-x-2">
                    <span className="text-2xl font-report-serif font-extrabold text-theme-text">LYA</span>
                    <span className="text-xs text-theme-subtle font-report-mono">v4.1.0 (Developmental Editor)</span>
                </div>
                
                {/* Links de Navegación usando las clases .nav-link definidas en CSS */}
                <div className="flex space-x-4">
                    <Link to="/" className="nav-link text-theme-primary border-b-2 border-theme-primary">
                      Dashboard
                    </Link>
                    <Link to="/library" className="nav-link text-theme-subtle hover:text-theme-text">
                      Biblioteca
                    </Link>
                    <Link to="/config" className="nav-link text-theme-subtle hover:text-theme-text">
                      Configuración IA
                    </Link>
                    <Link to="/api" className="nav-link text-theme-subtle hover:text-theme-text">
                      API Console
                    </Link>
                </div>
                
                {/* Botón de Acción */}
                <div className="flex items-center">
                    <button className="bg-theme-primary text-white text-xs font-bold px-4 py-2 rounded-sm uppercase tracking-wider hover:bg-theme-primary/80 transition duration-150">
                        Compilar & Desplegar
                    </button>
                </div>
            </div>
        </div>
      </nav>

      {/* Contenedor Principal: Padding top 24 para compensar el navbar fixed */}
      <main className="pt-24 max-w-7xl mx-auto px-8 pb-12">
        {children}
      </main>
    </div>
  );
};

export default Layout;