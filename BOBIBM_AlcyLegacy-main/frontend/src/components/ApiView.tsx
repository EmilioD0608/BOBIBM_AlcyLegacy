import React from 'react';
import { Code, Database, Server } from 'lucide-react';

interface ApiViewProps {
  lang: 'es' | 'en';
}

const ApiView: React.FC<ApiViewProps> = ({ lang }) => {
  const endpoints = [
    {
      method: 'POST',
      path: '/api/v1/analyze',
      desc: lang === 'es' ? 'Evalúa el riesgo de un archivo o fragmento de código legacy.' : 'Evaluate risk of a legacy file or code snippet.',
    },
    {
      method: 'GET',
      path: '/api/v1/graph/:moduleId',
      desc: lang === 'es' ? 'Obtiene el árbol/mapa de dependencias de un módulo.' : 'Retrieve dependency graph of a module.',
    },
    {
      method: 'POST',
      path: '/api/v1/refactor/simulate',
      desc: lang === 'es' ? 'Simula el impacto de un cambio antes de modificar el repositorio.' : 'Simulate impact of a change before repo mutation.',
    },
  ];

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="eyebrow mb-3">API REST & INTEGRACIONES</div>
      <h1 className="font-mono-custom text-2xl font-bold text-[var(--text)] mb-6">
        {lang === 'es' ? 'Documentación de API Alcy Legacy' : 'Alcy Legacy API Reference'}
      </h1>

      <div className="panel-custom p-6 mb-8">
        <h2 className="font-mono-custom text-sm font-bold text-[var(--blue)] mb-4 flex items-center gap-2">
          <Server className="w-4 h-4" />
          Base URL
        </h2>
        <div className="bg-[var(--grid-soft)] border border-[var(--grid)] p-3 font-mono-custom text-xs text-[var(--green)]">
          https://api.alcy-legacy.ibm.com/v1
        </div>
      </div>

      <div className="space-y-4 mb-8">
        <h2 className="font-mono-custom text-sm font-bold text-[var(--text)] mb-3">Endpoints Disponibles</h2>
        {endpoints.map((ep, i) => (
          <div key={i} className="panel-custom p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className={`font-mono-custom text-xs font-bold px-2.5 py-1 border ${
                ep.method === 'POST' ? 'text-[var(--blue)] border-[var(--blue)] bg-[var(--blue)]/10' : 'text-[var(--green)] border-[var(--green)] bg-[var(--green)]/10'
              }`}>
                {ep.method}
              </span>
              <span className="font-mono-custom text-sm font-bold text-[var(--text)]">{ep.path}</span>
            </div>
            <span className="text-xs text-[var(--muted)]">{ep.desc}</span>
          </div>
        ))}
      </div>

      <div className="panel-custom p-6">
        <h2 className="font-mono-custom text-sm font-bold text-[var(--blue)] mb-3 flex items-center gap-2">
          <Code className="w-4 h-4" />
          Ejemplo Request (JSON)
        </h2>
        <div className="bg-[var(--grid-soft)] border border-[var(--grid)] p-4 font-mono-custom text-xs text-[var(--text)] leading-relaxed">
          {`curl -X POST https://api.alcy-legacy.ibm.com/v1/analyze \\
  -H "Authorization: Bearer YOUR_IBM_BOB_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{
    "filePath": "src/legacy_module.py",
    "includeCoverage": true,
    "scanVulnerabilities": true
  }'`}
        </div>
      </div>
    </div>
  );
};

export default ApiView;
