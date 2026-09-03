from abc import ABC, abstractmethod
from pydantic import BaseModel

class DocumentData(BaseModel):
    """
    Represents the data of a document.
    """
    doc_id: str
    filename: str
    content: str
    metadata: dict

class ECMAdapter(ABC):
    """
    Abstract base class for ECM (Enterprise Content Management) adapters.
    """

    @abstractmethod
    def fetch_document(self, doc_id: str) -> DocumentData:
        """
        Fetches a document by its ID.

        Args:
            doc_id (str): The ID of the document to fetch.

        Returns:
            DocumentData: The fetched document data.
        """
        pass