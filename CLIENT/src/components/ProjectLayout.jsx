import { useState, useEffect } from 'react';
import { Outlet, NavLink, useParams, useLocation, Link, Navigate } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { 
  Activity, Book, FileText, ChevronRight, 
  ArrowLeft, Loader2, Layout as LayoutIcon 
} from 'lucide-react';

export default function ProjectLayout() {
  const { id: projectId } = useParams();
  const location = useLocation();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjectInfo();
  }, [projectId]);

  async function loadProjectInfo() {
    try {
      const data = await projectsAPI.getById(projectId);
      setProject(data);
    } catch (err) {
      console.error(err);
      // Redirigir si el proyecto no existe
      Navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  }

  if (loading) return (
    <div className="h-screen flex items-center justify-center bg-[#f8f9fa]">
      <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
    </div>
  );

  // Redirigir la ruta raíz del proyecto a 'status' si el usuario ingresa a /proyecto/:id
  if (location.pathname === `/proyecto/${projectId}`) {
    return <Navigate to={`/proyecto/${projectId}/status`} replace />;
  }

  return (
    <div className="flex flex-col h-screen bg-[#f8f9fa] font-sans">
      
      {/* --- TOP BAR DE NAVEGACIÓN --- */}
      <header className="bg-white border-b border-gray-200 shrink-0 z-30">
        
        {/* Fila 1: Info del Proyecto y Salida */}
        <div className="flex justify-between items-center px-6 py-3 border-b border-gray-100">
          <div className="flex items-center gap-3 text-sm">
            <Link to="/dashboard" className="text-gray-400 hover:text-gray-800 transition-colors flex items-center gap-1 font-bold uppercase tracking-wider text-xs">
              <ArrowLeft className="w-3 h-3" /> Biblioteca
            </Link>
            <ChevronRight className="w-3 h-3 text-gray-300" />
            <span className="font-bold text-gray-900 truncate max-w-xs md:max-w-md">
              {project?.book_name || 'Proyecto sin título'}
            </span>
            <StatusBadge status={project?.status} />
          </div>
        </div>

        {/* Fila 2: PESTAÑAS PRINCIPALES */}
        <nav className="flex px-6 gap-8">
          <ProjectTab 
            to={`/proyecto/${projectId}/status`} 
            icon={Activity} 
            label="1. Estado del Proceso" 
          />
          <ProjectTab 
            to={`/proyecto/${projectId}/biblia`} 
            icon={Book} 
            label="2. Biblia Narrativa" 
          />
          <ProjectTab 
            to={`/proyecto/${projectId}/resultados`} 
            icon={LayoutIcon} 
            label="3. Entregables Finales" 
            // La pestaña Resultados está activa si la ruta contiene /resultados, /carta o /editor
            isActive={location.pathname.includes('/resultados') || location.pathname.includes('/carta') || location.pathname.includes('/editor')}
          />
        </nav>
      </header>

      {/* --- CONTENIDO DE LA PESTAÑA SELECCIONADA --- */}
      <div className="flex-1 overflow-hidden relative">
        <Outlet context={{ project }} />
      </div>

    </div>
  );
}

function ProjectTab({ to, icon: Icon, label, isActive }) {
  return (
    <NavLink 
      to={to}
      className={({ isActive: routeActive }) => `
        flex items-center gap-2 py-4 text-sm font-bold border-b-2 transition-all
        ${(isActive || routeActive)
          ? 'border-theme-primary text-theme-primary' 
          : 'border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-200'}
      `}
    >
      <Icon className="w-4 h-4" />
      {label}
    </NavLink>
  );
}

function StatusBadge({ status }) {
  const styles = {
    completed: 'bg-green-100 text-green-700',
    processing: 'bg-yellow-100 text-yellow-700',
    failed: 'bg-red-100 text-red-700',
    pending: 'bg-gray-100 text-gray-600'
  };
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-extrabold tracking-wider ${styles[status] || styles.pending}`}>
      {status}
    </span>
  );
}