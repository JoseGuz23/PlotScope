import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsAPI } from '../services/api';

export default function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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

  if (loading) return (
    <div className="flex justify-center pt-20">
      <div className="animate-spin h-8 w-8 border-4 border-theme-primary border-t-transparent rounded-full"></div>
    </div>
  );

  return (
    <div>
      {/* Header de Sección */}
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
          className="bg-theme-primary text-white px-6 py-3 text-xs font-extrabold uppercase tracking-widest hover:bg-theme-primary-hover transition-colors shadow-md rounded-sm transform hover:-translate-y-0.5"
        >
          + Iniciar Análisis
        </Link>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-8">
          <p className="text-red-700 text-sm font-bold">{error}</p>
        </div>
      )}

      {/* Grid de Proyectos */}
      {projects.length === 0 && !error ? (
        <div className="text-center py-24 bg-white border-2 border-dashed border-gray-200 rounded-sm">
          <h3 className="font-serif text-2xl text-gray-400 mb-2">Tu escritorio está vacío</h3>
          <p className="text-gray-500 mb-8 max-w-md mx-auto text-sm">
            Comienza subiendo tu primer manuscrito para activar el orquestador.
          </p>
          <Link to="/nuevo" className="text-theme-primary font-bold hover:underline text-sm uppercase tracking-wide">
            Subir Manuscrito Ahora
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {projects.map((proj) => (
            <ProjectCard key={proj.id} project={proj} />
          ))}
        </div>
      )}
    </div>
  );
}

function ProjectCard({ project }) {
  const isComplete = project.status === 'completed';
  
  return (
    <Link 
      to={`/proyecto/${project.id}/editor`}
      className="group block bg-white border border-gray-200 p-8 hover:border-theme-primary hover:shadow-xl transition-all duration-300 relative rounded-sm"
    >
      {/* Barra de estado superior */}
      <div className={`absolute top-0 left-0 w-full h-1.5 ${isComplete ? 'bg-theme-primary' : 'bg-yellow-400'}`}></div>

      <div className="mb-6">
        <h3 className="font-editorial text-2xl font-bold text-gray-900 group-hover:text-theme-primary transition-colors line-clamp-2 leading-tight">
          {project.name || 'Sin Título'}
        </h3>
        <p className="font-mono text-[10px] text-gray-400 mt-2 uppercase tracking-wider">
          ID: {project.id.substring(0, 8)}
        </p>
      </div>

      <div className="flex justify-between items-center border-t border-gray-100 pt-4 mt-4">
        <span className={`text-[10px] font-extrabold uppercase tracking-widest ${isComplete ? 'text-theme-primary' : 'text-yellow-600'}`}>
          {isComplete ? '● Completado' : '● Procesando'}
        </span>
        <span className="text-xs font-bold text-gray-300 group-hover:text-theme-text transition-colors">
          Abrir →
        </span>
      </div>
    </Link>
  );
}