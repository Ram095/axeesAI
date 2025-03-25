"""
Script to demonstrate basic RAG evaluation using Ragas.
"""
from src.evaluation.evaluator import RagasEvaluator
from src.agents.accessibility_expert_agent import AccessibilityExpertAgent

def main():
    agent = AccessibilityExpertAgent()
    evaluator = RagasEvaluator(agent)
    # Generate answers and contexts using RAG system
    dataset = evaluator.get_responses_from_agent('src/evaluation/dataset/eval_dataset.json')
    results = evaluator.evaluate_rag(dataset)

    print("Evaluation completed")
    print("\nResults:")
    for metric, score in results.items():
        print(f"{metric}: {score:.4f}")

if __name__ == "__main__":
    main()
