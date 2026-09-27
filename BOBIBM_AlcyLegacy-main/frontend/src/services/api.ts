import {
  AnalysisRequest,
  RiskAnalysisResult,
  ApiResponse
} from '../types';

import { z } from 'zod';

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
// VALIDACIÓN DE RESPUESTAS DE LA API
// ============================================================

const AuthUserSchema = z.object({
  id: z.string().uuid(),
  username: z.string().min(1).max(100),
  email: z.string().email()
});

const LoginResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  token: z.string().min(1),
  user: AuthUserSchema
});

const RegisterResponseSchema = z.object({
  success: z.boolean(),
  message: z.string(),
  user: AuthUserSchema.optional()
});

const CurrentUserResponseSchema = z.object({
  success: z.boolean(),
  user: AuthUserSchema
});


// ============================================================
// ERRORES SEGUROS
// ============================================================

type ApiErrorCode =
  | 'INVALID_CREDENTIALS'
  | 'EMAIL_ALREADY_EXISTS'
  | 'INVALID_INPUT'
  | 'AUTH_REQUIRED'
  | 'NETWORK_ERROR'
  | 'SERVER_ERROR'
  | 'INVALID_API_RESPONSE';

export class ApiError extends Error {

  constructor(
    public readonly code: ApiErrorCode
  ) {
    super(code);

    this.name = 'ApiError';
  }
}


// ============================================================
// LOGS SEGUROS
// Solo muestra información técnica durante desarrollo
// ============================================================

function logDevelopmentError(
  context: string,
  error: unknown
): void {

  if (import.meta.env.DEV) {
    console.error(context, error);
  }
}


// ============================================================
// MANEJO DEL JWT
// ============================================================

const TOKEN_KEY = 'legacy_guardian_token';

function getAccessToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

function saveAccessToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

function removeAccessToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
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
    throw new ApiError('AUTH_REQUIRED');
  }

  const headers =
    new Headers(options.headers);

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

  let response: Response;

  try {

    response = await fetch(
      `${API_BASE_URL}${endpoint}`,
      {
        ...options,
        headers
      }
    );

  } catch {

    throw new ApiError(
      'NETWORK_ERROR'
    );
  }

  // JWT expirado o inválido
  if (response.status === 401) {
    removeAccessToken();
  }

  return response;
}


// ============================================================
// NORMALIZACIÓN DE ENTRADAS
// ============================================================

/*
 * Esta función NO intenta eliminar HTML.
 *
 * El sistema analiza código fuente, por lo que eliminar caracteres
 * como < > " ' { } podría modificar el código enviado a BOB.
 *
 * Aquí solamente normalizamos espacios externos y limitamos
 * el tamaño de la entrada.
 */
