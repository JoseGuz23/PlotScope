import { BrowserRouter, Routes, Route } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Aquí pondremos tus páginas pronto */}
        <Route path="/" element={<h1 className="text-3xl font-bold text-theme-primary p-10">LYA está lista para configurarse.</h1>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;