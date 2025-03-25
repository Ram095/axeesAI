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

    switch (request.command) {
        case "scan":
            if (request.prompt === "") {
                stream.markdown("⚠️ Please specify a URL to scan. Example: `/scan https://example.com`");
                return;
            }

            // Validate URL format
            try {
                new URL(request.prompt);
            } catch (e) {
                stream.markdown("⚠️ Invalid URL format. Please provide a valid URL including the protocol (http:// or https://)");
                return;
            }

            // Show scanning message
            stream.markdown(`🔍 Scanning ${request.prompt} for accessibility issues...`);

            try {
                // Perform scan and store complete response
                const scanResponse = await performAccessibilityScan(apiUrl, apiKey, request.prompt);

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

                stream.markdown(`\n# Accessibility Scan Results\n\n${formattedResults}\n\n> To fix an issue, use \`/fix <issue number>\``);
            } catch (error) {
                const errorMessage = error instanceof Error ? error.message : "unknown error";
                stream.markdown(
                    `❌ Error during scan: ${errorMessage}\n\nPlease ensure:\n- The URL is accessible\n- Your API key is valid\n- The API server is running`
                );
            }
            return;

        case "fix":
            if (scanResults.length === 0) {
                stream.markdown("⚠️ No scan results available. Please run `/scan <url>` first.");
                return;
            }
            const fixIndex = parseInt(request.prompt, 10);
            if (isNaN(fixIndex) || fixIndex < 0 || fixIndex >= scanResults.length) {
                stream.markdown("⚠️ Invalid issue number. Please provide a valid issue number from the scan results.");
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
        default:
            if (!request.prompt) {
                stream.markdown("⚠️ Please specify an issue or guideline to explain. Example: `/explain WCAG 2.1 AA`");
                return;
            }
            try {
                const apiResponse = await queryAccessibilityApi(apiUrl, "explain", apiKey, request.prompt);

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
