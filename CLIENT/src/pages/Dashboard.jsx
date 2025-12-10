import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { Trash2, FileText, Loader2, AlertCircle } from 'lucide-react';

export default function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      const data = await projectsAPI.getAll();
      setProjects(data);
    } catch (err) {
      console.error(err);
      setError('No se pudo conectar con el servidor.');
    } finally {
      setLoading(false);
    }
  }

  const handleDelete = async (e, projectId) => {
    e.preventDefault(); // Evitar navegación del Link
    e.stopPropagation();
    
    if (!confirm('¿Estás seguro de eliminar este proyecto permanentemente?')) return;

    setDeletingId(projectId);
    try {
      await projectsAPI.delete(projectId);
      // Actualizar lista localmente
      setProjects(prev => prev.filter(p => p.id !== projectId));
    } catch (err) {
      alert('Error al eliminar: ' + err.message);
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return (
    <div className="flex justify-center items-center h-screen">
      <Loader2 className="h-8 w-8 text-theme-primary animate-spin" />
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto px-4 pt-12">
      {/* Header */}
      <div className="flex justify-between items-end mb-12 border-b border-gray-200 pb-6">
        <div>
          <h1 className="font-editorial text-4xl font-bold text-gray-900 mb-2">
            Biblioteca de Manuscritos
          </h1>
          <p className="font-sans text-gray-500 text-sm font-medium">
            Gestión y estado de tus análisis activos.
          </p>
        </div>
        <Link 
          to="/nuevo" 
          className="bg-theme-primary text-white px-6 py-3 text-xs font-extrabold uppercase tracking-widest hover:bg-theme-primary-hover transition-colors shadow-md rounded-sm transform hover:-translate-y-0.5 flex items-center gap-2"
        >
          <span>+</span> Iniciar Análisis
        </Link>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-8 flex items-center gap-3">
          <AlertCircle className="text-red-500 w-5 h-5" />
          <p className="text-red-700 text-sm font-bold">{error}</p>
        </div>
      )}

      {/* Empty State */}
      {projects.length === 0 && !error ? (
        <div className="text-center py-24 bg-white border-2 border-dashed border-gray-200 rounded-sm">
          <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
          <h3 className="font-serif text-2xl text-gray-400 mb-2">Tu escritorio está vacío</h3>
          <p className="text-gray-500 mb-8 max-w-md mx-auto text-sm">
            Comienza subiendo tu primer manuscrito para activar el orquestador.
          </p>
          <Link to="/nuevo" className="text-theme-primary font-bold hover:underline text-sm uppercase tracking-wide">
            Subir Manuscrito Ahora
          </Link>
        </div>
      ) : (
        /* Grid de Proyectos */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 pb-20">
          {projects.map((proj) => (
            <ProjectCard 
              key={proj.id} 
              project={proj} 
              onDelete={handleDelete}
              isDeleting={deletingId === proj.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function ProjectCard({ project, onDelete, isDeleting }) {
  const isComplete = project.status === 'completed';
  const isTerminated = project.status === 'terminated';
  const isFailed = project.status === 'failed';
  
  // Determinar ruta de destino según estado
const destination = isComplete 
  ? `/proyecto/${project.id}/carta`  // <-- CAMBIO PRINCIPAL: Ir a la Carta primero
  : `/proyecto/${project.id}/status`;

  return (
    <Link 
      to={destination}
      className={`
        group block bg-white border border-gray-200 p-8 
        hover:border-theme-primary hover:shadow-xl transition-all duration-300 
        relative rounded-sm overflow-hidden
        ${isDeleting ? 'opacity-50 pointer-events-none' : ''}
      `}
    >
      {/* Barra de estado superior */}
      <div className={`absolute top-0 left-0 w-full h-1.5 
        ${isComplete ? 'bg-theme-primary' : 
          isTerminated || isFailed ? 'bg-red-400' : 'bg-yellow-400'}`}
      ></div>

      <div className="mb-6 pr-8">
        <h3 className="font-editorial text-2xl font-bold text-gray-900 group-hover:text-theme-primary transition-colors line-clamp-2 leading-tight">
          {project.name || 'Sin Título'}
        </h3>
        <p className="font-mono text-[10px] text-gray-400 mt-2 uppercase tracking-wider flex items-center gap-2">
          <span>ID: {project.id.substring(0, 8)}...</span>
          <span>•</span>
          <span>{new Date(project.createdAt).toLocaleDateString()}</span>
        </p>
      </div>

      {/* Botón Eliminar (Absoluto arriba derecha) */}
      <button
        onClick={(e) => onDelete(e, project.id)}
        disabled={isDeleting}
        className="absolute top-6 right-6 p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-full transition-all z-10"
        title="Eliminar proyecto"
      >
        {isDeleting ? (
          <Loader2 className="w-4 h-4 animate-spin text-red-500" />
        ) : (
          <Trash2 className="w-4 h-4" />
        )}
      </button>

      <div className="flex justify-between items-center border-t border-gray-100 pt-4 mt-4">
        <span className={`text-[10px] font-extrabold uppercase tracking-widest 
          ${isComplete ? 'text-theme-primary' : 
            isTerminated || isFailed ? 'text-red-500' : 'text-yellow-600'}`}
        >
          {isComplete ? '● Completado' : 
           isTerminated ? '● Detenido' :
           isFailed ? '● Error' : '● Procesando'}
        </span>
        <span className="text-xs font-bold text-gray-300 group-hover:text-theme-text transition-colors flex items-center gap-1">
          Abrir <span>→</span>
        </span>
      </div>
    </Link>
  );
}