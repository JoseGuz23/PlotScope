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
  { key: 'analyze2', icon: FileText, label: 'Análisis Estructural', description: 'Evaluación de ritmo' },
  { key: 'analyze3', icon: Brain, label: 'Análisis Cualitativo', description: 'Profundidad narrativa' },
  { key: 'bible', icon: Scroll, label: 'Biblia Narrativa', description: 'Generación de guía' },
  { key: 'arcs', icon: Map, label: 'Mapeo de Arcos', description: 'Trayectoria de personajes' },
  { key: 'edit', icon: Edit, label: 'Edición IA', description: 'Corrección estilística' },
  { key: 'save', icon: Save, label: 'Finalización', description: 'Compilando entregables' },
];

function getPhaseIndex(customStatus) {
  if (!customStatus) return 0;
  const status = customStatus.toLowerCase();
  
  if (status.includes('terminated')) return -1;
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
  const [projectCreatedAt, setProjectCreatedAt] = useState(null);
  const [error, setError] = useState(null);
  const [isTerminating, setIsTerminating] = useState(false);
  const [terminated, setTerminated] = useState(false);
  const [logs, setLogs] = useState([]);
  const [currentPhase, setCurrentPhase] = useState(0);
  const [elapsedTime, setElapsedTime] = useState('00:00');
  
  const pollIntervalRef = useRef(null);
  const timerIntervalRef = useRef(null);

  // 1. Obtener fecha de creación real
  useEffect(() => {
    projectsAPI.getById(projectId).then(data => {
      const dateStr = data?.created_at || data?.createdAt;
      if (dateStr) {
        setProjectCreatedAt(new Date(dateStr));
      } else {
        setProjectCreatedAt(new Date());
      }
    }).catch(() => setProjectCreatedAt(new Date()));
  }, [projectId]);

  // 2. Polling y Timer
  useEffect(() => {
    checkStatus();
    pollIntervalRef.current = setInterval(checkStatus, 4000);
    timerIntervalRef.current = setInterval(updateTimer, 1000);
    
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [projectId, projectCreatedAt]);

  function updateTimer() {
    if (status?.is_completed || status?.is_failed || terminated || !projectCreatedAt) return;
    
    const now = new Date();
    const diff = Math.floor((now - projectCreatedAt) / 1000);
    
    if (diff >= 0) {
      const minutes = Math.floor(diff / 60);
      const seconds = diff % 60;
      setElapsedTime(`${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
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
              time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }), 
              message: data.friendly_message || data.custom_status 
            }].slice(-50);
          }
          return prev;
        });
      }

      if (data.custom_status && data.custom_status.toLowerCase().includes('terminated')) {
        handleTerminationState();
        return;
      }
      
      setCurrentPhase(getPhaseIndex(data.custom_status));
      
      if (data.is_completed) {
        clearInterval(pollIntervalRef.current);
        setTimeout(() => navigate(`/proyecto/${projectId}/biblia`), 1500);
      }
      
      if (data.is_failed) {
        clearInterval(pollIntervalRef.current);
        setError('El orquestador reportó un fallo crítico.');
      }
      
    } catch (err) {
      // Ignorar errores temporales
    }
  }

  const handleStop = async () => {
    if (!confirm('¿Seguro que deseas detener el proceso?')) return;
    setIsTerminating(true);
    try {
      await projectsAPI.terminate(projectId);
      handleTerminationState();
    } catch (err) {
      alert('Error: ' + err.message);
      setIsTerminating(false);
    }
  };

  const handleTerminationState = () => {
    setTerminated(true);
    setIsTerminating(false);
    clearInterval(pollIntervalRef.current);
    setStatus(prev => ({ ...prev, custom_status: 'Detenido por usuario' }));
  };

  return (
    <div className="min-h-screen bg-gray-50 pt-8 pb-12 px-6">
      <div className="max-w-[1600px] mx-auto">
        
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="font-editorial text-3xl text-gray-900">Estado del Análisis</h1>
            <p className="text-gray-500 text-sm flex items-center gap-2 mt-1">
              ID: <span className="font-mono text-xs bg-white border border-gray-200 px-2 py-0.5 rounded text-gray-600">{projectId}</span>
            </p>
          </div>
          <Link to="/dashboard" className="group flex items-center gap-2 text-gray-500 hover:text-gray-900 text-sm font-bold transition-colors">
            <div className="w-8 h-8 rounded-full bg-white border border-gray-200 flex items-center justify-center group-hover:border-gray-400 transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </div>
            <span>Volver al Dashboard</span>
          </Link>
        </div>

        {/* LAYOUT: 2 COLUMNAS */}
        <div className="flex flex-col lg:flex-row gap-6 h-[calc(100vh-180px)] min-h-[600px]">
          
          {/* IZQUIERDA: Estado Visual */}
          <div className="flex-1 flex flex-col gap-6 h-full overflow-y-auto pr-2 custom-scrollbar">
            
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden shrink-0">
              
              <div className="px-8 py-8 border-b border-gray-100 flex justify-between items-center bg-white">
                <div className="flex items-center gap-6">
                  <div className={`
                    w-16 h-16 rounded-2xl flex items-center justify-center shadow-sm
                    ${status?.is_completed ? 'bg-green-50 text-green-600' : 'bg-blue-50 text-theme-primary'}
                    ${terminated ? '!bg-red-50 !text-red-500' : ''}
                  `}>
                    {status?.is_completed ? <CheckCircle2 className="w-8 h-8" /> : 
                     terminated ? <XCircle className="w-8 h-8" /> :
                     <Loader2 className="w-8 h-8 animate-spin" />}
                  </div>
                  
                  <div>
                    <h2 className="font-editorial text-2xl text-gray-900 mb-1">
                      {terminated ? 'Procesamiento Detenido' : 
                       status?.is_completed ? '¡Análisis Completado!' :
                       status?.friendly_message || 'Iniciando sistema...'}
                    </h2>
                    <p className="text-sm text-gray-500 font-medium">
                      {status?.is_completed ? 'Tu manuscrito está listo.' : 'Procesando en Azure Cloud con IA.'}
                    </p>
                  </div>
                </div>

                <div className="flex flex-col items-end border-l border-gray-100 pl-8 ml-4">
                   <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400 flex items-center gap-1.5 mb-1">
                      <Clock className="w-3 h-3" /> Transcurrido
                   </span>
                   <span className="text-4xl font-light tracking-tight text-gray-900 tabular-nums font-sans">
                      {elapsedTime}
                   </span>
                </div>
              </div>

              <div className="p-8 bg-gray-50/50">
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
                  {PHASES.map((phase, idx) => {
                    const isCompleted = currentPhase > idx || status?.is_completed;
                    const isCurrent = currentPhase === idx && !status?.is_completed && !terminated;
                    const isPending = currentPhase < idx;
                    
                    return (
                      <div key={phase.key} 
                        className={`
                          group flex items-center gap-4 p-4 rounded-xl border transition-all duration-300 relative overflow-hidden
                          ${isCurrent ? 'bg-white border-theme-primary shadow-lg ring-1 ring-theme-primary/10' : 'bg-white border-gray-100'}
                          ${isPending ? 'opacity-60 grayscale' : ''}
                        `}
                      >
                        {isCurrent && (
                          <div className="absolute bottom-0 left-0 h-1 bg-theme-primary/10 w-full">
                            <div className="h-full bg-theme-primary w-1/3 animate-pulse"></div>
                          </div>
                        )}

                        <div className={`
                          w-12 h-12 rounded-xl flex items-center justify-center shrink-0 transition-colors
                          ${isCompleted ? 'bg-green-100 text-green-600' : ''}
                          ${isCurrent ? 'bg-theme-primary text-white shadow-md shadow-blue-200' : ''}
                          ${isPending ? 'bg-gray-100 text-gray-400' : ''}
                        `}>
                          <phase.icon className="w-6 h-6" />
                        </div>
                        
                        <div>
                          <h3 className={`text-sm font-bold uppercase tracking-wide mb-0.5 ${isCurrent ? 'text-theme-primary' : 'text-gray-600'}`}>
                            {phase.label}
                          </h3>
                          <p className="text-[11px] text-gray-400 leading-tight">
                            {phase.description}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
            
            {error && (
              <div className="bg-red-50 border border-red-100 p-4 rounded-xl flex items-center gap-4 animate-fadeIn">
                <div className="bg-red-100 p-2 rounded-full text-red-600">
                  <AlertOctagon className="w-6 h-6" />
                </div>
                <div>
                  <p className="font-bold text-red-900">Error en el proceso</p>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            )}
          </div>

          {/* DERECHA: Terminal Logs */}
          <div className="w-full lg:w-[420px] shrink-0 h-full flex flex-col">
             <div className="bg-[#0f172a] rounded-xl shadow-xl border border-gray-800 overflow-hidden flex flex-col h-full">
                <div className="bg-[#1e293b] px-4 py-3 border-b border-gray-700 flex items-center justify-between shrink-0">
                   <div className="flex items-center gap-2">
                      <Terminal className="w-4 h-4 text-blue-400" />
                      <span className="text-gray-200 font-mono text-xs font-bold uppercase tracking-wider">System Logs</span>
                   </div>
                   <div className="flex gap-2">
                      <div className="w-2 h-2 rounded-full bg-red-500/50"></div>
                      <div className="w-2 h-2 rounded-full bg-yellow-500/50"></div>
                      <div className="w-2 h-2 rounded-full bg-green-500"></div>
                   </div>
                </div>

                <div className="p-4 overflow-y-auto font-mono text-[11px] space-y-2 flex-1 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent bg-[#0f172a]">
                   {logs.length === 0 ? (
                      <div className="h-full flex flex-col items-center justify-center text-gray-600 gap-3 opacity-50">
                         <div className="relative">
                           <div className="absolute inset-0 bg-blue-500 blur-xl opacity-10"></div>
                           <Loader2 className="w-8 h-8 text-blue-500 animate-spin relative z-10" />
                         </div>
                         <span className="uppercase tracking-widest text-[10px] text-blue-400/50">Conectando...</span>
                      </div>
                   ) : (
                      logs.map((log, i) => (
                         <div key={i} className="flex gap-3 text-gray-300 hover:bg-white/5 p-1.5 rounded transition-colors border-l-2 border-transparent hover:border-blue-500/50">
                            <span className="text-blue-400/70 shrink-0 select-none text-[10px] pt-0.5 font-bold">
                               {log.time}
                            </span>
                            <span className="break-words leading-relaxed text-gray-300">
                               {log.message}
                            </span>
                         </div>
                      ))
                   )}
                   {!status?.is_completed && !terminated && (
                      <div className="flex items-center gap-2 text-blue-500 pt-2 animate-pulse">
                        <span className="text-[10px]">➜</span>
                        <span className="w-1.5 h-3 bg-blue-500 block"></span>
                      </div>
                   )}
                </div>

                <div className="p-4 bg-[#1e293b] border-t border-gray-700">
                  {!status?.is_completed && !status?.is_failed && !terminated ? (
                    <button
                      onClick={handleStop}
                      disabled={isTerminating}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-xs font-bold text-red-400 hover:text-white hover:bg-red-500/20 border border-red-500/30 rounded-lg transition-all uppercase tracking-wide"
                    >
                      <AlertOctagon className="w-3.5 h-3.5" />
                      {isTerminating ? 'Deteniendo...' : 'Abortar Proceso'}
                    </button>
                  ) : (
                    <div className="flex items-center justify-center gap-2 text-xs text-gray-500 font-mono uppercase tracking-widest py-1.5">
                      <div className="w-2 h-2 bg-gray-600 rounded-full"></div>
                      Proceso Finalizado
                    </div>
                  )}
                </div>
             </div>
          </div>

        </div>
      </div>
    </div>
  );
}