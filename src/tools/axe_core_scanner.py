from typing import Dict, Any
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import json
from urllib.parse import urlparse
import os
import subprocess
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('axe-core-scanner')

# Try to import from package first, fall back to direct import for standalone usage
try:
    from src.logging import api_logger
except ImportError:
    api_logger = logger

class ScanError(Exception):
    """Custom exception for scan errors"""
    pass

def ensure_playwright_browsers():
    """Ensure Playwright browsers are installed"""
    try:
        logger.info("Checking Playwright browser installation")
        result = subprocess.run(['playwright', 'install', 'chromium'], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0:
            logger.info("Playwright browsers are installed")
        else:
            logger.error(f"Failed to install browsers: {result.stderr}")
            raise ScanError("Failed to install Playwright browsers")
    except FileNotFoundError:
        logger.error("Playwright CLI not found. Please ensure playwright is installed: 'pip install playwright'")
        raise ScanError("Playwright CLI not found")
    except Exception as e:
        logger.error(f"Error checking/installing browsers: {str(e)}")
        raise ScanError(f"Error checking/installing browsers: {str(e)}")

def validate_url(url: str) -> bool:
    """Validate if the provided URL is well-formed"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def _process_axe_results(violations: list) -> Dict[str, Any]:
    """
    Process and categorize axe-core scan results.
    
    Args:
        violations: Raw violations from axe-core scan
        
    Returns:
        Dict containing categorized violations and summary
    """
    try:
        # Categorize violations by impact
        categorized_violations = {
            'critical': [],
            'serious': [],
            'moderate': [],
            'minor': []
        }
        
        # If no violations, return empty categories
        if not violations:
            return categorized_violations, "No accessibility violations found"
        
        for violation in violations:
            # Default to moderate if impact is not specified
            impact = violation.get('impact', 'moderate')
            issue = {
                'id': violation.get('id'),
                'description': violation.get('description'),
                'help': violation.get('help'),
                'helpUrl': violation.get('helpUrl'),
                'nodes': len(violation.get('nodes', [])),
                'html': violation.get('nodes', [{}])[0].get('html', '') if violation.get('nodes') else ''
            }
            categorized_violations[impact].append(issue)
        
        # Create summary
        total_violations = sum(len(v) for v in categorized_violations.values())
        summary = f"Found {total_violations} accessibility violations"
        if total_violations > 0:
            summary += f" ({len(categorized_violations['critical'])} critical, "
            summary += f"{len(categorized_violations['serious'])} serious, "
            summary += f"{len(categorized_violations['moderate'])} moderate, "
            summary += f"{len(categorized_violations['minor'])} minor)"
        
        logger.info(f"Scan summary: {summary}")
        return categorized_violations, summary
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to process scan results: {error_msg}")
        raise ScanError(f"Failed to process scan results: {error_msg}")

def get_axe_violations(url: str) -> Dict[str, Any]:
    """
    Scan a URL for accessibility violations using axe-core.
    
    Args:
        url: The URL to scan
        
    Returns:
        Dict containing the scan results with violations categorized by severity
    """
    if not validate_url(url):
        raise ScanError(f"Invalid URL format: {url}")
    
    logger.info(f"Starting accessibility scan for URL: {url}")
    
    # Ensure browsers are installed
    ensure_playwright_browsers()
    
    try:
        logger.info("Initializing Playwright")
        playwright = sync_playwright().start()
        logger.info("Playwright initialized successfully")
        
        try:
            logger.info("Launching browser")
            browser = playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox']
            )
            logger.info("Browser launched successfully")
            
            try:
                context = browser.new_context()
                page = context.new_page()
                
                # Set a longer timeout for navigation
                page.set_default_navigation_timeout(120000)
                
                try:
                    logger.info(f"Navigating to URL: {url}")
                    page.goto(url, wait_until="domcontentloaded")
                    logger.info("Page loaded successfully")
                    
                    # Load axe-core from local file
                    axe_script_path = os.path.join(os.path.dirname(__file__), "axe.min.js")
                    logger.info(f"Loading axe-core script from: {axe_script_path}")
                    
                    with open(axe_script_path, "r", encoding="utf-8") as f:
                        axe_script = f.read()
                        page.evaluate(axe_script)
                        logger.info("axe-core script injected successfully")
                        
                        # Run the accessibility scan
                        logger.info("Running accessibility scan")
                        result = page.evaluate("async () => { return await axe.run(); }")
                        logger.info("Scan completed successfully")
                        
                        # Parse the result if it's a string
                        if isinstance(result, str):
                            result = json.loads(result)
                        
                        # Handle case where no violations are found
                        violations = result.get("violations", [])
                        if not violations:
                            logger.info("No accessibility violations found")
                            return {
                                'url': url,
                                'scan_result': "No accessibility violations found",
                                'raw_violations': {
                                    'critical': [],
                                    'serious': [],
                                    'moderate': [],
                                    'minor': []
                                }
                            }
                        
                        categorized_violations, summary = _process_axe_results(violations)
                        logger.info(f"Scanned {url} and found {summary}")
                        return {
                            'url': url,
                            'scan_result': summary,
                            'raw_violations': categorized_violations
                        }
                        
                except PlaywrightTimeout:
                    raise ScanError(f"Timeout while loading page: {url}")
                except Exception as e:
                    raise ScanError(f"Failed to scan page: {str(e)}")
                finally:
                    logger.info("Cleaning up context")
                    context.close()
            finally:
                logger.info("Cleaning up browser")
                browser.close()
        finally:
            logger.info("Cleaning up Playwright")
            playwright.stop()
                    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Scan failed: {error_msg}")
        raise ScanError(f"Scan failed: {error_msg}")

if __name__ == "__main__":
    import argparse
    import json
    
    # Add the parent directory to sys.path to allow running from any location
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.insert(0, root_dir)
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run accessibility scan on a URL')
    parser.add_argument('url', help='URL to scan (e.g., https://example.com)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    try:
        # Run the scan
        print(f"\nStarting accessibility scan for: {args.url}")
        print("=" * 50)
        
        result = get_axe_violations(args.url)
        
        # Print results in a readable format
        print("\nScan Results:")
        print("=" * 50)
        print(f"\n{result['scan_result']}\n")
        
        if args.debug:
            print("\nDetailed Violations:")
            print("=" * 50)
            for severity, issues in result['raw_violations'].items():
                if issues:
                    print(f"\n{severity.upper()} Issues:")
                    for issue in issues:
                        print(f"\n- ID: {issue['id']}")
                        print(f"  Description: {issue['description']}")
                        print(f"  Help: {issue['help']}")
                        print(f"  Help URL: {issue['helpUrl']}")
                        print(f"  Affected Elements: {issue['nodes']}")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        if args.debug:
            import traceback
            print("\nStacktrace:")
            traceback.print_exc()
        exit(1)

"""
Tools package for AxessAI.
Contains utility tools and scanners for accessibility testing.
"""

from .axe_core_scanner import get_axe_violations, ScanError, _process_axe_results

__all__ = ['get_axe_violations', 'ScanError', '_process_axe_results'] 