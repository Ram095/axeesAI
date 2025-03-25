from typing import Dict, List, Optional, TypedDict, Literal
import json
import re
import os
import logging
from openai import OpenAI

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class IntentMetadata(TypedDict, total=False):
    url: Optional[str]
    issue_number: Optional[int]
    topic: Optional[str]

class IntentAnalysisResult(TypedDict):
    command: Literal['scan', 'fix', 'explain']
    content: str
    confidence: float
    metadata: IntentMetadata

class IntentAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the intent analyzer with OpenAI API key."""
        self.logger = logging.getLogger("IntentAnalyzer")
        self.logger.info("Initializing IntentAnalyzer")
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            self.logger.error("OpenAI API key not provided")
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=self.api_key)
        self.logger.info("IntentAnalyzer initialization complete")

    async def analyze_intent(
        self,
        query: str,
        context: Optional[Dict[str, List[str]]] = None
    ) -> IntentAnalysisResult:
        """
        Analyze user intent using OpenAI to determine the most likely command and extract relevant information.
        
        Args:
            query: The user's query string
            context: Optional context containing scan_results and previous_commands
        
        Returns:
            IntentAnalysisResult containing the detected command, content, confidence, and metadata
        """
        self.logger.info(f"Starting intent analysis for query: '{query}'")
        
        if context:
            self.logger.debug(f"Context provided: {context}")
        
        try:
            # Prepare the prompt
            self.logger.debug("Preparing prompt for OpenAI")
            system_prompt = """You are an intent analyzer for an accessibility testing tool. 
            Analyze user queries and determine their intent among:
            - scan: User wants to scan a URL for accessibility issues
            - fix: User wants to fix a specific accessibility issue
            - explain: User wants to understand an accessibility concept or guideline
            
            Respond in JSON format with:
            {
                "command": "scan|fix|explain",
                "content": "processed user query",
                "confidence": 0.0-1.0,
                "metadata": {
                    "url": "extracted URL if present",
                    "issue_number": "extracted issue number if present",
                    "topic": "main accessibility topic if present"
                }
            }"""

            # Build the user message with context
            user_message = f"User Query: {query}\n"
            if context:
                if context.get('scan_results'):
                    user_message += f"\nContext - Previous scan results available with {len(context['scan_results'])} issues"
                    self.logger.debug(f"Added context with {len(context['scan_results'])} scan results")
                if context.get('previous_commands'):
                    user_message += f"\nContext - Previous commands: {', '.join(context['previous_commands'])}"
                    self.logger.debug(f"Added context with previous commands: {context['previous_commands']}")

            # Call OpenAI API
            self.logger.info("Calling OpenAI API")
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                max_tokens=150    # Limit response size since we only need the JSON
            )
            self.logger.debug("Received response from OpenAI API")

            # Parse the response
            self.logger.debug(f"Raw response content: {response.choices[0].message.content}")
            result = json.loads(response.choices[0].message.content)
            self.logger.debug(f"Parsed JSON result: {result}")
            
            # Validate and clean up the response
            cleaned_result = {
                "command": result["command"],
                "content": result.get("content", query),
                "confidence": result.get("confidence", 0.7),
                "metadata": {
                    "url": result.get("metadata", {}).get("url"),
                    "issue_number": int(result["metadata"]["issue_number"]) if result.get("metadata", {}).get("issue_number") else None,
                    "topic": result.get("metadata", {}).get("topic")
                }
            }
            
            self.logger.info(f"Analysis complete. Detected command: {cleaned_result['command']} with confidence: {cleaned_result['confidence']}")
            return cleaned_result

        except Exception as e:
            self.logger.error(f"AI intent analysis failed: {str(e)}", exc_info=True)
            self.logger.info("Falling back to basic intent detection")
            # Fallback to basic intent detection
            return self._fallback_intent_analysis(query)

    def _fallback_intent_analysis(self, query: str) -> IntentAnalysisResult:
        """Fallback intent detection in case AI analysis fails."""
        self.logger.info("Using fallback intent analysis")
        query = query.lower().strip()
        
        # URL pattern for scan detection
        url_pattern = r'https?://[^\s]+'
        url_match = re.search(url_pattern, query)
        if url_match:
            self.logger.info(f"Fallback detected 'scan' intent with URL: {url_match.group(0)}")
            return {
                "command": "scan",
                "content": query,
                "confidence": 0.8,
                "metadata": {
                    "url": url_match.group(0),
                    "issue_number": None,
                    "topic": None
                }
            }

        # Fix intent detection
        issue_match = re.search(r'(?:fix|issue|problem|error|violation|#?)(\d+)', query)
        if issue_match or any(word in query for word in ['fix', 'repair', 'solve', 'resolve']):
            issue_num = int(issue_match.group(1)) if issue_match else None
            self.logger.info(f"Fallback detected 'fix' intent with issue number: {issue_num}")
            return {
                "command": "fix",
                "content": query,
                "confidence": 0.7,
                "metadata": {
                    "url": None,
                    "issue_number": issue_num,
                    "topic": None
                }
            }

        # Default to explain
        self.logger.info(f"Fallback defaulting to 'explain' intent with topic: {query}")
        return {
            "command": "explain",
            "content": query,
            "confidence": 0.6,
            "metadata": {
                "url": None,
                "issue_number": None,
                "topic": query
            }
        }