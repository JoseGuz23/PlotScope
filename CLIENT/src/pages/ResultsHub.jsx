import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
// Asegúrate de que estas importaciones son CORRECTAS
import EditorialLetter from './EditorialLetter';
import Editor from './Editor';
import { FileText, PenTool, Layout as LayoutIcon, Loader2 } from 'lucide-react';

export default function ResultsHub() {
  // El contexto (project) se obtiene del componente padre ProjectLayout.
  const { project } = useOutletContext();
  const [activeSubTab, setActiveSubTab] = useState('carta'); 

  // Si el proyecto no está disponible o no ha pasado las fases iniciales
  if (project?.status !== 'completed' && project?.status !== 'failed' && project?.status !== 'terminated') {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-gray-50/50 text-center p-8">
        <div className="bg-white p-10 rounded-2xl shadow-lg border border-gray-100 max-w-md">
          <div className="w-16 h-16 bg-yellow-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <LayoutIcon className="w-8 h-8 text-yellow-500 opacity-70" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Entregables No Disponibles</h2>
          <p className="text-gray-500 mb-6">
            La Carta Editorial, las Notas de Margen y el Editor se generan después de la Fase de **Biblia Narrativa**. 
            Por favor, revisa la pestaña anterior y aprueba la Biblia para continuar.
          </p>
          <Loader2 className="w-6 h-6 animate-spin text-theme-primary mx-auto" />
        </div>
      </div>
    );
  }
  
  // Si está completado, mostramos el Hub de sub-pestañas
  return (
    <div className="flex flex-col h-full">
      {/* SUB-NAVEGACIÓN TIPO "TOGGLE" */}
      <div className="bg-white border-b border-gray-200 px-6 py-2 flex justify-center shrink-0">
        <div className="bg-gray-100 p-1 rounded-lg flex gap-1">
          <button
            onClick={() => setActiveSubTab('carta')}
            className={`
              flex items-center gap-2 px-6 py-2 rounded-md text-xs font-bold transition-all uppercase tracking-wide
              ${activeSubTab === 'carta' ? 'bg-white shadow text-theme-primary' : 'text-gray-500 hover:text-gray-700'}
            `}
          >
            <FileText className="w-4 h-4" /> Carta Editorial
          </button>
          <button
            onClick={() => setActiveSubTab('editor')}
            className={`
              flex items-center gap-2 px-6 py-2 rounded-md text-xs font-bold transition-all uppercase tracking-wide
              ${activeSubTab === 'editor' ? 'bg-white shadow text-theme-primary' : 'text-gray-500 hover:text-gray-700'}
            `}
          >
            <PenTool className="w-4 h-4" /> Editor & Notas
          </button>
        </div>
      </div>

      {/* CONTENIDO */}
      <div className="flex-1 overflow-hidden relative">
        {/* Aquí es donde se resuelven las importaciones de los componentes que estaban en gris */}
        {activeSubTab === 'carta' 
          ? <EditorialLetter /> 
          : <Editor />}
      </div>
    </div>
  );
}