import { AccessibilityResponse, ScanResponse, DetailedScanResults, DetailedViolation } from "./types";

export function formatAccessibilityResponse(response: AccessibilityResponse): string {
    // Type validation
    if (!response) {
        return "❌ Error: No response received from the API";
    }

    if (typeof response !== "object") {
        return "❌ Error: Invalid response type received from the API";
    }

    // Field validation
    const fields = ["answer", "explanation", "guidelines", "examples"] as const;
    const missingFields = fields.filter(field => !(field in response));
    if (missingFields.length > 0) {
        return `❌ Error: Response is missing required fields: ${missingFields.join(", ")}`;
    }

    // Type checking for each field
    const validatedResponse = { ...response };
    fields.forEach(field => {
        const value = validatedResponse[field];
        if (typeof value !== "string") {
            validatedResponse[field] = String(value || "");
        }
    });

    // Ensure all fields exist with proper fallbacks
    const answer = validatedResponse.answer?.trim() || "No answer provided";
    const explanation = validatedResponse.explanation?.trim() || "No explanation provided";
    const guidelines = validatedResponse.guidelines?.trim() || "No guidelines provided";
    const examples = validatedResponse.examples?.trim() || "No examples provided";

    // Format all sections of the response with better separation and formatting
    const sections = [
        "# Accessibility Response\n",
        "## 💡 Answer",
        answer,
        "\n---\n",
        "## 📝 Detailed Explanation",
        explanation,
        "\n---\n",
        "## 📋 Guidelines Referenced",
        guidelines,
        "\n---\n",
        "## 🔍 Implementation Examples",
        "```html",
        examples,
        "```"
    ];

    return sections.join("\n");
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

export function formatScanResults(scanResponse: ScanResponse): string[] {
    const results: string[] = [];

    // Add scan summary
    results.push(`📊 ${scanResponse.scan_result}`);

    // Add raw violations in a structured format
    if (scanResponse.raw_violations) {
        Object.entries(scanResponse.raw_violations).forEach(([severity, issues]) => {
            if (Array.isArray(issues) && issues.length > 0) {
                issues.forEach(issue => {
                    const icon = getSeverityIcon(severity);
                    results.push(`${icon} [${severity.toUpperCase()}] ${issue.help}`);
                });
            }
        });
    }

    return results;
}

export function extractDetailedScanResults(scanResponse: ScanResponse): DetailedScanResults {
    const detailedResults: DetailedScanResults = {
        summary: scanResponse.scan_result,
        violations: []
    };

    // Process violations in the same order as formatScanResults
    if (scanResponse.raw_violations) {
        Object.entries(scanResponse.raw_violations).forEach(([severity, issues]) => {
            if (Array.isArray(issues) && issues.length > 0) {
                issues.forEach(issue => {
                    detailedResults.violations.push({
                        id: issue.id,
                        help: issue.help,
                        html: issue.html
                    });
                });
            }
        });
    }

    return detailedResults;
}
