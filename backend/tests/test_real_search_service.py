import pytest
import asyncio
from unittest.mock import patch, AsyncMock
import httpx

from app.services.real_search_service import RealSearchService, SearchResult, SearchError


class TestRealSearchService:
    """Test cases for the real search service to ensure no mock data is generated."""

    @pytest.fixture
    def search_service(self):
        """Create a RealSearchService instance for testing."""
        return RealSearchService()

    def test_service_initialization(self, search_service):
        """Test that the service initializes correctly."""
        assert search_service.enable_real_search == True
        assert search_service.max_results == 10
        assert search_service.timeout == 30

    @pytest.mark.asyncio
    async def test_duckduckgo_search_success(self, search_service):
        """Test successful DuckDuckGo search."""
        mock_response = {
            "results": [
                {
                    "title": "Test Result 1",
                    "url": "https://example.com/1",
                    "snippet": "This is a test result"
                },
                {
                    "title": "Test Result 2", 
                    "url": "https://example.com/2",
                    "snippet": "This is another test result"
                }
            ]
        }

        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.status_code = 200

            results = await search_service._search_duckduckgo("test query")

            assert len(results) == 2
            assert results[0].title == "Test Result 1"
            assert results[0].url == "https://example.com/1"
            assert results[0].snippet == "This is a test result"
            assert results[0].source == "duckduckgo"

    @pytest.mark.asyncio
    async def test_duckduckgo_search_no_results(self, search_service):
        """Test DuckDuckGo search with no results."""
        mock_response = {"results": []}

        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.status_code = 200

            results = await search_service._search_duckduckgo("no results query")

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_duckduckgo_search_http_error(self, search_service):
        """Test DuckDuckGo search with HTTP error."""
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = httpx.HTTPError("Connection error")

            results = await search_service._search_duckduckgo("test query")

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_duckduckgo_search_json_error(self, search_service):
        """Test DuckDuckGo search with invalid JSON."""
        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value.status_code = 200

            results = await search_service._search_duckduckgo("test query")

            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_with_duckduckgo_fallback(self, search_service):
        """Test search method using DuckDuckGo fallback."""
        mock_response = {
            "results": [
                {
                    "title": "Fallback Result",
                    "url": "https://example.com/fallback",
                    "snippet": "This is a fallback result"
                }
            ]
        }

        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.status_code = 200

            results = await search_service.search("test query")

            assert len(results) == 1
            assert results[0].title == "Fallback Result"
            assert results[0].source == "duckduckgo"

    @pytest.mark.asyncio
    async def test_search_no_api_keys_configured(self, search_service):
        """Test search when no API keys are configured."""
        with patch.object(search_service, '_search_duckduckgo', new_callable=AsyncMock) as mock_ddg:
            mock_ddg.return_value = []

            results = await search_service.search("test query")

            assert isinstance(results, list)
            # Should return empty list, not mock data
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_error_handling(self, search_service):
        """Test that search handles errors gracefully without generating mock data."""
        with patch.object(search_service, '_search_duckduckgo', new_callable=AsyncMock) as mock_ddg:
            mock_ddg.side_effect = Exception("Search service unavailable")

            with pytest.raises(SearchError) as exc_info:
                await search_service.search("test query")

            assert "Search service temporarily unavailable" in str(exc_info.value)
            assert exc_info.value.service_unavailable == True

    def test_search_result_model(self):
        """Test SearchResult model validation."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            source="test_source",
            relevance_score=0.8
        )

        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.source == "test_source"
        assert result.relevance_score == 0.8

    def test_search_error_model(self):
        """Test SearchError model."""
        error = SearchError(
            message="Test error",
            service_unavailable=True,
            error_code="SERVICE_DOWN"
        )

        assert error.message == "Test error"
        assert error.service_unavailable == True
        assert error.error_code == "SERVICE_DOWN"

    @pytest.mark.asyncio
    async def test_no_mock_fallback_in_search(self, search_service):
        """Verify that search never returns mock data."""
        # Mock all search methods to return empty results
        with patch.object(search_service, '_search_duckduckgo', new_callable=AsyncMock) as mock_ddg:
            mock_ddg.return_value = []

            results = await search_service.search("any query")

            # Should return empty list, not mock data
            assert isinstance(results, list)
            assert len(results) == 0

    @pytest.mark.asyncio
    async def test_real_search_disabled(self):
        """Test behavior when real search is disabled."""
        disabled_service = RealSearchService(enable_real_search=False)

        with pytest.raises(SearchError) as exc_info:
            await disabled_service.search("test query")

        assert "Real search is disabled" in str(exc_info.value)
        assert exc_info.value.service_unavailable == True

    @pytest.mark.asyncio
    async def test_search_with_custom_max_results(self):
        """Test search with custom max_results parameter."""
        custom_service = RealSearchService(max_results=5)
        mock_response = {
            "results": [
                {"title": f"Result {i}", "url": f"https://example.com/{i}", "snippet": f"Snippet {i}"}
                for i in range(10)  # 10 results available
            ]
        }

        with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.status_code = 200

            results = await custom_service.search("test query")

            # Should respect max_results limit
            assert len(results) <= 5