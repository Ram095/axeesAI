import dspy
from typing import Dict, Any
import time
from src.rag.retriever import Retriever
from src.settings import RAGSettings
from .base_agent import BaseAgent
from src.core import BaseLogger
from src.utils.similarity_calculator import calculate_average_score
from src.logging import api_logger
import os
from contextlib import nullcontext
import mlflow
from pinecone import QueryResponse


class RetrieverModule(dspy.Module):
    """
    Retrieval module that wraps the vector db retriever for use with DSPy
    """

    def __init__(self, retriever: Retriever, k: int = 3):
        super().__init__()
        self.retriever = retriever
        self.k = k

    def forward(self, query_text: str) -> list[dspy.Prediction]:
        """Retrieve relevant context from vector store"""
        contexts = self.retriever.retrieve_context(query_text, top_k=self.k)
        return [dspy.Prediction(text=ctx['text'], score=ctx['score']) for ctx in contexts]

# Fix the InputField and OutputField definitions


class AccessibilityQuery(dspy.Signature):
    """User query about accessibility"""
    query = dspy.InputField(
        desc="The user's accessibility question or an accessibility issue description")


class AccessibilityAnswer(dspy.Signature):
    """Structured answer to an accessibility query or an issue"""
    answer = dspy.OutputField(
        desc="Direct answer to the accessibility question or solution to the issue")
    explanation = dspy.OutputField(
        desc="Detailed explanation of the answer or solution")
    guidelines = dspy.OutputField(
        desc="Relevant accessibility guidelines used to derive the answer")
    examples = dspy.OutputField(
        desc="Practical examples of implementation to solve the issue")


class AccessibilityExpertModule(dspy.Module):
    """
    DSPy module for answering accessibility questions using RAG
    """

    def __init__(self, retriever_module: RetrieverModule, logger: BaseLogger, lm: Any = None):
        super().__init__()
        self.retriever = retriever_module
        self.logger = logger
        self.lm = lm
        self.generate_answer = self._setup_chain_of_thought()

    def _setup_chain_of_thought(self) -> dspy.ChainOfThought:
        """Set up the chain of thought prompt template"""
        template = """You are an expert web accessibility consultant with deep knowledge of WCAG guidelines, 
        ARIA patterns, and accessibility best practices.

        Role: Web Accessibility Expert

        Let's approach this step by step:
        1. Check if the query is a question or an issue description
        2. If it's a question, answer it based on the relevant context provided
        3. If it's an issue description, analyze the issue from the query, consider the target HTML provided, and formulate a clear solution based on best practices
        4. Explain the reasoning behind the solution
        5. Reference specific guidelines
        6. Provide concrete implementation examples specific to the issue and target HTML provided
        
        Context information:
        {context}
        
        User query:
        {query}
        
        Let's think through this systematically to provide a comprehensive response.

        Answer: Provide a clear, direct solution or answer.
        
        Explanation: Explain the reasoning and importance of fixing this issue include context of the issue and the target HTML. If it's a question, explain the reasoning and importance of the answer.
        
        Guidelines: List relevant WCAG guidelines and standards.
        
        Examples: Show practical implementation examples.
        """

        # Create the chain of thought with explicit signature mapping
        cot = dspy.ChainOfThought(
            signature="query, context -> answer, explanation, guidelines, examples")

        # Set the prompt template using DSPy's templating
        cot.prompt = template

        # Configure generation parameters
        cot.temperature = 0.3
        cot.max_tokens = 1024
        return cot

    def forward(self, query: str, mlflow_session=None) -> tuple[Dict[str, str], list[QueryResponse]]:
        """Generate an accessibility answer using retrieved context"""
        # First retrieve relevant context
        api_logger.info(f"Retrieving context for query: {query}")
        start_time = time.time()
        contexts = self.retriever(query)
        context_text = "\n\n".join([c.text for c in contexts])

        # Use nested session if provided, otherwise use current session
        if mlflow_session:
            context_manager = mlflow_session
        else:
            # Don't create a new session if we're not provided one
            context_manager = nullcontext()

        with context_manager:
            try:
                self.logger.log_parameters(
                    {"query": query, "context": context_text})
                self.logger.log_metrics(
                    {"context_retrieval_time": round(time.time() - start_time, 3)})

                # Calculate average context relevance score
                avg_context_similarity_score = calculate_average_score(
                    contexts)
                self.logger.log_metrics(
                    {"context_relevance_score": round(avg_context_similarity_score, 3)})

                # Generate answer using query and context
                api_logger.info("Generating answer with context")
                generated = self.generate_answer(
                    query=query,
                    context=context_text
                )

                # Ensure all fields are present and properly formatted
                result = {
                    "answer": str(generated.answer).strip() if hasattr(generated, 'answer') and generated.answer else "",
                    "explanation": str(generated.explanation).strip() if hasattr(generated, 'explanation') and generated.explanation else "",
                    "guidelines": str(generated.guidelines).strip() if hasattr(generated, 'guidelines') and generated.guidelines else "",
                    "examples": str(generated.examples).strip() if hasattr(generated, 'examples') and generated.examples else ""
                }

                # Log the raw response for debugging
                api_logger.info(f"Generated response: {result}")

                # Log parameters and LM usage
                self.logger.log_parameters(result)

                if self.lm and hasattr(self.lm, 'history'):
                    self.logger.log_lm_usage(self.lm.history)

                return result, contexts
            except Exception as e:
                api_logger.error(f"Error generating answer: {str(e)}")
                raise ValueError(f"Failed to generate answer: {str(e)}")


