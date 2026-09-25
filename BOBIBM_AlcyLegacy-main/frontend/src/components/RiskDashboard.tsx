import React from 'react';
import { ShieldCheck, AlertTriangle, Download, FileText, Bot, Bug } from 'lucide-react';

interface FileAnalysisData {
  riskScore: number;
  riskLevel: 'high' | 'medium' | 'low';
  riskTitle: string;
  reason: string;
  dependencies: number;
  coverage: string;
  age: string;
  vulns: string[];
  explanation: string;
}

interface RiskDashboardProps {
  selectedFile: string;
  data: FileAnalysisData;
  lang: 'es' | 'en';
}

const RiskDashboard: React.FC<RiskDashboardProps> = ({ selectedFile, data, lang }) => {
  const downloadMarkdownReport = () => {
    const content = `# Reporte de Análisis de Riesgo — Alcy Legacy (IBM Bob)
**Archivo Analizado**: \`${selectedFile}\`
**Nivel de Riesgo**: ${data.riskTitle} (${data.riskScore}/100)
**Fecha**: ${new Date().toLocaleDateString()}

## 📊 Métricas Principales
- **Dependencias Directas**: ${data.dependencies} Módulos
- **Cobertura de Tests**: ${data.coverage}
- **Antigüedad del Código**: ${data.age}

## 🤖 Explicación de IA (IBM Bob)
${data.explanation}

## ⚠️ Razones del Diagnóstico
${data.reason}

---
*Generado automáticamente por Alcy Legacy Skill — IBM Bob 2.0 Hackathon*
`;

    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Alcy_Legacy_Report_${selectedFile}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="panel-custom p-6 md:p-8 mt-6">
      <div className="font-mono-custom text-xs text-[var(--muted)] uppercase tracking-wider mb-6 flex justify-between items-center border-b border-[var(--grid)] pb-4 flex-wrap gap-2">
        <span>{lang === 'es' ? 'Diagnóstico de Riesgo y Salud del Módulo' : 'Risk Diagnosis & Module Health'}</span>
        <span className="text-[var(--blue)] font-bold">— {selectedFile.toUpperCase()}</span>
      </div>

      {/* Semáforo + Score Dashboard */}
      <div className="flex flex-col md:flex-row items-center justify-center gap-8 py-4 mb-6">
        {/* Traffic Light */}
        <div className="flex gap-3 bg-[var(--grid-soft)] border border-[var(--grid)] p-3 shadow-inner">
          <div className={`tl-dot red ${data.riskLevel === 'high' ? 'on' : ''}`}></div>
          <div className={`tl-dot amber ${data.riskLevel === 'medium' ? 'on' : ''}`}></div>
          <div className={`tl-dot green ${data.riskLevel === 'low' ? 'on' : ''}`}></div>
        </div>

        {/* Score Number */}
        <div className="text-center">
          <div className={`font-mono-custom text-4xl font-extrabold ${
            data.riskLevel === 'high' ? 'text-[var(--red)]' : data.riskLevel === 'medium' ? 'text-[var(--amber)]' : 'text-[var(--green)]'
          }`}>
            {data.riskScore}<small className="text-sm font-normal text-[var(--muted)]">/100</small>
          </div>
          <div className="font-mono-custom text-[10px] text-[var(--muted)] uppercase tracking-wider mt-1">
            {lang === 'es' ? 'Puntaje de Riesgo' : 'Risk Score Index'}
          </div>
        </div>

        {/* Stamp Badge */}
        <div className="stamp-zone">
          <div className={`stamp stamp-anim ${data.riskLevel}`}>
            {data.riskTitle}
            <small>{lang === 'es' ? 'ALCY LEGACY GUARDIAN' : 'ALCY LEGACY GUARDIAN'}</small>
          </div>
        </div>
      </div>

      {/* Metric Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-[var(--grid)] my-6">
        <div className="bg-[var(--panel)] p-4">
          <div className="font-mono-custom text-[10.5px] text-[var(--muted)] uppercase tracking-wider mb-1">
            {lang === 'es' ? 'Dependencias Afectadas' : 'Dependencies'}
          </div>
          <div className="font-mono-custom text-xl font-bold text-[var(--text)]">
            {data.dependencies} {lang === 'es' ? 'Módulos' : 'Modules'}
          </div>
          <div className="text-xs text-[var(--muted)] mt-1 font-mono-custom">
            {data.dependencies > 10 ? (lang === 'es' ? 'Acoplamiento Crítico' : 'Critical Coupling') : (lang === 'es' ? 'Acoplamiento Moderado' : 'Moderate Coupling')}
          </div>
        </div>

        <div className="bg-[var(--panel)] p-4">
          <div className="font-mono-custom text-[10.5px] text-[var(--muted)] uppercase tracking-wider mb-1">
            {lang === 'es' ? 'Cobertura de Tests' : 'Test Coverage'}
          </div>
          <div className={`font-mono-custom text-xl font-bold ${
            parseInt(data.coverage) < 30 ? 'text-[var(--red)]' : 'text-[var(--green)]'
          }`}>
            {data.coverage}
          </div>
          <div className="text-xs text-[var(--muted)] mt-1 font-mono-custom">
            {parseInt(data.coverage) < 30 ? (lang === 'es' ? 'Sin Suite de Pruebas' : 'Missing Test Suite') : (lang === 'es' ? 'Protegido con Tests' : 'Protected with Tests')}
          </div>
        </div>

        <div className="bg-[var(--panel)] p-4">
          <div className="font-mono-custom text-[10.5px] text-[var(--muted)] uppercase tracking-wider mb-1">
            {lang === 'es' ? 'Antigüedad del Código' : 'Code Age'}
          </div>
          <div className="font-mono-custom text-xl font-bold text-[var(--text)]">
            {data.age}
          </div>
          <div className="text-xs text-[var(--muted)] mt-1 font-mono-custom">
            {lang === 'es' ? 'Última modificación registrada' : 'Last recorded commit'}
          </div>
        </div>
      </div>

      {/* Reason Breakdown */}
      <div className="font-mono-custom text-xs text-[var(--muted)] border-l-2 border-[var(--grid)] p-3 bg-[var(--panel-2)] mb-6 leading-relaxed">
        <b className="text-[var(--text)] font-semibold">{lang === 'es' ? 'Factores clave de riesgo:' : 'Key Risk Factors:'}</b>
        <p className="mt-1 text-[var(--text)]">{data.reason}</p>
      </div>

      {/* SVG Dependency Map Visualizer */}
      <div className="my-6 p-4 bg-[var(--panel-2)] border border-[var(--grid)]">
        <div className="font-mono-custom text-xs text-[var(--blue)] uppercase tracking-wider mb-4 flex items-center gap-2">
          <span>{lang === 'es' ? 'Grafo de Acoplamiento y Dependencias' : 'Dependency & Coupling Graph'}</span>
        </div>
        <div className="flex justify-center items-center py-4">
          <svg width="480" height="140" viewBox="0 0 480 140" className="max-w-full">
            <line x1="240" y1="70" x2="90" y2="35" stroke="var(--grid)" strokeWidth="2" strokeDasharray="4 4" />
            <line x1="240" y1="70" x2="90" y2="105" stroke="var(--grid)" strokeWidth="2" strokeDasharray="4 4" />
            <line x1="240" y1="70" x2="390" y2="35" stroke="var(--grid)" strokeWidth="2" strokeDasharray="4 4" />
            <line x1="240" y1="70" x2="390" y2="105" stroke="var(--grid)" strokeWidth="2" strokeDasharray="4 4" />

            {/* Sub-nodes */}
            <circle cx="90" cy="35" r="20" fill="var(--panel)" stroke="var(--grid)" strokeWidth="1.5" />
            <text x="90" y="39" textAnchor="middle" fill="var(--text)" fontSize="10" className="font-mono-custom">db_conn</text>

            <circle cx="90" cy="105" r="20" fill="var(--panel)" stroke="var(--grid)" strokeWidth="1.5" />
            <text x="90" y="109" textAnchor="middle" fill="var(--text)" fontSize="10" className="font-mono-custom">auth_v1</text>

            <circle cx="390" cy="35" r="20" fill="var(--panel)" stroke="var(--grid)" strokeWidth="1.5" />
            <text x="390" y="39" textAnchor="middle" fill="var(--text)" fontSize="10" className="font-mono-custom">billing</text>

            <circle cx="390" cy="105" r="20" fill="var(--panel)" stroke="var(--grid)" strokeWidth="1.5" />
            <text x="390" y="109" textAnchor="middle" fill="var(--text)" fontSize="10" className="font-mono-custom">logger</text>

            {/* Target Central Node */}
            <circle cx="240" cy="70" r="30" fill="var(--blue)" stroke="var(--blue-dim)" strokeWidth="3" />
            <text x="240" y="74" textAnchor="middle" fill="#FFFFFF" fontSize="11" fontWeight="bold" className="font-mono-custom">TARGET</text>
          </svg>
        </div>
      </div>

      {/* AI Explanation Box */}
      <div className="bg-gradient-to-r from-[var(--panel)] to-[var(--panel-2)] border border-[var(--blue-dim)] p-5 mb-6 relative">
        <div className="font-mono-custom text-xs text-[var(--blue)] font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
          <Bot className="w-4 h-4 text-[var(--blue)]" />
          <span>{lang === 'es' ? 'Análisis Inteligente de IBM Bob' : 'IBM Bob AI Analysis'}</span>
        </div>
        <p className="text-xs text-[var(--text)] leading-relaxed">
          {data.explanation}
        </p>
        <div className="font-mono-custom text-[10px] text-[var(--muted)] mt-3 pt-2 border-t border-[var(--grid)]">
          {lang === 'es' ? 'Verificado por Alcy Legacy Agent Skill' : 'Verified by Alcy Legacy Agent Skill'}
        </div>
      </div>

      {/* Vulnerabilities Card */}
      {data.vulns.length > 0 && (
        <div className="bg-[var(--panel-2)] border border-red-500/30 p-4 mb-6">
          <div className="font-mono-custom text-xs text-[var(--red)] font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
            <Bug className="w-4 h-4 text-[var(--red)]" />
            <span>{lang === 'es' ? 'Vulnerabilidades y Alertas de Librerías' : 'Vulnerabilities & Library Alerts'}</span>
          </div>
          <ul className="list-disc pl-5 font-mono-custom text-xs text-[var(--amber)] space-y-1">
            {data.vulns.map((v, i) => (
              <li key={i}>{v}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Download Action Row */}
      <div className="flex gap-3 flex-wrap">
        <button
          onClick={downloadMarkdownReport}
          className="bg-[var(--blue)] text-white font-mono-custom text-xs font-bold py-3 px-6 rounded hover:bg-[#3b66d9] transition-all flex items-center gap-2 shadow-[0_0_15px_rgba(76,126,255,0.3)]"
        >
          <Download className="w-4 h-4" />
          {lang === 'es' ? 'DESCARGAR REPORTE EN MARKDOWN' : 'DOWNLOAD MARKDOWN REPORT'}
        </button>
      </div>
    </div>
  );
};

export default RiskDashboard;
