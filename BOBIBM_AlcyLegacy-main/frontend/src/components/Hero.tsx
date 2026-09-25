import React, { useState } from 'react';
import { ArrowRight, Code, Upload, Github, FileCode, Play, Terminal, CheckCircle2, AlertCircle } from 'lucide-react';
import RiskDashboard from './RiskDashboard';

interface HeroProps {
  lang: 'es' | 'en';
}

const fileDataStore: Record<string, {
  riskScore: number;
  riskLevel: 'high' | 'medium' | 'low';
  riskTitle: string;
  reason: string;
  dependencies: number;
  coverage: string;
  age: string;
  vulns: string[];
  explanation: string;
}> = {
  'legacy_module.py': {
    riskScore: 87,
    riskLevel: 'high',
    riskTitle: 'ALTO RIESGO',
    reason: 'Acoplamiento elevado con 14 módulos críticos sin tests unitarios. Modificar sin precaución romperá la autenticación y facturación.',
    dependencies: 14,
    coverage: '12%',
    age: '4.2 años',
    vulns: ['CVE-2021-44228 (Log4j dependiente indirecto)', 'Librería pycrypto descontinuada'],
    explanation: 'El módulo legacy_module.py fue creado hace más de 4 años. Controla reglas de cálculo financiero heredadas. Posee solo 12% de cobertura de pruebas y es invocado por 14 microservicios en producción.',
  },
  'pricing_utils.py': {
    riskScore: 62,
    riskLevel: 'medium',
    riskTitle: 'RIESGO MEDIO',
    reason: 'Lógica matemática de precios moderadamente acoplada. Cobertura de pruebas al 45%.',
    dependencies: 8,
    coverage: '45%',
    age: '2.8 años',
    vulns: ['Depreciación de Python 3.7 type hints'],
    explanation: 'pricing_utils.py contiene utilidades de descuento. Las dependencias están acotadas a la pasarela de pagos. Se recomienda ejecutar pruebas sintéticas antes de desplegar.',
  },
  'notification_service.py': {
    riskScore: 24,
    riskLevel: 'low',
    riskTitle: 'BAJO RIESGO',
    reason: 'Módulo desacoplado de notificaciones con suite de tests sólida (89% cobertura). Es seguro modificar.',
    dependencies: 3,
    coverage: '89%',
    age: '0.9 años',
    vulns: [],
    explanation: 'notification_service.py utiliza patrones modernos de microservicios y cuenta con amplia cobertura de pruebas unitarias e integración.',
  },
};