class AccessibilityExpertAgent(BaseAgent):
    """
    Agent that answers accessibility questions using RAG and DSPy
    """

    def __init__(self, api_key: str | None = None):
        api_logger.info("Initializing AccessibilityExpertAgent")
        try:
            # Configure RAG
            api_logger.info("Creating RAGSettings instance")
            rag_config = RAGSettings()
            if not api_key:
                api_logger.info(
                    "No API key provided, using RAGSettings defaults")
                api_key = rag_config.openai_api_key
            else:
                api_logger.info("Overriding OpenAI API key with provided key")
                rag_config.openai_api_key = api_key

            # Initialize base agent first
            super().__init__(api_key=api_key)

            api_logger.info(
                "RAGSettings initialized with OpenAI key: present, Pinecone key: present")

            # Initialize retriever with config
            self.retriever = Retriever(rag_config)
            self.expert_module = AccessibilityExpertModule(
                RetrieverModule(self.retriever),
                self.logger,
                self.lm
            )

            api_logger.info(
                "AccessibilityExpertAgent initialized successfully")
        except Exception as e:
            api_logger.error(
                f"Failed to initialize AccessibilityExpertAgent: {str(e)}")
            raise ValueError(f"Failed to initialize agent: {str(e)}")

    def answer_query(self, query: str) -> tuple[Dict[str, str], list[QueryResponse]]:
        """Process an accessibility query and return structured response"""
        api_logger.info(f"Processing query: {query}")
        try:
            # Track execution with a single session
            def _execute_query(session):
                result, contexts = self.expert_module.forward(
                    query, mlflow_session=session)
                return result, contexts

            # Use a single session for the entire query processing
            result, contexts = self._track_execution(
                "accessibility_expert_agent_query", lambda: _execute_query(mlflow.active_run()))

            # Validate the response
            if not all(key in result for key in ['answer', 'explanation', 'guidelines', 'examples']):
                raise ValueError("Incomplete response from expert module")

            return result, contexts
        except Exception as e:
            api_logger.error(f"Error processing query: {str(e)}")
            raise ValueError(f"Failed to process query: {str(e)}")


def main():
    """CLI interface for the accessibility expert agent"""
    import argparse

    parser = argparse.ArgumentParser(description='Accessibility Expert Agent')
    parser.add_argument('--query', type=str,
                        help='Your accessibility question or issue description')

    args = parser.parse_args()

    try:
        print(f"Initializing Accessibility Expert Agent...")
        agent = AccessibilityExpertAgent()

        print(f"Processing query: '{args.query}'")
        result, contexts = agent.answer_query(args.query)

        print("\n=== Accessibility Expert Answer ===\n")
        print(f"Answer: {result['answer']}\n")
        print(f"Explanation: {result['explanation']}\n")
        print(f"Guidelines: {result['guidelines']}\n")
        print(f"Examples: {result['examples']}")
        print(f"Contexts: {contexts}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
