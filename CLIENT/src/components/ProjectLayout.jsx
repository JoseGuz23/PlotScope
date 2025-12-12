// =============================================================================
// ProjectLayout.jsx - CONTEXTO INTELIGENTE
// =============================================================================

import { useState, useEffect, useCallback } from 'react';
import { Outlet, useParams, Link, useLocation } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { 
  Layout, BookOpen, BarChart3, Settings, 
  ChevronLeft, Loader2, PenTool 
} from 'lucide-react';

export default function ProjectLayout() {
  const { id } = useParams();
  const location = useLocation();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);

  // --- 1. FUNCIÓN DE RECARGA (LA SOLUCIÓN) ---
  // Esta función se pasa a los hijos para que puedan pedir datos frescos
  const loadProjectData = useCallback(async () => {
    try {
      // No ponemos setLoading(true) aquí para evitar parpadeos en recargas silenciosas
      const data = await projectsAPI.getById(id);
      setProject(data);
    } catch (error) {
      console.error("❌ Error cargando proyecto:", error);
    } finally {
      setLoading(false);
    }
  }, [id]);

  // Carga inicial al montar
  useEffect(() => {
    setLoading(true);
    loadProjectData();
  }, [loadProjectData]);

  if (loading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-gray-50">
        <Loader2 className="w-8 h-8 text-theme-primary animate-spin" />
      </div>
    );
  }

  // --- RENDER UI ---
  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans text-gray-900">
      
      {/* SIDEBAR (Navegación Lateral) */}
      <aside className="w-64 bg-white border-r border-gray-200 flex-shrink-0 flex flex-col z-20">
        
        {/* Título del Proyecto */}
        <div className="p-6 border-b border-gray-100">
          <Link to="/dashboard" className="text-xs font-bold text-gray-400 hover:text-gray-600 flex items-center gap-1 mb-3 transition-colors">
            <ChevronLeft className="w-3 h-3" /> VOLVER
          </Link>
          <h1 className="font-serif text-xl font-bold text-gray-900 line-clamp-2 leading-tight">
            {project?.project_name || 'Cargando...'}
          </h1>
          <p className="text-xs text-gray-400 mt-1 font-mono uppercase tracking-wider">
            {project?.status === 'completed' || project?.status === 'success' ? 'Completado' : 'En Proceso'}
          </p>
        </div>

        {/* Menú */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <NavItem 
            to={`/proyecto/${id}/status`} 
            icon={<Layout className="w-4 h-4" />} 
            label="Estado del Proceso" 
            active={location.pathname.includes('/status')} 
          />
          <NavItem 
            to={`/proyecto/${id}/biblia`} 
            icon={<BookOpen className="w-4 h-4" />} 
            label="Biblia Narrativa" 
            active={location.pathname.includes('/biblia')} 
          />
          <NavItem 
            to={`/proyecto/${id}/editor`} 
            icon={<PenTool className="w-4 h-4" />} 
            label="Editor & Entregables" 
            active={location.pathname.includes('/editor')} 
            disabled={!project?.bible_approved} // Opcional: deshabilitar si no hay biblia
          />
        </nav>

        {/* Footer Sidebar */}
        <div className="p-4 border-t border-gray-100 bg-gray-50/50">
          <div className="text-[10px] text-gray-400 font-mono text-center">
            ID: {id?.substring(0, 8)}...
            <br />
            v6.0
          </div>
        </div>
      </aside>

      {/* CONTENIDO PRINCIPAL */}
      <main className="flex-1 overflow-auto bg-gray-50 relative">
        {/* AQUÍ PASAMOS LA MAGIA: 
            context={{ project, refreshProject: loadProjectData }}
        */}
        <Outlet context={{ project, refreshProject: loadProjectData }} />
      </main>

    </div>
  );
}

// Componente auxiliar para links del menú
function NavItem({ to, icon, label, active, disabled }) {
  if (disabled) {
    return (
      <div className="flex items-center gap-3 px-3 py-2 text-sm font-medium text-gray-300 cursor-not-allowed">
        {icon}
        <span>{label}</span>
      </div>
    );
  }
  return (
    <Link
      to={to}
      className={`
        flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all
        ${active 
          ? 'bg-theme-primary text-white shadow-md shadow-theme-primary/20' 
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'}
      `}
    >
      {icon}
      <span>{label}</span>
    </Link>
  );
}