// =============================================================================
// ProjectStatus.jsx - FIXED PHASE TRACKING & GREEN STEPS
// =============================================================================

import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { 
  Upload, BookOpen, Search, FileText, Brain, Scroll, 
  Map, Edit, Save, CheckCircle2, XCircle, Loader2, 
  Clock, AlertOctagon, Terminal, ArrowLeft
} from 'lucide-react';

const PHASES = [
  { key: 'upload', icon: Upload, label: 'Recepción', description: 'Archivo recibido' },
  { key: 'segment', icon: BookOpen, label: 'Segmentación', description: 'División estructural' },
  { key: 'analyze1', icon: Search, label: 'Análisis Factual', description: 'Extracción de datos' },
  { key: 'consolidate', icon: FileText, label: 'Consolidación', description: 'Unificando hallazgos' },
  { key: 'analyze2-3', icon: Brain, label: 'Análisis Profundo', description: 'Estructura y calidad' },
  { key: 'bible', icon: Scroll, label: 'Biblia Narrativa', description: 'Generación de guía' },
  { key: 'carta', icon: FileText, label: 'Carta Editorial', description: 'Recomendaciones' },
  { key: 'notas', icon: Edit, label: 'Notas de Margen', description: 'Anotaciones contextuales' },
  { key: 'arcs', icon: Map, label: 'Mapeo de Arcos', description: 'Trayectorias narrativas' },
  { key: 'edit', icon: Edit, label: 'Edición IA', description: 'Corrección estilística' },
  { key: 'save', icon: Save, label: 'Finalización', description: 'Compilando entregables' },
];

function getPhaseIndex(customStatus) {
  if (!customStatus) return 0;
  const s = String(customStatus).toLowerCase();
  
  if (s.includes('terminated')) return -1;
  
  // 1. Segmentación
  if (s.includes('segment')) return 1;
  
  // 2. Análisis Factual (incluye polling adaptativo)
  if (s.includes('capa 1') || s.includes('factual') || s.includes('batch c1') || 
      s.includes('batch analysis') || (s.includes('poll') && s.includes('c1'))) return 2;
  
  // 3. Consolidación
  if (s.includes('consolid') || s.includes('unificando')) return 3;
  
  // 4. Análisis Profundo (paralelo: layer2 + layer3)
  if (s.includes('paralelo') || s.includes('parallel') || 
      s.includes('layer2') || s.includes('estructur') || 
      s.includes('layer3') || s.includes('cualitativ')) return 4;
  
  // 5. Biblia
  if (s.includes('biblia') || s.includes('holistic') || 
      s.includes('esperando') || s.includes('aprobacion')) return 5;
  
  // 6. Carta Editorial
  if (s.includes('carta') || s.includes('editorial')) return 6;
  
  // 7. Notas de Margen
  if (s.includes('notas') || s.includes('margin')) return 7;
  
  // 8. Arcos
  if (s.includes('arc') || s.includes('arco') || s.includes('map')) return 8;
  
  // 9. Edición
  if (s.includes('edici') || s.includes('edit') || s.includes('claude')) return 9;
  
  // 10. Finalización
  if (s.includes('final') || s.includes('guard') || s.includes('reconst') || s.includes('save')) return 10;
  
  return 0;
}

