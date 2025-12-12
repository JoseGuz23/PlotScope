// =============================================================================
// ProjectStatus.jsx - DISEÑO LIMPIO + AUTORECARGA + NOTIFICACIONES (SIN EMOJIS)
// =============================================================================

import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, useOutletContext, Link } from 'react-router-dom';
import { projectsAPI } from '../services/api';
import {
  Upload, BookOpen, Search, FileText, Brain, Scroll,
  Map, Edit, Save, Loader2, Clock, AlertOctagon,
  StopCircle, ArrowRight, Check, Activity, Eye, Sparkles
} from 'lucide-react';

// --- SONIDO DE NOTIFICACIÓN (Tono tipo "Ping" suave) ---
const REAL_NOTIFICATION_SOUND = "https://www.soundjay.com/buttons/sounds/button-3.mp3";

const PHASES = [
  { key: 'upload', icon: Upload, label: 'Recepción', description: 'Carga del manuscrito' },
  { key: 'segment', icon: BookOpen, label: 'Segmentación', description: 'Estructura base' },
  { key: 'analyze1', icon: Search, label: 'Análisis Factual', description: 'Datos y hechos' },
  { key: 'consolidate', icon: FileText, label: 'Consolidación', description: 'Unificación' },
  { key: 'analyze2-3', icon: Brain, label: 'Análisis Profundo', description: 'Estructura y Tono' },
  { key: 'emotional', icon: Activity, label: 'Arco Emocional', description: 'Sentiment Analysis', badge: 'v6.0' },
  { key: 'sensory', icon: Eye, label: 'Detección Sensorial', description: 'Show vs Tell', badge: 'v6.0' },
  { key: 'bible', icon: Scroll, label: 'Biblia Narrativa', description: 'Documento Maestro' },
  { key: 'carta', icon: FileText, label: 'Carta Editorial', description: 'Feedback Humano' },
  { key: 'notas', icon: Edit, label: 'Notas de Margen', description: 'Contexto' },
  { key: 'arcs', icon: Map, label: 'Arcos Narrativos', description: 'Trayectorias' },
  { key: 'edit', icon: Edit, label: 'Edición Reflexiva', description: 'Corrección IA' },
  { key: 'save', icon: Save, label: 'Finalización', description: 'Empaquetado' },
];

