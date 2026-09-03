from .base import ECMAdapter, DocumentData

class LocalMockAdapter(ECMAdapter):
    """
    A mock implementation of the ECMAdapter for local testing.
    """

    def fetch_document(self, doc_id: str) -> DocumentData:
        """
        Fetches a mock document by its ID.

        Args:
            doc_id (str): The ID of the document to fetch.

        Returns:
            DocumentData: The fetched mock document data.
        """
        # Mock data for demonstration purposes
        return DocumentData(
            doc_id=doc_id,
            filename=f"mock_contract_{doc_id}.pdf",
            content="This is a mock contract. The liability clause is missing. The expiration date is 2026-12-31.",
            metadata={"author": "Pritam", "department": "Legal"}
        )
        return mock_document