export default function ProjectStatus() {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  
  const [status, setStatus] = useState(null);
  const [projectCreatedAt, setProjectCreatedAt] = useState(null);
  const [error, setError] = useState(null);
  const [isTerminating, setIsTerminating] = useState(false);
  const [terminated, setTerminated] = useState(false);
  const [logs, setLogs] = useState([]);
  const [currentPhase, setCurrentPhase] = useState(0);
  const [elapsedTime, setElapsedTime] = useState('00:00');
  
  const pollIntervalRef = useRef(null);
  const timerIntervalRef = useRef(null);

  useEffect(() => {
    projectsAPI.getById(projectId).then(data => {
      const dateStr = data?.created_at || data?.createdAt;
      if (dateStr) setProjectCreatedAt(new Date(dateStr));
      else setProjectCreatedAt(new Date());
    }).catch(() => setProjectCreatedAt(new Date()));
  }, [projectId]);

  useEffect(() => {
    checkStatus();
    pollIntervalRef.current = setInterval(checkStatus, 4000);
    timerIntervalRef.current = setInterval(updateTimer, 1000);
    return () => {
      clearInterval(pollIntervalRef.current);
      clearInterval(timerIntervalRef.current);
    };
  }, [projectId, projectCreatedAt]);

  function updateTimer() {
    if (status?.is_completed || status?.is_failed || terminated || !projectCreatedAt) return;
    const diff = Math.floor((new Date() - projectCreatedAt) / 1000);
    if (diff >= 0) {
      const m = Math.floor(diff / 60);
      const s = diff % 60;
      setElapsedTime(`${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`);
    }
  }

  async function checkStatus() {
    if (terminated) return;
    try {
      const data = await projectsAPI.getStatus(projectId);
      setStatus(data);
      
      if (data.custom_status) {
        setLogs(prev => {
          const last = prev[prev.length - 1];
          if (!last || last.message !== data.custom_status) {
            return [...prev, { 
              time: new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'}), 
              message: data.friendly_message || data.custom_status 
            }].slice(-50);
          }
          return prev;
        });
      }

      // IMPORTANTE: Si por alguna razón el status falla en matchear, 
      // mantenemos la fase anterior para evitar el "parpadeo" a recepción.
      const newPhase = getPhaseIndex(data.custom_status);
      if (newPhase > 0) {
        setCurrentPhase(newPhase);
      }
      
      if (data.is_completed) {
        clearInterval(pollIntervalRef.current);
        setTimeout(() => navigate(`/proyecto/${projectId}/editor`), 2000);
      }
      
      if (data.is_failed) {
        clearInterval(pollIntervalRef.current);
        setError('El orquestador reportó un fallo crítico.');
      }
    } catch (err) { /* ignore */ }
  }

  const handleStop = async () => {
    if (!confirm('¿Detener el proceso?')) return;
    setIsTerminating(true);
    try {
      await projectsAPI.terminate(projectId);
      setTerminated(true);
      setStatus(prev => ({ ...prev, custom_status: 'Detenido por usuario' }));
    } catch (err) {
      alert(err.message);
      setIsTerminating(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pt-8 pb-12 px-6">
      <div className="max-w-[1600px] mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="font-editorial text-3xl text-gray-900">Estado del Análisis</h1>
            <p className="text-gray-500 text-sm flex items-center gap-2 mt-1">
              ID: <span className="font-mono text-xs bg-white border px-2 rounded text-gray-600">{projectId}</span>
            </p>
          </div>
          <Link to="/dashboard" className="flex items-center gap-2 text-gray-500 hover:text-gray-900 text-sm font-bold">
            <ArrowLeft className="w-4 h-4" /> Volver
          </Link>
        </div>

        <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-180px)] min-h-[600px]">
          {/* COLUMNA IZQUIERDA */}
          <div className="flex-1 flex flex-col gap-6 h-full overflow-y-auto pr-2 custom-scrollbar">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden shrink-0">
              <div className="px-8 py-8 border-b border-gray-100 flex justify-between items-center bg-white">
                <div className="flex items-center gap-6">
                  <div className={`w-16 h-16 rounded-2xl flex items-center justify-center shadow-sm ${status?.is_completed ? 'bg-green-50 text-green-600' : 'bg-blue-50 text-theme-primary'}`}>
                    {status?.is_completed ? <CheckCircle2 className="w-8 h-8" /> : terminated ? <XCircle className="w-8 h-8" /> : <Loader2 className="w-8 h-8 animate-spin" />}
                  </div>
                  <div>
                    <h2 className="font-editorial text-2xl text-gray-900 mb-1">
                      {terminated ? 'Proceso Detenido' : status?.is_completed ? '¡Completado!' : status?.friendly_message || 'Iniciando sistema...'}
                    </h2>
                    {status?.custom_status?.includes('Esperando') && (
                       <Link to={`/proyecto/${projectId}/biblia`} className="text-sm font-bold text-blue-600 underline hover:text-blue-800 animate-pulse">
                         → Acción Requerida: Aprobar Biblia
                       </Link>
                    )}
                  </div>
                </div>
                <div className="text-right bg-gray-50 px-4 py-2 rounded-lg border border-gray-100">
                   <div className="flex items-center gap-2 text-gray-400 mb-0.5 justify-end">
                      <Clock className="w-3 h-3" /> <span className="text-[10px] font-bold tracking-widest">TIEMPO</span>
                   </div>
                   <div className="font-mono text-2xl font-bold text-gray-800 tabular-nums">{elapsedTime}</div>
                </div>
              </div>

              {/* GRID DE FASES - AQUÍ ESTÁ LA LÓGICA DE COLOR VERDE */}
              <div className="p-8 bg-gray-50/50">
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {PHASES.map((phase, idx) => {
                    // LOGICA CLAVE: Si ya completó TODO, o si el índice actual es mayor al de esta fase.
                    const isCompleted = status?.is_completed || currentPhase > idx;
                    const isCurrent = !status?.is_completed && !terminated && currentPhase === idx;
                    
                    return (
                      <div key={phase.key} className={`
                        flex items-center gap-4 p-4 rounded-xl border transition-all 
                        ${isCurrent ? 'bg-white border-theme-primary shadow-lg ring-1 ring-theme-primary/10' : 'bg-white border-gray-100'}
                        ${!isCompleted && !isCurrent ? 'opacity-50 grayscale' : ''}
                      `}>
                        <div className={`
                          w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-colors
                          ${isCompleted ? 'bg-green-100 text-green-600' : isCurrent ? 'bg-theme-primary text-white' : 'bg-gray-100 text-gray-400'}
                        `}>
                          {/* Icono: Si está completado, Check verde. Si es actual, Icono blanco. Si futuro, Icono gris */}
                          {isCompleted ? <CheckCircle2 className="w-6 h-6" /> : <phase.icon className="w-6 h-6" />}
                        </div>
                        <div>
                          <h3 className={`text-sm font-bold uppercase ${isCurrent ? 'text-theme-primary' : isCompleted ? 'text-green-700' : 'text-gray-500'}`}>
                            {phase.label}
                          </h3>
                          <p className="text-[11px] text-gray-400">{phase.description}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
            {error && <div className="bg-red-50 border border-red-200 p-4 rounded-xl text-red-700 font-bold flex items-center gap-3"><AlertOctagon /> {error}</div>}
          </div>

          {/* COLUMNA DERECHA */}
          <div className="w-full lg:w-[420px] shrink-0 h-full flex flex-col">
             <div className="bg-[#0f172a] rounded-xl shadow-xl border border-gray-800 overflow-hidden flex flex-col h-full">
                <div className="bg-[#1e293b] px-4 py-3 border-b border-gray-700 flex justify-between items-center"><span className="text-gray-200 font-mono text-xs font-bold uppercase">System Logs</span></div>
                <div className="p-4 overflow-y-auto font-mono text-[11px] space-y-2 flex-1 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent bg-[#0f172a]">
                   {logs.map((log, i) => (
                     <div key={i} className="flex gap-3 text-gray-300 border-l-2 border-transparent hover:border-blue-500/50 p-1">
                        <span className="text-blue-400/70 shrink-0 font-bold">{log.time}</span>
                        <span className="break-words text-gray-300">{log.message}</span>
                     </div>
                   ))}
                </div>
                {!status?.is_completed && !terminated && (
                    <div className="p-4 bg-[#1e293b] border-t border-gray-700">
                      <button onClick={handleStop} disabled={isTerminating} className="w-full py-2 text-xs font-bold text-red-400 hover:bg-red-500/10 border border-red-500/30 rounded-lg transition-all">
                        {isTerminating ? 'Deteniendo...' : 'ABORTAR PROCESO'}
                      </button>
                    </div>
                )}
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}