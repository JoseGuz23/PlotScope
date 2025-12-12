// =============================================================================
// SensoryAnalysisWidget.jsx - Widget de Análisis Sensorial (LYA 6.0)
// =============================================================================
// Diseño editorial vintage 1978 - Paleta teal/paper/tinta

import { Eye, AlertTriangle, CheckCircle, Info } from 'lucide-react';

export default function SensoryAnalysisWidget({ sensoryData }) {
  if (!sensoryData) return null;

  const { global_metrics, critical_issues } = sensoryData;
  const showingRatio = global_metrics?.avg_showing_ratio || 0;

  // Función de rating (paleta vintage: teal/grises)
  const getRatingColor = (ratio) => {
    if (ratio >= 0.6) return 'text-theme-primary';
    if (ratio >= 0.4) return 'text-gray-600';
    return 'text-gray-500';
  };

  const getRatingText = (ratio) => {
    if (ratio >= 0.6) return 'Excelente';
    if (ratio >= 0.4) return 'Aceptable';
    return 'Requiere trabajo';
  };

  const getRatingDescription = (ratio) => {
    if (ratio >= 0.6) return 'Tu manuscrito muestra más de lo que dice.';
    if (ratio >= 0.4) return 'Buen balance, pero hay escenas mejorables.';
    return 'Intenta convertir más declaraciones en acciones/sensaciones.';
  };

  const getProgressBarColor = (ratio) => {
    if (ratio >= 0.6) return 'bg-theme-primary';
    if (ratio >= 0.4) return 'bg-gray-500';
    return 'bg-gray-400';
  };

  return (
    <div className="bg-theme-paper rounded border border-theme-border shadow-sm hover:shadow transition-shadow">
      {/* Header */}
      <div className="border-b border-theme-border bg-gray-50 px-6 py-4">
        <div className="flex items-center gap-3">
          <Eye className="w-6 h-6 text-theme-primary" />
          <div>
            <h3 className="font-editorial text-xl font-bold text-theme-text">Show vs Tell</h3>
            <p className="text-xs text-theme-subtle">Detección Sensorial</p>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="p-6 space-y-5">

        {/* Explicación breve */}
        <div className="bg-blue-50 border-l-4 border-blue-400 p-3 text-xs text-gray-700">
          <div className="flex items-start gap-2">
            <Info className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-bold mb-1">¿Qué es esto?</p>
              <p className="leading-relaxed">
                Analizamos cada párrafo buscando <strong>palabras sensoriales</strong> (visuales, táctiles, auditivas, etc.)
                versus <strong>palabras abstractas</strong> (emociones nombradas, declaraciones, conceptos).
                Un ratio alto significa que "muestras" en lugar de "decir".
              </p>
            </div>
          </div>
        </div>

        {/* Showing Ratio */}
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500 mb-2 font-mono">Showing Ratio</p>
          <div className="bg-gray-50 border border-gray-200 p-4 rounded">
            <div className="flex items-baseline gap-3">
              <span className={`text-5xl font-editorial font-bold ${getRatingColor(showingRatio)}`}>
                {(showingRatio * 100).toFixed(0)}%
              </span>
              <div className="flex flex-col">
                <span className="text-sm font-bold text-gray-700">{getRatingText(showingRatio)}</span>
                <span className="text-xs text-gray-500">{getRatingDescription(showingRatio)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        <div>
          <div className="h-3 bg-gray-200 rounded-sm overflow-hidden border border-gray-300">
            <div
              className={`h-full transition-all ${getProgressBarColor(showingRatio)}`}
              style={{ width: `${showingRatio * 100}%` }}
            />
          </div>
        </div>

        {/* Reference Guide */}
        <div className="bg-gray-50 p-3 rounded border border-gray-200">
          <p className="text-xs font-bold text-gray-700 mb-2 font-mono">Guía de Referencia:</p>
          <div className="text-xs text-gray-600 space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-theme-primary rounded-full"></div>
              <span>&gt;60% = Excelente (inmersión fuerte)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
              <span>40-60% = Aceptable (balance funcional)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
              <span>&lt;40% = Mejorable (exceso de telling)</span>
            </div>
          </div>
        </div>

        {/* Ejemplos */}
        <div className="text-xs text-gray-600 bg-gray-50 p-3 rounded border border-gray-200">
          <p className="font-bold mb-2">Ejemplos:</p>
          <ul className="space-y-1 ml-4">
            <li><strong>Showing:</strong> "Las manos le temblaban mientras el sudor le corría por la frente."</li>
            <li><strong>Telling:</strong> "Estaba nervioso y asustado."</li>
          </ul>
        </div>

        {/* Critical Issues (si hay) */}
        {critical_issues && critical_issues.length > 0 && (
          <div className="pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-orange-600" />
              <p className="text-xs uppercase tracking-wide text-gray-700 font-bold">Pasajes Problemáticos</p>
            </div>
            {critical_issues.slice(0, 2).map((issue, i) => (
              <div key={i} className="text-xs text-orange-900 bg-orange-50 border border-orange-200 p-3 rounded mb-2">
                <span className="font-bold font-mono">Cap. {issue.chapter_id}:</span> {issue.description}
              </div>
            ))}
            {critical_issues.length > 2 && (
              <p className="text-xs text-gray-500 mt-2 italic">
                +{critical_issues.length - 2} problemas adicionales en el análisis completo
              </p>
            )}
          </div>
        )}

        {/* Sin issues */}
        {(!critical_issues || critical_issues.length === 0) && showingRatio >= 0.6 && (
          <div className="pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 text-theme-primary">
              <CheckCircle className="w-4 h-4" />
              <p className="text-xs font-bold">No se detectaron problemas graves de densidad sensorial</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
