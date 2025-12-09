// =============================================================================
// BibleReview.jsx - DASHBOARD DE APROBACIÓN EDITORIAL
// =============================================================================

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { bibleAPI } from '../services/api';
import { 
  Book, Users, Anchor, Flag, Save, CheckCircle2, 
  ChevronRight, AlertCircle, Loader2, Edit3, ArrowLeft 
} from 'lucide-react';

export default function BibleReview() {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  
  const [bible, setBible] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [approving, setApproving] = useState(false);
  const [activeSection, setActiveSection] = useState('resumen'); // 'resumen', 'personajes', 'temas'

  useEffect(() => {
    loadBible();
  }, [projectId]);

  async function loadBible() {
    try {
      const data = await bibleAPI.get(projectId);
      setBible(data);
    } catch (err) {
      console.error(err);
      alert('Error cargando la Biblia. Asegúrate de que la fase de análisis haya terminado.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSave() {
    setSaving(true);
    try {
      await bibleAPI.save(projectId, bible);
      // Feedback visual sutil podría ir aquí
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
      
      // 3. Redirigir al status para ver cómo avanza la edición
      navigate(`/proyecto/${projectId}/status`);
    } catch (err) {
      alert('Error al aprobar: ' + err.message);
      setApproving(false);
    }
  }

  // Render helpers
  const updateField = (section, key, value) => {
    setBible(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50 text-gray-500 gap-4">
      <Loader2 className="w-10 h-10 animate-spin text-theme-primary" />
      <p className="font-mono text-xs uppercase tracking-widest">Cargando Biblia Narrativa...</p>
    </div>
  );

  if (!bible) return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50 gap-4">
      <AlertCircle className="w-12 h-12 text-red-400" />
      <h2 className="text-xl font-bold text-gray-800">No se encontró la Biblia</h2>
      <button onClick={() => navigate(-1)} className="text-blue-600 hover:underline">Volver</button>
    </div>
  );

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden font-sans">
      
      {/* SIDEBAR DE NAVEGACIÓN */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0">
        <div className="p-6 border-b border-gray-100">
          <h1 className="font-editorial text-2xl font-bold text-gray-900">Biblia Narrativa</h1>
          <p className="text-xs text-gray-400 mt-1 font-mono">ID: {projectId.substring(0, 8)}</p>
        </div>
        
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <NavItem 
            icon={Book} label="Resumen y Tono" 
            active={activeSection === 'resumen'} 
            onClick={() => setActiveSection('resumen')} 
          />
          <NavItem 
            icon={Users} label="Personajes" 
            active={activeSection === 'personajes'} 
            onClick={() => setActiveSection('personajes')} 
          />
          <NavItem 
            icon={Anchor} label="Estructura" 
            active={activeSection === 'estructura'} 
            onClick={() => setActiveSection('estructura')} 
          />
          <NavItem 
            icon={Flag} label="Temas Clave" 
            active={activeSection === 'temas'} 
            onClick={() => setActiveSection('temas')} 
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
            <h2 className="text-sm font-bold uppercase tracking-widest text-gray-500">Editando Sección</h2>
            <p className="text-xl font-bold text-gray-900 capitalize">{activeSection}</p>
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
          <div className="max-w-4xl mx-auto space-y-8 pb-20">
            
            {/* RENDERIZADO DINÁMICO SEGÚN SECCIÓN */}
            {activeSection === 'resumen' && (
              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 animate-fadeIn">
                <SectionHeader title="Resumen Ejecutivo" icon={Book} />
                <JsonEditor data={bible.holistic_analysis || {}} onChange={(v) => updateField('holistic_analysis', null, v)} />
              </div>
            )}

            {activeSection === 'personajes' && (
              <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-200 animate-fadeIn">
                <SectionHeader title="Fichas de Personajes" icon={Users} />
                <JsonEditor data={bible.character_profiles || []} onChange={(v) => updateField('character_profiles', null, v)} />
              </div>
            )}

             {/* Puedes agregar más secciones específicas aquí */}
             
             {/* Fallback genérico para ver todo el JSON si hace falta */}
             <div className="mt-8 bg-gray-100 p-4 rounded-lg border border-gray-200">
               <h4 className="text-xs font-bold uppercase text-gray-500 mb-2">Vista Raw (Debug)</h4>
               <textarea 
                  className="w-full h-64 p-4 text-xs font-mono bg-white border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 outline-none"
                  value={JSON.stringify(bible, null, 2)}
                  onChange={(e) => {
                    try {
                      setBible(JSON.parse(e.target.value));
                    } catch(err) { /* ignore invalid json while typing */ }
                  }}
               />
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
        w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all group
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

function SectionHeader({ title, icon: Icon }) {
  return (
    <div className="flex items-center gap-3 mb-6 border-b border-gray-100 pb-4">
      <div className="p-2 bg-blue-50 rounded-lg text-theme-primary">
        <Icon className="w-5 h-5" />
      </div>
      <h3 className="font-editorial text-xl font-bold text-gray-900">{title}</h3>
    </div>
  );
}

// Editor simple para objetos JSON (se puede mejorar con un editor real si hay tiempo)
function JsonEditor({ data, onChange }) {
  const [text, setText] = useState(JSON.stringify(data, null, 2));

  const handleChange = (e) => {
    const val = e.target.value;
    setText(val);
    try {
      onChange(JSON.parse(val));
    } catch (err) {
      // Allow typing invalid JSON
    }
  };

  return (
    <div>
      <p className="text-sm text-gray-500 mb-2">Edita los valores directamente. Mantén el formato JSON.</p>
      <textarea
        className="w-full h-96 p-4 font-mono text-sm bg-gray-50 border border-gray-200 rounded-lg focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-all resize-y"
        value={text}
        onChange={handleChange}
        spellCheck={false}
      />
    </div>
  );
}