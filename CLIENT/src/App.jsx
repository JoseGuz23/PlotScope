// =============================================================================
// App.jsx - RUTAS PRINCIPALES DE SYLPHRENA (CON AUTH)
// =============================================================================

import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { authAPI } from './services/api';
import Layout from './components/Layout';

// Páginas
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import BibleReview from './pages/BibleReview';
import Editor from './pages/Editor';
import Login from './pages/Login';

// Componente para rutas protegidas
function ProtectedRoute({ children }) {
  if (!authAPI.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

// Página 404
function NotFound() {
  return (
    <div style={{ textAlign: 'center', padding: '4rem 0' }}>
      <h1 style={{ fontSize: '4rem', color: '#D1D5DB', marginBottom: '1rem' }}>404</h1>
      <p style={{ fontSize: '1.25rem', color: 'var(--color-subtle)', marginBottom: '1.5rem' }}>
        Página no encontrada
      </p>
      <a href="/" className="project-link">
        Volver al inicio →
      </a>
    </div>
  );
}

// Router inteligente para proyectos
function ProjectRouter() {
  const { id } = useParams();
  return <Navigate to={`/proyecto/${id}/editor`} replace />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Login - público */}
          <Route path="/login" element={<Login />} />
          
          {/* Rutas protegidas - requieren auth */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout><Dashboard /></Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/nuevo" element={
            <ProtectedRoute>
              <Layout><Upload /></Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/proyecto/:id" element={
            <ProtectedRoute>
              <Layout><ProjectRouter /></Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/proyecto/:id/biblia" element={
            <ProtectedRoute>
              <Layout><BibleReview /></Layout>
            </ProtectedRoute>
          } />
          
          <Route path="/proyecto/:id/editor" element={
            <ProtectedRoute>
              <Layout><Editor /></Layout>
            </ProtectedRoute>
          } />
          
          {/* Rutas legacy */}
          <Route path="/biblioteca" element={<Navigate to="/" replace />} />
          <Route path="/config" element={<Navigate to="/" replace />} />
          <Route path="/api" element={<Navigate to="/" replace />} />
          
          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
