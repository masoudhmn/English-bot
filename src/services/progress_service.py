"""
Progress service - handles statistics and progress tracking.
"""

from typing import Dict, Any

from src.leitner import get_user_statistics as leitner_statistics
from src.logger import setup_logger

logger = setup_logger(__name__)


async def get_user_statistics(session, user_id: int) -> Dict[str, Any]:
    """
    Get user's learning statistics.
    
    This is a wrapper around the Leitner statistics function.
    
    Args:
        session: Database session
        user_id: User ID
        
    Returns:
        Dictionary with statistics
    """
    return await leitner_statistics(session, user_id)
