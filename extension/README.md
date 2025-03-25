# AxessAI VS Code Extension

AxessAI is a VS Code extension that helps developers identify and fix accessibility issues in their web applications. It provides accessibility scanning, issue analysis, and guidance for making your applications more accessible.

## Features

- **Accessibility Scanning**: Scan websites for accessibility issues and get detailed reports
- **Issue Analysis**: Get specific guidance on how to fix identified accessibility issues
- **Accessibility Knowledge Base**: Query the AI with any accessibility-related questions
- **Copilot Integration**: Apply AI-generated code fixes directly to your codebase

## Requirements

- Visual Studio Code 1.60.0 or higher
- GitHub Copilot subscription (for AI-generated code fixes)
- OpenAI API Key

## Usage

1. Open VS Code and open CoPilot Chat. Type in @axessAI to interact with the agent
2. Currently it supports these commands:
    1. `/scan [url]` - Performs accessibility scanning on the supplied URL and returns formatted issues (coming soon)
    2. `/fix [issue number]` - Analyzes specific issue and returns steps to resolve with examples (coming soon)
    3. `/explain [question]` (default) - Answers any accessibility specific query.
3. Review multiple suggested fixes and code snippets (coming soon)
4. Apply fixes directly in your codebase (coming soon)
5. Optionally, request AI-generated code changes via Copilot integration (coming soon)

## Release Notes

### 2.0.0

This version contains ability to scan a static URL for accessibility issues.  
You can supply the issue number to get specific instructions and approach to resolve the same.

### 1.0.1

Initial release of AxessAI VS Code Extension with explanation capabilities using Accessibility Expert Agent.

---

**Enjoy!**
