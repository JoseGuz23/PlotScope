// =============================================================================
// EmotionalArcWidget.jsx - Widget de Arco Emocional (LYA 6.0)
// =============================================================================
// Diseño editorial vintage 1978 - Paleta teal/paper/tinta

import { TrendingUp, TrendingDown, Activity, AlertTriangle, Info } from 'lucide-react';

export default function EmotionalArcWidget({ emotionalData }) {
  if (!emotionalData) return null;

  const { global_arc, diagnostics } = emotionalData;
  const pattern = global_arc?.emotional_pattern || 'DESCONOCIDO';
  const valence = global_arc?.avg_valence || 0;

  // Iconos por patrón (solo teal/grises)
  const patternIcons = {
    'ASCENDENTE': <TrendingUp className="w-6 h-6 text-theme-primary" />,
    'DESCENDENTE': <TrendingDown className="w-6 h-6 text-gray-600" />,
    'VALLE': <Activity className="w-6 h-6 text-theme-primary" />,
    'MONTAÑA_RUSA': <Activity className="w-6 h-6 text-gray-700" />,
    'PLANO_POSITIVO': <Activity className="w-6 h-6 text-theme-subtle" />,
    'PLANO_NEGATIVO': <Activity className="w-6 h-6 text-gray-500" />,
  };

  // Descripciones amigables
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
    <div className="bg-theme-paper rounded border border-theme-border shadow-sm hover:shadow transition-shadow">
      {/* Header */}
      <div className="border-b border-theme-border bg-gray-50 px-6 py-4">
        <div className="flex items-center gap-3">
          {patternIcons[pattern] || <Activity className="w-6 h-6 text-gray-400" />}
          <div>
            <h3 className="font-editorial text-xl font-bold text-theme-text">Arco Emocional</h3>
            <p className="text-xs text-theme-subtle">Análisis de Sentiment</p>
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
                Usamos un modelo de <strong>sentiment analysis</strong> que lee tu manuscrito en ventanas de texto
                y asigna una <strong>valencia emocional</strong> (de -1.0 negativo a +1.0 positivo) a cada segmento.
                El patrón general revela la trayectoria emocional de tu historia.
              </p>
            </div>
          </div>
        </div>

        {/* Patrón Detectado */}
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500 mb-2 font-mono">Patrón Detectado</p>
          <div className="bg-gray-50 border border-gray-200 p-4 rounded">
            <p className="text-2xl font-editorial font-bold text-theme-primary mb-1">{pattern}</p>
            <p className="text-sm text-gray-600">{patternDescriptions[pattern]}</p>
          </div>
        </div>

        {/* Valencia Promedio */}
        <div>
          <p className="text-xs uppercase tracking-wide text-gray-500 mb-2 font-mono">Tono Emocional Promedio (Valencia)</p>

          {/* Barra de valencia */}
          <div className="flex items-center gap-3">
            <div className="flex-1 h-3 bg-gray-200 rounded-sm overflow-hidden border border-gray-300">
              <div
                className={`h-full transition-all ${valence >= 0 ? 'bg-theme-primary' : 'bg-gray-600'}`}
                style={{ width: `${Math.min(Math.abs(valence) * 100, 100)}%` }}
              />
            </div>
            <span className="text-lg font-mono font-bold text-gray-800 w-16 text-right">
              {valence.toFixed(2)}
            </span>
          </div>

          {/* Interpretación */}
          <div className="mt-2 text-xs text-gray-600 bg-gray-50 p-2 rounded border border-gray-200">
            <p className="font-bold mb-1">Interpretación:</p>
            <ul className="space-y-0.5 ml-4">
              <li><strong>+1.0:</strong> Extremadamente positivo/optimista</li>
              <li><strong>0.0:</strong> Neutro/balanceado</li>
              <li><strong>-1.0:</strong> Extremadamente negativo/sombrío</li>
            </ul>
            <p className="mt-2">
              {valence >= 0.3
                ? '→ Tu historia tiene un tono predominantemente optimista.'
                : valence <= -0.3
                ? '→ Tu historia tiene un tono predominantemente sombrío/pesimista.'
                : '→ Tu historia mantiene un tono neutro o balanceado.'}
            </p>
          </div>
        </div>

        {/* Diagnósticos (si hay) */}
        {diagnostics && diagnostics.length > 0 && (
          <div className="pt-4 border-t border-gray-200">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-4 h-4 text-orange-600" />
              <p className="text-xs uppercase tracking-wide text-gray-700 font-bold">Diagnósticos de Patrón</p>
            </div>
            {diagnostics.slice(0, 2).map((d, i) => (
              <div key={i} className="text-xs text-orange-900 bg-orange-50 border border-orange-200 p-3 rounded mb-2">
                <span className="font-bold font-mono">Cap. {d.chapter_id}:</span> {d.description}
              </div>
            ))}
            {diagnostics.length > 2 && (
              <p className="text-xs text-gray-500 mt-2 italic">
                +{diagnostics.length - 2} diagnósticos adicionales disponibles en la Biblia Narrativa
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
