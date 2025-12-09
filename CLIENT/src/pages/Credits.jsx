// =============================================================================
// Credits.jsx - TIENDA DE TOKENS (Diseño Jerárquico Final)
// =============================================================================

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Calculator, Zap, Crown, Check, AlertCircle, Sparkles, CreditCard, UploadCloud, Loader2 } from 'lucide-react';
import { uploadAPI } from '../services/api';

export default function Credits() {
  const [wordCount, setWordCount] = useState(80000);
  const [mode, setMode] = useState('standard'); 
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Simulación de saldo
  const userBalance = 0; 
  
  // Cálculo
  const baseTokens = Math.ceil(wordCount / 1000);
  const multiplier = mode === 'master' ? 2.5 : 1;
  const tokensNeeded = Math.ceil(baseTokens * multiplier);
  const tokensToBuy = Math.max(0, tokensNeeded - userBalance);

  // Recomendación
  const getRecommendation = () => {
    if (tokensToBuy <= 0) return { id: 'none', text: 'Saldo suficiente.' };
    if (tokensToBuy <= 50) return { id: 'starter', text: 'Pack Starter (50) cubre tu necesidad.' };
    if (tokensToBuy <= 150) return { id: 'autor', text: 'Pack Autor (150) es la opción justa.' };
    if (tokensToBuy <= 400) return { id: 'grand', text: 'Pack Grand Pro (400) cubre todo el proyecto.' };
    return { id: 'multi', text: 'Recomendamos combinar packs.' };
  };

  const recommendation = getRecommendation();

  // Carga de archivo
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsAnalyzing(true);
    try {
      const stats = await uploadAPI.analyzeForQuote(file);
      if (stats && stats.word_count) {
        setWordCount(stats.word_count);
      }
    } catch (error) {
      console.error("Error:", error);
      alert("Error al leer el archivo.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto">
      
      {/* HEADER */}
      <div className="mb-10 flex flex-col md:flex-row justify-between items-end border-b border-gray-200 pb-6">
        <div>
          <span className="font-mono text-xs font-bold text-theme-primary uppercase tracking-[0.2em] mb-2 block">
            Tienda
          </span>
          <h1 className="font-editorial text-4xl font-bold text-gray-900">
            Adquirir Créditos
          </h1>
        </div>
        <p className="font-sans text-gray-500 text-sm max-w-md text-right">
          Selecciona el paquete exacto para tu próxima sesión de edición.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        
        {/* COLUMNA IZQUIERDA: CALCULADORA */}
        <div className="lg:col-span-4 space-y-8">
          <div className="bg-white border-2 border-gray-100 p-6 rounded-sm sticky top-32 shadow-sm">
            <div className="flex items-center gap-2 mb-6 text-gray-400 uppercase tracking-widest text-xs font-bold">
              <Calculator className="w-4 h-4" />
              <span>Calculadora Rápida</span>
            </div>

            {/* Zona Carga */}
            <div className="bg-blue-50 border border-blue-100 p-4 rounded-sm mb-6 relative group transition-colors hover:bg-blue-100/50">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2 text-blue-800">
                  <UploadCloud className="w-4 h-4" />
                  <span className="text-xs font-bold uppercase tracking-wide">Analizar Archivo</span>
                </div>
                {isAnalyzing && <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />}
              </div>
              <input 
                type="file" 
                accept=".docx" 
                onChange={handleFileUpload}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                disabled={isAnalyzing}
              />
              <div className="w-full bg-white text-blue-700 text-center py-2 rounded-sm text-xs font-bold border border-blue-200 shadow-sm group-hover:border-blue-300">
                {isAnalyzing ? 'Calculando...' : 'Seleccionar .docx'}
              </div>
            </div>

            <div className="space-y-6">
              {/* Slider */}
              <div>
                <label className="block text-xs font-extrabold text-gray-900 uppercase mb-2">
                  Longitud ({wordCount.toLocaleString()} pal.)
                </label>
                <input 
                  type="range" 
                  min="5000" 
                  max="200000" 
                  step="1000" 
                  value={wordCount}
                  onChange={(e) => setWordCount(parseInt(e.target.value))}
                  className="w-full h-1.5 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-theme-primary"
                />
              </div>

              {/* Selector */}
              <div>
                <label className="block text-xs font-extrabold text-gray-900 uppercase mb-3">
                  Modo de Edición
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button 
                    onClick={() => setMode('standard')}
                    className={`p-3 border rounded-sm text-center transition-all ${mode === 'standard' ? 'border-theme-primary bg-green-50 text-theme-primary ring-1 ring-theme-primary' : 'border-gray-200 text-gray-500 hover:border-gray-300'}`}
                  >
                    <Zap className="w-4 h-4 mx-auto mb-1" />
                    <span className="text-[10px] font-bold uppercase tracking-wide block">Estándar</span>
                  </button>
                  <button 
                    onClick={() => setMode('master')}
                    className={`p-3 border rounded-sm text-center transition-all ${mode === 'master' ? 'border-purple-600 bg-purple-50 text-purple-700 ring-1 ring-purple-600' : 'border-gray-200 text-gray-500 hover:border-gray-300'}`}
                  >
                    <Crown className="w-4 h-4 mx-auto mb-1" />
                    <span className="text-[10px] font-bold uppercase tracking-wide block">Maestro</span>
                  </button>
                </div>
              </div>

              {/* Resultado */}
              <div className="bg-gray-50 p-4 rounded-sm border border-gray-200 mt-4">
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-500">Costo Proyecto:</span>
                  <span className="font-bold text-gray-900">{tokensNeeded} Tokens</span>
                </div>
                <div className="border-t border-gray-200 pt-3 flex justify-between items-center">
                  <span className="font-bold text-gray-900 text-sm">A Comprar:</span>
                  <span className="font-mono text-xl font-bold text-theme-primary">
                    {tokensToBuy > 0 ? tokensToBuy : 0}
                  </span>
                </div>
              </div>

              {/* Recomendación */}
              {tokensToBuy > 0 && (
                <div className="flex gap-3 bg-blue-50 p-3 rounded-sm text-blue-800 text-xs border border-blue-100 animate-fade-in shadow-sm">
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <p className="font-medium leading-relaxed">
                    {recommendation.text}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* COLUMNA DERECHA: TIENDA JERÁRQUICA */}
        <div className="lg:col-span-8 space-y-8">
          
          <div className="grid md:grid-cols-2 gap-6">
            
            {/* 1. STARTER: GRIS CLARITO (Básico) */}
            <div className={`border p-6 rounded-sm flex flex-col justify-between transition-all ${recommendation.id === 'starter' ? 'border-gray-400 shadow-md scale-[1.02]' : 'border-gray-200 bg-gray-50 hover:bg-white hover:border-gray-300'}`}>
              <div>
                <span className="font-mono text-xs font-bold text-gray-400 uppercase tracking-widest">Starter</span>
                <div className="flex justify-between items-end mt-2 mb-4">
                  <span className="text-4xl font-editorial font-bold text-gray-700">50 <span className="text-sm font-sans text-gray-400 font-normal">Tokens</span></span>
                  <span className="text-xl font-bold text-gray-700">$9.99</span>
                </div>
                <p className="text-xs text-gray-500 mb-6">Para pruebas o cuentos cortos.</p>
              </div>
              <button className="w-full py-3 border border-gray-300 bg-white text-gray-600 font-bold text-xs uppercase tracking-widest hover:border-gray-900 hover:text-gray-900 transition-colors rounded-sm">
                Comprar
              </button>
            </div>

            {/* 2. AUTOR: BLANCO + VERDE (Estándar/Recomendado) */}
            <div className={`border-2 p-6 rounded-sm flex flex-col justify-between relative transition-all bg-white ${recommendation.id === 'autor' ? 'border-theme-primary shadow-xl scale-[1.02] z-10' : 'border-theme-primary/30 hover:border-theme-primary'}`}>
              {recommendation.id === 'autor' && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-theme-primary text-white text-[10px] font-bold px-3 py-1 uppercase tracking-widest rounded-full shadow-sm">
                  Recomendado
                </div>
              )}
              <div>
                <span className="font-mono text-xs font-bold text-theme-primary uppercase tracking-widest">Pack Autor</span>
                <div className="flex justify-between items-end mt-2 mb-4">
                  <span className="text-4xl font-editorial font-bold text-gray-900">150 <span className="text-sm font-sans text-gray-400 font-normal">Tokens</span></span>
                  <span className="text-xl font-bold text-gray-900">$24.99</span>
                </div>
                <p className="text-xs text-gray-500 mb-6">El estándar para novelas (150k palabras).</p>
              </div>
              <button className="w-full py-3 bg-theme-primary text-white font-bold text-xs uppercase tracking-widest hover:bg-theme-primary-hover transition-colors rounded-sm shadow-md">
                Comprar
              </button>
            </div>

            {/* 3. GRAND PRO: BLANCO + MORADO (Premium) */}
            <div className={`border p-6 rounded-sm flex flex-col justify-between transition-all bg-white md:col-span-2 lg:col-span-1 ${recommendation.id === 'grand' ? 'border-purple-500 shadow-md scale-[1.02]' : 'border-purple-200 hover:border-purple-400'}`}>
              <div>
                <span className="font-mono text-xs font-bold text-purple-700 uppercase tracking-widest">Grand Pro</span>
                <div className="flex justify-between items-end mt-2 mb-4">
                  <span className="text-4xl font-editorial font-bold text-gray-900">400 <span className="text-sm font-sans text-gray-400 font-normal">Tokens</span></span>
                  <span className="text-xl font-bold text-gray-900">$59.99</span>
                </div>
                <p className="text-xs text-gray-500 mb-6">Máxima capacidad para obras épicas.</p>
              </div>
              {/* Botón Morado Sólido (Lo hace destacar sobre el starter) */}
              <button className="w-full py-3 bg-purple-600 text-white font-bold text-xs uppercase tracking-widest hover:bg-purple-700 transition-colors rounded-sm shadow-sm">
                Comprar
              </button>
            </div>

            {/* 4. MEMBRESÍA: NEGRO (VIP - Categoría Propia) */}
            <div className="bg-gray-900 text-white p-6 rounded-sm flex flex-col justify-between relative overflow-hidden md:col-span-2 lg:col-span-1 border border-gray-800">
              <div className="absolute top-0 right-0 p-6 opacity-10">
                <Sparkles className="w-24 h-24" />
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Crown className="w-4 h-4 text-purple-400" />
                  <span className="font-mono text-xs font-bold text-purple-300 uppercase tracking-widest">Club LYA</span>
                </div>
                <div className="flex justify-between items-end mb-4">
                  <span className="text-3xl font-editorial font-bold">150 <span className="text-sm font-sans text-gray-400 font-normal">Tokens</span></span>
                  <span className="text-xl font-bold">$19.99 <span className="text-xs font-normal text-gray-500">/mes</span></span>
                </div>
                <div className="text-xs text-gray-300 space-y-1 mb-6">
                  <p>• Recargas extra al <strong>75% OFF</strong></p>
                  <p>• Soporte Prioritario</p>
                </div>
              </div>
              <button className="w-full py-3 bg-purple-600 text-white font-bold text-xs uppercase tracking-widest hover:bg-purple-700 transition-colors rounded-sm">
                Suscribirse
              </button>
            </div>

          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-sm p-6 flex items-start gap-4">
            <CreditCard className="w-6 h-6 text-gray-400 mt-1" />
            <div>
              <h4 className="font-bold text-gray-900 text-sm mb-1">Pagos Seguros</h4>
              <p className="text-xs text-gray-500 leading-relaxed">
                Todas las transacciones están encriptadas. Garantía de reembolso en caso de fallos técnicos del sistema.
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}