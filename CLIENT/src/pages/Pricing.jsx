// =============================================================================
// Pricing.jsx - MODELO DE NEGOCIO HÍBRIDO (Con Carga de Archivo)
// =============================================================================

import { useState } from 'react';
import PublicNavbar from '../components/PublicNavbar';
import { Link } from 'react-router-dom';
import { Check, Zap, Crown, Sparkles, UploadCloud, Loader2 } from 'lucide-react'; // Asegúrate de importar los iconos
import { uploadAPI } from '../services/api'; // Importar la API

export default function Pricing() {
  const [wordCount, setWordCount] = useState(80000);
  const [mode, setMode] = useState('standard'); 
  const [isAnalyzing, setIsAnalyzing] = useState(false); // Estado de carga

  // Lógica: 1 Token = 1,000 palabras (Estándar)
  const baseTokens = Math.ceil(wordCount / 1000);
  const multiplier = mode === 'master' ? 2.5 : 1;
  const totalTokensNeeded = Math.ceil(baseTokens * multiplier);
  
  // Sugerencia Inteligente de Paquete
  const getSuggestedPack = () => {
    if (totalTokensNeeded <= 50) return 'Starter';
    if (totalTokensNeeded <= 150) return 'Autor';
    if (totalTokensNeeded <= 400) return 'Grand Pro';
    return 'Múltiples Packs';
  };

  // FUNCIÓN PARA ANALIZAR ARCHIVO
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsAnalyzing(true);
    try {
      // Llamamos al nuevo endpoint "analyze-file"
      const stats = await uploadAPI.analyzeForQuote(file);
      
      if (stats && stats.word_count) {
        setWordCount(stats.word_count); // ¡BAM! Actualiza el slider
        alert(`¡Análisis completado! Detectamos ${stats.word_count.toLocaleString()} palabras.`);
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Hubo un error leyendo el archivo. Intenta con un .docx válido.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F9FAFB] font-sans text-theme-text selection:bg-theme-primary selection:text-white">
      <PublicNavbar />

      <main className="pt-32 pb-20">
        
        {/* HEADER */}
        <section className="text-center px-6 mb-16 max-w-3xl mx-auto">
          <span className="font-mono text-xs font-bold text-theme-primary uppercase tracking-[0.2em] mb-4 block">
            Tokens de Edición
          </span>
          <h1 className="font-editorial text-5xl font-bold text-gray-900 mb-6">
            Flexibilidad total para tu obra.
          </h1>
          <p className="font-sans text-lg text-gray-600">
            Compra tokens cuando los necesites. Sin ataduras. <br/>
            O únete al <strong>Club de Editores</strong> para obtener precios mayoristas.
          </p>
        </section>

        {/* CALCULADORA */}
        <section className="px-6 mb-24">
          <div className="max-w-5xl mx-auto bg-white border border-gray-200 rounded-sm shadow-xl p-8 md:p-12">
            
            {/* SECCIÓN DE CARGA DE ARCHIVO (AQUÍ ESTABA EL PROBLEMA) */}
            <div className="bg-blue-50 border border-blue-100 p-4 rounded-sm mb-8 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="bg-blue-100 p-2 rounded-full text-blue-600">
                  <UploadCloud className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-blue-900">¿Quieres un presupuesto exacto?</h4>
                  <p className="text-xs text-blue-700 max-w-sm">
                    Sube tu manuscrito (.docx). Analizaremos la longitud real sin guardar tu archivo.
                  </p>
                </div>
              </div>
              
              <div className="relative group">
                <input 
                  type="file" 
                  accept=".docx" 
                  onChange={handleFileUpload}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-20"
                  disabled={isAnalyzing}
                />
                <button className={`
                  flex items-center gap-2 px-5 py-2.5 rounded-sm text-xs font-bold uppercase tracking-wider transition-all shadow-sm
                  ${isAnalyzing ? 'bg-blue-200 text-blue-800' : 'bg-white text-blue-900 border border-blue-200 hover:border-blue-400 group-hover:-translate-y-0.5'}
                `}>
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" /> Procesando...
                    </>
                  ) : (
                    "Subir Archivo"
                  )}
                </button>
              </div>
            </div>
            {/* FIN SECCIÓN CARGA */}

            <div className="flex flex-col md:flex-row gap-12 items-start">
              
              {/* Controles (Izquierda) */}
              <div className="w-full md:w-1/2 space-y-10">
                {/* Slider */}
                <div>
                  <div className="flex justify-between items-end mb-4">
                    <label className="font-bold text-sm text-gray-900 uppercase tracking-wide">
                      Longitud del Manuscrito
                    </label>
                    <div className="text-right">
                      <span className="text-3xl font-editorial font-bold text-theme-primary">
                        {wordCount.toLocaleString()}
                      </span>
                      <span className="text-xs text-gray-500 ml-1">palabras</span>
                    </div>
                  </div>
                  <input 
                    type="range" 
                    min="5000" 
                    max="160000" 
                    step="1000" 
                    value={wordCount}
                    onChange={(e) => setWordCount(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-theme-primary"
                  />
                  <div className="flex justify-between mt-2 font-mono text-[10px] text-gray-400">
                    <span>Cuento (5k)</span>
                    <span>Novela (80k)</span>
                    <span>Épica (160k)</span>
                  </div>
                </div>

                {/* Motor */}
                <div>
                  <label className="block font-bold text-sm text-gray-900 mb-4 uppercase tracking-wide">
                    Nivel de Inteligencia
                  </label>
                  <div className="space-y-3">
                    <button 
                      onClick={() => setMode('standard')}
                      className={`w-full p-4 border rounded-sm text-left transition-all flex gap-4 ${mode === 'standard' ? 'border-theme-primary bg-green-50 ring-1 ring-theme-primary' : 'border-gray-200 hover:border-gray-300'}`}
                    >
                      <div className={`mt-1 p-2 rounded-full ${mode === 'standard' ? 'bg-white text-theme-primary' : 'bg-gray-100 text-gray-400'}`}>
                        <Zap className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-bold text-gray-900">Motor Estándar</span>
                          <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">1x Costo</span>
                        </div>
                        <p className="text-xs text-gray-500 leading-snug">
                          Claude Sonnet 3.5. Excelente para estructura, ritmo y limpieza.
                        </p>
                      </div>
                    </button>

                    <button 
                      onClick={() => setMode('master')}
                      className={`w-full p-4 border rounded-sm text-left transition-all flex gap-4 ${mode === 'master' ? 'border-purple-600 bg-purple-50 ring-1 ring-purple-600' : 'border-gray-200 hover:border-gray-300'}`}
                    >
                      <div className={`mt-1 p-2 rounded-full ${mode === 'master' ? 'bg-white text-purple-600' : 'bg-gray-100 text-gray-400'}`}>
                        <Crown className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className="font-bold text-purple-900">Motor Maestro</span>
                          <span className="text-xs font-mono bg-purple-100 text-purple-800 px-2 py-1 rounded">2.5x Costo</span>
                        </div>
                        <p className="text-xs text-purple-800 leading-snug">
                          Claude Opus + Gemini 3.0 Pro. Matiz literario profundo y análisis de subtexto.
                        </p>
                      </div>
                    </button>
                  </div>
                </div>
              </div>

              {/* Resultado (Derecha) */}
              <div className="w-full md:w-1/2 bg-gray-900 text-white p-10 rounded-sm relative overflow-hidden flex flex-col justify-between min-h-[400px] shadow-2xl border-b-4 border-theme-primary">
                <div className="relative z-10">
                  <p className="font-mono text-xs text-gray-400 uppercase tracking-widest mb-2">Inversión Requerida</p>
                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-6xl font-editorial font-bold">{totalTokensNeeded}</span>
                    <span className="text-xl text-gray-400 font-sans">Tokens</span>
                  </div>
                  <p className="text-sm text-gray-400 mb-8 border-b border-gray-800 pb-8 leading-relaxed">
                    Para procesar <strong>{wordCount.toLocaleString()} palabras</strong> con calidad <strong>{mode === 'standard' ? 'Estándar' : 'Maestra'}</strong>.
                  </p>

                  <div className="space-y-4">
                    <div className="flex justify-between items-center text-sm bg-gray-800/50 p-3 rounded-sm border border-gray-800">
                      <span className="text-gray-300">Pack Ideal:</span>
                      <span className="font-bold text-theme-primary uppercase tracking-wider">{getSuggestedPack()}</span>
                    </div>
                    
                    <div className="flex justify-between items-center text-sm p-3">
                      <span className="text-gray-400">Miembros del Club:</span>
                      <span className="font-bold text-purple-300 flex items-center gap-1">
                        <Zap className="w-3 h-3 fill-current" /> 75% OFF en recargas
                      </span>
                    </div>
                  </div>
                </div>

                <Link to="/login" className="mt-8 block w-full py-4 bg-white text-gray-900 text-center font-bold text-xs uppercase tracking-[0.15em] hover:bg-theme-primary hover:text-white transition-all rounded-sm shadow-lg relative top-0 hover:-top-0.5">
                  Adquirir Tokens
                </Link>
              </div>

            </div>
          </div>
        </section>

        {/* PACKS DE COMPRA ÚNICA */}
        <section className="px-6 max-w-6xl mx-auto mb-24">
          <h2 className="text-center font-editorial text-3xl font-bold text-gray-900 mb-12">Paquetes de Tokens</h2>
          <div className="grid md:grid-cols-3 gap-8 items-end">
            
            {/* PACK STARTER */}
            <div className="bg-white p-8 border border-gray-200 rounded-sm hover:border-gray-300 transition-colors flex flex-col relative h-[420px]">
              <span className="font-mono text-xs font-bold text-gray-400 uppercase tracking-widest">Starter</span>
              <div className="mt-4 mb-2">
                <span className="text-4xl font-editorial font-bold text-gray-900">50</span>
                <span className="text-sm text-gray-500 ml-2">Tokens</span>
              </div>
              <p className="text-xl font-bold text-gray-900 mb-6">$9.99 <span className="text-xs font-normal text-gray-500">USD</span></p>
              <ul className="space-y-4 mb-8 flex-1 border-t border-gray-100 pt-6">
                <FeatureItem text="~50k palabras (Estándar)" />
                <FeatureItem text="Ideal para cuentos cortos" />
              </ul>
              <Link to="/login" className="btn-outline w-full py-3 text-center text-xs font-bold uppercase tracking-widest border-2 border-gray-200 hover:border-gray-900 text-gray-600 hover:text-gray-900 transition-all rounded-sm">Comprar</Link>
            </div>

            {/* PACK AUTOR */}
            <div className="bg-white p-8 border-2 border-theme-primary rounded-sm relative shadow-2xl flex flex-col h-[460px] z-10">
              <div className="absolute top-0 right-0 bg-theme-primary text-white text-[10px] font-bold px-4 py-1.5 uppercase tracking-widest rounded-bl-sm">
                Recomendado
              </div>
              <span className="font-mono text-xs font-bold text-theme-primary uppercase tracking-widest">Autor Independiente</span>
              <div className="mt-4 mb-2">
                <span className="text-5xl font-editorial font-bold text-gray-900">150</span>
                <span className="text-sm text-gray-500 ml-2">Tokens</span>
              </div>
              <p className="text-2xl font-bold text-gray-900 mb-6">$24.99 <span className="text-xs font-normal text-gray-500">USD</span></p>
              <ul className="space-y-4 mb-8 flex-1 border-t border-gray-100 pt-6">
                <FeatureItem text="~150k palabras (Estándar)" highlight />
                <FeatureItem text="~60k palabras (Maestro)" highlight />
                <FeatureItem text="Perfecto para una novela promedio" />
              </ul>
              <Link to="/login" className="bg-theme-primary text-white w-full py-4 text-center text-xs font-bold uppercase tracking-[0.15em] hover:bg-theme-primary-hover transition-all shadow-md rounded-sm hover:-translate-y-0.5">Comprar Pack</Link>
            </div>

            {/* PACK GRAND PRO */}
            <div className="bg-white p-8 border border-gray-200 rounded-sm hover:border-purple-500 transition-colors flex flex-col relative h-[420px]">
              <span className="font-mono text-xs font-bold text-purple-700 uppercase tracking-widest">Grand Pro</span>
              <div className="mt-4 mb-2">
                <span className="text-4xl font-editorial font-bold text-gray-900">400</span>
                <span className="text-sm text-gray-500 ml-2">Tokens</span>
              </div>
              <p className="text-xl font-bold text-gray-900 mb-6">$59.99 <span className="text-xs font-normal text-gray-500">USD</span></p>
              <ul className="space-y-4 mb-8 flex-1 border-t border-gray-100 pt-6">
                <FeatureItem text="~400k palabras (Estándar)" />
                <FeatureItem text="~160k palabras (Maestro)" highlightColor="text-purple-700" />
                <FeatureItem text="Para novelas épicas en máxima calidad" />
              </ul>
              <Link to="/login" className="btn-outline w-full py-3 text-center text-xs font-bold uppercase tracking-widest border-2 border-gray-200 hover:border-purple-600 text-gray-600 hover:text-purple-700 transition-all rounded-sm">Comprar</Link>
            </div>

          </div>
        </section>

        {/* SUSCRIPCIÓN - SECCIÓN ESPECIAL (Premium Redesign) */}
        <section className="px-6 max-w-5xl mx-auto">
          <div className="bg-gray-900 rounded-sm shadow-3xl overflow-hidden border border-gray-800 relative leading-relaxed">
            
            {/* Decoración de fondo sutil */}
            <div className="absolute top-0 right-0 p-12 opacity-5 pointer-events-none">
              <Crown className="w-64 h-64 text-purple-200" />
            </div>

            <div className="p-10 md:p-16 flex flex-col md:flex-row items-center gap-16 relative z-10">
              
              {/* Izquierda: Copy */}
              <div className="flex-1 text-center md:text-left">
                {/* Insignia Premium Sobria */}
                <div className="inline-flex items-center gap-2 mb-6 bg-gray-800/80 px-4 py-2 rounded-full border border-gray-700 backdrop-blur-sm">
                  <Sparkles className="w-4 h-4 text-purple-300" />
                  <span className="font-mono text-[10px] font-bold text-purple-200 uppercase tracking-[0.2em]">
                    Membresía Exclusiva
                  </span>
                </div>
                
                <h3 className="font-editorial text-4xl font-bold text-white mb-6">
                  El Club de Editores LYA.
                </h3>
                <p className="text-gray-400 text-lg mb-10 max-w-xl">
                  Para escritores prolíficos. Asegura tu flujo de trabajo con tokens mensuales y <span className="text-white font-bold">precios mayoristas vitalicios</span>.
                </p>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-8 text-sm text-gray-300">
                  <FeatureItemDark icon={<Check className="text-theme-primary"/>} text={<span><strong>150 Tokens</strong> (Pack Autor) cada mes</span>} />
                  <FeatureItemDark icon={<Check className="text-theme-primary"/>} text="Rollover: Nunca pierdes tokens" />
                  {/* Descuento destacado en púrpura real */}
                  <FeatureItemDark icon={<Zap className="text-purple-400 fill-current"/>} text={<><strong>75% OFF</strong> en recargas extra</>} />
                  <FeatureItemDark icon={<Crown className="text-purple-400"/>} text="Soporte Editorial Prioritario" />
                </div>
              </div>

              {/* Derecha: Pricing Box Sólido y Premium */}
              <div className="w-full md:w-auto bg-black/40 p-8 rounded-sm text-center border-2 border-purple-500/30 shadow-2xl backdrop-blur-md min-w-[300px]">
                <p className="font-mono text-xs font-bold text-purple-200 uppercase tracking-widest mb-2">Suscripción Mensual</p>
                <div className="flex items-baseline justify-center gap-1 mb-8">
                  <span className="text-5xl font-editorial font-bold text-white">$19.99</span>
                  <span className="text-sm font-bold text-gray-500">/ mes</span>
                </div>
                
                <Link to="/login" className="block w-full py-4 bg-purple-600 text-white font-bold text-xs uppercase tracking-[0.15em] hover:bg-purple-700 transition-all shadow-lg rounded-sm relative top-0 hover:-top-0.5">
                  Solicitar Acceso VIP
                </Link>
                <p className="text-[10px] text-gray-500 mt-4 font-mono">
                  Sin permanencia. Cancela en tu dashboard.
                </p>
              </div>

            </div>
          </div>
        </section>

      </main>
    </div>
  );
}

// Componente auxiliar para ítems claros
function FeatureItem({ text, highlight = false, highlightColor = 'text-theme-primary' }) {
  return (
    <li className="flex items-start gap-3 text-sm">
      <Check className={`w-4 h-4 mt-0.5 ${highlight ? highlightColor : 'text-gray-300'}`} />
      <span className={highlight ? 'font-bold text-gray-900' : 'text-gray-600'}>{text}</span>
    </li>
  );
}

// Componente auxiliar para ítems oscuros (Suscripción)
function FeatureItemDark({ icon, text }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-5 h-5 flex items-center justify-center">{icon}</div>
      <span>{text}</span>
    </div>
  );
}