import pytest

from smartgraph.logging import SmartGraphLogger


@pytest.fixture(autouse=True)
def setup_logger():
    logger = SmartGraphLogger.get_logger()
    logger.set_level("DEBUG")
    return logger


@pytest.fixture
def mock_duckduckgo_search():
    class MockDDGS:
        def text(self, keywords, max_results):
            return [{"title": "Test Result", "body": "This is a test search result."}]

        def news(self, keywords, max_results):
            return [{"title": "Test News", "body": "This is a test news article."}]

    return MockDDGS()
