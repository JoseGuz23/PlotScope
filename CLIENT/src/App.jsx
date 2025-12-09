// =============================================================================
// App.jsx - RUTAS COMPLETAS CON STATUS DE PROCESAMIENTO
// =============================================================================

import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { authAPI } from './services/api';
import Layout from './components/Layout';

// Páginas
import Landing from './pages/Landing';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import ProjectStatus from './pages/ProjectStatus';  // NUEVO
import BibleReview from './pages/BibleReview';
import Editor from './pages/Editor';
import Features from './pages/Features'; 
import Pricing from './pages/Pricing';   
import Credits from './pages/Credits';   

// --- CONTROL DE ACCESO ---

// 1. Ruta Protegida: Solo deja pasar si hay token
function ProtectedRoute({ children }) {
  if (!authAPI.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <Layout>{children}</Layout>;
}

// Router auxiliar para proyectos - redirige según estado
function ProjectRouter() {
  const { id } = useParams();
  // Por defecto ir al editor, pero el backend puede indicar otro destino
  return <Navigate to={`/proyecto/${id}/editor`} replace />;
}

// 404
function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 font-sans">
      <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
      <p className="text-xl text-gray-600 mb-8">Página no encontrada</p>
      <a href="/" className="text-theme-primary font-bold hover:underline">Volver al inicio</a>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* RUTA RAÍZ: Siempre muestra Landing */}
          <Route path="/" element={<Landing />} />
          
          {/* RUTAS PÚBLICAS */}
          <Route path="/caracteristicas" element={<Features />} />
          <Route path="/precios" element={<Pricing />} />
          <Route path="/login" element={<Login />} />
          
          {/* WORKSPACE (Rutas Protegidas) */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/creditos" element={
            <ProtectedRoute>
              <Credits />
            </ProtectedRoute>
          } />
          
          {/* NUEVO PROYECTO */}
          <Route path="/nuevo" element={
            <ProtectedRoute>
              <Upload />
            </ProtectedRoute>
          } />
          
          {/* PROYECTO: Redirige según estado */}
          <Route path="/proyecto/:id" element={
            <ProtectedRoute>
              <ProjectRouter />
            </ProtectedRoute>
          } />
          
          {/* NUEVO: Estado de procesamiento */}
          <Route path="/proyecto/:id/status" element={
            <ProtectedRoute>
              <ProjectStatus />
            </ProtectedRoute>
          } />
          
          {/* Revisión de Biblia */}
          <Route path="/proyecto/:id/biblia" element={
            <ProtectedRoute>
              <BibleReview />
            </ProtectedRoute>
          } />
          
          {/* Editor de cambios */}
          <Route path="/proyecto/:id/editor" element={
            <ProtectedRoute>
              <Editor />
            </ProtectedRoute>
          } />
          
          {/* Redirecciones Legacy */}
          <Route path="/biblioteca" element={<Navigate to="/dashboard" replace />} />
          <Route path="/config" element={<Navigate to="/dashboard" replace />} />
          <Route path="/api" element={<Navigate to="/dashboard" replace />} />
          
          {/* 404 Catch-all */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;