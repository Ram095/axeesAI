import * as vscode from "vscode";
import { initializeExtension } from "./config";
import { queryAccessibilityApi, performAccessibilityScan } from "./api-client";
import { formatScanResults, formatAccessibilityResponse, extractDetailedScanResults } from "./formatters";
import { ScanResponse, DetailedScanResults, AccessibilityResponse } from "./types";

let extensionContext: vscode.ExtensionContext;

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
    extensionContext = context;
    initializeExtension(context);

    const axess_ai_chat_participant = vscode.chat.createChatParticipant("vscode-axessai-chat", handler);
    context.subscriptions.push(axess_ai_chat_participant);
}

// Function to detect intent from user query
function detectIntent(query: string): { command: string; content: string } {
    query = query.toLowerCase().trim();

    // Check for URL pattern to detect scan intent
    const urlPattern = /https?:\/\/[^\s]+/;
    if (urlPattern.test(query)) {
        return { command: "scan", content: query.match(urlPattern)![0] };
    }

    // Check for fix intent - typically mentions issue numbers or fixing something
    if (query.match(/fix|issue|problem|error|violation|#\d+|\b\d+\b/)) {
        return { command: "fix", content: query };
    }

    // Default to explain for all other queries
    return { command: "explain", content: query };
}

// Handle chat requests
const handler: vscode.ChatRequestHandler = async (
    request: vscode.ChatRequest,
    context: vscode.ChatContext,
    stream: vscode.ChatResponseStream,
    token: vscode.CancellationToken
) => {
    const userQuery = request.prompt.trim();
    const chatModels = await vscode.lm.selectChatModels({ family: "gpt-4" });

    // Retrieve scan results from context state
    let scanResults: string[] = extensionContext.globalState.get<string[]>("scanResults", []);
    let detailedScanResults: DetailedScanResults = extensionContext.globalState.get<DetailedScanResults>("detailedScanResults", {
        summary: "",
        violations: []
    });
    const apiUrl = extensionContext.globalState.get<string>("apiUrl", "");
    const apiKey = extensionContext.globalState.get<string>("apiKey", "");

    // Detect intent from user query
    const { command, content } = detectIntent(userQuery);

    switch (command) {
        case "scan":
            if (!content) {
                stream.markdown("⚠️ Please provide a valid URL to scan. Example: `https://example.com`");
                return;
            }

            // Validate URL format
            try {
                new URL(content);
            } catch (e) {
                stream.markdown("⚠️ Invalid URL format. Please provide a valid URL including the protocol (http:// or https://)");
                return;
            }

            // Show scanning message
            stream.markdown(`🔍 Scanning ${content} for accessibility issues...`);

            try {
                // Perform scan and store complete response
                const scanResponse = await performAccessibilityScan(apiUrl, apiKey, content);

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

                stream.markdown(
                    `\n# Accessibility Scan Results\n\n${formattedResults}\n\n> To fix an issue, mention the issue number or describe the problem you want to fix.`
                );
            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : "unknown error";
                stream.markdown(
                    `❌ Error during scan: ${errorMessage}\n\nPlease ensure:\n- The URL is accessible\n- Your API key is valid\n- The API server is running`
                );
            }
            return;

        case "fix":
            if (scanResults.length === 0) {
                stream.markdown("⚠️ No scan results available. Please scan a URL first by providing a website URL.");
                return;
            }

            // Extract issue number if present in the query
            const issueMatch = content.match(/\b(\d+)\b/);
            const fixIndex = issueMatch ? parseInt(issueMatch[1], 10) : -1;

            if (isNaN(fixIndex) || fixIndex < 0 || fixIndex >= scanResults.length) {
                stream.markdown("⚠️ Please specify a valid issue number from the scan results, or describe the issue you want to fix.");
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
            if (!content) {
                stream.markdown("⚠️ Please specify what you'd like me to explain about accessibility.");
                return;
            }

            try {
                const apiResponse = await queryAccessibilityApi(apiUrl, "explain", apiKey, content);

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
};

// This method is called when your extension is deactivated
export function deactivate() {}
