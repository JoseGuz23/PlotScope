// =============================================================================
// ProjectStatus.jsx - ESTADO DE PROCESAMIENTO EN TIEMPO REAL
// =============================================================================

import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { projectsAPI } from '../services/api';

// Fases del orquestador con sus iconos y descripciones
const PHASES = [
  { key: 'upload', icon: '📤', label: 'Subida', description: 'Archivo recibido' },
  { key: 'segment', icon: '📖', label: 'Segmentación', description: 'Dividiendo en capítulos' },
  { key: 'analyze1', icon: '🔍', label: 'Análisis Factual', description: 'Extrayendo datos básicos' },
  { key: 'analyze2', icon: '📊', label: 'Análisis Estructural', description: 'Evaluando estructura' },
  { key: 'analyze3', icon: '🎭', label: 'Análisis Cualitativo', description: 'Profundizando en narrativa' },
  { key: 'bible', icon: '📜', label: 'Biblia Narrativa', description: 'Generando guía editorial' },
  { key: 'arcs', icon: '🗺️', label: 'Arcos', description: 'Mapeando personajes' },
  { key: 'edit', icon: '✏️', label: 'Edición', description: 'Aplicando correcciones' },
  { key: 'save', icon: '💾', label: 'Guardado', description: 'Finalizando' },
];

// Mapeo de customStatus del backend a índice de fase
function getPhaseIndex(customStatus) {
  if (!customStatus) return 0;
  const status = customStatus.toLowerCase();
  
  if (status.includes('segment')) return 1;
  if (status.includes('fase 2') || status.includes('capa 1') || status.includes('factual')) return 2;
  if (status.includes('fase 3') || status.includes('fase 4') || status.includes('estructur')) return 3;
  if (status.includes('fase 5') || status.includes('cualitativ')) return 4;
  if (status.includes('fase 6') || status.includes('biblia') || status.includes('holístic')) return 5;
  if (status.includes('fase 10') || status.includes('arco')) return 6;
  if (status.includes('fase 11') || status.includes('edici') || status.includes('claude')) return 7;
  if (status.includes('final') || status.includes('guard') || status.includes('recons')) return 8;
  
  return 0;
}

