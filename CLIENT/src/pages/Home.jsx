import React from 'react';

const Home = () => {
  return (
    <>
        {/* HEADER TIPO REPORTE (Clase .report-divider del CSS) */}
        <header className="report-divider py-4">
            <h1 className="text-4xl font-report-serif font-extrabold text-theme-text mb-2 tracking-tight">
                ANÁLISIS DE MANUSCRITO ACTIVO
            </h1>
            <p className="text-sm font-report-mono text-theme-subtle">
                DOCUMENTO CLASIFICADO: SUMNER_SUMMER_78 | ID: AD6B467 | Sincronización: 2025-11-28 08:15 MST
            </p>
        </header>

        {/* GRID DE DATOS (4 Columnas) */}
        <section className="grid grid-cols-4 gap-6 mb-10">
            {/* Tarjeta 1 */}
            <div className="border border-theme-border p-5 rounded-sm bg-white">
                <p className="data-label">Palabras (Total)</p>
                <span className="text-4xl font-report-mono font-bold text-theme-text block mt-1">85,240</span>
                <p className="text-xs text-theme-primary font-bold mt-2 font-report-mono">
                    [+] 2.5% vs último reporte
                </p>
            </div>
            
            {/* Tarjeta 2 */}
            <div className="border border-theme-border p-5 rounded-sm bg-white">
                <p className="data-label">Capítulos Analizados</p>
                <span className="text-4xl font-report-mono font-bold text-theme-text block mt-1">24/25</span>
                <p className="text-xs text-theme-subtle mt-2 font-report-mono">
                    Próximo: Capítulo 25
                </p>
            </div>

            {/* Tarjeta 3 */}
            <div className="border border-theme-border p-5 rounded-sm bg-white">
                <p className="data-label">Nivel de Lectura</p>
                <span className="text-4xl font-report-mono font-bold text-theme-text block mt-1">A+</span>
                <p className="text-xs text-theme-subtle mt-2 font-report-mono">
                    Público objetivo: Adulto Joven
                </p>
            </div>

            {/* Tarjeta 4 (Con animación ping) */}
            <div className="border border-theme-border p-5 rounded-sm bg-white">
                <p className="data-label">Estado del Análisis IA</p>
                <div className="flex items-center space-x-2 mt-2">
                    <span className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-theme-primary opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-theme-primary"></span>
                    </span>
                    <span className="text-sm font-bold text-theme-text font-report-mono">Análisis en curso...</span>
                </div>
                <p className="text-xs text-theme-subtle mt-2 font-report-mono">
                    <span className="text-theme-primary">45%</span> de Tono Procesado
                </p>
            </div>
        </section>

        {/* SECCIÓN DE CONTENIDO (Report Body) */}
        <section className="border border-theme-border p-8 bg-white mb-10">
            <h2 className="text-xl font-report-serif font-bold text-theme-subtle border-b-2 border-theme-border pb-2 mb-6">
                CONTENIDO ANALIZADO (ÚLTIMA EDICIÓN)
            </h2>

            <div className="report-body">
                <h3 className="text-base font-extrabold uppercase mb-3 border-b border-theme-border pb-1">
                    CAPÍTULO 2
                </h3>
                <p className="text-xs text-theme-subtle mb-4">
                    5 revisiones detectadas por el Orquestador.
                </p>

                {/* Texto Preformateado simulando máquina de escribir */}
                <pre className="whitespace-pre-wrap leading-snug font-report-mono text-sm">
Ángel se acercó despacio.

-No para encerrarlo... pero sí para retenerlo un tiempo. Tal vez el suficiente para que cante.
Henry negó con la cabeza. Sin dejar de mirar el horizonte.
-No es suficiente, muchacho. Toda esta situación me huele a mierda.
Guardó silencio unos segundos.
<span className="text-red-700 line-through">¿Tú crees que Emma alucinó lo del espía?</span>{' '}
<span className="text-theme-primary font-extrabold">Sabemos que el espía existe. Solo falta encontrarlo.</span>
{'\n'}Ángel se apoyó en la parte trasera de la valla, con un salto ágil, se sentó en el borde.
                </pre>
            </div>
        </section>

        {/* FOOTER INTERNO */}
        <footer className="text-center text-xs text-theme-subtle pt-4 border-t border-theme-border font-report-mono">
            LYA Orquestador de Edición &copy; 2025. Todos los derechos reservados. Ejecutándose en Azure Static Web Apps.
        </footer>
    </>
  );
};

export default Home;