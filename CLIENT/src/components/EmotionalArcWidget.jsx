// =============================================================================
// EmotionalArcWidget.jsx - Widget de Arco Emocional (LYA 6.0)
// =============================================================================
// Muestra el patrón emocional detectado en el manuscrito
// y diagnósticos sobre la progresión emocional de la narrativa.

import { TrendingUp, TrendingDown, Activity, AlertTriangle } from 'lucide-react';

export default function EmotionalArcWidget({ emotionalData }) {
  if (!emotionalData) return null;

  const { global_arc, diagnostics } = emotionalData;
  const pattern = global_arc?.emotional_pattern || 'DESCONOCIDO';
  const valence = global_arc?.avg_valence || 0;

  // Iconos por patrón
  const patternIcons = {
    'ASCENDENTE': <TrendingUp className="w-6 h-6 text-green-500" />,
    'DESCENDENTE': <TrendingDown className="w-6 h-6 text-red-500" />,
    'VALLE': <Activity className="w-6 h-6 text-blue-500" />,
    'MONTAÑA_RUSA': <Activity className="w-6 h-6 text-purple-500" />,
    'PLANO_POSITIVO': <Activity className="w-6 h-6 text-teal-500" />,
    'PLANO_NEGATIVO': <Activity className="w-6 h-6 text-gray-500" />,
  };

  // Descripciones amigables para escritores
  const patternDescriptions = {
    'ASCENDENTE': 'Tensión creciente (típico de thriller/suspense)',
    'DESCENDENTE': 'Arco trágico o decadente (grimdark)',
    'VALLE': 'Estructura clásica de 3 actos (bajada-subida)',
    'MONTAÑA_RUSA': 'Alta variación emocional (acción/aventura)',
    'PLANO_POSITIVO': 'Tono optimista constante (slice-of-life)',
    'PLANO_NEGATIVO': 'Tono sombrío constante (noir/distópico)',
    'DESCONOCIDO': 'Patrón no identificado',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 border border-gray-200 hover:shadow-xl transition-shadow">
      {/* Header */}
      <div className="flex items-center gap-3 mb-4">
        {patternIcons[pattern] || <Activity className="w-6 h-6 text-gray-400" />}
        <div>
          <h3 className="font-bold text-gray-900">Arco Emocional</h3>
          <p className="text-sm text-gray-500">Análisis de ritmo emocional</p>
        </div>
      </div>

      <div className="space-y-3">
        {/* Patrón Detectado */}
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Patrón Detectado</p>
          <p className="text-lg font-bold text-theme-primary">{pattern}</p>
          <p className="text-xs text-gray-600 mt-1">{patternDescriptions[pattern]}</p>
        </div>

        {/* Valencia Promedio (tono emocional) */}
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500 mb-1">Tono Emocional Promedio</p>
          <div className="flex items-center gap-2">
            <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all ${valence >= 0 ? 'bg-green-500' : 'bg-red-500'}`}
                style={{ width: `${Math.abs(valence) * 100}%` }}
              />
            </div>
            <span className="text-sm font-mono">{valence.toFixed(2)}</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            {valence >= 0.3 ? '✓ Tono optimista' : valence <= -0.3 ? '✓ Tono sombrío' : '~ Tono neutro/balanceado'}
          </p>
        </div>

        {/* Diagnósticos (si hay) */}
        {diagnostics && diagnostics.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className="w-4 h-4 text-orange-500" />
              <p className="text-xs uppercase tracking-wide text-gray-500 font-bold">Diagnósticos</p>
            </div>
            {diagnostics.slice(0, 2).map((d, i) => (
              <div key={i} className="text-xs text-orange-700 bg-orange-50 p-2 rounded mb-1">
                <span className="font-bold">Cap. {d.chapter_id}:</span> {d.description}
              </div>
            ))}
            {diagnostics.length > 2 && (
              <p className="text-xs text-gray-400 mt-1">
                +{diagnostics.length - 2} diagnósticos más en la Biblia
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
