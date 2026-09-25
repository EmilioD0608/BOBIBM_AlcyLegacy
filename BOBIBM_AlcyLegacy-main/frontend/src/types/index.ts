export interface RiskAnalysisResult {
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

export interface AnalysisRequest {
  filePath?: string;
  codeSnippet?: string;
  githubUrl?: string;
  scope: 'file' | 'folder' | 'repo';
}

export interface User {
  name: string;
  email: string;
  token?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
