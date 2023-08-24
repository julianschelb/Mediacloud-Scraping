# # ===========================================================================
# #                            Generic Parser Class
# # ===========================================================================

from abc import ABC, abstractmethod


class Parser(ABC):
    """Abstract parser class"""

    def __init__(self):
        pass

    @abstractmethod
    def extractText(self, url):
        pass
