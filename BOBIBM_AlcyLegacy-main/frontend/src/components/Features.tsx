import React from 'react';
import { AlertTriangle, GitMerge, ShieldCheck, FileText } from 'lucide-react';

const Features = () => {
  const features = [
    {
      icon: <AlertTriangle className="w-6 h-6 text-[#E8543E]" />,
      title: 'Análisis de Riesgo Impacto',
      desc: 'Calcula una métrica de riesgo 0-100 combinando acoplamiento de código, nivel de cobertura y antigüedad de última modificación.'
    },
    {
      icon: <GitMerge className="w-6 h-6 text-[#4C7EFF]" />,
      title: 'Mapa de Dependencias',
      desc: 'Escanea imports y llamadas para construir el grafo de dependencias de los módulos afectados por el cambio.'
    },
    {
      icon: <ShieldCheck className="w-6 h-6 text-[#3FB88A]" />,
      title: 'Cobertura & Vulnerabilidad',
      desc: 'Verifica la existencia de tests automáticos e identifica librerías desactualizadas o con CVEs conocidos.'
    },
    {
      icon: <FileText className="w-6 h-6 text-[#E0A526]" />,
      title: 'Documentación Automática',
      desc: 'Genera reportes de contexto estructurados en Markdown sin tocar ni alterar una sola línea de código.'
    }
  ];

  return (
    <section id="equipo" className="py-24 bg-[#0B1220] border-t border-[#1E2C47]">
      <div className="container mx-auto px-6 max-w-6xl">
        <h2 className="font-mono text-2xl md:text-4xl font-bold text-center mb-4 tracking-tight text-[#E8EDF5]">
          ¿Por qué Alcy Legacy?
        </h2>
        <p className="text-[#7C8BA8] text-center max-w-2xl mx-auto mb-16 text-base font-sans">
          El Skill de IBM Bob diseñado para proteger tus sistemas críticos antes de automatizar refactorizaciones.
        </p>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((item, idx) => (
            <div 
              key={idx} 
              className="group bg-[#101A2E] border border-[#1E2C47] rounded-xl p-8 hover:border-[#4C7EFF]/50 hover:-translate-y-1 transition-all duration-300 relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-[#4C7EFF] to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
              
              <div className="w-12 h-12 bg-[#0D1626] border border-[#1E2C47] flex items-center justify-center rounded-lg mb-6 group-hover:border-[#4C7EFF]/40 transition-colors">
                {item.icon}
              </div>
              
              <h3 className="font-mono text-base font-bold mb-3 text-[#E8EDF5]">{item.title}</h3>
              <p className="text-[#7C8BA8] text-xs leading-relaxed font-sans">
                {item.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
