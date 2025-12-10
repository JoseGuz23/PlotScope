// =============================================================================
// ProjectStatus.jsx - TIMER INFALIBLE (ID Parsing Fallback)
// =============================================================================

import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import { 
  Upload, BookOpen, Search, FileText, Brain, Scroll, 
  Map, Edit, Save, Loader2, Clock, AlertOctagon, 
  Terminal, StopCircle, ArrowRight, AlertTriangle, Check
} from 'lucide-react';

const PHASES = [
  { key: 'upload', icon: Upload, label: 'Recepción', description: 'Carga inicial del archivo' },
  { key: 'segment', icon: BookOpen, label: 'Segmentación', description: 'División estructural' },
  { key: 'analyze1', icon: Search, label: 'Análisis Factual', description: 'Extracción de datos duros' },
  { key: 'consolidate', icon: FileText, label: 'Consolidación', description: 'Unificación de hallazgos' },
  { key: 'analyze2-3', icon: Brain, label: 'Análisis Profundo', description: 'Estructura y calidad' },
  { key: 'bible', icon: Scroll, label: 'Biblia Narrativa', description: 'Generación de guía maestra' },
  { key: 'carta', icon: FileText, label: 'Carta Editorial', description: 'Feedback profesional' },
  { key: 'notas', icon: Edit, label: 'Notas de Margen', description: 'Anotaciones contextuales' },
  { key: 'arcs', icon: Map, label: 'Mapeo de Arcos', description: 'Trayectorias narrativas' },
  { key: 'edit', icon: Edit, label: 'Edición IA', description: 'Corrección estilística' },
  { key: 'save', icon: Save, label: 'Finalización', description: 'Compilando entregables' },
];

// --- FUNCIÓN DE RESCATE: EXTRAER FECHA DEL ID ---
// Formato esperado: UserID_YYYYMMDD_HHMMSS (Ej: 2110_20251210_204409)
function extractDateFromId(id) {
  try {
    if (!id) return null;
    const parts = id.split('_');
    // Buscamos las partes que parecen fecha y hora (normalmente indices 1 y 2)
    if (parts.length >= 3) {
      const datePart = parts[1]; // 20251210
      const timePart = parts[2]; // 204409
      
      if (datePart.length === 8 && timePart.length >= 6) {
        const year = parseInt(datePart.substring(0, 4));
        const month = parseInt(datePart.substring(4, 6)) - 1; // JS meses son 0-11
        const day = parseInt(datePart.substring(6, 8));
        
        const hour = parseInt(timePart.substring(0, 2));
        const min = parseInt(timePart.substring(2, 4));
        const sec = parseInt(timePart.substring(4, 6));
        
        const generatedDate = new Date(year, month, day, hour, min, sec);
        console.log("🕒 Fecha recuperada del ID:", generatedDate);
        return generatedDate;
      }
    }
  } catch (e) {
    console.warn("No se pudo extraer fecha del ID:", e);
  }
  return null;
}

