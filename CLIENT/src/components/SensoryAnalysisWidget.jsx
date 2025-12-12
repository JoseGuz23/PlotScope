// =============================================================================
// SensoryAnalysisWidget.jsx - Widget de Análisis Sensorial (LYA 6.0)
// =============================================================================
// Muestra el ratio de "Show vs Tell" y diagnósticos de densidad sensorial.
// Ayuda al escritor a identificar áreas con exceso de "telling" abstracto.

import { Eye, AlertTriangle, CheckCircle } from 'lucide-react';

export default function SensoryAnalysisWidget({ sensoryData }) {
  if (!sensoryData) return null;

  const { global_metrics, critical_issues } = sensoryData;
  const showingRatio = global_metrics?.avg_showing_ratio || 0;

  // Función de rating
  const getRatingColor = (ratio) => {
    if (ratio >= 0.6) return 'text-green-600';
    if (ratio >= 0.4) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRatingText = (ratio) => {
    if (ratio >= 0.6) return 'Excelente';
    if (ratio >= 0.4) return 'Aceptable';
    return 'Requiere trabajo';
  };

  const getRatingDescription = (ratio) => {
    if (ratio >= 0.6) return 'Tu manuscrito muestra más de lo que dice. ¡Sigue así!';
    if (ratio >= 0.4) return 'Buen balance, pero puedes mejorar algunas escenas.';
    return 'Intenta convertir más declaraciones en acciones/sensaciones.';
  };

  const getProgressBarColor = (ratio) => {
    if (ratio >= 0.6) return 'bg-green-500';
    if (ratio >= 0.4) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200 hover:shadow-xl transition-shadow">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        <Eye className="w-6 h-6 text-purple-500" />
        <div>
          <h3 className="font-bold text-gray-900">Show vs Tell</h3>
          <p className="text-sm text-gray-500">Detección sensorial</p>
        </div>
      </div>

      <div className="space-y-3">
        {/* Showing Ratio */}
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Showing Ratio</p>
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-bold ${getRatingColor(showingRatio)}`}>
              {(showingRatio * 100).toFixed(0)}%
            </span>
            <span className="text-sm text-gray-500">{getRatingText(showingRatio)}</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all ${getProgressBarColor(showingRatio)}`}
            style={{ width: `${showingRatio * 100}%` }}
          />
        </div>

        {/* Descripción */}
        <p className="text-xs text-gray-600">
          {getRatingDescription(showingRatio)}
        </p>

        {/* Reference Bar (muestra el objetivo ideal) */}
        <div className="bg-gray-50 p-3 rounded-lg border border-gray-100">
          <p className="text-xs font-bold text-gray-700 mb-2">Referencia:</p>
          <div className="flex items-center gap-2 text-xs text-gray-600">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span>&gt;60% = Excelente</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
              <span>40-60% = Aceptable</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span>&lt;40% = Mejorable</span>
            </div>
          </div>
        </div>

        {/* Critical Issues (si hay) */}
        {critical_issues && critical_issues.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-orange-500" />
              <p className="text-xs uppercase tracking-wide text-gray-500 font-bold">Issues Críticos</p>
            </div>
            {critical_issues.slice(0, 2).map((issue, i) => (
              <div key={i} className="text-xs text-orange-700 bg-orange-50 p-2 rounded mb-1">
                <span className="font-bold">Cap. {issue.chapter_id}:</span> {issue.description}
              </div>
            ))}
            {critical_issues.length > 2 && (
              <p className="text-xs text-gray-400 mt-1">
                +{critical_issues.length - 2} issues más en el análisis completo
              </p>
            )}
          </div>
        )}

        {/* Sin issues */}
        {(!critical_issues || critical_issues.length === 0) && showingRatio >= 0.6 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle className="w-4 h-4" />
              <p className="text-xs font-bold">No se detectaron problemas graves</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
