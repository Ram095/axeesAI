import * as vscode from "vscode";
import { initializeExtension } from "./config";
import { queryAccessibilityApi, performAccessibilityScan, analyzeIntent } from "./api-client";
import { formatScanResults, formatAccessibilityResponse, extractDetailedScanResults } from "./formatters";
import { ScanResponse, DetailedScanResults, AccessibilityResponse } from "./types";

let extensionContext: vscode.ExtensionContext;
let outputChannel: vscode.OutputChannel;

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
    extensionContext = context;
    initializeExtension(context);

    // Create output channel for logging
    outputChannel = vscode.window.createOutputChannel("AxessAI");
    context.subscriptions.push(outputChannel);

    outputChannel.appendLine("AxessAI Extension Activated");

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
    outputChannel.appendLine(`\n[${new Date().toISOString()}] [intent_analyser] Processing user query: "${userQuery}"`);
    
    // Retrieve scan results from context state
    let scanResults: string[] = extensionContext.globalState.get<string[]>("scanResults", []);
    let detailedScanResults: DetailedScanResults = extensionContext.globalState.get<DetailedScanResults>("detailedScanResults", {
        summary: "",
        violations: []
    });
    const apiUrl = extensionContext.globalState.get<string>("apiUrl", "");
    const apiKey = extensionContext.globalState.get<string>("apiKey", "");

    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Context loaded - Previous scan results: ${scanResults.length}`);

    // Get previous commands for context
    const previousCommands = extensionContext.globalState.get<string[]>("previousCommands", []);
    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Previous commands loaded: ${previousCommands.length}`);

    try {
        outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Starting intent analysis...`);
        // Analyze intent using API
        const intentAnalysis = await analyzeIntent(apiUrl, apiKey, userQuery, {
            scan_results: scanResults,
            previous_commands: previousCommands.slice(-5) // Last 5 commands for context
        });

        outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Intent analysis result:
    Command: ${intentAnalysis.command}
    Confidence: ${intentAnalysis.confidence}
    Content: ${intentAnalysis.content}
    Metadata: ${JSON.stringify(intentAnalysis.metadata, null, 2)}`);

        // Store the command in history
        previousCommands.push(intentAnalysis.command);
        await extensionContext.globalState.update("previousCommands", previousCommands.slice(-10)); // Keep last 10 commands
        outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Command history updated`);

        switch (intentAnalysis.command) {
            case "scan":
                outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Processing SCAN command`);
                const url = intentAnalysis.metadata?.url || intentAnalysis.content;
                if (!url) {
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Error: No URL provided`);
                    stream.markdown("⚠️ Please provide a valid URL to scan. Example: `https://example.com`");
                    return;
                }

                // Validate URL format
                try {
                    new URL(url);
                } catch (e) {
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Error: Invalid URL format - ${url}`);
                    stream.markdown("⚠️ Invalid URL format. Please provide a valid URL including the protocol (http:// or https://)");
                    return;
                }

                // Show scanning message
                outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Starting scan for URL: ${url}`);
                stream.markdown(`🔍 Scanning ${url} for accessibility issues...`);

                try {
                    // Perform scan and store complete response
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Calling accessibility scan API`);
                    const scanResponse = await performAccessibilityScan(apiUrl, apiKey, url);

                    // Extract and store detailed results
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Processing scan results`);
                    detailedScanResults = extractDetailedScanResults(scanResponse);
                    await extensionContext.globalState.update("detailedScanResults", detailedScanResults);

                    // Format results for display
                    scanResults = formatScanResults(scanResponse);
                    await extensionContext.globalState.update("scanResults", scanResults);
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Scan results stored - ${scanResults.length} items`);

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

                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Displaying scan results to user`);
                    stream.markdown(`\n# Accessibility Scan Results\n\n${formattedResults}\n\n> You can ask me to fix any specific issue by mentioning its number or describing the problem.`);
                } catch (error) {
                    const errorMessage = error instanceof Error ? error.message : "unknown error";
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Scan error: ${errorMessage}`);
                    stream.markdown(
                        `❌ Error during scan: ${errorMessage}\n\nPlease ensure:\n- The URL is accessible\n- Your API key is valid\n- The API server is running`
                    );
                }
                return;

            case "fix":
                outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Processing FIX command`);
                if (scanResults.length === 0) {
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Error: No scan results available`);
                    stream.markdown("⚠️ No scan results available. Please provide a website URL to scan first.");
                    return;
                }

                // Get issue number from metadata or try to extract from content
                const fixIndex = intentAnalysis.metadata?.issue_number || -1;
                outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Attempting to fix issue #${fixIndex}`);

                if (isNaN(fixIndex) || fixIndex < 0 || fixIndex >= scanResults.length) {
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Error: Invalid issue number ${fixIndex}`);
                    stream.markdown("⚠️ I couldn't determine which issue you want to fix. Please specify the issue number or describe the specific problem you want to fix.");
                    return;
                }

                // Get the detailed violation information
                const violation = detailedScanResults.violations[fixIndex - 1]; // Subtract 1 to account for summary line
                if (!violation) {
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Error: No detailed information found for issue #${fixIndex}`);
                    stream.markdown("⚠️ Could not find detailed information for this issue.");
                    return;
                }

                try {
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Requesting fix for issue: ${violation.help}`);
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
                        outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Error: Invalid API response format`);
                        throw new Error("Invalid response received from API");
                    }

                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Fix solution received from API`);
                    const formattedResponse = formatAccessibilityResponse(apiResponse as AccessibilityResponse);
                    stream.markdown(formattedResponse);
                } catch (error) {
                    const errorMessage = error instanceof Error ? error.message : "unknown error";
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Fix error: ${errorMessage}`);
                    stream.markdown(`❌ Error processing fix request: ${errorMessage}`);
                }
                return;

            case "explain":
                outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Processing EXPLAIN command`);
                const topic = intentAnalysis.metadata?.topic || intentAnalysis.content;
                if (!topic) {
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Error: No topic provided for explanation`);
                    stream.markdown("⚠️ Please specify what you'd like me to explain about accessibility.");
                    return;
                }
                try {
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Requesting explanation for topic: ${topic}`);
                    const apiResponse = await queryAccessibilityApi(apiUrl, "explain", apiKey, topic);

                    // Validate API response
                    if (!apiResponse || typeof apiResponse !== "object") {
                        outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Error: Invalid API response format`);
                        throw new Error("Invalid response received from API");
                    }

                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Explanation received from API`);
                    const formattedResponse = formatAccessibilityResponse(apiResponse as AccessibilityResponse);
                    stream.markdown(formattedResponse);
                } catch (error) {
                    const errorMessage = error instanceof Error ? error.message : "unknown error";
                    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] Explanation error: ${errorMessage}`);
                    stream.markdown(`Error processing explanation request: ${errorMessage}`);
                }
                return;
        }
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "unknown error";
        outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] General error: ${errorMessage}`);
        stream.markdown(`❌ An error occurred while processing your request: ${errorMessage}`);
    }
};

// This method is called when your extension is deactivated
export function deactivate() {
    outputChannel.appendLine(`[${new Date().toISOString()}] [intent_analyser] AxessAI Extension Deactivated`);
    outputChannel.dispose();
}
