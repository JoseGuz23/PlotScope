import React from 'react';

const Home = () => {
  return (
    <div className="space-y-10 animate-fade-in">
      
      {/* HEADER TIPO REPORTE CLASIFICADO */}
      <header className="border-b-4 border-theme-text pb-6">
        <div className="flex justify-between items-end">
          <div>
            <h1 className="text-5xl font-report-serif font-black text-theme-text mb-2 tracking-tight">
              PANEL DE CONTROL
            </h1>
            <p className="font-report-mono text-theme-subtle text-sm">
              BIENVENIDO, OPERADOR. SISTEMA SYLPHRENA LISTO PARA ANÁLISIS.
            </p>
          </div>
          <div className="text-right hidden md:block">
            <div className="text-xs font-report-mono text-theme-subtle uppercase tracking-widest mb-1">Fecha del Sistema</div>
            <div className="text-xl font-report-serif font-bold">2025-11-28</div>
          </div>
        </div>
      </header>

      {/* KPI GRID - Estilo Tarjetas de Datos */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* KPI 1 */}
        <div className="bg-white border border-theme-border p-5 shadow-sm hover:border-theme-primary transition-colors group">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-xs font-report-mono uppercase font-bold text-theme-subtle tracking-widest">Palabras Proc.</h3>
            <span className="text-theme-primary bg-theme-primary/10 px-2 py-0.5 text-[10px] font-bold rounded">+12%</span>
          </div>
          <div className="text-3xl font-report-serif font-bold text-theme-text group-hover:text-theme-primary transition-colors">
            1.2M
          </div>
          <p className="text-xs text-theme-subtle mt-2 font-report-mono">Total histórico acumulado</p>
        </div>

        {/* KPI 2 */}
        <div className="bg-white border border-theme-border p-5 shadow-sm hover:border-theme-primary transition-colors group">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-xs font-report-mono uppercase font-bold text-theme-subtle tracking-widest">Token Cost</h3>
            <span className="text-theme-subtle bg-gray-100 px-2 py-0.5 text-[10px] font-bold rounded">AVG</span>
          </div>
          <div className="text-3xl font-report-serif font-bold text-theme-text">
            $0.42
          </div>
          <p className="text-xs text-theme-subtle mt-2 font-report-mono">Costo promedio por capítulo</p>
        </div>

        {/* KPI 3 - Estado Crítico */}
        <div className="bg-white border border-theme-border p-5 shadow-sm hover:border-theme-primary transition-colors group col-span-2">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-xs font-report-mono uppercase font-bold text-theme-subtle tracking-widest">Orchestrator Health</h3>
            <div className="flex gap-1">
                <span className="w-2 h-2 bg-theme-primary rounded-full"></span>
                <span className="w-2 h-2 bg-theme-primary rounded-full"></span>
                <span className="w-2 h-2 bg-theme-primary rounded-full"></span>
            </div>
          </div>
          <div className="flex items-center gap-4 mt-3">
             <div className="flex-1">
                <div className="flex justify-between text-xs font-report-mono mb-1">
                    <span>API LOAD</span>
                    <span>34%</span>
                </div>
                <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-theme-text h-full w-1/3"></div>
                </div>
             </div>
             <div className="flex-1">
                <div className="flex justify-between text-xs font-report-mono mb-1">
                    <span>ERROR RATE</span>
                    <span className="text-theme-primary">0.01%</span>
                </div>
                <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
                    <div className="bg-theme-primary h-full w-[1px]"></div>
                </div>
             </div>
          </div>
        </div>
      </section>

      {/* TABLA DE PROYECTOS ACTIVOS */}
      <section className="bg-white border border-theme-border shadow-sm">
        <div className="p-4 border-b border-theme-border bg-gray-50 flex justify-between items-center">
            <h2 className="text-sm font-bold font-report-mono uppercase tracking-widest text-theme-text">
                Manuscritos Activos
            </h2>
            <button className="text-[10px] font-bold font-report-mono uppercase text-theme-primary hover:underline">Ver Todos →</button>
        </div>
        
        <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
                <thead>
                    <tr className="bg-white border-b border-theme-border text-xs font-report-mono text-theme-subtle uppercase tracking-wider">
                        <th className="p-4 font-bold">ID / Título</th>
                        <th className="p-4 font-bold">Progreso</th>
                        <th className="p-4 font-bold">Fase Actual</th>
                        <th className="p-4 font-bold">Última Mod.</th>
                        <th className="p-4 font-bold text-right">Acción</th>
                    </tr>
                </thead>
                <tbody className="text-sm font-report-mono">
                    {/* Fila 1 */}
                    <tr className="border-b border-theme-border/50 hover:bg-theme-bg/50 transition-colors group">
                        <td className="p-4">
                            <div className="font-bold text-theme-text">SUMNER_SUMMER_78</div>
                            <div className="text-[10px] text-theme-subtle">ID: AD6B467</div>
                        </td>
                        <td className="p-4">
                            <div className="flex items-center gap-2">
                                <span className="font-bold">92%</span>
                                <div className="w-16 bg-gray-200 h-1 rounded-full">
                                    <div className="bg-theme-primary h-1 w-[92%] rounded-full"></div>
                                </div>
                            </div>
                        </td>
                        <td className="p-4">
                            <span className="bg-blue-50 text-blue-700 px-2 py-1 rounded text-[10px] font-bold border border-blue-100 uppercase">
                                Edición Capa 3
                            </span>
                        </td>
                        <td className="p-4 text-theme-subtle text-xs">Hace 2 horas</td>
                        <td className="p-4 text-right">
                            <button className="text-theme-subtle hover:text-theme-primary font-bold text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                                ABRIR CONSOLA &gt;
                            </button>
                        </td>
                    </tr>

                    {/* Fila 2 */}
                    <tr className="border-b border-theme-border/50 hover:bg-theme-bg/50 transition-colors group">
                        <td className="p-4">
                            <div className="font-bold text-theme-text">PIEL_MORENA_REV2</div>
                            <div className="text-[10px] text-theme-subtle">ID: B9X2210</div>
                        </td>
                        <td className="p-4">
                            <div className="flex items-center gap-2">
                                <span className="font-bold">45%</span>
                                <div className="w-16 bg-gray-200 h-1 rounded-full">
                                    <div className="bg-theme-text h-1 w-[45%] rounded-full"></div>
                                </div>
                            </div>
                        </td>
                        <td className="p-4">
                            <span className="bg-yellow-50 text-yellow-700 px-2 py-1 rounded text-[10px] font-bold border border-yellow-100 uppercase">
                                Análisis Estructural
                            </span>
                        </td>
                        <td className="p-4 text-theme-subtle text-xs">Ayer, 18:30</td>
                        <td className="p-4 text-right">
                            <button className="text-theme-subtle hover:text-theme-primary font-bold text-xs opacity-0 group-hover:opacity-100 transition-opacity">
                                ABRIR CONSOLA &gt;
                            </button>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
      </section>

      {/* ÁREA DE NOTIFICACIONES TÉCNICAS */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
            <h4 className="font-report-serif font-bold text-lg mb-4 text-theme-text flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-red-500 rounded-full"></span>
                Alertas de Edición
            </h4>
            <div className="bg-red-50 border border-red-100 p-4 rounded-sm">
                <p className="text-xs font-report-mono text-red-800 leading-relaxed">
                    <strong>DETECTADA INCONSISTENCIA EN CAPÍTULO 4:</strong> El personaje "Henry" cambia de motivación sin evento catalizador previo. Se recomienda revisión manual antes de proceder a la Fase 3.
                </p>
                <div className="mt-3 flex gap-2">
                    <button className="text-[10px] font-bold uppercase text-red-700 border border-red-200 bg-white px-2 py-1 hover:bg-red-50">Ver Análisis</button>
                    <button className="text-[10px] font-bold uppercase text-red-700 hover:underline px-2 py-1">Descartar</button>
                </div>
            </div>
        </div>

        <div>
            <h4 className="font-report-serif font-bold text-lg mb-4 text-theme-text">
                Actividad Reciente del Sistema
            </h4>
            <ul className="space-y-3 font-report-mono text-xs text-theme-subtle">
                <li className="flex gap-3">
                    <span className="text-theme-primary font-bold">[10:42 AM]</span>
                    <span>Batch "Gemini-Pro-Analysis" completado (24 items).</span>
                </li>
                <li className="flex gap-3">
                    <span className="text-theme-subtle font-bold">[10:38 AM]</span>
                    <span>Iniciando segmentación para "Piel_Morena.docx"...</span>
                </li>
                <li className="flex gap-3">
                    <span className="text-theme-subtle font-bold">[09:15 AM]</span>
                    <span>Conexión establecida con Azure Blob Storage.</span>
                </li>
            </ul>
        </div>
      </section>

    </div>
  );
};

export default Home;