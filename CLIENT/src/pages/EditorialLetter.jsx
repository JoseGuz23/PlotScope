import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { editorialAPI } from '../services/api';
import { 
  BookOpen, Star, TrendingUp, Users, Layout as LayoutIcon, 
  ArrowRight, Download, Loader2, AlertCircle, CheckCircle2 
} from 'lucide-react';
import { saveAs } from 'file-saver';

export default function EditorialLetter() {
  const { id: projectId } = useParams();
  const [letter, setLetter] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('resumen');

  useEffect(() => {
    loadLetter();
  }, [projectId]);

  async function loadLetter() {
    try {
      // Intentamos cargar la carta
      const data = await editorialAPI.getLetter(projectId);
      setLetter(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const downloadLetter = () => {
    if (letter?.carta_markdown) {
      const blob = new Blob([letter.carta_markdown], { type: "text/markdown;charset=utf-8" });
      saveAs(blob, `Carta_Editorial_${projectId}.md`);
    } else {
      alert("El formato Markdown no está disponible en este momento.");
    }
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-screen bg-[#f8f9fa]">
      <Loader2 className="w-10 h-10 animate-spin text-theme-primary mb-4" />
      <p className="text-gray-500 font-mono text-xs uppercase tracking-widest">Generando Carta Editorial...</p>
    </div>
  );

  if (!letter || !letter.carta_editorial) return (
    <div className="flex flex-col items-center justify-center h-screen bg-red-50 text-center px-4">
      <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
      <h2 className="text-xl font-bold text-gray-900">Carta Editorial Pendiente</h2>
      <p className="text-gray-600 mb-6 max-w-md mt-2">
        El análisis editorial aún no se ha generado o está en proceso. Por favor, verifica el estado del proyecto.
      </p>
      <Link to={`/proyecto/${projectId}/status`} className="text-theme-primary font-bold hover:underline border border-theme-primary px-6 py-2 rounded-lg">
        Ver Estado de Procesamiento
      </Link>
    </div>
  );

  const content = letter.carta_editorial;

  return (
    <div className="flex h-screen bg-[#f8f9fa] font-sans overflow-hidden">
      
      {/* SIDEBAR NAVEGACIÓN CARTA */}
      <aside className="w-72 bg-white border-r border-gray-200 flex flex-col shrink-0 z-20">
        <div className="p-6 border-b border-gray-100">
          <h1 className="font-editorial text-2xl font-bold text-gray-900">Carta Editorial</h1>
          <p className="text-xs text-gray-400 mt-1 uppercase tracking-wider">Developmental Edit</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <TabButton id="resumen" label="Resumen Ejecutivo" icon={BookOpen} active={activeTab} set={setActiveTab} />
          <TabButton id="fortalezas" label="Lo que Funciona" icon={Star} active={activeTab} set={setActiveTab} />
          <TabButton id="mejoras" label="Áreas de Mejora" icon={TrendingUp} active={activeTab} set={setActiveTab} />
          <TabButton id="personajes" label="Análisis de Personajes" icon={Users} active={activeTab} set={setActiveTab} />
          <TabButton id="estructura" label="Estructura y Ritmo" icon={LayoutIcon} active={activeTab} set={setActiveTab} />
        </nav>

        <div className="p-6 border-t border-gray-100 bg-gray-50/50">
          <Link 
            to={`/proyecto/${projectId}/editor`}
            className="flex items-center justify-center gap-2 w-full py-3 bg-theme-primary text-white rounded-lg font-bold text-sm shadow-lg hover:bg-theme-primary-hover transition-all transform hover:-translate-y-0.5"
          >
            Ir al Editor <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </aside>

      {/* CONTENIDO PRINCIPAL */}
      <main className="flex-1 overflow-y-auto p-12 custom-scrollbar">
        <div className="max-w-4xl mx-auto">
          
          <div className="flex justify-end mb-8">
            <button onClick={downloadLetter} className="flex items-center gap-2 text-gray-500 hover:text-gray-900 text-sm font-medium transition-colors border border-gray-200 bg-white px-4 py-2 rounded-lg shadow-sm">
              <Download className="w-4 h-4" /> Descargar Carta (.md)
            </button>
          </div>

          <div className="bg-white p-10 rounded-xl shadow-sm border border-gray-100 min-h-[800px]">
            
            {/* 1. RESUMEN EJECUTIVO */}
            {activeTab === 'resumen' && (
              <div className="animate-fadeIn">
                <h2 className="font-editorial text-4xl text-gray-900 mb-6">Resumen Ejecutivo</h2>
                <div className="prose prose-lg max-w-none text-gray-600">
                  
                  {/* Potencial de Mercado */}
                  <div className="bg-blue-50 p-6 rounded-lg border border-blue-100 mb-8">
                    <h3 className="text-blue-900 font-bold text-lg mb-2 flex items-center gap-2">
                      <Star className="w-5 h-5" /> Potencial Comercial
                    </h3>
                    <p className="text-blue-800/80 text-base leading-relaxed">
                      {content.resumen_ejecutivo?.potencial_mercado || "Análisis pendiente."}
                    </p>
                  </div>

                  <h3 className="text-gray-900 font-bold mt-6 mb-2 text-xl">Sinopsis Profesional</h3>
                  <p className="whitespace-pre-wrap leading-relaxed text-gray-700 mb-8">
                    {content.resumen_ejecutivo?.sinopsis_profesional || content.resumen_ejecutivo?.sinopsis || "..."}
                  </p>
                  
                  <h3 className="text-gray-900 font-bold mt-8 mb-2 text-xl">Evaluación General</h3>
                  <p className="whitespace-pre-wrap leading-relaxed text-gray-700">
                    {content.resumen_ejecutivo?.evaluacion_general || "..."}
                  </p>
                </div>
              </div>
            )}

            {/* 2. FORTALEZAS */}
            {activeTab === 'fortalezas' && (
              <div className="animate-fadeIn">
                <h2 className="font-editorial text-4xl text-gray-900 mb-8 flex items-center gap-3">
                  <span className="text-green-500 text-2xl">●</span> Lo que Funciona
                </h2>
                <div className="space-y-8">
                  {(content.lo_que_funciona?.fortalezas || content.lo_que_funciona?.puntos || []).map((punto, idx) => (
                    <div key={idx} className="border-l-4 border-green-400 pl-6 py-1">
                      <h3 className="font-bold text-xl text-gray-900 mb-2">{punto.elemento || punto.titulo}</h3>
                      <p className="text-gray-600 leading-relaxed mb-3">{punto.descripcion}</p>
                      {punto.ejemplo && (
                        <div className="bg-gray-50 p-4 rounded-lg text-sm italic text-gray-500 font-serif border border-gray-100">
                          "{punto.ejemplo}"
                        </div>
                      )}
                    </div>
                  ))}
                  {(!content.lo_que_funciona?.fortalezas && !content.lo_que_funciona?.puntos) && <p>No hay datos disponibles.</p>}
                </div>
              </div>
            )}

            {/* 3. ÁREAS DE MEJORA */}
            {activeTab === 'mejoras' && (
              <div className="animate-fadeIn">
                <h2 className="font-editorial text-4xl text-gray-900 mb-8 flex items-center gap-3">
                  <span className="text-amber-500 text-2xl">●</span> Áreas de Mejora
                </h2>
                <div className="space-y-6">
                  {(content.areas_mejora?.problemas || []).map((prob, idx) => (
                    <div key={idx} className="bg-amber-50/40 p-6 rounded-xl border border-amber-100/60">
                      <div className="flex flex-col sm:flex-row gap-4 items-start">
                        <span className={`px-3 py-1 rounded text-xs font-bold uppercase tracking-wide shrink-0 mt-1
                          ${prob.prioridad === 'alta' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
                          Prioridad {prob.prioridad || 'Media'}
                        </span>
                        <div>
                          <h3 className="font-bold text-xl text-gray-900 mb-2">{prob.problema || prob.titulo}</h3>
                          <p className="text-gray-700 mb-4 leading-relaxed">{prob.descripcion}</p>
                          <div className="flex items-start gap-3 mt-4 pt-4 border-t border-amber-200/30">
                            <CheckCircle2 className="w-5 h-5 text-green-600 shrink-0 mt-0.5" />
                            <div>
                              <span className="font-bold text-green-700 text-sm block mb-1">Sugerencia:</span>
                              <p className="text-sm text-gray-600">{prob.sugerencia}</p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. PERSONAJES */}
            {activeTab === 'personajes' && (
               <div className="animate-fadeIn">
                 <h2 className="font-editorial text-4xl text-gray-900 mb-6">Análisis de Personajes</h2>
                 <div className="space-y-10">
                    {(content.analisis_personajes?.personajes || []).map((pj, idx) => (
                      <div key={idx}>
                        <div className="flex items-baseline gap-3 mb-3 border-b border-gray-100 pb-2">
                          <h3 className="text-2xl font-bold text-gray-800">{pj.nombre}</h3>
                          <span className="text-sm text-gray-400 font-mono uppercase">{pj.rol || "Personaje"}</span>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                          <div>
                            <span className="text-xs font-bold uppercase text-gray-400 block mb-1">Arco Actual</span>
                            <p className="text-gray-700 text-sm leading-relaxed">{pj.arco_actual}</p>
                          </div>
                          <div>
                            <span className="text-xs font-bold uppercase text-gray-400 block mb-1">Sugerencia Desarrollo</span>
                            <p className="text-blue-700 text-sm leading-relaxed bg-blue-50 p-3 rounded-lg border border-blue-100">{pj.sugerencias}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                 </div>
               </div>
            )}

            {/* 5. ESTRUCTURA */}
            {activeTab === 'estructura' && (
               <div className="animate-fadeIn">
                 <h2 className="font-editorial text-4xl text-gray-900 mb-6">Estructura y Ritmo</h2>
                 <div className="bg-gray-50 rounded-xl p-6 border border-gray-200 mb-8">
                    <h3 className="font-bold text-lg text-gray-900 mb-2">Modelo Identificado</h3>
                    <p className="text-gray-700">{content.analisis_estructura?.modelo_identificado || "No detectado"}</p>
                 </div>
                 
                 <h3 className="font-bold text-xl text-gray-900 mb-4">Puntos de Giro Detectados</h3>
                 <div className="space-y-4">
                    {(content.analisis_estructura?.puntos_giro || []).map((pg, idx) => (
                      <div key={idx} className="flex gap-4">
                        <div className="w-20 shrink-0 text-right text-sm font-mono text-gray-400 pt-1">
                          {pg.ubicacion || "Cap. ?"}
                        </div>
                        <div className="pb-4 border-l-2 border-gray-200 pl-6 relative">
                          <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full bg-white border-4 border-theme-primary"></div>
                          <h4 className="font-bold text-gray-900">{pg.evento}</h4>
                          <p className="text-sm text-gray-600 mt-1">{pg.comentario_efectividad}</p>
                        </div>
                      </div>
                    ))}
                 </div>
               </div>
            )}

          </div>
        </div>
      </main>
    </div>
  );
}

function TabButton({ id, label, icon: Icon, active, set }) {
  const isActive = active === id;
  return (
    <button
      onClick={() => set(id)}
      className={`
        w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all
        ${isActive 
          ? 'bg-gray-100 text-gray-900 shadow-sm' 
          : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'}
      `}
    >
      <Icon className={`w-4 h-4 ${isActive ? 'text-theme-primary' : 'text-gray-400'}`} />
      {label}
    </button>
  );
}