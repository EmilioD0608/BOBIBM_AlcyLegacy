import React from 'react';
import { BookOpen, Terminal, Shield, Zap } from 'lucide-react';

interface DocViewProps {
  lang: 'es' | 'en';
}

const DocView: React.FC<DocViewProps> = ({ lang }) => {
  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="eyebrow mb-3">DOCUMENTACIÓN & GUÍA</div>
      <h1 className="font-mono-custom text-2xl font-bold text-[var(--text)] mb-6">
        {lang === 'es' ? 'Cómo funciona Alcy Legacy — Skill de IBM Bob' : 'How Alcy Legacy works — IBM Bob Skill'}
      </h1>

      <div className="space-y-8">
        <section className="panel-custom p-6">
          <h2 className="font-mono-custom text-base font-bold text-[var(--blue)] mb-3 flex items-center gap-2">
            <Zap className="w-5 h-5 text-[var(--blue)]" />
            {lang === 'es' ? '1. Arquitectura del Skill' : '1. Skill Architecture'}
          </h2>
          <p className="text-xs text-[var(--muted)] leading-relaxed mb-4">
            {lang === 'es' 
              ? 'Alcy Legacy actúa como una barrera de seguridad previa a cualquier ejecución de agente. Antes de permitir que IBM Bob realice modificaciones o refactorizaciones de código, este Skill analiza la estructura del módulo.'
              : 'Alcy Legacy acts as a pre-execution safety barrier for AI agents. Before allowing IBM Bob to edit or refactor legacy code, this skill inspects the module structure.'}
          </p>
          <div className="bg-[var(--grid-soft)] border border-[var(--grid)] p-4 font-mono-custom text-xs text-[var(--text)] overflow-x-auto leading-relaxed">
            <span className="text-[var(--blue)]">Bob Agent Directive</span>: [USER_REQUEST] -&gt; <span className="text-[var(--amber)]">Alcy Legacy Skill</span> -&gt; [RISK_EVALUATION] -&gt; <span className="text-[var(--green)]">Safe Edit / Refactor Approval</span>
          </div>
        </section>

        <section className="panel-custom p-6">
          <h2 className="font-mono-custom text-base font-bold text-[var(--blue)] mb-3 flex items-center gap-2">
            <Shield className="w-5 h-5 text-[var(--blue)]" />
            {lang === 'es' ? '2. Algoritmo de Cálculo de Riesgo' : '2. Risk Calculation Algorithm'}
          </h2>
          <p className="text-xs text-[var(--muted)] leading-relaxed mb-4">
            {lang === 'es'
              ? 'El Puntaje de Riesgo (0-100) se calcula ponderando tres ejes principales:'
              : 'The Risk Score (0-100) is calculated by weighting three main axes:'}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-[var(--panel-2)] p-4 border border-[var(--grid)]">
              <h3 className="font-mono-custom text-xs font-bold text-[var(--text)] mb-2">Acoplamiento (40%)</h3>
              <p className="text-xs text-[var(--muted)]">Cantidad de módulos que importan o consumen la lógica de este archivo.</p>
            </div>
            <div className="bg-[var(--panel-2)] p-4 border border-[var(--grid)]">
              <h3 className="font-mono-custom text-xs font-bold text-[var(--text)] mb-2">Cobertura (35%)</h3>
              <p className="text-xs text-[var(--muted)]">Porcentaje de tests automáticos asociados al módulo.</p>
            </div>
            <div className="bg-[var(--panel-2)] p-4 border border-[var(--grid)]">
              <h3 className="font-mono-custom text-xs font-bold text-[var(--text)] mb-2">Antigüedad (25%)</h3>
              <p className="text-xs text-[var(--muted)]">Tiempo transcurrido desde el último commit o modificación humana.</p>
            </div>
          </div>
        </section>

        <section className="panel-custom p-6">
          <h2 className="font-mono-custom text-base font-bold text-[var(--blue)] mb-3 flex items-center gap-2">
            <Terminal className="w-5 h-5 text-[var(--blue)]" />
            {lang === 'es' ? '3. Uso desde CLI / Terminal' : '3. CLI / Terminal Usage'}
          </h2>
          <div className="bg-[var(--grid-soft)] border border-[var(--grid)] p-4 font-mono-custom text-xs text-[var(--text)]">
            <p className="text-[var(--muted)]"># Ejecutar análisis en un archivo local</p>
            <p className="text-[var(--green)]">alcy-legacy analyze ./src/legacy_module.py --output json</p>
            <br />
            <p className="text-[var(--muted)]"># Integración con IBM Bob Skill Runner</p>
            <p className="text-[var(--blue)]">bob run --skill alcy-legacy --target ./src/legacy_module.py</p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default DocView;
