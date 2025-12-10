// =============================================================================
// BibleReview.jsx - DASHBOARD DE APROBACIÓN EDITORIAL (CORREGIDO)
// =============================================================================

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { bibleAPI } from '../services/api';
import { 
  Book, Users, Anchor, Flag, Save, CheckCircle2, 
  ChevronRight, AlertCircle, Loader2, ArrowLeft, PenTool
} from 'lucide-react';

export default function BibleReview() {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  
  const [bible, setBible] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [approving, setApproving] = useState(false);
  const [activeSection, setActiveSection] = useState('identidad'); // identidad, reparto, arco, voz

  useEffect(() => {
    loadBible();
  }, [projectId]);

  async function loadBible() {
    try {
      const data = await bibleAPI.get(projectId);
      console.log("Biblia cargada:", data);
      setBible(data);
    } catch (err) {
      console.warn("Biblia no disponible aún o error:", err);
      // No mostramos alert ni error crítico si es 404, mantenemos loading o estado vacío
      if (err.message && err.message.includes('404')) {
         // Opcional: Podrías implementar un polling aquí si quisieras reintentar
         console.log("Esperando generación de la biblia...");
      } else {
         alert('Error cargando la Biblia: ' + err.message);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      await bibleAPI.save(projectId, bible);
    } catch (err) {
      alert('Error al guardar: ' + err.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleApprove() {
    if (!confirm('¿Apruebas esta guía narrativa? El orquestador usará estos datos para editar tu libro.')) return;
    
    setApproving(true);
    try {
      // 1. Guardar últimos cambios
      await bibleAPI.save(projectId, bible);
      // 2. Aprobar y despertar orquestador
      await bibleAPI.approve(projectId);
      
      // 3. Redirigir al status
      navigate(`/proyecto/${projectId}/status`);
    } catch (err) {
      alert('Error al aprobar: ' + err.message);
      setApproving(false);
    }
  }

  // Helper para actualizar una sección completa del JSON
  const updateSection = (sectionName, newData) => {
    setBible(prev => ({
      ...prev,
      [sectionName]: newData
    }));
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50 text-gray-500 gap-4">
      <Loader2 className="w-10 h-10 animate-spin text-theme-primary" />
      <p className="font-mono text-xs uppercase tracking-widest">Cargando Biblia Narrativa...</p>
    </div>
  );

  if (!bible && !loading) return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50 gap-4">
      <div className="p-4 bg-yellow-50 rounded-full">
         <Loader2 className="w-8 h-8 text-yellow-600 animate-spin" />
      </div>
      <h2 className="text-xl font-bold text-gray-800">Generando Biblia...</h2>
      <p className="text-gray-500 text-sm max-w-md text-center">
        El orquestador está escribiendo la Biblia Narrativa. Esto puede tomar unos minutos.
        <br/>Por favor, recarga la página en un momento.
      </p>
      <button onClick={() => window.location.reload()} className="mt-4 px-4 py-2 bg-theme-primary text-white rounded hover:bg-blue-700 transition">
        Recargar
      </button>
      <button onClick={() => navigate(-1)} className="text-gray-400 text-sm hover:underline">Volver</button>
    </div>
  );
  
  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans">
      
      {/* SIDEBAR DE NAVEGACIÓN */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0 z-20 shadow-sm">
        <div className="p-6 border-b border-gray-100">
          <h1 className="font-editorial text-2xl font-bold text-gray-900">Biblia Narrativa</h1>
          <p className="text-xs text-gray-400 mt-1 font-mono">ID: {projectId.substring(0, 8)}</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <NavItem 
            icon={Book} label="Identidad y Tono" 
            active={activeSection === 'identidad'} 
            onClick={() => setActiveSection('identidad')} 
          />
          <NavItem 
            icon={Users} label="Reparto (Personajes)" 
            active={activeSection === 'reparto'} 
            onClick={() => setActiveSection('reparto')} 
          />
          <NavItem 
            icon={Anchor} label="Arco Narrativo" 
            active={activeSection === 'arco'} 
            onClick={() => setActiveSection('arco')} 
          />
          <NavItem 
            icon={PenTool} label="Voz del Autor" 
            active={activeSection === 'voz'} 
            onClick={() => setActiveSection('voz')} 
          />
           <NavItem 
            icon={Flag} label="Instrucciones IA" 
            active={activeSection === 'guia'} 
            onClick={() => setActiveSection('guia')} 
          />
        </nav>

        <div className="p-4 border-t border-gray-100">
          <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 text-gray-500 hover:text-gray-900 text-sm font-medium transition-colors w-full px-2 py-2">
            <ArrowLeft className="w-4 h-4" /> Volver al Dashboard
          </button>
        </div>
      </aside>

      {/* ÁREA PRINCIPAL */}
      <main className="flex-1 flex flex-col min-w-0 bg-gray-50/50">
        
        {/* Toolbar Superior */}
        <header className="bg-white border-b border-gray-200 px-8 py-4 flex justify-between items-center shrink-0 shadow-sm z-10">
          <div>
            <h2 className="text-xs font-bold uppercase tracking-widest text-gray-500 mb-1">Editando Sección</h2>
            <p className="text-xl font-bold text-gray-900 capitalize">
              {activeSection === 'identidad' && 'Identidad de la Obra'}
              {activeSection === 'reparto' && 'Reparto Completo'}
              {activeSection === 'arco' && 'Estructura y Arco'}
              {activeSection === 'voz' && 'Voz del Autor'}
              {activeSection === 'guia' && 'Guía para Claude'}
            </p>
          </div>
          
          <div className="flex gap-3">
            <button 
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-bold text-sm hover:bg-gray-50 transition-all"
            >
              {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              {saving ? 'Guardando...' : 'Guardar Borrador'}
            </button>
            
            <button 
              onClick={handleApprove}
              disabled={approving}
              className="flex items-center gap-2 px-6 py-2.5 rounded-lg bg-theme-primary text-white font-bold text-sm hover:bg-blue-700 shadow-lg shadow-blue-200 transition-all transform hover:-translate-y-0.5"
            >
              {approving ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
              {approving ? 'Iniciando Edición...' : 'Aprobar y Editar'}
            </button>
          </div>
        </header>

        {/* Contenido Scrollable */}
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          <div className="max-w-5xl mx-auto space-y-8 pb-20">
            
            {/* 1. IDENTIDAD */}
            {activeSection === 'identidad' && (
              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 animate-fadeIn">
                <SectionHeader title="Identidad y Género" icon={Book} description="Define el alma del libro, su género y el contrato con el lector." />
                <JsonEditor 
                  data={bible.identidad_obra || {}} 
                  onChange={(v) => updateSection('identidad_obra', v)} 
                />
              </div>
            )}

            {/* 2. REPARTO (PERSONAJES) */}
            {activeSection === 'reparto' && (
              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 animate-fadeIn">
                <SectionHeader title="Fichas de Personajes" icon={Users} description="Protagonistas, antagonistas y roles secundarios detectados." />
                <JsonEditor 
                  data={bible.reparto_completo || {}} 
                  onChange={(v) => updateSection('reparto_completo', v)} 
                />
              </div>
            )}

            {/* 3. ARCO NARRATIVO */}
            {activeSection === 'arco' && (
              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 animate-fadeIn">
                <SectionHeader title="Estructura Narrativa" icon={Anchor} description="Puntos de giro, clímax y estructura global detectada." />
                <JsonEditor 
                  data={bible.arco_narrativo || {}} 
                  onChange={(v) => updateSection('arco_narrativo', v)} 
                />
              </div>
            )}

            {/* 4. VOZ DEL AUTOR */}
            {activeSection === 'voz' && (
              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 animate-fadeIn">
                <SectionHeader title="Estilo y Voz" icon={PenTool} description="Elementos estilísticos que se deben preservar o potenciar." />
                <JsonEditor 
                  data={bible.voz_del_autor || {}} 
                  onChange={(v) => updateSection('voz_del_autor', v)} 
                />
              </div>
            )}

             {/* 5. GUIA PARA CLAUDE */}
             {activeSection === 'guia' && (
              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 animate-fadeIn">
                <SectionHeader title="Instrucciones de Edición" icon={Flag} description="Directrices específicas que la IA seguirá durante la reescritura." />
                <JsonEditor 
                  data={bible.guia_para_claude || {}} 
                  onChange={(v) => updateSection('guia_para_claude', v)} 
                />
              </div>
            )}
             
             {/* Fallback Debug */}
             <div className="mt-12 pt-8 border-t border-gray-200">
               <details>
                 <summary className="cursor-pointer text-xs font-bold uppercase text-gray-400 hover:text-gray-600 mb-2 select-none">
                    Ver JSON Completo (Raw Debug)
                 </summary>
                 <textarea 
                    className="w-full h-64 p-4 text-xs font-mono bg-gray-100 border border-gray-200 rounded text-gray-600 outline-none mt-2"
                    value={JSON.stringify(bible, null, 2)}
                    readOnly
                 />
               </details>
             </div>

          </div>
        </div>
      </main>
    </div>
  );
}

// --- Componentes UI ---

function NavItem({ icon: Icon, label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all group mb-1
        ${active 
          ? 'bg-blue-50 text-theme-primary ring-1 ring-blue-100' 
          : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}
      `}
    >
      <div className="flex items-center gap-3">
        <Icon className={`w-4 h-4 ${active ? 'text-theme-primary' : 'text-gray-400 group-hover:text-gray-600'}`} />
        <span>{label}</span>
      </div>
      {active && <ChevronRight className="w-3 h-3 text-theme-primary" />}
    </button>
  );
}

function SectionHeader({ title, icon: Icon, description }) {
  return (
    <div className="flex items-start gap-4 mb-6 border-b border-gray-100 pb-6">
      <div className="p-3 bg-blue-50 rounded-xl text-theme-primary shrink-0">
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <h3 className="font-editorial text-2xl font-bold text-gray-900 leading-tight">{title}</h3>
        {description && <p className="text-gray-500 mt-1 text-sm">{description}</p>}
      </div>
    </div>
  );
}

// Editor JSON mejorado
function JsonEditor({ data, onChange }) {
  const [text, setText] = useState(JSON.stringify(data, null, 2));
  const [error, setError] = useState(false);

  // Sincronizar si la data externa cambia (ej. al cambiar de tab)
  useEffect(() => {
    setText(JSON.stringify(data, null, 2));
  }, [data]);

  const handleChange = (e) => {
    const val = e.target.value;
    setText(val);
    try {
      const parsed = JSON.parse(val);
      onChange(parsed);
      setError(false);
    } catch (err) {
      setError(true);
    }
  };

  return (
    <div className="relative group">
      <div className={`absolute top-2 right-2 px-2 py-1 rounded text-xs font-bold ${error ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600 opacity-0 group-hover:opacity-100 transition-opacity'}`}>
        {error ? 'JSON Inválido' : 'Válido'}
      </div>
      <textarea
        className={`
          w-full h-[500px] p-4 font-mono text-sm leading-relaxed rounded-lg border outline-none transition-all resize-y
          ${error 
            ? 'bg-red-50 border-red-300 focus:ring-red-200' 
            : 'bg-gray-50 border-gray-200 focus:border-blue-500 focus:ring-2 focus:ring-blue-100'}
        `}
        value={text}
        onChange={handleChange}
        spellCheck={false}
      />
      <p className="text-xs text-gray-400 mt-2 text-right">
        Edita con cuidado. La IA usará estos valores estrictamente.
      </p>
    </div>
  );
}