import logging
import random

from langchain_core.tools import tool

from langgraph_supervisor.hosting import container

logger = container[logging.Logger]


@tool
def saving_interest_rate() -> float:
    """
    Return the saving interest rate.
    """
    rate = random.randrange(1, 8) / 10
    logger.info(f"[TOOL]: saving_interest_rate, {rate}")
    return rate


@tool
def cd_interest_rate() -> float:
    """
    Return the CD interest rate.
    """
    rate = random.randrange(1, 5) / 10
    logger.info(f"[TOOL]: cd_interest_rate, {rate}")
    return rate
