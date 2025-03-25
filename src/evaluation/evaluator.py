"""
Main evaluator class for RAG system evaluation.
"""
import json
from typing import List, Dict, Protocol

import pandas as pd
from datasets import Dataset
from src.settings import RAGSettings
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall, answer_similarity, answer_correctness


class AgentProtocol(Protocol):
    """Protocol defining the interface for agents that can be evaluated."""
    def answer_query(self, query: str) -> Dict[str, str]:
        """Answer a query and return a dictionary with answer, explanation, guidelines, and examples."""
    
    def expert_module(self):
        """Return the expert module with a retriever method."""

class RagasEvaluator:
    """Evaluator class for RAG systems using Ragas metrics."""
    
    def __init__(self, agent: AgentProtocol):
        """
        Initialize the evaluator.
        
        Args:
            agent: Agent instance that implements the AgentProtocol
        """
        self.agent = agent
        rag_config = RAGSettings()
        self.api_key = rag_config.ragas_app_token
        

    def get_responses_from_agent(self, eval_dataset_path: str) -> Dataset:
        """
        Generate answers and contexts for all questions in the evaluation dataset.
        
        Returns:
            HuggingFace dataset with generated answers and retrieved contexts
        """
        # Read JSON file
        with open(eval_dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Convert to DataFrame
        # Create a pandas DataFrame from the questions data
        dataset = pd.DataFrame(data['questions']).rename(columns={
            'question': 'question',  # Keep original question column name
            'ground_truth': 'ground_truth'  # Keep original ground truth column name
        })

        # Extract list of questions to process
        questions = dataset['question'].tolist()

        # Initialize lists to store generated answers and retrieved contexts
        generated_answers = []
        retrieved_contexts = []

        # Process each question through the agent
        for question in questions:
            # Get answer and contexts from agent
            result, contexts = self.agent.answer_query(question)
            
            # Store the full structured response with all fields
            generated_answers.append({
                'answer': result['answer'],  # Main answer text
                'explanation': result['explanation'],  # Supporting explanation
                'guidelines': result['guidelines'],  # Relevant guidelines
                'examples': result['examples']  # Example cases
            })
            
            retrieved_contexts.append([context.text for context in contexts])

        # Extract concatenated answer text from the full responses for evaluation
        answer_texts = [
            f"{answer['answer']}\n\n{answer['explanation']}\n\n{answer['guidelines']}\n\n{answer['examples']}"
            for answer in generated_answers
        ]
        
        # Add the concatenated answer texts as a new column to the dataset
        dataset = dataset.assign(answer=answer_texts)
        dataset = dataset.assign(retrieved_contexts=retrieved_contexts)        
        dataset = Dataset.from_pandas(dataset)
        
        return dataset
    
    def evaluate_rag(self, dataset: Dataset) -> Dict[str, float]:
        """
        Evaluate RAG system performance.
        
        Args:
            answers: List of generated answers with all fields
            contexts: List of retrieved contexts
            
        Returns:
            Dict containing metric scores
        """
        # Calculate metrics
        results = evaluate(
        dataset=dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            answer_similarity,
            answer_correctness
        ]
        )        
        results.upload(dataset)
        
        # Convert results to dictionary, taking mean of scores
        return {
            'faithfulness': float(sum(results['faithfulness']) / len(results['faithfulness'])),
            'answer_relevancy': float(sum(results['answer_relevancy']) / len(results['answer_relevancy'])),
            'context_precision': float(sum(results['context_precision']) / len(results['context_precision'])),
            'context_recall': float(sum(results['context_recall']) / len(results['context_recall'])),
            "semantic_similarity": float(sum(results['semantic_similarity']) / len(results['semantic_similarity'])),
            "answer_correctness": float(sum(results['answer_correctness']) / len(results['answer_correctness']))
        }
    