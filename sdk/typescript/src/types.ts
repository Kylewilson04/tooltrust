// Tool Trust TypeScript SDK — v0.1.0
// "Replayable autonomous tool execution."

export enum RiskClass {
  ReadOnly = "read_only",
  DataAccess = "data_access",
  CodeExecution = "code_execution",
  ExternalCommunication = "external_communication",
  WriteAction = "write_action",
  InfrastructureMutation = "infrastructure_mutation",
  FinancialAction = "financial_action",
  RegulatedDataAction = "regulated_data_action",
}

export enum AuthorityLevel {
  Observer = 0,
  Reader = 1,
  Contributor = 2,
  Operator = 3,
  Admin = 4,
  Root = 5,
}

export enum DdcEventType {
  DestructionConfirmed = "DestructionConfirmed",
  AbortBurned = "AbortBurned",
  DestructionFailed = "DestructionFailed",
  SessionCrashed = "SessionCrashed",
  Attested = "Attested",
  SovereigntyVerified = "SovereigntyVerified",
  CertificationGatePassed = "CertificationGatePassed",
  CertificationGateRejected = "CertificationGateRejected",
}

export enum DdcClass {
  DDC_A = "DDC-A",
  DDC_S = "DDC-S",
  DDC_H = "DDC-H",
}

export enum AdapterType {
  MCP = "mcp",
  LangChain = "langchain",
  CrewAI = "crewai",
  Http = "http",
  Shell = "shell",
  CodeExecution = "code_execution",
}

export interface ToolDescriptor {
  name: string;
  description: string;
  riskClass: RiskClass;
  authorityRequired: AuthorityLevel;
  adapter: AdapterType;
  fn?: (...args: any[]) => any;
}

export interface ToolTrace {
  toolName: string;
  riskClass: RiskClass;
  authorityUsed: AuthorityLevel;
  inputHash: string;
  outputHash: string;
  durationMs: number;
  success: boolean;
  errorMessage?: string;
}

export interface DdcCertificate {
  ddcId: string;
  sessionId: string;
  eventType: DdcEventType;
  eventHash: string;
  ddcClass: DdcClass;
  burnedAt: string;
  verificationTier: string;
  // Provenance
  issuer: string;
  verificationProvider: string;
  verificationUrl: string;
  trustSubstrate: string;
  schemaVersion: string;
}

export interface DdcLedgerRecord {
  schema: string;
  ddcId: string;
  orgId: string;
  tenantId: string;
  sessionId: string;
  eventType: string;
  eventHash: string;
  prevHash: string;
  recordHash: string;
  signerPublicKeyHex: string;
  signatureHex: string;
  evidenceBundleId: string;
  destructionVerified: boolean;
  scrubbed: boolean;
  resultReleased: boolean;
  scuMinted: boolean;
  ddcClass: string;
  burnedAt: string;
  metadata: Record<string, any>;
}

export interface ToolResult {
  toolName: string;
  success: boolean;
  data: any;
  trace: ToolTrace;
  ddcId?: string;
  ddcClass?: DdcClass;
  scuConsumed: number;
  atpUpdated: boolean;
}

export interface VerificationResult {
  ddcId: string;
  signatureValid: boolean;
  chainValid: boolean;
  found: boolean;
  details: string[];
  // Provenance
  issuer: string;
  verifiedBy: string;
  replayAuthority: string;
  verificationUrl: string;
}

export interface AgentTrustProfile {
  agentId: string;
  sessionCount: number;
  totalDdcs: number;
  riskClassesUsed: string[];
  highestRiskAuthorized: string;
  trustScore: number;
  createdAt: string;
  lastSeen: string;
}

export function hashInput(...args: any[]): string {
  const crypto = require("crypto");
  return crypto.createHash("sha256").update(JSON.stringify(args)).digest("hex");
}

export function hashOutput(result: any): string {
  const crypto = require("crypto");
  return crypto.createHash("sha256").update(JSON.stringify({ result })).digest("hex");
}
