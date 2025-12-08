// =============================================================================
// BibleReview.jsx - REVISAR Y EDITAR BIBLIA NARRATIVA
// =============================================================================
// Transforma el JSON técnico en formato visual humano editable
// =============================================================================

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { bibleAPI } from '../services/api';
import {
  BookOpen,
  Users,
  Sparkles,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Save,
  CheckCircle,
  Loader2,
  Plus,
  Trash2,
  ArrowRight,
} from 'lucide-react';

// Componente para secciones colapsables
function Section({ title, icon: Icon, children, defaultOpen = true }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-theme-border bg-white rounded-sm mb-6">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 transition"
      >
        <div className="flex items-center gap-3">
          <Icon className="text-theme-primary" size={20} />
          <h2 className="font-report-serif font-bold text-lg text-theme-text">
            {title}
          </h2>
        </div>
        {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
      </button>
      {isOpen && <div className="px-4 pb-4 border-t border-theme-border pt-4">{children}</div>}
    </div>
  );
}

// Campo editable
function EditableField({ label, value, onChange, type = 'text', placeholder = '' }) {
  return (
    <div className="mb-4">
      <label className="data-label block mb-1">{label}</label>
      {type === 'textarea' ? (
        <textarea
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full px-3 py-2 border border-theme-border rounded-sm font-report-mono text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/30 min-h-[80px]"
        />
      ) : (
        <input
          type={type}
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full px-3 py-2 border border-theme-border rounded-sm font-report-mono text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/30"
        />
      )}
    </div>
  );
}

// Lista editable (para NO_CORREGIR, recursos, etc.)
function EditableList({ items, onChange, placeholder = 'Nuevo elemento...' }) {
  const [newItem, setNewItem] = useState('');

  const addItem = () => {
    if (newItem.trim()) {
      onChange([...items, newItem.trim()]);
      setNewItem('');
    }
  };

  const removeItem = (index) => {
    onChange(items.filter((_, i) => i !== index));
  };

  return (
    <div>
      <ul className="space-y-2 mb-3">
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-sm">
            <span className="flex-1 text-sm font-report-mono">{item}</span>
            <button
              onClick={() => removeItem(index)}
              className="text-red-500 hover:text-red-700 transition"
            >
              <Trash2 size={16} />
            </button>
          </li>
        ))}
      </ul>
      <div className="flex gap-2">
        <input
          type="text"
          value={newItem}
          onChange={(e) => setNewItem(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && addItem()}
          placeholder={placeholder}
          className="flex-1 px-3 py-2 border border-theme-border rounded-sm text-sm focus:outline-none focus:ring-2 focus:ring-theme-primary/30"
        />
        <button
          onClick={addItem}
          className="px-3 py-2 bg-theme-primary text-white rounded-sm hover:bg-theme-primary/80 transition"
        >
          <Plus size={18} />
        </button>
      </div>
    </div>
  );
}

// Tarjeta de personaje
function CharacterCard({ character, onChange, onRemove, type }) {
  const bgColor = type === 'protagonista' 
    ? 'bg-blue-50 border-blue-200' 
    : type === 'antagonista' 
      ? 'bg-red-50 border-red-200' 
      : 'bg-gray-50 border-gray-200';

  return (
    <div className={`border ${bgColor} rounded-sm p-4 mb-4`}>
      <div className="flex justify-between items-start mb-3">
        <input
          type="text"
          value={character.nombre || ''}
          onChange={(e) => onChange({ ...character, nombre: e.target.value })}
          className="font-bold text-lg bg-transparent border-b border-transparent hover:border-theme-border focus:border-theme-primary focus:outline-none"
          placeholder="Nombre del personaje"
        />
        <button onClick={onRemove} className="text-red-500 hover:text-red-700">
          <Trash2 size={18} />
        </button>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="data-label block mb-1">Rol / Arquetipo</label>
          <input
            type="text"
            value={character.rol_arquetipo || ''}
            onChange={(e) => onChange({ ...character, rol_arquetipo: e.target.value })}
            className="w-full px-2 py-1 border border-theme-border rounded-sm text-sm"
          />
        </div>
        <div>
          <label className="data-label block mb-1">Motivación</label>
          <input
            type="text"
            value={character.motivacion_principal || ''}
            onChange={(e) => onChange({ ...character, motivacion_principal: e.target.value })}
            className="w-full px-2 py-1 border border-theme-border rounded-sm text-sm"
          />
        </div>
      </div>
      
      <div className="mt-3">
        <label className="data-label block mb-1">Arco del Personaje</label>
        <textarea
          value={character.arco_personaje || ''}
          onChange={(e) => onChange({ ...character, arco_personaje: e.target.value })}
          className="w-full px-2 py-1 border border-theme-border rounded-sm text-sm min-h-[60px]"
        />
      </div>
    </div>
  );
}

