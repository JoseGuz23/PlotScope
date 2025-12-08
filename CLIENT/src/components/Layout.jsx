// =============================================================================
// Layout.jsx - LAYOUT PROFESIONAL LYA
// =============================================================================

import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Layout = ({ children }) => {
  const location = useLocation();
  const { user } = useAuth();
  
  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <>
      {/* NAVBAR */}
      <nav className="navbar">
        <div className="navbar-inner">
          {/* Logo */}
          <div className="navbar-logo">
            <span className="navbar-logo-text">LYA</span>
            <span className="navbar-logo-version">v4.1.0 (Developmental Editor)</span>
          </div>
          
          {/* Links */}
          <div className="navbar-links">
            <Link 
              to="/" 
              className={`navbar-link ${isActive('/') && location.pathname === '/' ? 'active' : ''}`}
            >
              Dashboard
            </Link>
            <Link 
              to="/biblioteca" 
              className={`navbar-link ${isActive('/biblioteca') ? 'active' : ''}`}
            >
              Biblioteca
            </Link>
            <Link 
              to="/config" 
              className={`navbar-link ${isActive('/config') ? 'active' : ''}`}
            >
              Configuración IA
            </Link>
            <Link 
              to="/api" 
              className={`navbar-link ${isActive('/api') ? 'active' : ''}`}
            >
              API Console
            </Link>
          </div>
          
          {/* User info - opcional */}
          <div style={{ width: '150px' }}></div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main-content">
        <div className="container">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="footer">
        <p className="footer-text">
          LYA Orquestador de Edición © 2025. Todos los derechos reservados. 
          Ejecutándose en Azure Static Web Apps.
        </p>
      </footer>
    </>
  );
};

export default Layout;
