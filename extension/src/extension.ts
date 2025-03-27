import * as vscode from "vscode";
import { initializeExtension } from "./config";
import { queryAccessibilityApi, performAccessibilityScan, analyzeIntent } from "./api-client";
import { formatScanResults, formatAccessibilityResponse, extractDetailedScanResults } from "./formatters";
import { ScanResponse, DetailedScanResults, AccessibilityResponse } from "./types";

let extensionContext: vscode.ExtensionContext;

// Helper function to normalize URLs
function normalizeUrl(url: string): string {
    // Remove any whitespace
    url = url.trim();
    
    // If URL doesn't start with http:// or https://, add https://
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = 'https://' + url;
    }
    
    return url;
}

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
    extensionContext = context;
    initializeExtension(context);

    const axess_ai_chat_participant = vscode.chat.createChatParticipant("vscode-axessai-chat", handler);
    context.subscriptions.push(axess_ai_chat_participant);
}

// Handle chat requests
const handler: vscode.ChatRequestHandler = async (
    request: vscode.ChatRequest,
    context: vscode.ChatContext,
    stream: vscode.ChatResponseStream,
    token: vscode.CancellationToken
) => {
    const userQuery = request.prompt.trim();
    
    // Retrieve scan results from context state
    let scanResults: string[] = extensionContext.globalState.get<string[]>("scanResults", []);
    let detailedScanResults: DetailedScanResults = extensionContext.globalState.get<DetailedScanResults>("detailedScanResults", {
        summary: "",
        violations: []
    });
    const apiUrl = extensionContext.globalState.get<string>("apiUrl", "");
    const apiKey = extensionContext.globalState.get<string>("apiKey", "");

    // Get previous commands for context
    const previousCommands = extensionContext.globalState.get<string[]>("previousCommands", []);

    try {
        // Check for explicit commands in request.command
        let intentAnalysis;
        if (request.command === 'scan' || request.command === 'fix' || request.command === 'explain') {
            intentAnalysis = {
                command: request.command,
                content: userQuery.trim(),
                confidence: 1.0,
                metadata: {
                    url: userQuery.trim()
                }
            };
        } else {
            // If no explicit command, analyze intent using API
            intentAnalysis = await analyzeIntent(apiUrl, apiKey, userQuery, {
                scan_results: scanResults,
                previous_commands: previousCommands.slice(-5) // Last 5 commands for context
            });
        }

        // Store the command in history
        previousCommands.push(intentAnalysis.command);
        await extensionContext.globalState.update("previousCommands", previousCommands.slice(-10)); // Keep last 10 commands

        switch (intentAnalysis.command) {
            case "scan":
                const url = intentAnalysis.metadata?.url || intentAnalysis.content;
                if (!url) {
                    stream.markdown("⚠️ Please provide a valid URL to scan. Example: `example.com`");
                    return;
                }

                // Normalize and validate URL
                const normalizedUrl = normalizeUrl(url);
                try {
                    new URL(normalizedUrl);
                } catch (e) {
                    stream.markdown("⚠️ Invalid URL format. Please provide a valid domain name or URL.");
                    return;
                }

                // Show scanning message
                stream.markdown(`🔍 Scanning ${normalizedUrl} for accessibility issues...`);

                try {
                    // Perform scan and store complete response
                    const scanResponse = await performAccessibilityScan(apiUrl, apiKey, normalizedUrl);

                    // Extract and store detailed results
                    detailedScanResults = extractDetailedScanResults(scanResponse);
                    await extensionContext.globalState.update("detailedScanResults", detailedScanResults);

                    // Format results for display
                    scanResults = formatScanResults(scanResponse);
                    await extensionContext.globalState.update("scanResults", scanResults);

                    // Format and display results
                    const formattedResults = scanResults
                        .map((result, index) => {
                            // Don't add number to summary line
                            if (index === 0) {
                                return result;
                            }
                            return `${index}. ${result}`;
                        })
                        .join("\n\n");

                    stream.markdown(`\n# Accessibility Scan Results\n\n${formattedResults}\n\n> You can ask me to fix any specific issue by mentioning its number or describing the problem.`);
                } catch (error) {
                    const errorMessage = error instanceof Error ? error.message : "unknown error";
                    stream.markdown(
                        `❌ Error during scan: ${errorMessage}\n\nPlease ensure:\n- The URL is accessible\n- Your API key is valid\n- The API server is running`
                    );
                }
                return;

            case "fix":
                if (scanResults.length === 0) {
                    stream.markdown("⚠️ No scan results available. Please provide a website URL to scan first.");
                    return;
                }

                // Get issue number from metadata or try to extract from content
                const fixIndex = intentAnalysis.metadata?.issue_number || -1;

                if (isNaN(fixIndex) || fixIndex < 0 || fixIndex >= scanResults.length) {
                    stream.markdown("⚠️ I couldn't determine which issue you want to fix. Please specify the issue number or describe the specific problem you want to fix.");
                    return;
                }

                // Get the detailed violation information
                const violation = detailedScanResults.violations[fixIndex - 1]; // Subtract 1 to account for summary line
                if (!violation) {
                    stream.markdown("⚠️ Could not find detailed information for this issue.");
                    return;
                }

                try {
                    const apiResponse = await queryAccessibilityApi(
                        apiUrl,
                        "fix",
                        apiKey,
                        `Fix this accessibility issue:  
                            Description: ${violation.help}
                            HTML Context: ${violation.html}`
                    );

                    // Validate API response
                    if (!apiResponse || typeof apiResponse !== "object") {
                        throw new Error("Invalid response received from API");
                    }

                    const formattedResponse = formatAccessibilityResponse(apiResponse as AccessibilityResponse);
                    stream.markdown(formattedResponse);
                } catch (error) {
                    const errorMessage = error instanceof Error ? error.message : "unknown error";
                    stream.markdown(`❌ Error processing fix request: ${errorMessage}`);
                }
                return;

            case "explain":
                const topic = intentAnalysis.metadata?.topic || intentAnalysis.content;
                if (!topic) {
                    stream.markdown("⚠️ Please specify what you'd like me to explain about accessibility.");
                    return;
                }
                try {
                    const apiResponse = await queryAccessibilityApi(apiUrl, "explain", apiKey, topic);

                    // Validate API response
                    if (!apiResponse || typeof apiResponse !== "object") {
                        throw new Error("Invalid response received from API");
                    }

                    const formattedResponse = formatAccessibilityResponse(apiResponse as AccessibilityResponse);
                    stream.markdown(formattedResponse);
                } catch (error) {
                    const errorMessage = error instanceof Error ? error.message : "unknown error";
                    stream.markdown(`Error processing explanation request: ${errorMessage}`);
                }
                return;
        }
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "unknown error";
        stream.markdown(`❌ An error occurred while processing your request: ${errorMessage}`);
    }
};

// This method is called when your extension is deactivated
export function deactivate() {
}