export default function ProjectStatus() {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [logs, setLogs] = useState([]);
  const [currentPhase, setCurrentPhase] = useState(0);
  const [startTime] = useState(Date.now());
  const [elapsedTime, setElapsedTime] = useState('0:00');
  
  const pollIntervalRef = useRef(null);
  const timerIntervalRef = useRef(null);

  // Polling del estado
  useEffect(() => {
    checkStatus();
    
    pollIntervalRef.current = setInterval(checkStatus, 5000); // Cada 5 segundos
    timerIntervalRef.current = setInterval(updateTimer, 1000);
    
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [projectId]);

  function updateTimer() {
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    setElapsedTime(`${minutes}:${seconds.toString().padStart(2, '0')}`);
  }

  async function checkStatus() {
    try {
      const data = await projectsAPI.getStatus(projectId);
      setStatus(data);
      
      // Agregar al log si hay nuevo status
      if (data.custom_status) {
        setLogs(prev => {
          const lastLog = prev[prev.length - 1];
          if (!lastLog || lastLog.message !== data.custom_status) {
            return [...prev, {
              time: new Date().toLocaleTimeString(),
              message: data.friendly_message || data.custom_status
            }].slice(-15); // Mantener últimos 15 logs
          }
          return prev;
        });
      }
      
      // Actualizar fase actual
      const phaseIdx = getPhaseIndex(data.custom_status);
      setCurrentPhase(phaseIdx);
      
      // Si completó, redirigir a la biblia
      if (data.is_completed) {
        clearInterval(pollIntervalRef.current);
        clearInterval(timerIntervalRef.current);
        
        // Esperar un momento y redirigir
        setTimeout(() => {
          navigate(`/proyecto/${projectId}/biblia`);
        }, 2000);
      }
      
      // Si falló, mostrar error
      if (data.is_failed) {
        clearInterval(pollIntervalRef.current);
        clearInterval(timerIntervalRef.current);
        setError('El procesamiento falló. Por favor, intenta de nuevo.');
      }
      
    } catch (err) {
      console.error('Error checking status:', err);
      // No mostrar error inmediatamente, puede ser que el orquestador aún no inicie
    }
  }

  return (
    <div className="max-w-3xl mx-auto pt-10">
      {/* Header */}
      <div className="text-center mb-12">
        <span className="font-mono text-xs font-bold text-theme-primary uppercase tracking-widest mb-2 block">
          Paso 2 de 3
        </span>
        <h1 className="font-editorial text-4xl font-bold text-gray-900 mb-4">
          Procesando Manuscrito
        </h1>
        <p className="font-sans text-gray-500">
          Nuestro orquestador está analizando tu obra. Esto puede tomar varios minutos.
        </p>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border-t-4 border-red-500 p-6 mb-8 rounded-sm">
          <div className="flex items-center gap-3">
            <span className="text-2xl">❌</span>
            <div>
              <p className="font-bold text-red-800">{error}</p>
              <Link to="/nuevo" className="text-red-600 underline text-sm mt-2 inline-block">
                Intentar de nuevo
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Main Card */}
      <div className="bg-white border-t-4 border-gray-900 shadow-xl rounded-sm overflow-hidden">
        
        {/* Timer */}
        <div className="bg-gray-50 border-b border-gray-200 px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${status?.is_completed ? 'bg-green-500' : status?.is_failed ? 'bg-red-500' : 'bg-theme-primary animate-pulse'}`}></div>
            <span className="font-mono text-sm text-gray-600">
              {status?.is_completed ? 'Completado' : status?.is_failed ? 'Error' : 'En progreso'}
            </span>
          </div>
          <div className="font-mono text-2xl font-bold text-gray-900">
            {elapsedTime}
          </div>
        </div>

        {/* Phases Progress */}
        <div className="p-8">
          <div className="space-y-4">
            {PHASES.map((phase, idx) => (
              <PhaseRow 
                key={phase.key}
                phase={phase}
                index={idx}
                currentPhase={currentPhase}
                isCompleted={status?.is_completed}
              />
            ))}
          </div>
        </div>

        {/* Current Status Message */}
        <div className="bg-gray-50 border-t border-gray-200 px-8 py-6">
          <div className="flex items-center gap-4">
            <div className="text-3xl">
              {status?.is_completed ? '✅' : status?.is_failed ? '❌' : PHASES[currentPhase]?.icon || '⏳'}
            </div>
            <div>
              <p className="font-bold text-gray-900">
                {status?.is_completed 
                  ? '¡Procesamiento completado!' 
                  : status?.friendly_message || 'Iniciando procesamiento...'}
              </p>
              <p className="font-mono text-xs text-gray-500 mt-1">
                ID: {projectId}
              </p>
            </div>
          </div>
        </div>

        {/* Log Console */}
        <div className="border-t border-gray-200">
          <button 
            className="w-full px-8 py-3 text-left text-xs font-bold uppercase tracking-wide text-gray-500 hover:bg-gray-50 flex justify-between items-center"
            onClick={() => document.getElementById('log-panel').classList.toggle('hidden')}
          >
            <span>📋 Registro de actividad</span>
            <span>▼</span>
          </button>
          <div id="log-panel" className="hidden bg-gray-900 text-green-400 font-mono text-xs p-4 max-h-48 overflow-y-auto">
            {logs.length === 0 ? (
              <p className="text-gray-500">Esperando actividad...</p>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className="py-1">
                  <span className="text-gray-500">[{log.time}]</span> {log.message}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-8 flex justify-between items-center">
        <Link 
          to="/dashboard" 
          className="font-mono text-sm text-gray-500 hover:text-gray-700"
        >
          ← Volver al dashboard
        </Link>
        
        {status?.is_completed && (
          <button
            onClick={() => navigate(`/proyecto/${projectId}/biblia`)}
            className="bg-theme-primary hover:bg-theme-primary-hover text-white font-extrabold py-3 px-6 rounded-sm shadow-lg transition-all uppercase tracking-widest text-sm"
          >
            Revisar Biblia →
          </button>
        )}
      </div>

      {/* Info */}
      <div className="mt-12 bg-blue-50 border border-blue-200 rounded-sm p-6">
        <h3 className="font-bold text-blue-900 mb-2">💡 ¿Qué está pasando?</h3>
        <ul className="text-sm text-blue-800 space-y-2">
          <li>• <strong>Segmentación:</strong> Dividimos tu libro en capítulos manejables</li>
          <li>• <strong>Análisis:</strong> Tres capas de análisis con Gemini AI</li>
          <li>• <strong>Biblia:</strong> Generamos una guía con el ADN de tu obra</li>
          <li>• <strong>Edición:</strong> Claude aplica correcciones respetando tu voz</li>
        </ul>
        <p className="text-xs text-blue-600 mt-4">
          Tiempo estimado: 5-30 minutos dependiendo del tamaño del manuscrito
        </p>
      </div>
    </div>
  );
}

// =============================================================================
// COMPONENTE AUXILIAR: Fila de fase
// =============================================================================

function PhaseRow({ phase, index, currentPhase, isCompleted }) {
  const isPast = isCompleted || index < currentPhase;
  const isCurrent = !isCompleted && index === currentPhase;
  const isFuture = !isCompleted && index > currentPhase;
  
  return (
    <div className={`
      flex items-center gap-4 p-3 rounded-sm transition-all
      ${isCurrent ? 'bg-theme-primary/10 border-l-4 border-theme-primary' : ''}
      ${isPast ? 'opacity-60' : ''}
    `}>
      {/* Icon */}
      <div className={`
        w-10 h-10 rounded-full flex items-center justify-center text-lg
        ${isPast ? 'bg-green-100 text-green-600' : ''}
        ${isCurrent ? 'bg-theme-primary text-white' : ''}
        ${isFuture ? 'bg-gray-100 text-gray-400' : ''}
      `}>
        {isPast ? '✓' : phase.icon}
      </div>
      
      {/* Label */}
      <div className="flex-1">
        <p className={`
          font-bold text-sm
          ${isPast ? 'text-green-700' : ''}
          ${isCurrent ? 'text-theme-primary' : ''}
          ${isFuture ? 'text-gray-400' : ''}
        `}>
          {phase.label}
        </p>
        <p className={`
          text-xs
          ${isPast ? 'text-green-600' : ''}
          ${isCurrent ? 'text-theme-primary' : ''}
          ${isFuture ? 'text-gray-300' : ''}
        `}>
          {phase.description}
        </p>
      </div>
      
      {/* Status indicator */}
      {isCurrent && (
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-theme-primary rounded-full animate-ping"></div>
          <span className="font-mono text-xs text-theme-primary">Procesando</span>
        </div>
      )}
      {isPast && (
        <span className="font-mono text-xs text-green-600">Completado</span>
      )}
    </div>
  );
}