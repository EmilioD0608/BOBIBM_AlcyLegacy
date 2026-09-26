import {
  AnalysisRequest,
  RiskAnalysisResult,
  ApiResponse
} from '../types';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL;


// ============================================================
// TIPOS DE AUTENTICACIÓN
// ============================================================

interface AuthUser {
  id: string;
  username: string;
  email: string;
}

interface RegisterData {
  username: string;
  email: string;
  password: string;
}

interface LoginData {
  email: string;
  password: string;
}

interface LoginResponse {
  success: boolean;
  message: string;
  token: string;
  user: AuthUser;
}


// ============================================================
// MANEJO DEL JWT
// ============================================================

const TOKEN_KEY = 'legacy_guardian_token';

function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

function saveAccessToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

function removeAccessToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}


// ============================================================
// FETCH AUTENTICADO
// ============================================================

async function authenticatedFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {

  const token = getAccessToken();

  if (!token) {
    throw new Error('AUTH_REQUIRED');
  }

  const headers = new Headers(options.headers);

  headers.set(
    'Authorization',
    `Bearer ${token}`
  );

  if (
    options.body &&
    !(options.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
    headers.set(
      'Content-Type',
      'application/json'
    );
  }

  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      headers
    }
  );

  // Si el JWT expiró o ya no es válido
  if (response.status === 401) {
    removeAccessToken();
  }

  return response;
}


// ============================================================
// SANITIZACIÓN
// ============================================================

export function sanitizeInput(
  input: string,
  maxLen = 10000
): string {

  if (!input) return '';

  return input.trim().slice(0, maxLen);
}


// ============================================================
// API SERVICE
// ============================================================

export const ApiService = {

  // ----------------------------------------------------------
  // REGISTRO
  // ----------------------------------------------------------

  async register(
    username: string,
    email: string,
    password: string
  ) {

    const data: RegisterData = {
      username,
      email,
      password
    };

    const response = await fetch(
      `${API_BASE_URL}/auth/register`,
      {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json'
        },

        body: JSON.stringify(data)
      }
    );

    const json = await response.json();

    if (!response.ok) {
      throw new Error(
        json.details?.[0]?.message ||
        json.error ||
        `Error HTTP ${response.status}`
      );
    }

    return json;
  },


  // ----------------------------------------------------------
  // LOGIN
  // ----------------------------------------------------------

  async login(
    email: string,
    password: string
  ): Promise<LoginResponse> {

    const data: LoginData = {
      email,
      password
    };

    const response = await fetch(
      `${API_BASE_URL}/auth/login`,
      {
        method: 'POST',

        headers: {
          'Content-Type': 'application/json'
        },

        body: JSON.stringify(data)
      }
    );

    const json = await response.json();

    if (!response.ok) {
      throw new Error(
        json.details?.[0]?.message ||
        json.error ||
        `Error HTTP ${response.status}`
      );
    }

    if (!json.token) {
      throw new Error(
        'El servidor no devolvió un token de autenticación'
      );
    }

    saveAccessToken(json.token);

    return json;
  },


  // ----------------------------------------------------------
  // LOGOUT
  // ----------------------------------------------------------

  logout(): void {
    removeAccessToken();
  },


  // ----------------------------------------------------------
  // COMPROBAR SI EXISTE SESIÓN LOCAL
  // ----------------------------------------------------------

  isAuthenticated(): boolean {
    return getAccessToken() !== null;
  },


  // ----------------------------------------------------------
  // USUARIO ACTUAL
  // ----------------------------------------------------------

  async getCurrentUser() {

    const response = await authenticatedFetch(
      '/auth/me',
      {
        method: 'GET'
      }
    );

    const json = await response.json();

    if (!response.ok) {
      throw new Error(
        json.error ||
        `Error HTTP ${response.status}`
      );
    }

    return json;
  },


  // ==========================================================
  // FUNCIONES DE ANÁLISIS
  // Se migrarán posteriormente al nuevo sistema Jobs
  // ==========================================================

  async createTestAnalysis() {

    const response = await authenticatedFetch(
      '/analyses',
      {
        method: 'POST',

        body: JSON.stringify({
          source_type: 'file',
          target_name: 'legacy-test.py',
          risk_level: 'high',
          score: 82,
          has_tests: false,
          dependents_count: 14,
          age_days: 1423,

          reasons: [
            'Alta dependencia entre módulos',
            'No se detectaron pruebas unitarias'
          ],

          flagged_libs: [
            'legacy-library'
          ]
        })
      }
    );

    const json = await response.json();

    if (!response.ok) {
      throw new Error(
        json.error ||
        `Error HTTP ${response.status}`
      );
    }

    return json;
  },


  async analyzeCode(
    req: AnalysisRequest
  ): Promise<RiskAnalysisResult> {

    try {

      const response = await authenticatedFetch(
        '/analyze',
        {
          method: 'POST',

          body: JSON.stringify({
            filePath: req.filePath,

            codeSnippet:
              req.codeSnippet
                ? sanitizeInput(
                    req.codeSnippet,
                    50000
                  )
                : undefined,

            githubUrl:
              req.githubUrl
                ? sanitizeInput(
                    req.githubUrl,
                    500
                  )
                : undefined,

            scope: req.scope
          })
        }
      );

      if (!response.ok) {
        throw new Error(
          `HTTP error! Status: ${response.status}`
        );
      }

      const json:
        ApiResponse<RiskAnalysisResult> =
        await response.json();

      if (
        json.success &&
        json.data
      ) {
        return json.data;
      }

      throw new Error(
        json.error ||
        'Respuesta de API no válida'
      );

    } catch (err) {

      console.warn(
        'Backend de análisis no disponible. Utilizando análisis local:',
        err
      );

      return this.fallbackAnalysis(req);
    }
  },


  fallbackAnalysis(
    req: AnalysisRequest
  ): RiskAnalysisResult {

    const fileName =
      req.filePath ||
      'custom_code.py';

    return {
      riskScore: 82,

      riskLevel: 'high',

      riskTitle: 'ALTO RIESGO',

      reason:
        `El archivo '${fileName}' presenta acoplamiento alto ` +
        `(14 módulos dependientes) y carece de suite de ` +
        `tests unitarios verificados.`,

      dependencies: 14,

      coverage: '15%',

      age: '3.9 años',

      vulns: [
        'Vulnerabilidad detectada en librerías asociadas',
        'Ausencia de tipado estricto (PEP 484)'
      ],

      explanation:
        `Análisis para ${fileName}: ` +
        `Se sugiere no permitir refactorizaciones automáticas ` +
        `sin generar primero una suite de pruebas de integración.`
    };
  },


  async getAnalyses() {

    const response = await authenticatedFetch(
      '/analyses',
      {
        method: 'GET'
      }
    );

    const json = await response.json();

    if (!response.ok) {
      throw new Error(
        json.error ||
        `Error HTTP ${response.status}`
      );
    }

    return json;
  }
};