import { env } from "../config/env.js";

const getBobUrl = (path: string): string => {
  const baseUrl = env.BOB_AI_URL.replace(/\/+$/, "");
  return `${baseUrl}${path}`;
};

export interface BobFileAnalysis {
  filePath: string;
  riskScore: number;
  riskLevel: "low" | "medium" | "high";
  dependencies: number;
  coverage: string;
  age: string;
  blockers: string[];
  safeToRefactorDirectly: boolean;
  recommendation: string;
}

export interface BobAnalyzeResponse {
  success: boolean;

  summary: {
    overallRisk: number;
    riskLevel: "low" | "medium" | "high";
    totalFiles: number;
    highRiskFilesCount: number;
  };

  files: BobFileAnalysis[];
}

interface AnalyzeRepositoryParams {
  repoPath: string;
  targetFiles: string[];
  scope: "file" | "folder" | "repo";
}
interface RefactorRepositoryParams {
  filePath: string;
  originalCode: string;

  userSpecs: {
    targetLanguage: string;
    targetVersion: string;
    framework: string;
    customInstructions: string;
  };

  generateTests: boolean;
  riskScore?: number;
}

export interface BobRefactorResponse {
  success: boolean;
  filePath: string;
  refactoredCode: string;
  generatedTests: string;
  diff: string;
  changesSummary: string[];
}

export async function checkBobHealth() {
  const response = await fetch(
    getBobUrl("/internal/v1/health"),
    {
      method: "GET",
      headers: {
        "X-Internal-Secret": env.BOB_INTERNAL_SECRET,
        Accept: "application/json",
      },
      signal: AbortSignal.timeout(5000),
    }
  );

  if (!response.ok) {
    const body = await response.text();

    throw new Error(
      `BOB Health respondió HTTP ${response.status}: ${body}`
    );
  }

  return response.json();
}

export async function analyzeRepository(
  params: AnalyzeRepositoryParams
): Promise<BobAnalyzeResponse> {

  const response = await fetch(
    getBobUrl("/internal/v1/analyze"),
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Internal-Secret": env.BOB_INTERNAL_SECRET,
      },

      body: JSON.stringify({
        repoPath: params.repoPath,
        targetFiles: params.targetFiles,
        scope: params.scope,
      }),

      // El análisis puede tardar bastante más que health
      signal: AbortSignal.timeout(120000),
    }
  );

  if (!response.ok) {
    const body = await response.text();

    throw new Error(
      `BOB Analyze respondió HTTP ${response.status}: ${body}`
    );
  }

  return (await response.json()) as BobAnalyzeResponse;
}
export async function refactorRepository(
  params: RefactorRepositoryParams
): Promise<BobRefactorResponse> {

  const response = await fetch(
    getBobUrl("/internal/v1/refactor"),
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        "X-Internal-Secret": env.BOB_INTERNAL_SECRET,
      },

      body: JSON.stringify({
        filePath: params.filePath,
        originalCode: params.originalCode,

        userSpecs: {
          targetLanguage: params.userSpecs.targetLanguage,
          targetVersion: params.userSpecs.targetVersion,
          framework: params.userSpecs.framework,
          customInstructions:
            params.userSpecs.customInstructions,
        },

        generateTests: params.generateTests,
        riskScore: params.riskScore,
      }),

      signal: AbortSignal.timeout(120000),
    }
  );

  if (!response.ok) {
    const body = await response.text();

    throw new Error(
      `BOB Refactor respondió HTTP ${response.status}: ${body}`
    );
  }

  return (await response.json()) as BobRefactorResponse;
}