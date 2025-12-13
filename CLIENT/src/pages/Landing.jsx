import PublicNavbar from '../components/PublicNavbar';
import { Link } from 'react-router-dom';

const Landing = () => {
  return (
    <div className="min-h-screen bg-[#F9FAFB] text-gray-900 font-sans selection:bg-theme-primary selection:text-white">
      <PublicNavbar />

      <main className="pt-36 pb-20">
        
        {/* HERO SECTION */}
        <div className="max-w-4xl mx-auto px-6 text-center mb-24">
          <div className="inline-block mb-6 border-b-2 border-theme-primary pb-1">
            <span className="font-mono text-xs text-theme-primary font-bold uppercase tracking-[0.2em]">
              Tecnología de Edición Profunda
            </span>
          </div>
          
          {/* Título más grueso (semibold) para mejor lectura */}
          <h1 className="font-editorial text-5xl md:text-7xl font-semibold leading-[1.1] mb-8 text-gray-900">
            Donde la intuición creativa encuentra la <span className="italic text-gray-500 font-medium">precisión estructural.</span>
          </h1>
          
          <p className="font-editorial text-xl text-gray-600 leading-relaxed max-w-2xl mx-auto mb-12">
            LYA no corrige, ELEVA. Analiza el ritmo, la causalidad y los arcos de personajes, transformando tu manuscrito en una obra editorialmente viable.
          </p>

          <div className="flex justify-center gap-4">
            {/* CTA PRINCIPAL MEJORADO: Texto más grande (text-sm) y tracking moderado */}
            <Link 
              to="/login"
              className="bg-theme-primary text-white px-12 py-4 text-sm font-bold uppercase tracking-wider shadow-lg transition-all duration-300 transform hover:bg-theme-primaryHover hover:scale-105 hover:-translate-y-1 rounded-sm"
            >
              Comenzar Ahora
            </Link>
          </div>
        </div>

        {/* FEATURES GRID */}
        <div className="max-w-7xl mx-auto px-6 border-t border-gray-300 pt-16">
          <div className="grid md:grid-cols-3 gap-12 lg:gap-16">
            
            {/* Feature 1 */}
            <article className="group cursor-default">
              <div className="flex items-baseline gap-3 mb-4">
                <span className="font-mono text-4xl font-light text-theme-primary/40 group-hover:text-theme-primary transition-colors duration-300">01</span>
                <h3 className="font-editorial text-2xl font-bold group-hover:text-theme-primary transition-colors duration-300">Análisis Estructural</h3>
              </div>
              <p className="font-serif text-gray-600 leading-7 text-sm text-justify border-l-2 border-transparent group-hover:border-theme-primary pl-4 transition-all duration-300">
                Disección automática de cada escena. Evaluamos los vectores de tensión y los puntos de giro para asegurar que la narrativa nunca pierda impulso.
              </p>
            </article>

            {/* Feature 2 */}
            <article className="group cursor-default">
              <div className="flex items-baseline gap-3 mb-4">
                <span className="font-mono text-4xl font-light text-theme-primary/40 group-hover:text-theme-primary transition-colors duration-300">02</span>
                <h3 className="font-editorial text-2xl font-bold group-hover:text-theme-primary transition-colors duration-300">Mapa de Arcos</h3>
              </div>
              <p className="font-serif text-gray-600 leading-7 text-sm text-justify border-l-2 border-transparent group-hover:border-theme-primary pl-4 transition-all duration-300">
                Seguimiento psicológico de personajes. Detectamos inconsistencias en el comportamiento y la voz a lo largo de miles de páginas.
              </p>
            </article>

            {/* Feature 3 */}
            <article className="group cursor-default">
              <div className="flex items-baseline gap-3 mb-4">
                <span className="font-mono text-4xl font-light text-theme-primary/40 group-hover:text-theme-primary transition-colors duration-300">03</span>
                <h3 className="font-editorial text-2xl font-bold group-hover:text-theme-primary transition-colors duration-300">Edición LYA</h3>
              </div>
              <p className="font-serif text-gray-600 leading-7 text-sm text-justify border-l-2 border-transparent group-hover:border-theme-primary pl-4 transition-all duration-300">
                Sugerencias de reescritura que respetan tu estilo. No corregimos ortografía; elevamos tu prosa utilizando modelos de lenguaje calibrados editorialmente.
              </p>
            </article>

          </div>
        </div>

      </main>

      <footer className="bg-white border-t border-gray-200 py-12 text-center">
        <div className="flex flex-col items-center gap-2">
            <p className="font-serif text-3xl font-bold text-gray-900">LYA</p>
            
            {/* SIGNIFICADO - EDITABLE AQUÍ */}
            <p className="font-mono text-[10px] text-theme-primary font-bold uppercase tracking-[0.25em]">
                LOGIC YIELD ASSISTANT
            </p>
            {/* --------------------------- */}

            <a href="https://plotscope.net" className="font-sans text-xs font-bold text-gray-500 hover:text-theme-primary transition-colors mt-8 mb-2 uppercase tracking-wide flex items-center gap-1">
              Conoce PlotScope, la empresa detrás de LYA <span>&rarr;</span>
            </a>

            <p className="font-mono text-[10px] text-gray-400 uppercase tracking-widest mt-4">
              © 2025 PlotScope. Todos los derechos reservados.
            </p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
