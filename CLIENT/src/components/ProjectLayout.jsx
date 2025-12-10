// =============================================================================
// ProjectLayout.jsx - SIN CUADRO RANDOM (Fix Final)
// =============================================================================

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
      setProject(null); 
    } finally {
      setLoading(false);
    }
  }

  if (loading) return (
    // Quitamos pt-20 aquí también para centrar el loader
    <div className="min-h-screen flex items-center justify-center bg-white">
      <Loader2 className="w-10 h-10 animate-spin text-theme-primary" />
    </div>
  );
  
  if (!project) return <Navigate to="/dashboard" replace />;
  
  if (location.pathname === `/proyecto/${projectId}`) {
    return <Navigate to={`/proyecto/${projectId}/status`} replace />;
  }

  return (
    // 1. ELIMINADO EL pt-20. Esto borra el cuadro blanco gigante.
    // El Layout padre ya se encarga de no tapar el contenido inicial.
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans">
      
      {/* HEADER DEL PROYECTO */}
      {/* 2. sticky top-20: Cuando bajes, este header se quedará pegado justo debajo 
             de tu Navbar principal (que mide 80px / 20 tailwind units). */}
      <header className="bg-white border-b border-gray-200 shrink-0 z-40 shadow-sm w-full sticky top-20 transition-all">
        
        {/* Fila 1: Breadcrumbs */}
        <div className="px-8 py-3 border-b border-gray-100 flex justify-between items-center bg-white">
          <div className="flex items-center gap-3 text-sm">
            <Link to="/dashboard" className="text-gray-400 hover:text-theme-primary transition-colors flex items-center gap-2 font-bold uppercase tracking-wider text-xs">
              <ArrowLeft className="w-4 h-4" /> Biblioteca
            </Link>
            
            <ChevronRight className="w-4 h-4 text-gray-300" />
            
            <span className="font-editorial font-bold text-xl text-gray-900 truncate max-w-md">
              {project?.book_name || 'Manuscrito sin título'}
            </span>
            
            <StatusBadge status={project?.status} />
          </div>
        </div>

        {/* Fila 2: TABS (Font corregida) */}
        <nav className="flex px-8 gap-8 bg-white">
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
            isActive={location.pathname.includes('/resultados') || location.pathname.includes('/carta') || location.pathname.includes('/editor')}
          />
        </nav>
      </header>

      {/* CONTENIDO PRINCIPAL */}
      <main className="flex-1 w-full">
        <Outlet context={{ project }} />
      </main>

    </div>
  );
}

function ProjectTab({ to, icon: Icon, label, isActive }) {
  return (
    <NavLink 
      to={to}
      className={({ isActive: routeActive }) => `
        flex items-center gap-2 py-4 border-b-[3px] transition-all 
        font-sans text-xs font-extrabold uppercase tracking-wide
        ${(isActive || routeActive)
          ? 'border-theme-primary text-theme-primary' 
          : 'border-transparent text-gray-400 hover:text-theme-primary hover:border-gray-200'}
      `}
    >
      <Icon className="w-4 h-4 mb-0.5" />
      {label}
    </NavLink>
  );
}

function StatusBadge({ status }) {
  const styles = {
    completed: 'bg-green-100 text-green-800 border-green-200',
    processing: 'bg-blue-50 text-blue-700 border-blue-100 animate-pulse',
    failed: 'bg-red-50 text-red-700 border-red-100',
    terminated: 'bg-gray-100 text-gray-600 border-gray-200',
    pending: 'bg-gray-50 text-gray-400 border-gray-100'
  };
  return (
    <span className={`ml-4 px-2 py-0.5 rounded-sm border text-[10px] uppercase font-black tracking-widest ${styles[status] || styles.pending}`}>
      {status}
    </span>
  );
}