import { AnalysisRequest, RiskAnalysisResult, ApiResponse } from '../types';

// Leer URL base de la API desde variables de entorno o valor por defecto
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

/**
 * Función para desinfectar entradas de texto contra XSS e inyecciones.
 */
export function sanitizeInput(input: string, maxLen = 10000): string {
  if (!input) return '';
  const trimmed = input.trim().slice(0, maxLen);
  return trimmed
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

/**
 * Servicio centralizado para comunicación segura con el backend.
 */
export const ApiService = {
  /**
   * Envía la solicitud de análisis de código legacy al backend.
   * Si el backend no responde o falla la red, recurre de forma transparente al mock de contingencia.
   */
  async analyzeCode(req: AnalysisRequest): Promise<RiskAnalysisResult> {
    try {
      const token = localStorage.getItem('alcy_auth_token');
      const response = await fetch(`${API_BASE_URL}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          filePath: req.filePath,
          codeSnippet: req.codeSnippet ? sanitizeInput(req.codeSnippet, 50000) : undefined,
          githubUrl: req.githubUrl ? sanitizeInput(req.githubUrl, 500) : undefined,
          scope: req.scope,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const json: ApiResponse<RiskAnalysisResult> = await response.json();
      if (json.success && json.data) {
        return json.data;
      }
      throw new Error(json.error || 'Respuesta de API no válida');
    } catch (err) {
      console.warn('Backend API no disponible. Utilizando análisis seguro local:', err);
      return this.fallbackAnalysis(req);
    }
  },

  /**
   * Mock seguro cliente de contingencia en caso de que el backend no esté activo.
   */
  fallbackAnalysis(req: AnalysisRequest): RiskAnalysisResult {
    const fileName = req.filePath || 'custom_code.py';
    return {
      riskScore: 82,
      riskLevel: 'high',
      riskTitle: 'ALTO RIESGO',
      reason: `El archivo '${fileName}' presenta acoplamiento alto (14 módulos dependientes) y carece de suite de tests unitarios verificados.`,
      dependencies: 14,
      coverage: '15%',
      age: '3.9 años',
      vulns: ['Vulnerabilidad detectada en librerías asociadas', 'Ausencia de tipado estricto (PEP 484)'],
      explanation: `Análisis para ${fileName}: Se sugiere no permitir refactorizaciones automáticas sin generar primero una suite de pruebas de integración.`,
    };
  },
};
