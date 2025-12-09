import { Link } from 'react-router-dom';

const PublicNavbar = () => {
  return (
    <nav className="w-full bg-white border-t-4 border-theme-primary border-b border-gray-200 fixed top-0 z-50 shadow-sm h-20 transition-all">
      <div className="max-w-7xl mx-auto px-6 h-full flex items-center justify-between">
        
        {/* LOGO */}
        <Link to="/" className="flex items-baseline gap-3 group text-decoration-none">
          <span className="font-serif text-3xl font-bold text-gray-900 tracking-tight group-hover:text-theme-primary transition-colors">
            LYA
          </span>
          <span className="hidden md:block w-px h-6 bg-gray-300 mx-2"></span>
          <span className="hidden md:block font-mono text-xs text-theme-primary font-bold uppercase tracking-widest pt-1">
            Orquestador Editorial
          </span>
        </Link>

        {/* NAV DERECHA */}
        <div className="flex items-center gap-8">
          <div className="hidden md:flex gap-6">
            <Link to="/" className="font-sans text-xs font-extrabold uppercase tracking-wide text-gray-500 hover:text-theme-primary transition-colors">
              Características
            </Link>
            <Link to="/" className="font-sans text-xs font-extrabold uppercase tracking-wide text-gray-500 hover:text-theme-primary transition-colors">
              Precios
            </Link>
          </div>

          <Link 
            to="/login"
            className="flex items-center justify-center bg-theme-primary hover:bg-theme-primary-hover text-white px-8 py-2.5 font-sans text-sm font-extrabold uppercase tracking-wide shadow-md transition-all duration-300 transform hover:scale-105 hover:shadow-lg rounded-sm"
          >
            Iniciar Sesión
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default PublicNavbar;