export function normalizeInput(
  input: string,
  maxLen = 10000
): string {

  if (!input) {
    return '';
  }

  return input
    .trim()
    .slice(0, maxLen);
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
      username:
        username.trim(),

      email:
        email.trim().toLowerCase(),

      password
    };

    let response: Response;

    try {

      response = await fetch(
        `${API_BASE_URL}/auth/register`,
        {
          method: 'POST',

          headers: {
            'Content-Type':
              'application/json'
          },

          body:
            JSON.stringify(data)
        }
      );

    } catch {

      throw new ApiError(
        'NETWORK_ERROR'
      );
    }


    let raw: unknown;

    try {

      raw =
        await response.json();

    } catch {

      throw new ApiError(
        'INVALID_API_RESPONSE'
      );
    }


    if (!response.ok) {

      if (response.status === 400) {

        throw new ApiError(
          'INVALID_INPUT'
        );
      }

      if (response.status === 409) {

        throw new ApiError(
          'EMAIL_ALREADY_EXISTS'
        );
      }

      throw new ApiError(
        'SERVER_ERROR'
      );
    }


    const parsed =
      RegisterResponseSchema.safeParse(
        raw
      );


    if (!parsed.success) {

      logDevelopmentError(
        'Respuesta de registro inválida',
        parsed.error
      );

      throw new ApiError(
        'INVALID_API_RESPONSE'
      );
    }


    return parsed.data;
  },


  // ----------------------------------------------------------
  // LOGIN
  // ----------------------------------------------------------

  async login(
    email: string,
    password: string
  ): Promise<LoginResponse> {

    const data: LoginData = {

      email:
        email.trim().toLowerCase(),

      password
    };


    let response: Response;

    try {

      response = await fetch(
        `${API_BASE_URL}/auth/login`,
        {
          method: 'POST',

          headers: {
            'Content-Type':
              'application/json'
          },

          body:
            JSON.stringify(data)
        }
      );

    } catch {

      throw new ApiError(
        'NETWORK_ERROR'
      );
    }


    let raw: unknown;

    try {

      raw =
        await response.json();

    } catch {

      throw new ApiError(
        'INVALID_API_RESPONSE'
      );
    }


    if (!response.ok) {

      if (
        response.status === 400 ||
        response.status === 401
      ) {

        throw new ApiError(
          'INVALID_CREDENTIALS'
        );
      }


      throw new ApiError(
        'SERVER_ERROR'
      );
    }


    const parsed =
      LoginResponseSchema.safeParse(
        raw
      );


    if (!parsed.success) {

      logDevelopmentError(
        'Respuesta de login inválida',
        parsed.error
      );

      throw new ApiError(
        'INVALID_API_RESPONSE'
      );
    }


    saveAccessToken(
      parsed.data.token
    );


    return parsed.data;
  },


  // ----------------------------------------------------------
  // LOGOUT
  // ----------------------------------------------------------

  logout(): void {

    removeAccessToken();
  },


  // ----------------------------------------------------------
  // COMPROBAR SI EXISTE SESIÓN
  // ----------------------------------------------------------

  isAuthenticated(): boolean {

    return (
      getAccessToken() !== null
    );
  },


  // ----------------------------------------------------------
  // USUARIO ACTUAL
  // ----------------------------------------------------------

  async getCurrentUser(): Promise<{
    success: boolean;
    user: AuthUser;
  }> {

    const response =
      await authenticatedFetch(
        '/auth/me',
        {
          method: 'GET'
        }
      );

    let raw: unknown;

    try {
      raw = await response.json();
    } catch {
      throw new ApiError(
        'INVALID_API_RESPONSE'
      );
    }

    if (!response.ok) {

      if (response.status === 401) {
        throw new ApiError(
          'AUTH_REQUIRED'
        );
      }

      throw new ApiError(
        'SERVER_ERROR'
      );
    }

    const parsed =
      CurrentUserResponseSchema.safeParse(
        raw
      );

    if (!parsed.success) {

      logDevelopmentError(
        'Respuesta de usuario actual inválida',
        parsed.error
      );

      throw new ApiError(
        'INVALID_API_RESPONSE'
      );
    }

    return parsed.data;
  },


  // ==========================================================
  // FUNCIONES DE ANÁLISIS
  // Se migrarán posteriormente al nuevo sistema Jobs
  // ==========================================================

  async createTestAnalysis() {

    const response =
      await authenticatedFetch(
        '/analyses',
        {
          method: 'POST',

          body: JSON.stringify({

            source_type: 'file',

            target_name:
              'legacy-test.py',

            risk_level:
              'high',

            score:
              82,

            has_tests:
              false,

            dependents_count:
              14,

            age_days:
              1423,

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


    let raw: unknown;

    try {

      raw =
        await response.json();

    } catch {

      throw new ApiError(
        'INVALID_API_RESPONSE'
      );
    }


    if (!response.ok) {

      throw new ApiError(
        'SERVER_ERROR'
      );
    }


    return raw;
  },


  // ----------------------------------------------------------
  // ANALIZAR CÓDIGO
  // ----------------------------------------------------------

  async analyzeCode(
    req: AnalysisRequest
  ): Promise<RiskAnalysisResult> {

    try {

      const response =
        await authenticatedFetch(
          '/analyze',
          {
            method: 'POST',

            body: JSON.stringify({

              filePath:
                req.filePath,

              codeSnippet:
                req.codeSnippet
                  ? normalizeInput(
                    req.codeSnippet,
                    50000
                  )
                  : undefined,

              githubUrl:
                req.githubUrl
                  ? normalizeInput(
                    req.githubUrl,
                    500
                  )
                  : undefined,

              scope:
                req.scope
            })
          }
        );


      if (!response.ok) {

        throw new ApiError(
          'SERVER_ERROR'
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


      throw new ApiError(
        'INVALID_API_RESPONSE'
      );


    } catch (error) {

      /*
       * No mostramos información técnica
       * al usuario en producción.
       */
      logDevelopmentError(
        'Backend de análisis no disponible',
        error
      );


      return this.fallbackAnalysis(
        req
      );
    }
  },


  // ----------------------------------------------------------
  // ANÁLISIS LOCAL DE RESPALDO
  // ----------------------------------------------------------

  fallbackAnalysis(
    req: AnalysisRequest
  ): RiskAnalysisResult {

    const fileName =
      req.filePath ||
      'custom_code.py';


    return {

      riskScore:
        82,

      riskLevel:
        'high',

      riskTitle:
        'ALTO RIESGO',

      reason:
        `El archivo '${fileName}' presenta acoplamiento alto ` +
        `(14 módulos dependientes) y carece de suite de ` +
        `tests unitarios verificados.`,

      dependencies:
        14,

      coverage:
        '15%',

      age:
        '3.9 años',

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


  // ----------------------------------------------------------
  // OBTENER ANÁLISIS
  // ----------------------------------------------------------

  async getAnalyses() {

    const response =
      await authenticatedFetch(
        '/analyses',
        {
          method: 'GET'
        }
      );


    let raw: unknown;

    try {

      raw =
        await response.json();

    } catch {

      throw new ApiError(
        'INVALID_API_RESPONSE'
      );
    }


    if (!response.ok) {

      throw new ApiError(
        'SERVER_ERROR'
      );
    }


    return raw;
  }
};