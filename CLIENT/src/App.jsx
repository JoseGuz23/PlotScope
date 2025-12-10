// =============================================================================
// App.jsx - RUTAS 5.0 (Centro de Mando)
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
import Features from './pages/Features'; 
import Pricing from './pages/Pricing';   
import Credits from './pages/Credits';
// Componentes de Estructura 5.0
import ProjectLayout from './components/ProjectLayout'; 
import ResultsHub from './pages/ResultsHub'; 

function ProtectedRoute({ children }) {
  if (!authAPI.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return <Layout>{children}</Layout>;
}

function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 font-sans">
      <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
      <p className="text-xl text-gray-600 mb-8">Página no encontrada</p>
      <a href="/" className="text-theme-primary font-bold hover:underline">Inicio</a>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/caracteristicas" element={<Features />} />
          <Route path="/precios" element={<Pricing />} />
          <Route path="/login" element={<Login />} />
          
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/creditos" element={<ProtectedRoute><Credits /></ProtectedRoute>} />
          <Route path="/nuevo" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
          
          {/* --- CENTRO DE MANDO DEL PROYECTO --- */}
          <Route path="/proyecto/:id" element={<ProtectedRoute><ProjectLayout /></ProtectedRoute>}>
            <Route index element={<Navigate to="status" replace />} />
            
            {/* Pestaña 1: Estado */}
            <Route path="status" element={<ProjectStatus />} />
            
            {/* Pestaña 2: Biblia */}
            <Route path="biblia" element={<BibleReview />} />
            
            {/* Pestaña 3: Resultados (Carta + Editor) */}
            <Route path="resultados" element={<ResultsHub />} />
            
            {/* Redirecciones de seguridad */}
            <Route path="carta" element={<Navigate to="../resultados" replace />} />
            <Route path="editor" element={<Navigate to="../resultados" replace />} />
          </Route>
          
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;