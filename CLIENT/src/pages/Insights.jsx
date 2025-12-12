// =============================================================================
// Insights.jsx - Página de Insights de LYA 6.0
// =============================================================================
// Muestra análisis emocional, sensorial y estadísticas de reflection
// generados por LYA 6.0

import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { Loader2, TrendingUp, Eye, Zap, BarChart3, Activity } from 'lucide-react';
import EmotionalArcWidget from '../components/EmotionalArcWidget';
import SensoryAnalysisWidget from '../components/SensoryAnalysisWidget';
import ReflectionBadge from '../components/ReflectionBadge';

export default function Insights() {
  const { id: projectId } = useParams();
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadProjectData();
  }, [projectId]);

  async function loadProjectData() {
    try {
      const data = await projectsAPI.getById(projectId);
      setProject(data);
    } catch (err) {
      console.error("Error cargando insights:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return (
    <div className="flex justify-center items-center h-screen bg-gray-50">
      <Loader2 className="h-8 w-8 text-theme-primary animate-spin" />
    </div>
  );

  if (error) return (
    <div className="flex justify-center items-center h-screen bg-gray-50">
      <div className="text-center">
        <p className="text-red-600 font-bold mb-2">Error cargando insights</p>
        <p className="text-gray-500 text-sm">{error}</p>
      </div>
    </div>
  );

  const hasV6Data = project?.emotional_arc_analysis || project?.sensory_detection_analysis || project?.reflection_stats;

  if (!hasV6Data) return (
    <div className="flex flex-col items-center justify-center h-full bg-gray-50 p-8">
      <div className="bg-white p-10 rounded-2xl shadow-lg border border-gray-100 max-w-lg text-center">
        <div className="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <BarChart3 className="w-8 h-8 text-theme-primary" />
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Insights LYA 6.0 No Disponibles</h2>
        <p className="text-gray-600 mb-4">
          Este manuscrito fue procesado con una versión anterior de LYA.
        </p>
        <p className="text-sm text-gray-500">
          Para obtener análisis emocional y sensorial, procesa un nuevo manuscrito con LYA 6.0.
        </p>
      </div>
    </div>
  );

  return (
    <div className="h-full overflow-y-auto bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <BarChart3 className="w-8 h-8 text-theme-primary" />
            <h1 className="font-editorial text-4xl font-bold text-gray-900">
              Insights de LYA 6.0
            </h1>
          </div>
          <p className="text-gray-600">
            Análisis avanzado de arco emocional, detección sensorial y estadísticas de refinamiento.
          </p>

          {/* Reflection Badge en el header */}
          {project?.reflection_stats && (
            <div className="mt-4">
              <ReflectionBadge stats={project.reflection_stats} />
            </div>
          )}
        </div>

        {/* Grid de Widgets */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Widget de Arco Emocional */}
          {project?.emotional_arc_analysis && (
            <EmotionalArcWidget emotionalData={project.emotional_arc_analysis} />
          )}

          {/* Widget de Detección Sensorial */}
          {project?.sensory_detection_analysis && (
            <SensoryAnalysisWidget sensoryData={project.sensory_detection_analysis} />
          )}
        </div>

        {/* Sección de Detalles por Capítulo */}
        {(project?.emotional_arc_analysis?.chapter_arcs || project?.sensory_detection_analysis?.chapter_details) && (
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h2 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-theme-primary" />
              Análisis por Capítulo
            </h2>

            <div className="space-y-4">
              {project.emotional_arc_analysis?.chapter_arcs?.map((arc, idx) => {
                const sensoryDetail = project.sensory_detection_analysis?.chapter_details?.find(
                  d => d.chapter_id === arc.chapter_id
                );

                return (
                  <div key={idx} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <h3 className="font-bold text-gray-900 mb-2">
                      Capítulo {arc.chapter_id}
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      {/* Datos emocionales */}
                      {arc && (
                        <div className="space-y-1">
                          <p className="text-xs uppercase tracking-wide text-gray-500 font-bold">Arco Emocional</p>
                          <p className="text-gray-700">
                            <span className="font-bold">Patrón:</span> {arc.pattern || 'N/A'}
                          </p>
                          <p className="text-gray-700">
                            <span className="font-bold">Valencia:</span>{' '}
                            <span className={arc.avg_valence >= 0 ? 'text-green-600' : 'text-red-600'}>
                              {arc.avg_valence?.toFixed(2) || 'N/A'}
                            </span>
                          </p>
                        </div>
                      )}

                      {/* Datos sensoriales */}
                      {sensoryDetail && (
                        <div className="space-y-1">
                          <p className="text-xs uppercase tracking-wide text-gray-500 font-bold">Análisis Sensorial</p>
                          <p className="text-gray-700">
                            <span className="font-bold">Showing Ratio:</span>{' '}
                            <span className={
                              sensoryDetail.showing_ratio >= 0.6 ? 'text-green-600' :
                              sensoryDetail.showing_ratio >= 0.4 ? 'text-yellow-600' : 'text-red-600'
                            }>
                              {(sensoryDetail.showing_ratio * 100).toFixed(0)}%
                            </span>
                          </p>
                          <p className="text-gray-700">
                            <span className="font-bold">Showing:</span> {sensoryDetail.showing_paragraphs} párrafos |{' '}
                            <span className="font-bold">Telling:</span> {sensoryDetail.telling_paragraphs} párrafos
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Info Footer */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-sm text-blue-900">
            <span className="font-bold">💡 Nota:</span> Estos insights fueron generados por LYA 6.0
            usando análisis de sentiment (arco emocional) y detección de léxicos sensoriales (show vs tell).
            Úsalos como guía para identificar áreas de mejora en tu manuscrito.
          </p>
        </div>

      </div>
    </div>
  );
}
