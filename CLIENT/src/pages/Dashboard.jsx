// =============================================================================
// Dashboard.jsx - LISTA DE PROYECTOS DEL USUARIO
// =============================================================================

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { projectsAPI } from '../services/api';
import { 
  Plus, 
  BookOpen, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Loader2,
  FileText,
  ChevronRight
} from 'lucide-react';

// Estados posibles de un proyecto
const STATUS_CONFIG = {
  pending: {
    label: 'En cola',
    color: 'text-gray-500',
    bg: 'bg-gray-100',
    icon: Clock,
  },
  processing: {
    label: 'Procesando',
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    icon: Loader2,
    animate: true,
  },
  pending_bible: {
    label: 'Esperando aprobación',
    color: 'text-amber-600',
    bg: 'bg-amber-50',
    icon: AlertCircle,
  },
  editing: {
    label: 'En edición',
    color: 'text-purple-600',
    bg: 'bg-purple-50',
    icon: FileText,
  },
  completed: {
    label: 'Completado',
    color: 'text-green-600',
    bg: 'bg-green-50',
    icon: CheckCircle,
  },
  error: {
    label: 'Error',
    color: 'text-red-600',
    bg: 'bg-red-50',
    icon: AlertCircle,
  },
};

function ProjectCard({ project }) {
  const status = STATUS_CONFIG[project.status] || STATUS_CONFIG.pending;
  const StatusIcon = status.icon;

  // Determinar la ruta según el estado
  const getProjectRoute = () => {
    switch (project.status) {
      case 'pending_bible':
        return `/proyecto/${project.id}/biblia`;
      case 'completed':
      case 'editing':
        return `/proyecto/${project.id}/editor`;
      default:
        return `/proyecto/${project.id}`;
    }
  };

  return (
    <Link 
      to={getProjectRoute()}
      className="block border border-theme-border bg-white rounded-sm hover:shadow-md transition-shadow duration-200"
    >
      <div className="p-5">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="font-report-serif font-bold text-lg text-theme-text">
              {project.name.replace(/_/g, ' ')}
            </h3>
            <p className="text-xs text-theme-subtle font-report-mono mt-1">
              ID: {project.id.slice(0, 8)}...
            </p>
          </div>
          <div className={`flex items-center gap-1.5 px-2 py-1 rounded-sm ${status.bg}`}>
            <StatusIcon 
              size={14} 
              className={`${status.color} ${status.animate ? 'animate-spin' : ''}`} 
            />
            <span className={`text-xs font-bold ${status.color}`}>
              {status.label}
            </span>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <p className="data-label">Palabras</p>
            <p className="font-report-mono font-bold text-theme-text">
              {project.wordCount?.toLocaleString() || '—'}
            </p>
          </div>
          <div>
            <p className="data-label">Capítulos</p>
            <p className="font-report-mono font-bold text-theme-text">
              {project.chaptersCount || '—'}
            </p>
          </div>
          <div>
            <p className="data-label">Cambios</p>
            <p className="font-report-mono font-bold text-theme-text">
              {project.changesCount || '—'}
            </p>
          </div>
        </div>

        {/* Progress bar si está procesando */}
        {project.status === 'processing' && project.progress && (
          <div className="mb-4">
            <div className="flex justify-between text-xs mb-1">
              <span className="text-theme-subtle">Progreso</span>
              <span className="font-report-mono text-theme-primary font-bold">
                {project.progress}%
              </span>
            </div>
            <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-theme-primary transition-all duration-500"
                style={{ width: `${project.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex justify-between items-center pt-3 border-t border-theme-border">
          <span className="text-xs text-theme-subtle font-report-mono">
            {new Date(project.createdAt).toLocaleDateString('es-MX', {
              day: '2-digit',
              month: 'short',
              year: 'numeric',
            })}
          </span>
          <span className="text-theme-primary text-sm font-bold flex items-center gap-1">
            Abrir <ChevronRight size={16} />
          </span>
        </div>
      </div>
    </Link>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      setIsLoading(true);
      const data = await projectsAPI.getAll();
      setProjects(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <>
      {/* Header */}
      <header className="report-divider py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-4xl font-report-serif font-extrabold text-theme-text mb-2 tracking-tight">
              MIS PROYECTOS
            </h1>
            <p className="text-sm font-report-mono text-theme-subtle">
              Bienvenido, {user?.name || 'Usuario'} | Plan: {user?.plan?.toUpperCase() || 'FREE'}
            </p>
          </div>
          <Link
            to="/nuevo"
            className="flex items-center gap-2 bg-theme-primary text-white text-sm font-bold px-5 py-3 rounded-sm uppercase tracking-wider hover:bg-theme-primary/80 transition duration-150"
          >
            <Plus size={18} />
            Nuevo Proyecto
          </Link>
        </div>
      </header>

      {/* Estado de carga */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="animate-spin text-theme-primary" size={40} />
          <span className="ml-3 text-theme-subtle">Cargando proyectos...</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-sm mb-6">
          <p className="font-bold">Error al cargar proyectos</p>
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Lista de proyectos */}
      {!isLoading && !error && (
        <>
          {projects.length === 0 ? (
            <div className="text-center py-20 border border-dashed border-theme-border rounded-sm bg-white">
              <BookOpen className="mx-auto text-theme-subtle mb-4" size={48} />
              <h2 className="text-xl font-report-serif font-bold text-theme-text mb-2">
                No tienes proyectos aún
              </h2>
              <p className="text-theme-subtle mb-6">
                Sube tu primer manuscrito para comenzar
              </p>
              <Link
                to="/nuevo"
                className="inline-flex items-center gap-2 bg-theme-primary text-white text-sm font-bold px-5 py-3 rounded-sm uppercase tracking-wider hover:bg-theme-primary/80 transition"
              >
                <Plus size={18} />
                Crear Proyecto
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map(project => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          )}
        </>
      )}

      {/* Stats globales */}
      {!isLoading && projects.length > 0 && (
        <section className="mt-10 grid grid-cols-4 gap-6">
          <div className="border border-theme-border p-5 rounded-sm bg-white">
            <p className="data-label">Total Proyectos</p>
            <span className="text-3xl font-report-mono font-bold text-theme-text block mt-1">
              {projects.length}
            </span>
          </div>
          <div className="border border-theme-border p-5 rounded-sm bg-white">
            <p className="data-label">Completados</p>
            <span className="text-3xl font-report-mono font-bold text-green-600 block mt-1">
              {projects.filter(p => p.status === 'completed').length}
            </span>
          </div>
          <div className="border border-theme-border p-5 rounded-sm bg-white">
            <p className="data-label">En Proceso</p>
            <span className="text-3xl font-report-mono font-bold text-blue-600 block mt-1">
              {projects.filter(p => p.status === 'processing').length}
            </span>
          </div>
          <div className="border border-theme-border p-5 rounded-sm bg-white">
            <p className="data-label">Pendientes</p>
            <span className="text-3xl font-report-mono font-bold text-amber-600 block mt-1">
              {projects.filter(p => p.status === 'pending_bible').length}
            </span>
          </div>
        </section>
      )}
    </>
  );
}
