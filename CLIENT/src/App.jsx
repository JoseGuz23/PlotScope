// =============================================================================
// App.jsx - RUTAS PRINCIPALES DE SYLPHRENA
// =============================================================================

import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { authAPI } from './services/api';
import Layout from './components/Layout';

// Páginas
import Landing from './pages/Landing'; // Asegúrate de haber creado este archivo
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import BibleReview from './pages/BibleReview';
import Editor from './pages/Editor';

// --- CONTROL DE RUTAS ---

// 1. Si no hay usuario, mostrar Landing
function HomeWrapper() {
  if (authAPI.isAuthenticated()) {
    return <Navigate to="/dashboard" replace />;
  }
  return <Landing />;
}

// 2. Si hay usuario, permitir acceso (Layout interno)
function ProtectedRoute({ children }) {
  if (!authAPI.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <Layout>{children}</Layout>;
}

// 3. Router para proyectos
function ProjectRouter() {
  const { id } = useParams();
  return <Navigate to={`/proyecto/${id}/editor`} replace />;
}

// 4. Página 404
function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 font-editorial">
      <h1 className="text-6xl text-gray-300 mb-4">404</h1>
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
          {/* Ruta Raíz: Landing o Dashboard según estado */}
          <Route path="/" element={<HomeWrapper />} />

          {/* Login Público */}
          <Route path="/login" element={<Login />} />
          
          {/* Rutas Protegidas (Dashboard ahora es explícito) */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/nuevo" element={
            <ProtectedRoute>
              <Upload />
            </ProtectedRoute>
          } />
          
          <Route path="/proyecto/:id" element={
            <ProtectedRoute>
              <ProjectRouter />
            </ProtectedRoute>
          } />
          
          <Route path="/proyecto/:id/biblia" element={
            <ProtectedRoute>
              <BibleReview />
            </ProtectedRoute>
          } />
          
          <Route path="/proyecto/:id/editor" element={
            <ProtectedRoute>
              <Editor />
            </ProtectedRoute>
          } />
          
          {/* Redirecciones Legacy */}
          <Route path="/biblioteca" element={<Navigate to="/dashboard" replace />} />
          <Route path="/config" element={<Navigate to="/dashboard" replace />} />
          <Route path="/api" element={<Navigate to="/dashboard" replace />} />
          
          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;