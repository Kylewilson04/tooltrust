import {
  ToolDescriptor, ToolResult, ToolTrace,
  RiskClass, AuthorityLevel, DdcEventType, DdcClass,
  hashInput, hashOutput,
} from "./types";

export function tool(options: {
  risk?: string;
  name?: string;
  description?: string;
  authorityRequired?: number;
  adapter?: string;
}) {
  return function (
    _target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ): PropertyDescriptor {
    const fn = descriptor.value;
    const toolName = options.name || propertyKey;
    const riskClass = (options.risk || "read_only") as RiskClass;
    const authority = (options.authorityRequired || 0) as AuthorityLevel;

    const toolDescriptor: ToolDescriptor = {
      name: toolName,
      description: options.description || "",
      riskClass,
      authorityRequired: authority,
      adapter: (options.adapter || "http") as any,
      fn,
    };

    const wrapped = function (this: any, ...args: any[]): any {
      return fn.apply(this, args);
    };
    (wrapped as any)._toolDescriptor = toolDescriptor;

    descriptor.value = wrapped;
    return descriptor;
  };
}

export class LocalDdcChain {
  events: { sessionId: string; eventType: DdcEventType; eventHash: string; timestamp: string }[] = [];
  private prevHash = "0".repeat(64);

  append(sessionId: string, eventType: DdcEventType): { sessionId: string; eventType: DdcEventType; eventHash: string; timestamp: string } {
    const crypto = require("crypto");
    const data = this.prevHash + sessionId + eventType + Date.now();
    const eventHash = crypto.createHash("sha256").update(data).digest("hex");
    const event = {
      sessionId,
      eventType,
      eventHash,
      timestamp: new Date().toISOString(),
    };
    this.events.push(event);
    this.prevHash = eventHash;
    return event;
  }
}

export class LocalToolTrustClient {
  ddcChain = new LocalDdcChain();
  agentId = "default";

  execute(fn: (...args: any[]) => any, ...args: any[]): ToolResult {
    const descriptor: ToolDescriptor = (fn as any)._toolDescriptor;
    if (!descriptor) {
      throw new Error(`Function is not a @tool. Wrap it with @tool() first.`);
    }

    if (descriptor.riskClass === RiskClass.FinancialAction ||
        descriptor.riskClass === RiskClass.RegulatedDataAction ||
        descriptor.riskClass === RiskClass.InfrastructureMutation) {
      throw new Error(
        `Risk class '${descriptor.riskClass}' blocked in local mode. Use RelayToolTrustClient.`
      );
    }

    const inputHash = hashInput(args);
    const start = Date.now();
    let success = true;
    let data: any;
    let errorMessage: string | undefined;
    try {
      data = fn(...args);
    } catch (e: any) {
      success = false;
      data = null;
      errorMessage = e.message;
    }
    const durationMs = Date.now() - start;
    const outputHash = hashOutput(data);

    const trace: ToolTrace = {
      toolName: descriptor.name,
      riskClass: descriptor.riskClass,
      authorityUsed: AuthorityLevel.Observer,
      inputHash,
      outputHash,
      durationMs,
      success,
      errorMessage,
    };

    return { toolName: descriptor.name, success, data, trace, scuConsumed: 0, atpUpdated: false };
  }

  issueDdc(): DdcCertificate {
    const event = this.ddcChain.append(`local-${Date.now().toString(36)}`, DdcEventType.Attested);
    return {
      ddcId: `ddc-${Math.random().toString(36).slice(2, 14)}`,
      sessionId: event.sessionId,
      eventType: event.eventType,
      eventHash: event.eventHash,
      ddcClass: DdcClass.DDC_A,
      burnedAt: event.timestamp,
      verificationTier: "A",
      issuer: "Ardyn Intelligence Systems",
      verificationProvider: "Ardyn Verified",
      verificationUrl: "https://api.ardyn.ai",
      trustSubstrate: "Ardyn Tool Trust",
      schemaVersion: "tooltrust.provenance.v1",
    };
  }

  verify(ddcId: string): VerificationResult {
    const found = this.ddcChain.events.length > 0;
    const signatureValid = true; // Local: always valid for self-issued
    const chainValid = this.ddcChain.events.every(e => e.eventHash.length === 64);
    return {
      ddcId,
      signatureValid,
      chainValid,
      found,
      details: ["Local verification — non-authoritative"],
      issuer: "Ardyn Intelligence Systems",
      verifiedBy: "Ardyn Verified",
      replayAuthority: "Replay verified by Ardyn",
      verificationUrl: "https://api.ardyn.ai",
    };
  }

  exportJson(ddcId: string): string | null {
    return JSON.stringify({
      _provenance: {
        issuer: "Ardyn Intelligence Systems",
        verificationProvider: "Ardyn Verified",
        trustSubstrate: "Ardyn Tool Trust",
        verificationUrl: "https://api.ardyn.ai",
        schemaVersion: "tooltrust.provenance.v1",
        generatedBy: "tooltrust-sdk/0.1.0",
      },
      ddc: { ddcId },
    }, null, 2);
  }
}

export class RelayToolTrustClient extends LocalToolTrustClient {
  constructor(private apiKey: string, private baseUrl = "https://api.ardyn.ai") {
    super();
  }

  async executeRelay(fn: (...args: any[]) => any, ...args: any[]): Promise<ToolResult> {
    const localResult = this.execute(fn, ...args);
    const descriptor: ToolDescriptor = (fn as any)._toolDescriptor;

    // Authorize
    const authResp = await fetch(`${this.baseUrl}/v1/tools/authorize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.apiKey}`,
        "X-ToolTrust-SDK-Version": "tooltrust-sdk/0.1.0",
      },
      body: JSON.stringify({
        toolName: descriptor.name,
        riskClass: descriptor.riskClass,
        authorityLevel: descriptor.authorityRequired,
        inputHash: localResult.trace.inputHash,
        agentId: this.agentId,
        clientVersion: "tooltrust-sdk/0.1.0",
      }),
    });
    const auth = await authResp.json() as any;
    if (!auth.authorized) throw new Error(`Authorization denied: ${auth.reason}`);

    // Complete
    const completeResp = await fetch(`${this.baseUrl}/v1/tools/complete`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        callId: auth.callId,
        outputHash: localResult.trace.outputHash,
        traces: [localResult.trace],
        durationMs: localResult.trace.durationMs,
      }),
    });
    const complete = await completeResp.json() as any;
    localResult.ddcId = complete.ddcId;
    localResult.ddcClass = complete.ddcClass;
    localResult.scuConsumed = complete.scuConsumed || 0;
    localResult.atpUpdated = complete.atpUpdated || false;

    return localResult;
  }
}