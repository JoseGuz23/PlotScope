// =============================================================================
// Features.jsx - ARQUITECTURA DE EDICIÓN LYA (Updated Models)
// =============================================================================

import { useState } from 'react';
import PublicNavbar from '../components/PublicNavbar';
import { Link } from 'react-router-dom';
import { BookOpen, BrainCircuit, ScrollText, PenTool, BarChart3, AlertTriangle, Wand2 } from 'lucide-react';

export default function Features() {
  const [activeStep, setActiveStep] = useState(0);

  const pipelineSteps = [
    {
      id: 0,
      title: "1. Segmentación Semántica",
      desc: "El motor descompone tu manuscrito en fragmentos lógicos, preservando el contexto narrativo de cada escena mediante procesamiento de lenguaje natural.",
      tech: "Azure Serverless + Python NLTK",
      icon: <BookOpen className="w-6 h-6" />
    },
    {
      id: 1,
      title: "2. Análisis Híbrido",
      desc: "Implementamos una arquitectura 'Teacher-Student': Flash procesa datos factuales a alta velocidad, mientras Pro deduce subtexto y estructura profunda.",
      // ADORNADO: Suena a estrategia de ingeniería avanzada
      tech: "Gemini 3.0 Pro (Reasoning) + Flash 2.5",
      icon: <BrainCircuit className="w-6 h-6" />
    },
    {
      id: 2,
      title: "3. La Biblia Narrativa",
      desc: "LYA genera una base de datos viva de tus personajes, lugares y reglas del mundo. Mantiene la coherencia a lo largo de millones de tokens de contexto.",
      tech: "Holistic Memory Engine (Gemini 3.0-pro)",
      icon: <ScrollText className="w-6 h-6" />
    },
    {
      id: 3,
      title: "4. Edición de Matiz",
      desc: "Aplicando las reglas de la Biblia, el motor sugiere reescrituras que respetan tu voz, elevando la prosa sin sonar robótica. Claude será tu editor principal: eliminando grasa, corrigiendo problemas de ortografía y gramática, y manteniendo tu estilo único.",
      // ACTUALIZADO: El modelo más potente para escritura
      tech: "Anthropic Claude 4.5 Sonnet", // Asegúrate de que el nombre del modelo sea correcto
      icon: <PenTool className="w-6 h-6" />
    }
  ];

  return (
    <div className="min-h-screen bg-[#F9FAFB] font-sans text-theme-text selection:bg-theme-primary selection:text-white">
      <PublicNavbar />

      <main className="pt-32 pb-20">
        
        {/* HEADER */}
        <section className="text-center px-6 mb-24 max-w-4xl mx-auto">
          <span className="font-mono text-xs font-bold text-theme-primary uppercase tracking-[0.2em] mb-4 block">
            Arquitectura del Sistema
          </span>
          <h1 className="font-editorial text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Ingeniería de precisión <br/>
            <span className="italic text-gray-500 font-serif">impulsada por IAs de vanguardia.</span>
          </h1>
          <p className="font-sans text-lg text-gray-600 max-w-2xl mx-auto">
            No usamos un solo modelo genérico. LYA orquesta una red especializada donde cada IA hace lo que mejor sabe hacer: Analizar, Recordar o Escribir.
          </p>
        </section>

        {/* DIAGRAMA INTERACTIVO DEL PIPELINE */}
        <section className="px-6 mb-32">
          <div className="max-w-6xl mx-auto bg-white border border-gray-200 rounded-sm shadow-xl overflow-hidden flex flex-col md:flex-row h-auto md:h-[600px]">
            
            {/* IZQUIERDA: La Lista de Pasos */}
            <div className="w-full md:w-1/3 border-r border-gray-200 bg-gray-50 flex flex-col">
              {pipelineSteps.map((step) => (
                <button
                  key={step.id}
                  onClick={() => setActiveStep(step.id)}
                  className={`
                    text-left p-8 border-b border-gray-200 transition-all duration-300 group
                    ${activeStep === step.id ? 'bg-white border-l-4 border-l-theme-primary shadow-inner' : 'hover:bg-gray-100 border-l-4 border-l-transparent'}
                  `}
                >
                  <div className={`mb-3 transition-colors duration-300 ${activeStep === step.id ? 'text-theme-primary' : 'text-gray-400 group-hover:text-gray-600'}`}>
                    {step.icon}
                  </div>
                  <h3 className={`font-editorial text-lg font-bold mb-1 ${activeStep === step.id ? 'text-theme-primary' : 'text-gray-700'}`}>
                    {step.title}
                  </h3>
                  <p className="font-mono text-[10px] text-gray-400 uppercase tracking-wider font-bold">
                    {step.tech}
                  </p>
                </button>
              ))}
            </div>

            {/* DERECHA: El Visualizador */}
            <div className="w-full md:w-2/3 p-12 flex flex-col justify-center relative overflow-hidden bg-gray-50/50">
              {/* Fondo decorativo técnico */}
              <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none select-none">
                <pre className="font-mono text-xs leading-tight">
                  {`
class LYA_Orchestrator:
  def process_step_${activeStep + 1}(self, manuscript):
      # Initializing ${pipelineSteps[activeStep].tech.split(' ')[0]}...
      context = self.load_context()
      return ai_model.generate(
          temperature=0.7,
          context=context
      )
                  `}
                </pre>
              </div>

              {/* Contenido Dinámico */}
              <div className="relative z-10 animate-fade-in">
                <span className="font-mono text-xs font-bold text-theme-primary bg-green-50 px-3 py-1 rounded-full mb-6 inline-block border border-green-100">
                  FASE DE PROCESAMIENTO 0{activeStep + 1}
                </span>
                
                <h2 className="font-editorial text-4xl font-bold text-gray-900 mb-6 leading-tight">
                  {pipelineSteps[activeStep].title.split('. ')[1]}
                </h2>
                
                <p className="font-sans text-xl text-gray-600 leading-relaxed mb-8">
                  {pipelineSteps[activeStep].desc}
                </p>

                {/* Detalles Técnicos Específicos */}
                <div className="grid grid-cols-2 gap-6 border-t border-gray-200 pt-8">
                  <div>
                    <h4 className="font-bold text-xs uppercase tracking-widest text-gray-400 mb-2 font-mono">Motor Principal</h4>
                    <p className="text-sm text-gray-900 font-bold font-sans">{pipelineSteps[activeStep].tech}</p>
                  </div>
                  <div>
                    <h4 className="font-bold text-xs uppercase tracking-widest text-gray-400 mb-2 font-mono">Output</h4>
                    <p className="text-sm text-gray-900 font-bold font-sans">JSON Estructurado / Markdown</p>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* CARACTERÍSTICAS SECUNDARIAS (Grid) */}
        <section className="max-w-6xl mx-auto px-6 mb-24">
          <div className="text-center mb-16">
            <h2 className="font-editorial text-3xl font-bold text-gray-900">
              Capacidades Extendidas
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<BarChart3 className="w-8 h-8" />}
              title="Arcos Emocionales" 
              desc="Visualiza la evolución de tus personajes mediante gráficos de sentimiento generados por Gemini 3.0."
            />
            <FeatureCard 
              icon={<AlertTriangle className="w-8 h-8" />}
              title="Cazador de Incoherencias" 
              desc="El sistema cruza datos de la Biblia Narrativa para encontrar contradicciones lógicas (Plot Holes) en tiempo real."
            />
            <FeatureCard 
              icon={<Wand2 className="w-8 h-8" />}
              title="Mimetismo de Estilo" 
              desc="Claude 4.5 aprende tu sintaxis, ritmo y vocabulario para que las sugerencias sean indistinguibles de tu escritura."
            />
          </div>
        </section>

        {/* CTA FINAL */}
        <section className="bg-gray-900 text-white py-24 text-center px-6">
          <h2 className="font-editorial text-4xl md:text-5xl font-bold mb-6">
            Tu manuscrito merece la mejor tecnología.
          </h2>
          <p className="font-sans text-gray-400 mb-10 max-w-xl mx-auto text-lg">
            Únete al workspace y deja que Logic Yield Assistant potencie tu proceso creativo con la precisión de una máquina y el alma de un editor.
          </p>
          <Link 
            to="/login" 
            className="inline-block bg-theme-primary hover:bg-theme-primary-hover text-white px-10 py-4 text-xs font-bold uppercase tracking-widest transition-all transform hover:-translate-y-1 shadow-lg rounded-sm"
          >
            Acceder al Workspace
          </Link>
        </section>

      </main>

      {/* FOOTER */}
      <footer className="bg-white border-t border-gray-200 py-12 text-center">
        <div className="flex flex-col items-center gap-3">
            <p className="font-serif text-3xl font-bold text-gray-900">LYA</p>
            <p className="font-mono text-[10px] text-theme-primary font-bold uppercase tracking-[0.25em]">
                LOGIC YIELD ASSISTANT
            </p>
            <p className="font-mono text-[10px] text-gray-400 uppercase tracking-widest mt-4">
              © 2025 PlotScope. Todos los derechos reservados.
            </p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ title, desc, icon }) {
  return (
    <div className="p-8 border border-gray-200 bg-white hover:border-theme-primary transition-all duration-300 hover:shadow-lg rounded-sm group">
      <div className="text-theme-primary mb-6 opacity-80 group-hover:opacity-100 transition-opacity transform group-hover:scale-110 duration-300 origin-left">
        {icon}
      </div>
      <h3 className="font-editorial text-xl font-bold mb-3 group-hover:text-theme-primary transition-colors">{title}</h3>
      <p className="font-sans text-gray-600 text-sm leading-relaxed">{desc}</p>
    </div>
  );
}