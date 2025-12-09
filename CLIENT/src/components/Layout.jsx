// =============================================================================
// Layout.jsx - WORKSPACE LYA v5.0 (Color Corregido)
// =============================================================================

import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Coins, LogOut } from 'lucide-react'; 

const Layout = ({ children }) => {
  const location = useLocation();
  const { logout } = useAuth(); 

  const isActive = (path) => location.pathname === path;
  
  // DATO MOCKUP
  const userBalance = 0; 

  return (
    <div className="min-h-screen bg-theme-bg font-sans text-theme-text selection:bg-theme-primary selection:text-white flex flex-col">
      
      {/* NAVBAR */}
      <nav className="fixed top-0 w-full bg-white border-t-4 border-theme-primary border-b border-gray-200 z-50 h-20 shadow-sm transition-all">
        <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
          
          {/* IZQUIERDA: Logo */}
          <Link to="/" className="flex items-baseline gap-3 group text-decoration-none">
            <span className="font-serif text-3xl font-bold text-gray-900 tracking-tight group-hover:text-theme-primary transition-colors">
              LYA
            </span>
            <span className="hidden md:block w-px h-6 bg-gray-300 mx-2"></span>
            <span className="hidden md:block font-mono text-xs text-theme-primary font-bold uppercase tracking-widest pt-1">
              Logic Yield Assistant v5.0
            </span>
          </Link>

          {/* DERECHA: Menú + Saldo */}
          <div className="flex items-center gap-8">
            
            <div className="hidden md:flex gap-6 items-center">
              {/* Navegación */}
              <NavLink to="/dashboard" active={isActive('/dashboard')}>
                Proyectos
              </NavLink>
              <NavLink to="/nuevo" active={isActive('/nuevo')}>
                Nuevo Análisis
              </NavLink>
              
              <div className="h-6 w-px bg-gray-200 mx-2"></div>

              {/* INDICADOR DE SALDO + BOTÓN OFICIAL */}
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 text-gray-500 font-mono text-xs">
                  <Coins className="w-4 h-4" />
                  <span className="font-bold">{userBalance}</span>
                </div>
                
                {/* BOTÓN RECARGAR: Ahora usa 'bg-theme-primary' (Tu verde elegante) */}
                <Link 
                  to="/creditos" 
                  className="bg-theme-primary hover:bg-theme-primary-hover text-white text-xs font-extrabold px-5 py-2.5 rounded-sm uppercase tracking-wider shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5 flex items-center gap-2"
                >
                  + Recargar
                </Link>
              </div>
            </div>

            <div className="h-6 w-px bg-gray-200 hidden md:block"></div>

            {/* Salir */}
            <button 
              onClick={() => {
                if (logout) logout();
                else {
                  localStorage.removeItem('sylphrena_token');
                  window.location.href = '/login';
                }
              }}
              className="text-gray-400 hover:text-red-600 transition-colors"
              title="Cerrar Sesión"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>

        </div>
      </nav>

      {/* CONTENIDO */}
      <main className="pt-32 pb-12 px-6 max-w-7xl mx-auto w-full animate-fade-in flex-grow">
        {children}
      </main>

      {/* FOOTER */}
      <footer className="bg-white border-t border-gray-200 py-12 text-center mt-auto">
        <div className="flex flex-col items-center gap-2">
            <p className="font-serif text-3xl font-bold text-gray-900">LYA</p>
            
            <p className="font-mono text-[10px] text-theme-primary font-bold uppercase tracking-[0.25em]">
                LOGIC YIELD ASSISTANT <span className="text-gray-400 ml-1">v5.0</span>
            </p>

            <p className="font-mono text-[10px] text-gray-400 uppercase tracking-widest mt-6">
              © 2025 PlotScope. Arquitectura Narrativa Avanzada.
            </p>
        </div>
      </footer>
    </div>
  );
};

function NavLink({ to, children, active }) {
  return (
    <Link 
      to={to} 
      className={`
        font-sans text-xs font-extrabold uppercase tracking-wide transition-all duration-200
        ${active 
          ? 'text-gray-900 border-b-2 border-theme-primary pb-1' 
          : 'text-gray-500 hover:text-theme-primary'}
      `}
    >
      {children}
    </Link>
  );
}

export default Layout;