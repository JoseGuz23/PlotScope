// =============================================================================
// App.jsx - RUTAS COMPLETAS SYLPHRENA 5.0 (Navegación Unificada)
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
import ProjectStatus from './pages/ProjectStatus';
import BibleReview from './pages/BibleReview';
import EditorialLetter from './pages/EditorialLetter'; // Se mantiene importado para el ResultsHub
import Editor from './pages/Editor'; // Se mantiene importado para el ResultsHub
import Features from './pages/Features'; 
import Pricing from './pages/Pricing';   
import Credits from './pages/Credits';
// NUEVOS COMPONENTES DE ESTRUCTURA
import ProjectLayout from './components/ProjectLayout'; 
import ResultsHub from './pages/ResultsHub'; 

// --- CONTROL DE ACCESO ---

// 1. Ruta Protegida: Solo deja pasar si hay token
function ProtectedRoute({ children }) {
  if (!authAPI.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <Layout>{children}</Layout>;
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
          
          {/* ======================================================= */}
          {/* ESTRUCTURA UNIFICADA DE PROYECTO (Centro de Mando)      */}
          {/* ======================================================= */}
          <Route path="/proyecto/:id" element={
            <ProtectedRoute>
              <ProjectLayout />
            </ProtectedRoute>
          }>
            {/* Redirección por defecto al Estado (Pestaña 1) */}
            <Route index element={<Navigate to="status" replace />} />

            {/* PESTAÑA 1: Estado del Proceso */}
            <Route path="status" element={<ProjectStatus />} />

            {/* PESTAÑA 2: Biblia Narrativa */}
            <Route path="biblia" element={<BibleReview />} />
            
            {/* PESTAÑA 3: Entregables Finales (Hub) */}
            <Route path="resultados" element={<ResultsHub />} />
            
            {/* Redirecciones Internas para Legacy/Botones */}
            <Route path="carta" element={<Navigate to="../resultados" replace />} />
            <Route path="editor" element={<Navigate to="../resultados" replace />} />

          </Route>
          
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