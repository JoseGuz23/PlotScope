// =============================================================================
// ReflectionBadge.jsx - Badge de Estadísticas de Reflection (LYA 6.0)
// =============================================================================
// Muestra cuántos capítulos usaron reflection loops y el promedio de iteraciones.
// Le indica al escritor qué capítulos necesitaron refinamiento adicional.

import { Zap, Info } from 'lucide-react';

export default function ReflectionBadge({ stats }) {
  if (!stats || !stats.chapters_with_reflection) return null;

  const percentage = ((stats.chapters_with_reflection / stats.total_chapters) * 100).toFixed(0);
  const hasHighReflection = stats.chapters_with_reflection > stats.total_chapters / 2;

  return (
    <div className="inline-flex items-center gap-2 bg-purple-50 text-purple-700 px-4 py-2 rounded-full text-xs font-medium border border-purple-200">
      <Zap className="w-4 h-4" />
      <span className="font-bold">
        Reflection: {stats.chapters_with_reflection}/{stats.total_chapters} capítulos
      </span>
      <span className="text-purple-500">
        ({stats.avg_iterations.toFixed(1)}x promedio)
      </span>

      {/* Tooltip informativo */}
      <div className="group relative">
        <Info className="w-3 h-3 text-purple-400 cursor-help" />
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 bg-gray-900 text-white text-xs rounded-lg p-3 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 shadow-xl">
          <p className="font-bold mb-1">¿Qué es Reflection?</p>
          <p className="text-gray-300">
            {hasHighReflection
              ? `${percentage}% de los capítulos necesitaron refinamiento iterativo (auto-crítica). Esto indica que LYA mejoró significativamente el borrador inicial.`
              : `Solo ${percentage}% de los capítulos necesitaron refinamiento adicional. El resto ya tenían alta calidad.`
            }
          </p>
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-gray-900"></div>
        </div>
      </div>
    </div>
  );
}
