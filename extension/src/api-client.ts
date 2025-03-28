import axios from "axios";
import * as vscode from "vscode";
import { AccessibilityResponse, ScanResponse, ScanRequest, HealthResponse } from "./types";

const TIMEOUT = 120000;

export async function checkApiHealth(apiUrl: string, context: vscode.ExtensionContext): Promise<boolean> {
    try {
        const response = await axios.get<HealthResponse>(`${apiUrl}/health`, { timeout: TIMEOUT });
        const isHealthy = response.data?.status === "healthy";
        await context.globalState.update("apiHealth", isHealthy);
        return isHealthy;
    } catch (error) {
        await context.globalState.update("apiHealth", false);
        return false;
    }
}

export async function queryAccessibilityApi<AccessibilityResponse>(
    apiUrl: string,
    command: string,
    apiKey: string,
    query: string
): Promise<AccessibilityResponse> {
    try {
        // Parse the query if it's a JSON string, otherwise use it as is
        const queryData = query.startsWith("{") ? JSON.parse(query) : { query };

        const response = await axios.post<AccessibilityResponse>(`${apiUrl}/api/accessibility/${command}`, queryData, {
            headers: {
                "Content-Type": "application/json",
                "X-Open-API-Key": apiKey
            },
            timeout: TIMEOUT
        });
        return response.data as AccessibilityResponse;
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "unknown error";
        throw new Error(`API request failed: ${errorMessage}`);
    }
}

export async function performAccessibilityScan(apiUrl: string, apiKey: string, target: string): Promise<ScanResponse> {
    if (!apiKey) {
        throw new Error("API key not configured. Please set your API key in the extension settings.");
    }
    if (!apiUrl) {
        throw new Error("API URL not configured. Please set your API URL in the extension settings.");
    }
    try {
        const response = await axios.post<ScanResponse>(`${apiUrl}/api/accessibility/scan`, { url: target } as ScanRequest, {
            headers: {
                "Content-Type": "application/json",
                "X-Open-API-Key": apiKey
            },
            timeout: TIMEOUT
        });

        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            if (error.response?.status === 401) {
                throw new Error("Invalid or missing API key. Please check your API key in the extension settings.");
            } else if (error.response?.status === 400) {
                throw new Error("Invalid URL format or request. Please check the URL and try again.");
            } else if (error.code === "ECONNREFUSED") {
                throw new Error("Could not connect to the API server. Please ensure it's running.");
            }
        }
        throw error;
    }
}

function getSeverityIcon(severity: string): string {
    switch (severity.toLowerCase()) {
        case "critical":
            return "🔴";
        case "serious":
            return "🟠";
        case "moderate":
            return "🟡";
        case "minor":
            return "🔵";
        default:
            return "⚪";
    }
}

export interface IntentAnalysisResult {
    command: 'scan' | 'fix' | 'explain';
    content: string;
    confidence: number;
    metadata: {
        url?: string;
        issue_number?: number;
        topic?: string;
    };
}

export async function analyzeIntent(
    apiUrl: string,
    apiKey: string,
    query: string,
    context?: { scan_results?: string[]; previous_commands?: string[] }
): Promise<IntentAnalysisResult> {
    if (!apiKey) {
        throw new Error("API key not configured. Please set your API key in the extension settings.");
    }
    if (!apiUrl) {
        throw new Error("API URL not configured. Please set your API URL in the extension settings.");
    }
    try {
        const response = await axios.post<IntentAnalysisResult>(
            `${apiUrl}/api/accessibility/analyze-intent`,
            { query, context },
            {
                headers: {
                    "Content-Type": "application/json",
                    "X-Open-API-Key": apiKey
                },
                timeout: TIMEOUT
            }
        );
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error)) {
            if (error.response?.status === 401) {
                throw new Error("Invalid or missing API key. Please check your API key in the extension settings.");
            } else if (error.response?.status === 400) {
                throw new Error("Invalid request format. Please try again.");
            } else if (error.code === "ECONNREFUSED") {
                throw new Error("Could not connect to the API server. Please ensure it's running.");
            }
        }
        throw error;
    }
}
