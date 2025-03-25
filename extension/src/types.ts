export interface AccessibilityResponse {
    answer: string;
    explanation: string;
    guidelines: string;
    examples: string;
}

export interface AccessibilityIssue {
    id: string;
    description: string;
    help: string;
    helpUrl: string;
    nodes: number;
    html: string;
}

export interface CategorizedViolations {
    critical: AccessibilityIssue[];
    serious: AccessibilityIssue[];
    moderate: AccessibilityIssue[];
    minor: AccessibilityIssue[];
}

export interface ScanRequest {
    url: string;
}

export interface HealthResponse {
    status: string;
}
export interface DetailedViolation {
    id: string;
    help: string;
    html: string;
}

export interface DetailedScanResults {
    summary: string;
    violations: DetailedViolation[];
}

export interface ScanResponse {
    url: string;
    scan_result: string;
    raw_violations: {
        [severity: string]: Array<{
            id: string;
            description: string;
            help: string;
            html: string;
            impact: string;
        }>;
    };
}
