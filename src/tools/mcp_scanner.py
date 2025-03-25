from typing import Dict, Any, Optional
import asyncio
from playwright.async_api import async_playwright
import logging
import json
from urllib.parse import urlparse
import sys
import os

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [mcp_scanner] - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mcp_scanner')

class MCPScanError(Exception):
    """Custom exception for MCP scan errors"""
    pass

class MCPScanner:
    """Scanner class using Playwright for accessibility testing"""
    
    def __init__(self):
        self.logger = logger

    async def validate_url(self, url: str) -> bool:
        """Validate if the provided URL is well-formed"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    async def scan_for_accessibility(self, url: str) -> Dict[str, Any]:
        """
        Scan a URL for accessibility issues using Playwright
        
        Args:
            url: The URL to scan
            
        Returns:
            Dict containing the scan results with violations categorized by severity
        """
        if not await self.validate_url(url):
            raise MCPScanError(f"Invalid URL format: {url}")
        
        self.logger.info(f"[mcp_scanner] Starting accessibility scan for URL: {url}")
        
        try:
            async with async_playwright() as playwright:
                # Launch browser directly instead of connecting via WebSocket
                browser = await playwright.chromium.launch(headless=True)
                
                try:
                    context = await browser.new_context()
                    page = await context.new_page()
                    
                    # Set a longer timeout for navigation
                    page.set_default_timeout(120000)
                    
                    try:
                        self.logger.info(f"[mcp_scanner] Navigating to URL: {url}")
                        await page.goto(url, wait_until="domcontentloaded")
                        self.logger.info("[mcp_scanner] Page loaded successfully")
                        
                        # Execute accessibility scan
                        violations = await self._execute_accessibility_scan(page)
                        
                        # Process and categorize results
                        categorized_results = await self._process_scan_results(violations)
                        
                        self.logger.info(f"[mcp_scanner] Scan completed successfully for {url}")
                        return {
                            'url': url,
                            'scan_result': categorized_results['summary'],
                            'raw_violations': categorized_results['violations']
                        }
                        
                    except Exception as e:
                        raise MCPScanError(f"Failed to scan page: {str(e)}")
                    finally:
                        await context.close()
                finally:
                    await browser.close()
                    
        except Exception as e:
            self.logger.error(f"[mcp_scanner] Scan failed: {str(e)}")
            raise MCPScanError(f"Scan failed: {str(e)}")

    async def _execute_accessibility_scan(self, page) -> list:
        """Execute accessibility scan using Playwright's accessibility features"""
        try:
            # Execute accessibility audit using Playwright's built-in accessibility features
            snapshot = await page.accessibility.snapshot()
            
            # Get all elements for manual checking
            elements = await page.evaluate("""() => {
                const violations = [];
                
                // Check for images without alt text
                document.querySelectorAll('img').forEach(img => {
                    if (!img.hasAttribute('alt')) {
                        violations.push({
                            type: 'missing-alt',
                            impact: 'critical',
                            element: img.outerHTML,
                            help: 'Images must have alt text',
                            helpUrl: 'https://www.w3.org/WAI/tutorials/images/'
                        });
                    }
                });
                
                // Check for form controls without labels
                document.querySelectorAll('input, select, textarea').forEach(control => {
                    if (!control.hasAttribute('aria-label') && 
                        !control.hasAttribute('aria-labelledby') &&
                        !document.querySelector(`label[for="${control.id}"]`)) {
                        violations.push({
                            type: 'missing-label',
                            impact: 'serious',
                            element: control.outerHTML,
                            help: 'Form controls must have labels',
                            helpUrl: 'https://www.w3.org/WAI/tutorials/forms/labels/'
                        });
                    }
                });
                
                // Check for buttons without accessible names
                document.querySelectorAll('button').forEach(button => {
                    if (!button.textContent.trim() && 
                        !button.hasAttribute('aria-label') && 
                        !button.hasAttribute('aria-labelledby')) {
                        violations.push({
                            type: 'button-name',
                            impact: 'serious',
                            element: button.outerHTML,
                            help: 'Buttons must have accessible names',
                            helpUrl: 'https://www.w3.org/WAI/WCAG21/Understanding/name-role-value'
                        });
                    }
                });
                
                return violations;
            }""")
            
            return elements
            
        except Exception as e:
            self.logger.error(f"[mcp_scanner] Error during accessibility scan: {str(e)}")
            raise MCPScanError(f"Error during accessibility scan: {str(e)}")

    async def _process_scan_results(self, violations: list) -> Dict[str, Any]:
        """Process and categorize scan results"""
        try:
            categorized = {
                'critical': [],
                'serious': [],
                'moderate': [],
                'minor': []
            }
            
            for violation in violations:
                impact = violation.get('impact', 'moderate')
                if impact in categorized:
                    categorized[impact].append({
                        'id': violation.get('type'),
                        'help': violation.get('help'),
                        'helpUrl': violation.get('helpUrl'),
                        'html': violation.get('element')
                    })
            
            total_violations = sum(len(v) for v in categorized.values())
            summary = f"Found {total_violations} accessibility violations"
            if total_violations > 0:
                summary += f" ({len(categorized['critical'])} critical, "
                summary += f"{len(categorized['serious'])} serious, "
                summary += f"{len(categorized['moderate'])} moderate, "
                summary += f"{len(categorized['minor'])} minor)"
            
            return {
                'summary': summary,
                'violations': categorized
            }
            
        except Exception as e:
            self.logger.error(f"[mcp_scanner] Error processing scan results: {str(e)}")
            raise MCPScanError(f"Error processing scan results: {str(e)}")

# Example usage
async def main():
    scanner = MCPScanner()
    try:
        results = await scanner.scan_for_accessibility("https://example.com")
        print(json.dumps(results, indent=2))
    except MCPScanError as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 