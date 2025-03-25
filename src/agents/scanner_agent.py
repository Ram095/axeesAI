from typing import Dict, Any, Optional, List
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from langchain.agents import initialize_agent, AgentType
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from src.tools.axe_core_scanner import get_axe_violations, _process_axe_results
from src.agents.base_agent import BaseAgent
from src.logging import api_logger, mlflow_logger
from src.settings import RAGSettings
import mlflow

class ScannerAgent(BaseAgent):
    """Agent that scans websites for accessibility issues using axe-core"""
    
    def __init__(self, api_key: Optional[str] = None):
        api_logger.info("Initializing ScannerAgent")
        try:
            # Initialize configuration
            self.config = RAGSettings()
            
            # Use provided API key or get from config
            api_key = api_key or self.config.openai_api_key
            
            # Initialize base agent
            super().__init__(api_key=api_key)
            
            # Create thread pool for running sync code
            self.executor = ThreadPoolExecutor(max_workers=1)
            
            # Initialize tools and LangChain agent
            self.tools = self._setup_tools()
            self.scanner_agent = self._setup_scanner_agent()
            
            api_logger.info("ScannerAgent initialized successfully")
        except Exception as e:
            api_logger.error(f"Failed to initialize ScannerAgent: {str(e)}")
            raise ValueError(f"Failed to initialize agent: {str(e)}")
    
    def __del__(self):
        """Clean up resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
    
    def _find_accessibility_issues(self, url: str) -> Dict[str, Any]:
        """Find accessibility issues for a given URL and return formatted results"""
        api_logger.info(f"Scanning URL for accessibility issues: {url}")
        try:
            start_time = time.time()
            result = get_axe_violations(url)
            
            # Log scan metrics
            self.logger.log_metrics({
                "scan_time": round(time.time() - start_time, 3),
                "violation_count": len(result.get('raw_violations', []))
            })
            
            return result
        except Exception as e:
            api_logger.error(f"Error scanning URL {url}: {str(e)}")
            raise ValueError(f"Failed to scan URL: {str(e)}")
    
    def _setup_tools(self) -> list[Tool]:
        """Set up the tools for the scanner agent"""
        try:
            return [
                Tool(
                    name="AccessibilityScanner",
                    func=self._find_accessibility_issues,
                    description="Find the accessibility issues of a given URL and return formatted results"
                )
            ]
        except Exception as e:
            api_logger.error(f"Failed to setup tools: {str(e)}")
            raise ValueError(f"Failed to setup tools: {str(e)}")
    
    def _setup_scanner_agent(self) -> Any:
        """Set up the LangChain agent with tools"""
        try:
            llm = ChatOpenAI(  # TODO: check if we should be using chat open ai
                model=self.config.scanner_model,
                temperature=self.config.scanner_temperature,
                api_key=self.api_key
            )
            
            return initialize_agent(
                self.tools,
                llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, # TODO: check if we should be using zero shot react description
                verbose=True,
                handle_parsing_errors=True
            )
        except Exception as e:
            api_logger.error(f"Failed to setup scanner agent: {str(e)}")
            raise ValueError(f"Failed to setup scanner agent: {str(e)}")
    
    async def scan_url(self, url: str) -> Dict[str, Any]:
        """Scan a URL for accessibility issues and return structured response"""
        api_logger.info(f"Processing URL scan request: {url}")
        
        def _run_scan():
            """Run the scan in a separate thread"""
            try:
                result = self._find_accessibility_issues(url)
                
                # Validate the result format
                if not isinstance(result, dict):
                    raise ValueError(f"Invalid result format: expected dict, got {type(result)}")
                
                required_fields = {'url', 'scan_result', 'raw_violations'}
                missing_fields = required_fields - set(result.keys())
                if missing_fields:
                    raise ValueError(f"Missing required fields in result: {missing_fields}")
                
                return result
            except Exception as e:
                api_logger.error(f"Error during scan execution: {str(e)}")
                raise
        
        try:
            # Run the sync code in a thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(self.executor, _run_scan)
            
            return result
        except Exception as e:
            api_logger.error(f"Error processing scan: {str(e)}")
            raise ValueError(f"Failed to process scan: {str(e)}")