function getPhaseIndex(customStatus) {
    if (!customStatus) return 0;
    const s = String(customStatus).toLowerCase();

    if (s.includes('terminated')) return -1;
    if (s.includes('segment')) return 1;
    if (s.includes('capa 1') || s.includes('factual')) return 2;
    if (s.includes('consolid')) return 3;
    if (s.includes('paralelo') || s.includes('layer2') || s.includes('estructur') || s.includes('qualitative')) return 4;
    if (s.includes('biblia') || s.includes('holistic') || s.includes('esperando')) return 5;
    if (s.includes('carta') || s.includes('editorial')) return 6;
    if (s.includes('notas') || s.includes('margin')) return 7;
    if (s.includes('arc') || s.includes('arco')) return 8;
    if (s.includes('edici') || s.includes('edit')) return 9;
    if (s.includes('final') || s.includes('guard')) return 10;

    // Si contiene "batch" pero no es Capa 1, intentar identificar contexto
    if (s.includes('batch')) {
      if (s.includes('arc_maps') || s.includes('arcs')) return 8;
      if (s.includes('notas') || s.includes('margin')) return 7;
      if (s.includes('edit') || s.includes('edicion')) return 9;
      return 2; // Por defecto, batch es Capa 1
    }

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
  const logsContainerRef = useRef(null);

  // 1. CARGA INICIAL ROBUSTA
  useEffect(() => {
    console.log("🔍 Intentando extraer fecha del projectId:", projectId);

    // Intento 1: Extraer del ID inmediatamente (Es lo más rápido y CORRECTO)
    const dateFromId = extractDateFromId(projectId);
    if (dateFromId) {
      console.log("✅ Fecha extraída del ID:", dateFromId);
      setProjectCreatedAt(dateFromId);
    } else {
      console.warn("⚠️ No se pudo extraer fecha del ID, usando fallback API");

      // SOLO si no hay fecha del ID, consultar API como fallback
      projectsAPI.getById(projectId).then(data => {
        console.log("📡 Respuesta API getById (fallback):", data);
        const apiDate = data?.created_at || data?.createdAt || data?.timestamp;
        if (apiDate) {
          console.log("✅ Fecha obtenida de API (fallback):", apiDate);
          setProjectCreatedAt(new Date(apiDate));
        } else {
          console.warn("⚠️ API no retornó fecha válida");
        }
      }).catch(err => {
        console.error("❌ Error consultando API:", err);
      });
    }
  }, [projectId]);

  // 2. POLLING Y TIMER (corregido para reiniciar cuando projectCreatedAt cambie)
  useEffect(() => {
    checkStatus();
    pollIntervalRef.current = setInterval(checkStatus, 4000);

    return () => {
      clearInterval(pollIntervalRef.current);
    };
  }, [projectId]);

  // 2B. TIMER SEPARADO - Se reinicia cuando projectCreatedAt se establece
  useEffect(() => {
    if (timerIntervalRef.current) {
      clearInterval(timerIntervalRef.current);
    }

    if (projectCreatedAt && !status?.is_completed && !status?.is_failed && !terminated) {
      console.log("⏱️ Timer iniciado con fecha:", projectCreatedAt);

      // Función de actualización del timer dentro del useEffect
      const tick = () => {
        const now = new Date();
        const diff = Math.floor((now.getTime() - projectCreatedAt.getTime()) / 1000);

        if (diff >= 0) {
          const m = Math.floor(diff / 60);
          const s = diff % 60;
          setElapsedTime(`${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`);
        }
      };

      tick(); // Actualizar inmediatamente
      timerIntervalRef.current = setInterval(tick, 1000);
    }

    return () => {
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
      }
    };
  }, [projectCreatedAt, status?.is_completed, status?.is_failed, terminated]);

  // 3. AUTO-SCROLL LOGS
  useEffect(() => {
    if (logsContainerRef.current) {
        const container = logsContainerRef.current;
        container.scrollTop = container.scrollHeight;
    }
  }, [logs]);

  async function checkStatus() {
    if (terminated) return;
    try {
      const data = await projectsAPI.getStatus(projectId);
      setStatus(data);

      // Si aun no tenemos fecha y la API de status la trae, úsala
      if (!projectCreatedAt && (data.created_at || data.createdAt || data.startTime)) {
         const dateStr = data.created_at || data.createdAt || data.startTime;
         if (dateStr) setProjectCreatedAt(new Date(dateStr));
      }
      
      // Logs
      if (data.custom_status) {
        setLogs(prev => {
          const last = prev[prev.length - 1];
          if (!last || last.message !== data.custom_status) {
            return [...prev, { 
              time: new Date().toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'}), 
              message: data.friendly_message || data.custom_status 
            }].slice(-200);
          }
          return prev;
        });
      }

      // Fases
      const newPhase = getPhaseIndex(data.custom_status);
      if (newPhase > 0) setCurrentPhase(newPhase);
      
      // Finalización
      if (data.is_completed) {
        clearInterval(pollIntervalRef.current);
        setTimeout(() => navigate(`/proyecto/${projectId}/editor`), 2000);
      }
      
      if (data.is_failed) {
        clearInterval(pollIntervalRef.current);
        setError('El orquestador reportó un fallo crítico. Revise los logs.');
      }
    } catch (err) { 
        console.warn("Error polling status:", err);
    }
  }

  const handleStop = async () => {
    if (!confirm('¿Desea detener el análisis permanentemente?')) return;
    setIsTerminating(true);
    try {
      await projectsAPI.terminate(projectId);
      setTerminated(true);
      setStatus(prev => ({ ...prev, custom_status: 'Detenido por usuario' }));
    } catch (err) {
      setIsTerminating(false);
    }
  };

  const isWaitingForBible = status?.custom_status?.toLowerCase().includes('esperando') || 
                            status?.custom_status?.toLowerCase().includes('waiting');

  return (
    <div className="flex flex-col lg:flex-row items-start min-h-full">
      
      {/* SECCIÓN IZQUIERDA: DIAGRAMA */}
      <div className="flex-1 w-full p-8 lg:p-12">
        
         {/* HEADER */}
         <div className="flex flex-col xl:flex-row justify-between items-start xl:items-end mb-12 border-b border-gray-200 pb-8 gap-6">
            <div className="max-w-3xl">
               <h2 className="text-4xl font-editorial font-bold text-gray-900 leading-tight mb-3">
                 {terminated ? 'Proceso Detenido' : status?.is_completed ? 'Análisis Completado' : status?.friendly_message || 'Iniciando sistema...'}
               </h2>
               <div className="flex items-center gap-3">
                 <span className={`w-2.5 h-2.5 rounded-full ${status?.is_completed ? 'bg-green-500' : terminated ? 'bg-red-500' : 'bg-theme-primary animate-pulse'}`}></span>
                 <p className="text-sm text-gray-500 font-mono uppercase tracking-widest">
                    {status?.custom_status || 'Inicializando...'}
                 </p>
               </div>
            </div>

            <div className="flex items-center gap-6 shrink-0">
               <div className="text-right">
                 <div className="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-1 flex items-center justify-end gap-1">
                   <Clock className="w-3 h-3" /> Tiempo Total
                 </div>
                 <div className="text-3xl font-mono font-bold text-gray-800 tabular-nums">
                    {/* Renderizado condicional del tiempo */}
                    {projectCreatedAt ? elapsedTime : '--:--'}
                 </div>
               </div>

               {!status?.is_completed && !terminated && (
                 <button 
                    onClick={handleStop} 
                    disabled={isTerminating}
                    className="
                      flex items-center gap-2 px-5 py-3 
                      bg-white border-2 border-red-100 text-red-500 hover:bg-red-50 hover:border-red-200 hover:text-red-700
                      rounded-sm transition-all text-xs font-extrabold uppercase tracking-widest shadow-sm
                    "
                 >
                    {isTerminating ? <Loader2 className="w-4 h-4 animate-spin" /> : <StopCircle className="w-4 h-4" />}
                    Abortar
                 </button>
               )}
            </div>
        </div>

        {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-6 mb-10 text-red-800 font-bold flex items-center gap-4 text-lg shadow-sm animate-pulse">
                <AlertOctagon className="w-6 h-6 shrink-0" /> {error}
            </div>
        )}

        {isWaitingForBible && (
             <div className="mb-12 animate-in fade-in slide-in-from-top-4 duration-500">
                <Link 
                  to={`/proyecto/${projectId}/biblia`} 
                  className="
                    w-full md:w-auto inline-flex items-center justify-center gap-3
                    bg-theme-primary text-white 
                    px-8 py-5 rounded-md text-base font-bold uppercase tracking-widest
                    shadow-xl shadow-theme-primary/30 hover:shadow-theme-primary/50
                    hover:bg-theme-primary-hover
                    transition-all transform hover:-translate-y-1 ring-4 ring-theme-primary/10
                  "
                >
                   <AlertTriangle className="w-5 h-5 animate-bounce" /> 
                   ACCIÓN REQUERIDA: REVISAR BIBLIA NARRATIVA
                   <ArrowRight className="w-5 h-5" />
                </Link>
             </div>
        )}
        
        {/* GRID DE FASES */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-8">
            {PHASES.map((phase, idx) => {
                const isCompleted = status?.is_completed || currentPhase > idx;
                const isCurrent = !status?.is_completed && !terminated && currentPhase === idx;

                return (
                    <div key={phase.key} className={`
                        relative flex flex-col items-center text-center p-8 rounded-xl border-2 transition-all duration-300
                        min-h-[220px] justify-center
                        ${isCurrent 
                            ? 'bg-white border-theme-primary shadow-2xl scale-[1.03] z-10' 
                            : isCompleted 
                                ? 'bg-white border-green-200/60'
                                : 'bg-white border-gray-100'}
                        ${!isCompleted && !isCurrent ? 'opacity-40 grayscale' : ''}
                    `}>
                        <div className={`
                            w-16 h-16 rounded-2xl flex items-center justify-center mb-5 transition-colors duration-300
                            ${isCompleted 
                                ? 'bg-green-50 text-green-600' 
                                : isCurrent 
                                    ? 'bg-theme-primary text-white shadow-lg shadow-theme-primary/20' 
                                    : 'bg-gray-50 text-gray-300'}
                        `}>
                            <phase.icon className="w-8 h-8" />
                        </div>

                        <h3 className={`text-sm font-black uppercase tracking-widest mb-2 w-full text-balance
                            ${isCompleted ? 'text-green-800' : isCurrent ? 'text-theme-primary' : 'text-gray-400'}`}>
                            {phase.label}
                        </h3>
                        
                        <p className="text-xs text-gray-400 leading-relaxed max-w-[80%] text-balance">
                            {phase.description}
                        </p>

                        <div className="absolute top-4 right-4">
                            {isCompleted && <Check className="w-5 h-5 text-green-500" />}
                            {isCurrent && (
                                <span className="flex h-3 w-3">
                                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-theme-primary opacity-75"></span>
                                  <span className="relative inline-flex rounded-full h-3 w-3 bg-theme-primary"></span>
                                </span>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
      </div>

      {/* DERECHA: LOGS */}
      <aside className="hidden lg:flex w-[380px] bg-[#0f172a] border-l border-gray-800 shrink-0 flex-col shadow-2xl z-20 
          sticky top-[200px] h-[calc(100vh-200px)]">
         
         <div className="bg-[#1e293b] px-6 py-4 border-b border-gray-700 flex justify-between items-center shrink-0">
             <div className="flex items-center gap-3">
                 <Terminal className="w-4 h-4 text-theme-primary" />
                 <span className="text-gray-200 font-mono text-xs font-bold uppercase tracking-widest">System Output</span>
             </div>
             <div className="flex gap-2">
                 <div className={`w-2 h-2 rounded-full ${status?.is_completed ? 'bg-green-500' : 'bg-gray-700'}`}></div>
                 <div className={`w-2 h-2 rounded-full ${!status?.is_completed && !terminated ? 'bg-yellow-500 animate-pulse' : 'bg-gray-700'}`}></div>
             </div>
         </div>

         <div 
            ref={logsContainerRef}
            className="flex-1 overflow-y-auto p-6 space-y-4 font-mono text-[11px] custom-scrollbar bg-[#0f172a]"
         >
             {logs.length === 0 && (
                <div className="h-full flex flex-col items-center justify-center text-gray-600 opacity-50 space-y-2">
                    <Loader2 className="w-8 h-8 animate-spin" />
                    <p>Conectando con el orquestador...</p>
                </div>
             )}
             {logs.map((log, i) => (
                 <div key={i} className="flex flex-col border-l-2 border-transparent hover:border-theme-primary/50 pl-3 transition-colors duration-200">
                     <span className="text-blue-400/60 font-bold text-[10px] mb-1">{log.time}</span>
                     <span className="text-gray-300 break-words leading-relaxed">{log.message}</span>
                 </div>
             ))}
         </div>
      </aside>
    </div>
  );
}