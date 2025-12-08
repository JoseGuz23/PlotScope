// =============================================================================
// Layout.jsx - LAYOUT PRINCIPAL DE SYLPHRENA
// =============================================================================

import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { 
  Home, 
  Plus, 
  Settings, 
  LogOut,
  BookOpen,
  User,
} from 'lucide-react';

const Layout = ({ children }) => {
  const location = useLocation();
  const { user, logout } = useAuth();
  
  // Helper para saber si un link está activo
  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen">
      {/* NAVBAR */}
      <nav className="bg-white shadow-sm border-b border-theme-border fixed w-full z-10">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex justify-between h-16 items-center">
            
            {/* Logo e Identidad */}
            <Link to="/" className="flex items-center space-x-3">
              <BookOpen className="text-theme-primary" size={28} />
              <div>
                <span className="text-xl font-report-serif font-extrabold text-theme-text">
                  SYLPHRENA
                </span>
                <span className="text-[10px] text-theme-subtle font-report-mono block -mt-1">
                  AI Literary Editor
                </span>
              </div>
            </Link>
            
            {/* Links de Navegación */}
            <div className="flex items-center space-x-1">
              <Link 
                to="/" 
                className={`nav-link flex items-center gap-2 ${
                  isActive('/') && location.pathname === '/'
                    ? 'text-theme-primary border-b-2 border-theme-primary' 
                    : 'text-theme-subtle hover:text-theme-text'
                }`}
              >
                <Home size={16} />
                Proyectos
              </Link>
              
              <Link 
                to="/nuevo" 
                className={`nav-link flex items-center gap-2 ${
                  isActive('/nuevo')
                    ? 'text-theme-primary border-b-2 border-theme-primary' 
                    : 'text-theme-subtle hover:text-theme-text'
                }`}
              >
                <Plus size={16} />
                Nuevo
              </Link>
            </div>
            
            {/* Usuario y Acciones */}
            <div className="flex items-center gap-4">
              {user && (
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-8 h-8 bg-theme-primary/10 rounded-full flex items-center justify-center">
                    <User size={16} className="text-theme-primary" />
                  </div>
                  <div className="hidden sm:block">
                    <p className="font-bold text-theme-text text-xs">{user.name}</p>
                    <p className="text-[10px] text-theme-subtle uppercase">{user.plan}</p>
                  </div>
                </div>
              )}
              
              <button 
                onClick={logout}
                className="p-2 text-theme-subtle hover:text-red-600 transition"
                title="Cerrar sesión"
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Contenedor Principal */}
      <main className="pt-24 max-w-7xl mx-auto px-8 pb-12">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-theme-border py-6 mt-12">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex justify-between items-center text-xs text-theme-subtle font-report-mono">
            <p>Sylphrena © 2025 | AI-Powered Literary Editing</p>
            <p>
              <a href="https://fintechmx.pro" className="hover:text-theme-primary">
                fintechmx.pro
              </a>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
