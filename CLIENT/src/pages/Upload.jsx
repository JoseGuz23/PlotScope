import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadAPI } from '../services/api';

export default function Upload() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      if (!projectName) {
        const name = e.target.files[0].name.replace(/\.[^/.]+$/, "");
        setProjectName(name);
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file || !projectName) return;

    setIsUploading(true);
    setError('');

    try {
      await uploadAPI.uploadManuscript(file, projectName);
      navigate('/dashboard');
    } catch (err) {
      console.error(err);
      setError('Error al subir el archivo. Intenta de nuevo.');
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto pt-10">
      <div className="text-center mb-12">
        <span className="font-mono text-xs font-bold text-theme-primary uppercase tracking-widest mb-2 block">
          Paso 1 de 3
        </span>
        <h1 className="font-editorial text-4xl font-bold text-gray-900 mb-4">
          Cargar Manuscrito
        </h1>
        <p className="font-sans text-gray-500">
          Sube tu archivo .docx para comenzar la segmentación y análisis.
        </p>
      </div>

      <div className="bg-white border-t-4 border-gray-900 shadow-xl p-10 rounded-sm">
        <form onSubmit={handleSubmit} className="space-y-8">
          
          <div>
            <label className="block text-xs font-extrabold uppercase text-gray-500 mb-2 tracking-wide">
              Título de la Obra
            </label>
            <input
              type="text"
              value={projectName}
              onChange={(e) => setProjectName(e.target.value)}
              placeholder="Ej. La Sombra del Viento"
              className="w-full p-4 border-2 border-gray-200 rounded-sm font-editorial text-xl text-gray-900 focus:border-theme-primary focus:outline-none transition-colors placeholder-gray-300"
              disabled={isUploading}
            />
          </div>

          <div>
            <label className="block text-xs font-extrabold uppercase text-gray-500 mb-2 tracking-wide">
              Archivo Fuente (.docx)
            </label>
            <div className={`
              border-2 border-dashed rounded-sm p-12 text-center transition-all cursor-pointer group
              ${file ? 'border-theme-primary bg-green-50' : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'}
            `}>
              <input
                type="file"
                accept=".docx"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
                disabled={isUploading}
              />
              <label htmlFor="file-upload" className="cursor-pointer block w-full h-full">
                {file ? (
                  <div>
                    <div className="text-4xl mb-3"></div>
                    <p className="font-bold text-theme-primary text-lg">{file.name}</p>
                    <p className="font-mono text-xs text-gray-500 mt-2">{(file.size / 1024 / 1024).toFixed(2)} MB • Listo para subir</p>
                  </div>
                ) : (
                  <div>
                    <div className="text-4xl mb-3 text-gray-300 group-hover:text-gray-400 transition-colors">⬇</div>
                    <p className="font-bold text-gray-900">Haz clic para seleccionar</p>
                    <p className="font-sans text-sm text-gray-500 mt-1">Soporta documentos Word estándar</p>
                  </div>
                )}
              </label>
            </div>
          </div>

          {error && (
            <div className="text-red-700 text-sm font-bold text-center bg-red-50 p-4 border border-red-100 rounded-sm">
              ⚠️ {error}
            </div>
          )}

          <div className="pt-6">
            <button
              type="submit"
              disabled={!file || !projectName || isUploading}
              className="w-full bg-theme-primary hover:bg-theme-primary-hover text-white font-extrabold py-4 px-6 rounded-sm shadow-lg transition-all transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed uppercase tracking-widest text-sm"
            >
              {isUploading ? 'Procesando Manuscrito...' : 'INICIAR ORQUESTACIÓN'}
            </button>
          </div>

        </form>
      </div>
    </div>
  );
}