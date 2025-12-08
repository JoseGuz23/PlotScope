// =============================================================================
// Dashboard.jsx - DASHBOARD PROFESIONAL LYA
// =============================================================================

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { projectsAPI } from '../services/api';

export default function Dashboard() {
  const [projects, setProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
    try {
      setIsLoading(true);
      const data = await projectsAPI.getAll();
      setProjects(data);
      if (data.length > 0) {
        setActiveProject(data[0]);
      }
    } catch (err) {
      console.error('Error:', err);
    } finally {
      setIsLoading(false);
    }
  }

  const formatDate = () => {
    return new Date().toLocaleString('es-MX', {
      day: '2-digit',
      month: '2-digit', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '4rem 0' }}>
        <div className="status-indicator" style={{ justifyContent: 'center' }}>
          <div className="status-dot"></div>
          <span className="status-text">Cargando...</span>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* PAGE HEADER */}
      <header className="page-header">
        <h1 className="title-main">ANÁLISIS DE MANUSCRITO ACTIVO</h1>
        <p className="page-header-meta">
          DOCUMENTO CLASIFICADO: {activeProject?.name || 'Ninguno'} | ID: {activeProject?.id?.slice(0, 7).toUpperCase() || 'N/A'} | Sincronización: {formatDate()} MST
        </p>
      </header>

      {/* STATS GRID */}
      <div className="stats-grid">
        {/* Palabras */}
        <div className="stat-card">
          <p className="label">Palabras (Total)</p>
          <p className="stat-value">{activeProject?.wordCount?.toLocaleString() || '0'}</p>
          <p className="stat-meta positive">[+] 2.5% vs último reporte</p>
        </div>

        {/* Capítulos */}
        <div className="stat-card">
          <p className="label">Capítulos Analizados</p>
          <p className="stat-value">{activeProject?.chaptersCount || 0}/{(activeProject?.chaptersCount || 0) + 1}</p>
          <p className="stat-meta">Próximo: Capítulo {(activeProject?.chaptersCount || 0) + 1}</p>
        </div>

        {/* Nivel */}
        <div className="stat-card">
          <p className="label">Nivel de Lectura</p>
          <p className="stat-value">A+</p>
          <p className="stat-meta">Público objetivo: Adulto Joven</p>
        </div>

        {/* Estado */}
        <div className="stat-card">
          <p className="label">Estado del Análisis IA</p>
          <div className="status-indicator">
            <div className="status-dot"></div>
            <span className="status-text">Análisis en curso...</span>
          </div>
          <p className="stat-meta"><span className="text-primary">45%</span> de Tono Procesado</p>
        </div>
      </div>

      {/* CONTENT SECTION - Track Changes Preview */}
      <section className="content-section">
        <h2 className="title-section">CONTENIDO ANALIZADO (ÚLTIMA EDICIÓN)</h2>
        
        <h3 className="chapter-title">CAPÍTULO 2</h3>
        <p className="chapter-meta">5 revisiones detectadas por el Orquestador.</p>
        
        <div className="content-body">
{`Ángel se acercó despacio.

-No para encerrarlo... pero sí para retenerlo un tiempo. Tal vez el suficiente para que cante.
Henry negó con la cabeza. Sin dejar de mirar el horizonte.
-No es suficiente, muchacho. Toda esta situación me huele a mierda.
Guardó silencio unos segundos.`}
<span className="text-deleted">¿Tú crees que Emma alucinó lo del espía?</span>
<span className="text-added">Sabemos que el espía existe. Solo falta encontrarlo.</span>
{`
Ángel se apoyó en la parte trasera de la valla, con un salto ágil, se sentó en el borde.`}
        </div>
      </section>

      {/* ACTION CARDS */}
      <div className="actions-grid">
        <Link to={`/proyecto/${activeProject?.id || 'demo'}/biblia`} className="action-card">
          <p className="label">Revisar Biblia</p>
          <p className="action-card-link">Ver análisis narrativo completo →</p>
        </Link>

        <Link to={`/proyecto/${activeProject?.id || 'demo'}/editor`} className="action-card">
          <p className="label">Abrir Editor</p>
          <p className="action-card-link">Revisar cambios editoriales →</p>
        </Link>

        <Link to="/nuevo" className="action-card dashed">
          <p className="label">Nuevo Proyecto</p>
          <p className="action-card-link">Subir manuscrito →</p>
        </Link>
      </div>

      {/* PROJECTS LIST */}
      <section className="content-section">
        <h2 className="title-section">PROYECTOS RECIENTES</h2>
        
        <div className="project-list">
          {projects.map(project => (
            <div key={project.id} className="project-item">
              <div>
                <h3 className="project-title">{project.name.replace(/_/g, ' ')}</h3>
                <p className="project-meta">
                  ID: {project.id.slice(0, 8)}... | {project.wordCount?.toLocaleString()} palabras | {project.chaptersCount} capítulos
                </p>
              </div>
              <div className="project-actions">
                {project.status === 'completed' && (
                  <>
                    <span className="badge badge-success">COMPLETADO</span>
                    <Link to={`/proyecto/${project.id}/editor`} className="project-link">
                      Abrir →
                    </Link>
                  </>
                )}
                {project.status === 'processing' && (
                  <>
                    <span className="badge badge-processing">PROCESANDO {project.progress}%</span>
                    <span className="text-subtle mono" style={{ fontSize: '0.875rem' }}>En cola...</span>
                  </>
                )}
                {project.status === 'pending_bible' && (
                  <>
                    <span className="badge badge-warning">ESPERANDO BIBLIA</span>
                    <Link to={`/proyecto/${project.id}/biblia`} className="project-link">
                      Revisar →
                    </Link>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}
