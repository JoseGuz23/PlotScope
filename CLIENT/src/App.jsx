import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          {/* Futuras rutas:
          <Route path="/project/:id" element={<ProjectDashboard />} />
          <Route path="/config" element={<ConfigPage />} />
          */}
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;