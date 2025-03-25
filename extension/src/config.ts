import * as vscode from "vscode";
import { checkApiHealth } from "./api-client";

export async function initializeExtension(context: vscode.ExtensionContext): Promise<void> {
    const config = vscode.workspace.getConfiguration("axessAI");
    const apiUrl = config.get<string>("apiEndPoint") || "http://localhost:8000";
    let apiKey = config.get<string>("openApiKey") || "";

    // Ask for API key if not set
    if (!apiKey) {
        vscode.window.showWarningMessage("⚠️ No API key found for Axess AI. Some features may not work.");
        const input = await vscode.window.showInputBox({
            prompt: "Please enter Open API key",
            ignoreFocusOut: true, // Prevents the input box from closing when focus is lost
            placeHolder: "sk-..."
        });

        if (input) {
            apiKey = input;
            // Save to both configuration and global state
            await config.update("openApiKey", input, vscode.ConfigurationTarget.Global);
            context.globalState.update("apiKey", input);
            vscode.window.showInformationMessage("API key saved successfully.");
        } else {
            vscode.window.showErrorMessage("No API key entered. Some features may not work.");
        }
    }

    // Update global state
    context.globalState.update("apiUrl", apiUrl);
    context.globalState.update("apiKey", apiKey);

    // Check API health
    const isHealthy = await checkApiHealth(apiUrl, context);
    if (isHealthy) {
        vscode.window.showInformationMessage("Axess AI is active!");
    } else {
        vscode.window.showErrorMessage("Axess AI could not connect to the accessibility API.");
    }
}