export default function BibleReview() {
  const { id: projectId } = useParams();
  const navigate = useNavigate();
  
  const [bible, setBible] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    loadBible();
  }, [projectId]);

  async function loadBible() {
    try {
      setIsLoading(true);
      const data = await bibleAPI.get(projectId);
      setBible(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }

  // Helper para actualizar campos anidados
  function updateBible(path, value) {
    setBible(prev => {
      const newBible = { ...prev };
      const keys = path.split('.');
      let obj = newBible;
      
      for (let i = 0; i < keys.length - 1; i++) {
        obj[keys[i]] = { ...obj[keys[i]] };
        obj = obj[keys[i]];
      }
      
      obj[keys[keys.length - 1]] = value;
      return newBible;
    });
    setHasChanges(true);
  }

  async function handleSave() {
    try {
      setIsSaving(true);
      await bibleAPI.save(projectId, bible);
      setHasChanges(false);
      alert('Biblia guardada correctamente');
    } catch (err) {
      alert('Error al guardar: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleApprove() {
    if (hasChanges) {
      if (!confirm('Tienes cambios sin guardar. ¿Guardar antes de aprobar?')) {
        return;
      }
      await handleSave();
    }

    try {
      setIsSaving(true);
      await bibleAPI.approve(projectId);
      navigate(`/proyecto/${projectId}/editor`);
    } catch (err) {
      alert('Error al aprobar: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="animate-spin text-theme-primary" size={40} />
        <span className="ml-3 text-theme-subtle">Cargando biblia narrativa...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-sm">
        <p className="font-bold">Error al cargar la biblia</p>
        <p>{error}</p>
      </div>
    );
  }

  if (!bible) return null;

  return (
    <>
      {/* Header */}
      <header className="report-divider py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-report-serif font-extrabold text-theme-text mb-2">
              BIBLIA NARRATIVA
            </h1>
            <p className="text-sm font-report-mono text-theme-subtle">
              Revisa y ajusta el análisis de tu obra antes de continuar
            </p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              className={`flex items-center gap-2 px-4 py-2 rounded-sm font-bold text-sm transition ${
                hasChanges 
                  ? 'bg-gray-800 text-white hover:bg-gray-700' 
                  : 'bg-gray-200 text-gray-500 cursor-not-allowed'
              }`}
            >
              <Save size={18} />
              Guardar
            </button>
            <button
              onClick={handleApprove}
              disabled={isSaving}
              className="flex items-center gap-2 bg-theme-primary text-white px-5 py-2 rounded-sm font-bold text-sm hover:bg-theme-primary/80 transition"
            >
              <CheckCircle size={18} />
              Aprobar y Continuar
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </header>

      {/* Indicador de cambios */}
      {hasChanges && (
        <div className="bg-amber-50 border border-amber-200 text-amber-700 px-4 py-2 rounded-sm mb-6 flex items-center gap-2">
          <AlertTriangle size={18} />
          <span className="text-sm font-bold">Tienes cambios sin guardar</span>
        </div>
      )}

      {/* SECCIÓN: IDENTIDAD DE LA OBRA */}
      <Section title="IDENTIDAD DE LA OBRA" icon={BookOpen}>
        <div className="grid grid-cols-2 gap-6">
          <EditableField
            label="Género"
            value={bible.identidad_obra?.genero}
            onChange={(v) => updateBible('identidad_obra.genero', v)}
          />
          <EditableField
            label="Subgénero"
            value={bible.identidad_obra?.subgenero}
            onChange={(v) => updateBible('identidad_obra.subgenero', v)}
          />
          <EditableField
            label="Tono Predominante"
            value={bible.identidad_obra?.tono_predominante}
            onChange={(v) => updateBible('identidad_obra.tono_predominante', v)}
          />
          <EditableField
            label="Estilo Narrativo"
            value={bible.identidad_obra?.estilo_narrativo}
            onChange={(v) => updateBible('identidad_obra.estilo_narrativo', v)}
          />
        </div>
        <EditableField
          label="Tema Central"
          value={bible.identidad_obra?.tema_central}
          onChange={(v) => updateBible('identidad_obra.tema_central', v)}
          type="textarea"
        />
        <EditableField
          label="Contrato con el Lector"
          value={bible.identidad_obra?.contrato_con_lector}
          onChange={(v) => updateBible('identidad_obra.contrato_con_lector', v)}
          type="textarea"
          placeholder="¿Qué promesa le haces al lector?"
        />
      </Section>

      {/* SECCIÓN: PERSONAJES */}
      <Section title="REPARTO DE PERSONAJES" icon={Users}>
        {/* Protagonistas */}
        <h3 className="font-bold text-theme-primary mb-3 uppercase text-sm tracking-wider">
          Protagonistas
        </h3>
        {bible.reparto_completo?.protagonistas?.map((char, idx) => (
          <CharacterCard
            key={idx}
            character={char}
            type="protagonista"
            onChange={(newChar) => {
              const updated = [...bible.reparto_completo.protagonistas];
              updated[idx] = newChar;
              updateBible('reparto_completo.protagonistas', updated);
            }}
            onRemove={() => {
              const updated = bible.reparto_completo.protagonistas.filter((_, i) => i !== idx);
              updateBible('reparto_completo.protagonistas', updated);
            }}
          />
        ))}
        <button
          onClick={() => {
            const updated = [...(bible.reparto_completo?.protagonistas || []), {
              nombre: '',
              rol_arquetipo: '',
              motivacion_principal: '',
              arco_personaje: '',
            }];
            updateBible('reparto_completo.protagonistas', updated);
          }}
          className="text-theme-primary text-sm font-bold flex items-center gap-1 hover:underline mb-6"
        >
          <Plus size={16} /> Agregar protagonista
        </button>

        {/* Antagonistas */}
        <h3 className="font-bold text-red-600 mb-3 uppercase text-sm tracking-wider">
          Antagonistas
        </h3>
        {bible.reparto_completo?.antagonistas?.map((char, idx) => (
          <CharacterCard
            key={idx}
            character={char}
            type="antagonista"
            onChange={(newChar) => {
              const updated = [...bible.reparto_completo.antagonistas];
              updated[idx] = newChar;
              updateBible('reparto_completo.antagonistas', updated);
            }}
            onRemove={() => {
              const updated = bible.reparto_completo.antagonistas.filter((_, i) => i !== idx);
              updateBible('reparto_completo.antagonistas', updated);
            }}
          />
        ))}
        <button
          onClick={() => {
            const updated = [...(bible.reparto_completo?.antagonistas || []), {
              nombre: '',
              rol_arquetipo: '',
              motivacion_principal: '',
              arco_personaje: '',
            }];
            updateBible('reparto_completo.antagonistas', updated);
          }}
          className="text-red-600 text-sm font-bold flex items-center gap-1 hover:underline mb-6"
        >
          <Plus size={16} /> Agregar antagonista
        </button>

        {/* Secundarios */}
        <h3 className="font-bold text-gray-600 mb-3 uppercase text-sm tracking-wider">
          Secundarios
        </h3>
        {bible.reparto_completo?.secundarios?.map((char, idx) => (
          <CharacterCard
            key={idx}
            character={char}
            type="secundario"
            onChange={(newChar) => {
              const updated = [...bible.reparto_completo.secundarios];
              updated[idx] = newChar;
              updateBible('reparto_completo.secundarios', updated);
            }}
            onRemove={() => {
              const updated = bible.reparto_completo.secundarios.filter((_, i) => i !== idx);
              updateBible('reparto_completo.secundarios', updated);
            }}
          />
        ))}
        <button
          onClick={() => {
            const updated = [...(bible.reparto_completo?.secundarios || []), {
              nombre: '',
              rol_arquetipo: '',
              motivacion_principal: '',
              arco_personaje: '',
            }];
            updateBible('reparto_completo.secundarios', updated);
          }}
          className="text-gray-600 text-sm font-bold flex items-center gap-1 hover:underline"
        >
          <Plus size={16} /> Agregar secundario
        </button>
      </Section>

      {/* SECCIÓN: VOZ DEL AUTOR */}
      <Section title="VOZ DEL AUTOR" icon={Sparkles}>
        <div className="grid grid-cols-2 gap-6 mb-6">
          <EditableField
            label="Estilo Detectado"
            value={bible.voz_del_autor?.estilo_detectado}
            onChange={(v) => updateBible('voz_del_autor.estilo_detectado', v)}
          />
          <EditableField
            label="Longitud de Oraciones"
            value={bible.voz_del_autor?.longitud_oraciones}
            onChange={(v) => updateBible('voz_del_autor.longitud_oraciones', v)}
          />
        </div>

        <div className="mb-6">
          <label className="data-label block mb-2">RECURSOS DISTINTIVOS</label>
          <EditableList
            items={bible.voz_del_autor?.recursos_distintivos || []}
            onChange={(v) => updateBible('voz_del_autor.recursos_distintivos', v)}
            placeholder="Nuevo recurso distintivo..."
          />
        </div>

        <div className="bg-amber-50 border border-amber-200 rounded-sm p-4">
          <label className="data-label block mb-2 text-amber-800">
            ⚠️ NO CORREGIR (Elementos intencionales)
          </label>
          <p className="text-xs text-amber-700 mb-3">
            Agrega aquí elementos que el editor NO debe modificar porque son intencionales.
          </p>
          <EditableList
            items={bible.voz_del_autor?.NO_CORREGIR || []}
            onChange={(v) => updateBible('voz_del_autor.NO_CORREGIR', v)}
            placeholder="Ej: Uso de regionalismos como 'chingón'"
          />
        </div>
      </Section>

      {/* SECCIÓN: MÉTRICAS */}
      <Section title="MÉTRICAS GLOBALES" icon={AlertTriangle} defaultOpen={false}>
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-sm">
            <p className="data-label">Palabras Totales</p>
            <p className="text-2xl font-report-mono font-bold">
              {bible.metricas_globales?.total_palabras?.toLocaleString() || '—'}
            </p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-sm">
            <p className="data-label">Capítulos</p>
            <p className="text-2xl font-report-mono font-bold">
              {bible.metricas_globales?.total_capitulos || '—'}
            </p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-sm">
            <p className="data-label">Score Global</p>
            <p className="text-2xl font-report-mono font-bold text-theme-primary">
              {bible.metricas_globales?.score_global || '—'}
            </p>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-sm">
            <p className="data-label">Coherencia</p>
            <p className="text-2xl font-report-mono font-bold text-green-600">
              {bible.metricas_globales?.score_coherencia_personajes || '—'}
            </p>
          </div>
        </div>
      </Section>

      {/* Footer con acciones */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-theme-border p-4 shadow-lg">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <p className="text-sm text-theme-subtle">
            {hasChanges ? '⚠️ Cambios sin guardar' : '✓ Todo guardado'}
          </p>
          <div className="flex gap-3">
            <button
              onClick={handleSave}
              disabled={!hasChanges || isSaving}
              className={`flex items-center gap-2 px-4 py-2 rounded-sm font-bold text-sm transition ${
                hasChanges 
                  ? 'bg-gray-800 text-white hover:bg-gray-700' 
                  : 'bg-gray-200 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isSaving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
              Guardar
            </button>
            <button
              onClick={handleApprove}
              disabled={isSaving}
              className="flex items-center gap-2 bg-theme-primary text-white px-6 py-2 rounded-sm font-bold text-sm hover:bg-theme-primary/80 transition"
            >
              <CheckCircle size={18} />
              Aprobar y Continuar al Editor
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Espaciado para el footer fijo */}
      <div className="h-24"></div>
    </>
  );
}
