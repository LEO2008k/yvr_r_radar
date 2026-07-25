from abc import ABC, abstractmethod
from typing import List, Dict

class BaseScraper(ABC):
    @abstractmethod
    def scrape(self) -> List[Dict]:
        """
        Should return a list of events.
        Each event is a dictionary containing:
        - title: str
        - time: str
        - lat: float
        - lng: float
        - address: str
        - source: str
        """
        pass
