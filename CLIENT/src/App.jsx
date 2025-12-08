// =============================================================================
// App.jsx - RUTAS PRINCIPALES DE SYLPHRENA
// =============================================================================

import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Layout from './components/Layout';

// Páginas
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import BibleReview from './pages/BibleReview';
import Editor from './pages/Editor';

// Página 404
function NotFound() {
  return (
    <div className="text-center py-20">
      <h1 className="text-6xl font-report-mono font-bold text-gray-300 mb-4">404</h1>
      <p className="text-xl text-theme-subtle mb-6">Página no encontrada</p>
      <a 
        href="/" 
        className="text-theme-primary font-bold hover:underline"
      >
        Volver al inicio
      </a>
    </div>
  );
}

// Router inteligente para proyectos - decide a dónde ir según estado
function ProjectRouter() {
  const { id } = useParams();
  // TODO: Obtener estado real del proyecto y redirigir apropiadamente
  // Por ahora redirige al editor
  return <Navigate to={`/proyecto/${id}/editor`} replace />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            {/* Dashboard principal */}
            <Route path="/" element={<Dashboard />} />
            
            {/* Nuevo proyecto */}
            <Route path="/nuevo" element={<Upload />} />
            
            {/* Vista de proyecto - redirige según estado */}
            <Route path="/proyecto/:id" element={<ProjectRouter />} />
            
            {/* Revisión de Biblia */}
            <Route path="/proyecto/:id/biblia" element={<BibleReview />} />
            
            {/* Editor de manuscrito */}
            <Route path="/proyecto/:id/editor" element={<Editor />} />
            
            {/* Rutas legacy - redirigen */}
            <Route path="/library" element={<Navigate to="/" replace />} />
            <Route path="/config" element={<Navigate to="/" replace />} />
            <Route path="/api" element={<Navigate to="/" replace />} />
            
            {/* 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