const Hero: React.FC<HeroProps> = ({ lang }) => {
  const [activeMode, setActiveMode] = useState<'demo' | 'refactoring'>('demo');
  const [scope, setScope] = useState<'file' | 'folder' | 'repo'>('file');
  const [selectedFile, setSelectedFile] = useState('legacy_module.py');
  const [showCodePaste, setShowCodePaste] = useState(false);
  const [pastedCode, setPastedCode] = useState('');
  const [githubUrl, setGithubUrl] = useState('');
  
  // Execution state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [consoleLogs, setConsoleLogs] = useState<string[]>([]);
  const [hasAnalyzed, setHasAnalyzed] = useState(false);

  const runAnalysis = () => {
    setIsAnalyzing(true);
    setHasAnalyzed(false);
    setConsoleLogs([]);

    const steps = [
      lang === 'es' ? '[1/4] Inicializando IBM Bob Skill Kernel...' : '[1/4] Initializing IBM Bob Skill Kernel...',
      lang === 'es' ? `[2/4] Escaneando árbol de AST y dependencias para ${selectedFile}...` : `[2/4] Scanning AST tree & dependencies for ${selectedFile}...`,
      lang === 'es' ? '[3/4] Auditando suite de pruebas unitarias y firmas de vulnerabilidades CVE...' : '[3/4] Auditing unit test suite & CVE vulnerability signatures...',
      lang === 'es' ? '[4/4] Calculando matriz de riesgo Alcy Legacy Guardian...' : '[4/4] Computing Alcy Legacy Guardian risk matrix...',
      lang === 'es' ? '✔ ANÁLISIS COMPLETADO EXITOSAMENTE.' : '✔ ANALYSIS COMPLETED SUCCESSFULLY.',
    ];

    steps.forEach((step, idx) => {
      setTimeout(() => {
        setConsoleLogs((prev) => [...prev, step]);
        if (idx === steps.length - 1) {
          setIsAnalyzing(false);
          setHasAnalyzed(true);
        }
      }, (idx + 1) * 600);
    });
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const fileName = e.target.files[0].name;
      setSelectedFile(fileName);
      fileDataStore[fileName] = {
        riskScore: 75,
        riskLevel: 'high',
        riskTitle: 'ALTO RIESGO',
        reason: `Archivo subido '${fileName}' analizado. Se detectaron 9 acoplamientos sin tests automáticos.`,
        dependencies: 9,
        coverage: '18%',
        age: 'Subido recientemente',
        vulns: ['Auditoría requerida'],
        explanation: `Archivo subido por el usuario (${fileName}). Alcy Legacy sugiere inspección de dependencias antes de autorizar refactorización por IBM Bob.`,
      };
      runAnalysis();
    }
  };

  return (
    <section className="py-10">
      <div className="text-center max-w-3xl mx-auto mb-10">
        <div className="eyebrow justify-center mb-3">SKILL DE IBM BOB — HACKATHON 2.0</div>
        <h1 className="font-mono-custom text-3xl md:text-5xl font-bold tracking-tight mb-4 text-[var(--text)]">
          {lang === 'es' 
            ? 'Analiza el riesgo de tu código legacy antes de que ' 
            : 'Analyze legacy code risk before '}
          <span className="text-[var(--blue)]">Bob</span>
          {lang === 'es' ? ' lo modifique' : ' modifies it'}
        </h1>
        <p className="text-sm md:text-base text-[var(--muted)] font-mono-custom leading-relaxed">
          {lang === 'es'
            ? 'Alcy Legacy analiza dependencias, cobertura de tests, antigüedad y vulnerabilidades antes de modificar código legacy.'
            : 'Alcy Legacy inspects dependencies, test coverage, code age, and vulnerabilities before executing AI edits.'}
        </p>
      </div>

      {/* Mode Switcher */}
      <div className="flex border border-[var(--grid)] bg-[var(--grid)] mb-6 max-w-2xl mx-auto">
        <button
          onClick={() => setActiveMode('demo')}
          className={`flex-1 py-3 px-4 font-mono-custom text-xs transition-all ${
            activeMode === 'demo' ? 'bg-[var(--panel)] text-[var(--text)] font-bold border-t-2 border-t-[var(--blue)]' : 'bg-[var(--panel-2)] text-[var(--muted)]'
          }`}
        >
          {lang === 'es' ? 'Mode 1: Guardián de Riesgo (Demo)' : 'Mode 1: Risk Guardian (Demo)'}
        </button>
        <button
          onClick={() => setActiveMode('refactoring')}
          className={`flex-1 py-3 px-4 font-mono-custom text-xs transition-all ${
            activeMode === 'refactoring' ? 'bg-[var(--panel)] text-[var(--text)] font-bold border-t-2 border-t-[var(--blue)]' : 'bg-[var(--panel-2)] text-[var(--muted)]'
          }`}
        >
          {lang === 'es' ? 'Mode 2: Refactorización Asistida (Bob AI)' : 'Mode 2: AI Refactor (Bob AI)'}
        </button>
      </div>

      {/* Scope Selector Tabs */}
      <div className="flex border border-[var(--grid)] max-w-4xl mx-auto mb-6">
        <button
          onClick={() => setScope('file')}
          className={`flex-1 py-2.5 px-3 font-mono-custom text-xs transition-colors ${
            scope === 'file' ? 'bg-[var(--panel)] text-[var(--blue)] font-bold' : 'bg-[var(--panel-2)] text-[var(--muted)]'
          }`}
        >
          📄 {lang === 'es' ? 'Archivo Individual' : 'Single File'}
        </button>
        <button
          onClick={() => setScope('folder')}
          className={`flex-1 py-2.5 px-3 font-mono-custom text-xs transition-colors ${
            scope === 'folder' ? 'bg-[var(--panel)] text-[var(--blue)] font-bold' : 'bg-[var(--panel-2)] text-[var(--muted)]'
          }`}
        >
          📁 {lang === 'es' ? 'Carpeta / Módulo' : 'Folder / Module'}
        </button>
        <button
          onClick={() => setScope('repo')}
          className={`flex-1 py-2.5 px-3 font-mono-custom text-xs transition-colors ${
            scope === 'repo' ? 'bg-[var(--panel)] text-[var(--blue)] font-bold' : 'bg-[var(--panel-2)] text-[var(--muted)]'
          }`}
        >
          🌐 {lang === 'es' ? 'Repositorio GitHub' : 'GitHub Repository'}
        </button>
      </div>

      {/* Main Control Panel */}
      <div className="panel-custom p-6 max-w-4xl mx-auto">
        {scope === 'repo' ? (
          <div className="space-y-4">
            <label className="block font-mono-custom text-xs text-[var(--muted)] uppercase tracking-wider">
              {lang === 'es' ? 'URL del Repositorio GitHub' : 'GitHub Repository URL'}
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                placeholder="https://github.com/org/legacy-app.git"
                className="flex-1 bg-[var(--grid-soft)] border border-[var(--grid)] p-3 text-xs font-mono-custom text-[var(--text)] focus:outline-none focus:border-[var(--blue)]"
              />
              <button
                onClick={runAnalysis}
                className="bg-[var(--blue)] text-white font-mono-custom text-xs font-bold px-6 py-3 uppercase hover:bg-[#3b66d9] transition-all flex items-center gap-2"
              >
                <Github className="w-4 h-4" /> {lang === 'es' ? 'Escanear Repo' : 'Scan Repo'}
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="font-mono-custom text-xs text-[var(--muted)] uppercase tracking-wider">
                {lang === 'es' ? 'Seleccionar Módulo de Ejemplo' : 'Select Sample Module'}
              </span>
              <button 
                onClick={() => setShowCodePaste(!showCodePaste)}
                className="font-mono-custom text-xs text-[var(--blue)] underline underline-offset-2"
              >
                {showCodePaste ? (lang === 'es' ? 'Ver Archivos' : 'View Files') : (lang === 'es' ? '+ Pegar Código Directo' : '+ Paste Code')}
              </button>
            </div>

            {showCodePaste ? (
              <div className="space-y-4">
                <textarea
                  value={pastedCode}
                  onChange={(e) => setPastedCode(e.target.value)}
                  placeholder="// Paste your legacy code snippet here..."
                  className="w-full h-36 bg-[var(--grid-soft)] border border-[var(--grid)] p-3 font-mono-custom text-xs text-[var(--text)] focus:outline-none focus:border-[var(--blue)] resize-none"
                />
                <button
                  onClick={() => {
                    if (pastedCode) {
                      setSelectedFile('custom_snippet.py');
                      fileDataStore['custom_snippet.py'] = {
                        riskScore: 78,
                        riskLevel: 'high',
                        riskTitle: 'ALTO RIESGO',
                        reason: 'Snippet pegado requiere auditoría de excepciones y acoplamiento.',
                        dependencies: 6,
                        coverage: '0%',
                        age: 'En Vivo',
                        vulns: ['Sin pruebas unitarias asociadas'],
                        explanation: 'Fragmento de código pegado directamente. Alcy Legacy detecta falta de tipado estricto y ausencia de pruebas.',
                      };
                      runAnalysis();
                    }
                  }}
                  className="bg-[var(--blue)] text-white font-mono-custom text-xs font-bold px-6 py-2.5 uppercase hover:bg-[#3b66d9]"
                >
                  {lang === 'es' ? 'Analizar Snippet Pegado' : 'Analyze Snippet'}
                </button>
              </div>
            ) : (
              <div>
                <div className="flex flex-wrap gap-3 mb-6">
                  {Object.keys(fileDataStore).map((fileName) => (
                    <button
                      key={fileName}
                      onClick={() => {
                        setSelectedFile(fileName);
                        setHasAnalyzed(false);
                      }}
                      className={`flex items-center gap-2 px-4 py-3 font-mono-custom text-xs border transition-all ${
                        selectedFile === fileName
                          ? 'border-[var(--blue)] text-[var(--blue)] bg-[var(--blue)]/10 font-bold'
                          : 'border-[var(--grid)] text-[var(--muted)] hover:border-[var(--blue-dim)] hover:text-[var(--text)]'
                      }`}
                    >
                      <FileCode className="w-4 h-4" />
                      {fileName}
                    </button>
                  ))}

                  <label className="flex items-center gap-2 px-4 py-3 font-mono-custom text-xs border border-dashed border-[var(--grid)] text-[var(--muted)] hover:border-[var(--blue)] hover:text-[var(--text)] cursor-pointer transition-all">
                    <Upload className="w-4 h-4 text-[var(--blue)]" />
                    <span>{lang === 'es' ? 'Subir Archivo (.py, .js, .java)' : 'Upload File'}</span>
                    <input type="file" onChange={handleFileUpload} className="hidden" />
                  </label>
                </div>

                <div className="flex gap-4">
                  <button
                    onClick={runAnalysis}
                    disabled={isAnalyzing}
                    className="flex-1 bg-[var(--blue)] text-white font-mono-custom text-xs font-bold py-3.5 px-6 uppercase tracking-wider hover:bg-[#3b66d9] transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_rgba(76,126,255,0.3)] disabled:opacity-50"
                  >
                    <Play className="w-4 h-4 fill-white" />
                    {lang === 'es' ? 'EJECUTAR ANÁLISIS DE RIESGO' : 'RUN RISK ANALYSIS'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Live Terminal Console Log Simulator */}
        {consoleLogs.length > 0 && (
          <div className="mt-6 bg-[var(--grid-soft)] border border-[var(--grid)] p-4 font-mono-custom text-xs leading-relaxed space-y-1">
            <div className="text-[var(--muted)] border-b border-[var(--grid)] pb-2 mb-2 flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[var(--blue)]" />
              <span>IBM Bob Skill Runner — Execution Output</span>
            </div>
            {consoleLogs.map((log, index) => (
              <div key={index} className={log.startsWith('✔') ? 'text-[var(--green)] font-bold' : 'text-[var(--text)]'}>
                {log}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Render Risk Dashboard once analyzed or selected */}
      {(hasAnalyzed || !isAnalyzing) && fileDataStore[selectedFile] && (
        <div className="max-w-4xl mx-auto">
          <RiskDashboard 
            selectedFile={selectedFile}
            data={fileDataStore[selectedFile]}
            lang={lang}
          />
        </div>
      )}
    </section>
  );
};

export default Hero;
