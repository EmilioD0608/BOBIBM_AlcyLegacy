import React from 'react';
import { ShieldAlert } from 'lucide-react';

interface FooterProps {
  setActiveTab: (tab: string) => void;
  lang: 'es' | 'en';
}

const Footer: React.FC<FooterProps> = ({ setActiveTab, lang }) => {
  return (
    <footer className="border-t border-[var(--grid)] bg-[var(--panel-2)] pt-12 pb-8 mt-20">
      <div className="max-w-5xl mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between gap-8 mb-8">
          <div className="max-w-xs">
            <div className="flex items-center gap-2 mb-3">
              <ShieldAlert className="w-5 h-5 text-[var(--blue)]" />
              <span className="font-mono-custom text-sm font-bold text-[var(--text)]">Alcy Legacy</span>
            </div>
            <p className="text-xs text-[var(--muted)] leading-relaxed">
              {lang === 'es'
                ? 'El Skill de IBM Bob que evalúa el riesgo de tocar código legacy antes de ejecutar refinamientos o refactorizaciones.'
                : 'The IBM Bob Skill that evaluates risk on legacy code before executing refactors.'}
            </p>
          </div>

          <div className="flex gap-12 flex-wrap">
            <div>
              <h5 className="font-mono-custom text-[11px] text-[var(--muted)] uppercase tracking-wider mb-3">
                {lang === 'es' ? 'Producto' : 'Product'}
              </h5>
              <div className="flex flex-col space-y-2 font-mono-custom text-xs">
                <button onClick={() => setActiveTab('demo')} className="text-left text-[var(--text)] hover:text-[var(--blue)] transition-colors">Demo</button>
                <button onClick={() => setActiveTab('analizar')} className="text-left text-[var(--text)] hover:text-[var(--blue)] transition-colors">
                  {lang === 'es' ? 'Analizar' : 'Analyze'}
                </button>
                <button onClick={() => setActiveTab('equipo')} className="text-left text-[var(--text)] hover:text-[var(--blue)] transition-colors">
                  {lang === 'es' ? 'Equipo' : 'Team'}
                </button>
                <a href="/standalone.html" target="_blank" rel="noopener noreferrer" className="text-left text-[var(--blue)] hover:underline transition-colors">
                  {lang === 'es' ? 'Versión Standalone ↗' : 'Standalone Version ↗'}
                </a>
              </div>
            </div>

            <div>
              <h5 className="font-mono-custom text-[11px] text-[var(--muted)] uppercase tracking-wider mb-3">
                {lang === 'es' ? 'Proyecto' : 'Project'}
              </h5>
              <div className="flex flex-col space-y-2 font-mono-custom text-xs">
                <a href="https://github.com/EmilioD0608/BOBIBM_AlcyLegacy" target="_blank" rel="noopener noreferrer" className="text-left text-[var(--text)] hover:text-[var(--blue)] transition-colors">
                  {lang === 'es' ? 'Repositorio en GitHub' : 'GitHub Repository'}
                </a>
                <a href="https://lablab.ai/ai-hackathons/ibm-bob-2-hackathon" target="_blank" rel="noopener noreferrer" className="text-left text-[var(--text)] hover:text-[var(--blue)] transition-colors">
                  IBM Bob 2.0 Hackathon
                </a>
                <a href="https://lablab.ai/" target="_blank" rel="noopener noreferrer" className="text-left text-[var(--text)] hover:text-[var(--blue)] transition-colors">
                  lablab.ai
                </a>
              </div>
            </div>

            <div>
              <h5 className="font-mono-custom text-[11px] text-[var(--muted)] uppercase tracking-wider mb-3">
                {lang === 'es' ? 'Recursos' : 'Resources'}
              </h5>
              <div className="flex flex-col space-y-2 font-mono-custom text-xs">
                <button onClick={() => setActiveTab('docs')} className="text-left text-[var(--text)] hover:text-[var(--blue)] transition-colors">
                  {lang === 'es' ? 'Documentación' : 'Documentation'}
                </button>
                <button onClick={() => setActiveTab('api')} className="text-left text-[var(--text)] hover:text-[var(--blue)] transition-colors">
                  API REST
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-[var(--grid)] pt-6 flex flex-col md:flex-row items-center justify-between gap-4 font-mono-custom text-xs text-[var(--muted)]">
          <p>© 2026 Alcy Legacy — IBM Bob 2.0 Hackathon. {lang === 'es' ? 'Todos los derechos reservados.' : 'All rights reserved.'}</p>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[var(--green)]"></span>
            <span>Skill Status: Operational</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
