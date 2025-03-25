from typing import List
from pinecone import QueryResponse

def calculate_average_score(matches: List[QueryResponse]) -> float:
    """Calculate the average similarity score from a list of matched vectors."""
    return sum(match.score for match in matches) / len(matches) if matches else 0 