// --- HELPERS ---
function extractDateFromId(id) {
  try {
    if (!id) return null;
    const parts = id.split('_');
    if (parts.length >= 3) {
      const datePart = parts[1];
      const timePart = parts[2];
      if (datePart.length === 8 && timePart.length >= 6) {
        const year = parseInt(datePart.substring(0, 4));
        const month = parseInt(datePart.substring(4, 6)) - 1;
        const day = parseInt(datePart.substring(6, 8));
        const hour = parseInt(timePart.substring(0, 2));
        const min = parseInt(timePart.substring(2, 4));
        const sec = parseInt(timePart.substring(4, 6));
        return new Date(year, month, day, hour, min, sec);
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
    if (s.includes('emotional') || s.includes('emocional') || s.includes('fase 5.5')) return 5;
    if (s.includes('sensory') || s.includes('sensorial') || s.includes('fase 5.6')) return 6;
    if (s.includes('biblia') || s.includes('holistic') || s.includes('esperando')) return 7;
    if (s.includes('carta') || s.includes('editorial')) return 8;
    if (s.includes('notas') || s.includes('margin')) return 9;
    if (s.includes('arc') || s.includes('arco')) return 10;
    if (s.includes('edici') || s.includes('edit') || s.includes('reflection')) return 11;
    if (s.includes('final') || s.includes('guard')) return 12;

    if (s.includes('batch')) {
      if (s.includes('arc_maps') || s.includes('arcs')) return 10;
      if (s.includes('notas') || s.includes('margin')) return 9;
      if (s.includes('edit') || s.includes('edicion')) return 11;
      return 2; 
    }
    return 0;
}

export default function ProjectStatus() {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  
  // 1. OBTENER LA FUNCION DE RECARGA DEL CONTEXTO
  const { refreshProject } = useOutletContext(); 
  
  const [status, setStatus] = useState(null);
  const [projectCreatedAt, setProjectCreatedAt] = useState(null);
  const [error, setError] = useState(null);
  const [isTerminating, setIsTerminating] = useState(false);
  const [terminated, setTerminated] = useState(false);
  const [currentPhase, setCurrentPhase] = useState(0);
  const [elapsedTime, setElapsedTime] = useState('00:00');
  
  // Refs
  const pollIntervalRef = useRef(null);
  const timerIntervalRef = useRef(null);
  // Refs para notificaciones
  const titleIntervalRef = useRef(null);
  const hasPlayedSoundRef = useRef(false);

  // --- LOGICA DE NOTIFICACIONES (INICIO) ---
  useEffect(() => {
    // Limpieza al desmontar
    return () => {
      clearInterval(titleIntervalRef.current);
      document.title = "LYA - Plataforma";
    };
  }, []);

  useEffect(() => {
    if (!status) return;

    const isWaiting = status?.custom_status?.toLowerCase().includes('esperando') || 
                      status?.custom_status?.toLowerCase().includes('waiting');
    
    clearInterval(titleIntervalRef.current);

    if (isWaiting) {
      // --- ATENCION REQUERIDA ---
      
      // 1. Audio (Solo una vez)
      if (!hasPlayedSoundRef.current) {
        try {
          const audio = new Audio(REAL_NOTIFICATION_SOUND);
          audio.volume = 0.4;
          audio.play().catch(e => console.warn("Autoplay bloqueado", e));
          hasPlayedSoundRef.current = true;
        } catch (e) { console.error("Error audio", e); }
      }

      // 2. Titulo Parpadeante (Texto plano)
      let toggle = false;
      titleIntervalRef.current = setInterval(() => {
        document.title = toggle ? "Acción Requerida" : "Aprobar Biblia - LYA";
        toggle = !toggle;
      }, 1000);

    } else if (status.is_completed) {
      // --- COMPLETADO ---
      document.title = "Finalizado - LYA";
      hasPlayedSoundRef.current = false;

    } else if (terminated) {
      // --- DETENIDO ---
      document.title = "Detenido - LYA";

    } else {
      // --- PROCESANDO ---
      const phaseName = status.friendly_message || "Procesando...";
      const shortPhase = phaseName.length > 25 ? phaseName.substring(0, 25) + "..." : phaseName;
      document.title = `${shortPhase} | LYA`;
      hasPlayedSoundRef.current = false;
    }
  }, [status, terminated]);
  // --- LOGICA DE NOTIFICACIONES (FIN) ---

  // 1. CARGA INICIAL
  useEffect(() => {
    const dateFromId = extractDateFromId(projectId);
    if (dateFromId) {
      setProjectCreatedAt(dateFromId);
    } else {
      projectsAPI.getById(projectId).then(data => {
        const apiDate = data?.created_at || data?.createdAt || data?.timestamp;
        if (apiDate) setProjectCreatedAt(new Date(apiDate));
      }).catch(err => console.error(err));
    }
  }, [projectId]);

  // 2. POLLING
  useEffect(() => {
    checkStatus();
    pollIntervalRef.current = setInterval(checkStatus, 4000);
    return () => clearInterval(pollIntervalRef.current);
  }, [projectId]);

  // 3. TIMER
  useEffect(() => {
    if (!projectCreatedAt) return;
    const tick = () => {
      if (status?.is_completed || status?.is_failed || terminated) {
        if (timerIntervalRef.current) {
          clearInterval(timerIntervalRef.current);
          timerIntervalRef.current = null;
        }
        return;
      }
      const now = new Date();
      const diff = Math.floor((now.getTime() - projectCreatedAt.getTime()) / 1000);
      if (diff >= 0) {
        const m = Math.floor(diff / 60);
        const s = diff % 60;
        setElapsedTime(`${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`);
      }
    };
    tick();
    timerIntervalRef.current = setInterval(tick, 1000);
    return () => clearInterval(timerIntervalRef.current);
  }, [projectCreatedAt, status, terminated]);

  async function checkStatus() {
    if (terminated) return;
    try {
      const data = await projectsAPI.getStatus(projectId);
      setStatus(data);

      if (!projectCreatedAt && (data.created_at || data.createdAt || data.startTime)) {
         const dateStr = data.created_at || data.createdAt || data.startTime;
         if (dateStr) setProjectCreatedAt(new Date(dateStr));
      }
      
      const newPhase = getPhaseIndex(data.custom_status);
      if (newPhase > 0) setCurrentPhase(newPhase);
      
      // --- FINALIZACION ---
      if (data.is_completed) {
        clearInterval(pollIntervalRef.current);
        
        // 2. FORZAR ACTUALIZACION DEL CONTEXTO (Solución al F5)
        await refreshProject(); 

        // 3. REDIRIGIR A EDITOR
        setTimeout(() => navigate(`/proyecto/${projectId}/editor`), 1000);
      }
      
      if (data.is_failed) {
        clearInterval(pollIntervalRef.current);
        setError('El orquestador reportó un fallo crítico.');
      }
    } catch (err) { 
        console.warn("Polling error:", err);
    }
  }

  const handleStop = async () => {
    if (!confirm('¿Detener análisis permanentemente?')) return;
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

  // --- RENDER ---
  return (
    <div className="min-h-screen bg-gray-50/50 p-8 lg:p-12 font-sans">
      
      <div className="max-w-7xl mx-auto">
        
        {/* HEADER SUPERIOR */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-end mb-16 gap-6">
           <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-white border border-gray-200 rounded-full shadow-sm">
                <span className={`relative flex h-2.5 w-2.5`}>
                  <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${status?.is_completed ? 'bg-green-400' : terminated ? 'bg-red-400' : 'bg-theme-primary'}`}></span>
                  <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${status?.is_completed ? 'bg-green-500' : terminated ? 'bg-red-500' : 'bg-theme-primary'}`}></span>
                </span>
                <span className="text-xs font-bold uppercase tracking-widest text-gray-500">
                  {status?.custom_status || 'Inicializando...'}
                </span>
              </div>
              
              <h1 className="text-4xl md:text-5xl font-editorial font-bold text-gray-900 leading-tight">
                {terminated ? 'Proceso Detenido' : status?.is_completed ? 'Análisis Completado' : status?.friendly_message || 'Iniciando LYA...'}
              </h1>
           </div>

           {/* Timer y Acciones */}
           <div className="flex flex-col items-end gap-4">
              <div className="flex items-center gap-3 bg-white px-5 py-3 rounded-lg border border-gray-200 shadow-sm">
                 <Clock className="w-5 h-5 text-gray-400" />
                 <div className="text-3xl font-mono font-bold text-gray-800 tracking-tight">
                    {projectCreatedAt ? elapsedTime : '--:--'}
                 </div>
              </div>

              {!status?.is_completed && !terminated && (
                <button 
                  onClick={handleStop} 
                  disabled={isTerminating}
                  className="text-xs font-bold text-red-400 hover:text-red-600 transition-colors uppercase tracking-widest flex items-center gap-2 px-2"
                >
                  {isTerminating ? <Loader2 className="w-3 h-3 animate-spin" /> : <StopCircle className="w-3 h-3" />}
                  Cancelar Proceso
                </button>
              )}
           </div>
        </header>

        {/* ALERTA DE ACCION (BIBLIA) */}
        {isWaitingForBible && (
             <div className="mb-16 animate-in fade-in slide-in-from-top-4 duration-700">
                <Link 
                  to={`/proyecto/${projectId}/biblia`} 
                  className="group relative w-full flex items-center justify-center gap-4 bg-gradient-to-r from-theme-primary to-purple-700 text-white px-8 py-8 rounded-xl shadow-2xl shadow-theme-primary/30 hover:shadow-theme-primary/50 transition-all transform hover:-translate-y-1 overflow-hidden"
                >
                   <div className="absolute inset-0 bg-white/10 group-hover:bg-white/20 transition-colors"></div>
                   <div className="absolute -inset-full top-0 block h-full w-1/2 -skew-x-12 bg-gradient-to-r from-transparent to-white opacity-20 group-hover:animate-shine" />
                   
                   <div className="relative flex items-center gap-4">
                     <div className="p-3 bg-white/20 rounded-full backdrop-blur-sm">
                        <Scroll className="w-8 h-8 text-white" />
                     </div>
                     <div className="text-left">
                        <p className="text-xs font-bold text-purple-200 uppercase tracking-widest mb-1">Pausa Automatica</p>
                        <h3 className="text-2xl font-bold">Revision de Biblia Narrativa Requerida</h3>
                     </div>
                     <ArrowRight className="w-6 h-6 ml-4 group-hover:translate-x-2 transition-transform" />
                   </div>
                </Link>
             </div>
        )}

        {/* ERROR */}
        {error && (
            <div className="max-w-2xl mx-auto bg-red-50 border-l-4 border-red-500 p-6 mb-12 rounded-r-lg shadow-sm flex gap-4 items-start">
               <AlertOctagon className="w-6 h-6 text-red-600 shrink-0 mt-1" />
               <div>
                 <h3 className="text-red-800 font-bold text-lg mb-1">Error del Sistema</h3>
                 <p className="text-red-700">{error}</p>
               </div>
            </div>
        )}
        
        {/* GRID DE FASES (PIPELINE) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 relative">
            {/* Linea conectora visual (solo desktop) */}
            <div className="hidden xl:block absolute top-12 left-0 w-full h-0.5 bg-gray-100 -z-10"></div>

            {PHASES.map((phase, idx) => {
                const isCompleted = status?.is_completed || currentPhase > idx;
                const isCurrent = !status?.is_completed && !terminated && currentPhase === idx;

                return (
                    <div key={phase.key} className={`
                        group relative flex flex-col p-6 rounded-2xl border transition-all duration-500 overflow-hidden
                        ${isCurrent 
                            ? 'bg-white border-theme-primary shadow-2xl scale-105 z-10 ring-4 ring-theme-primary/5' 
                            : isCompleted 
                                ? 'bg-white border-green-100 shadow-sm opacity-90 hover:opacity-100'
                                : 'bg-gray-50 border-gray-100 opacity-60 grayscale'}
                    `}>
                        {/* Indicador de estado superior */}
                        <div className="flex justify-between items-start mb-4">
                            <div className={`
                                w-12 h-12 rounded-xl flex items-center justify-center transition-colors duration-300
                                ${isCompleted ? 'bg-green-100 text-green-600' : isCurrent ? 'bg-theme-primary text-white shadow-lg shadow-theme-primary/30' : 'bg-gray-200 text-gray-400'}
                            `}>
                                <phase.icon className="w-6 h-6" />
                            </div>
                            {isCompleted && <div className="bg-green-100 p-1 rounded-full"><Check className="w-4 h-4 text-green-600" /></div>}
                            {isCurrent && <div className="bg-purple-100 p-1 rounded-full"><Loader2 className="w-4 h-4 text-theme-primary animate-spin" /></div>}
                        </div>

                        {/* Contenido */}
                        <div className="relative">
                            <h3 className={`text-base font-bold mb-1 ${isCompleted ? 'text-gray-800' : isCurrent ? 'text-theme-primary' : 'text-gray-400'}`}>
                                {phase.label}
                            </h3>
                            <p className="text-xs text-gray-500 leading-relaxed mb-3">
                                {phase.description}
                            </p>
                            
                            {/* Badges v6.0 */}
                            {phase.badge && (
                                <span className={`
                                    inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider
                                    ${isCurrent || isCompleted ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white' : 'bg-gray-200 text-gray-500'}
                                `}>
                                    <Sparkles className="w-2 h-2" /> {phase.badge}
                                </span>
                            )}
                        </div>

                        {/* Barra de progreso sutil para fase actual */}
                        {isCurrent && (
                           <div className="absolute bottom-0 left-0 h-1 bg-theme-primary/20 w-full">
                              <div className="h-full bg-theme-primary animate-progress-indeterminate"></div>
                           </div>
                        )}
                    </div>
                );
            })}
        </div>

      </div>
    </div>
  );
}