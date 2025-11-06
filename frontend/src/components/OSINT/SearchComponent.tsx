import React, { useState } from 'react';
import { searchApi, SearchResult, SearchResponse } from '../../services/osintAgentApi';

interface SearchComponentProps {
  investigationId?: string;
  onSearchComplete?: (results: SearchResponse) => void;
  placeholder?: string;
  className?: string;
}

const SearchComponent: React.FC<SearchComponentProps> = ({
  investigationId,
  onSearchComplete,
  placeholder = "Search the web...",
  className = ""
}) => {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [searchMeta, setSearchMeta] = useState<{
    total_results: number;
    engines_used: string[];
    search_time: number;
    timestamp: string;
  } | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setIsSearching(true);
    setError(null);
    setResults([]);

    try {
      let searchResponse: SearchResponse;
      
      if (investigationId) {
        // Search within investigation context
        const investigationResponse = await searchApi.searchInInvestigation(
          investigationId, 
          query, 
          10
        );
        searchResponse = investigationResponse;
        setResults(investigationResponse.results);
      } else {
        // Regular web search
        searchResponse = await searchApi.searchWeb(query, 10);
        setResults(searchResponse.results);
      }

      setSearchMeta({
        total_results: searchResponse.total_results,
        engines_used: searchResponse.engines_used,
        search_time: searchResponse.search_time,
        timestamp: searchResponse.timestamp
      });

      onSearchComplete?.(searchResponse);
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Search failed. Please try again.');
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className={`search-component ${className}`}>
      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isSearching}
          />
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {/* Search Meta Information */}
      {searchMeta && (
        <div className="mb-4 p-3 bg-gray-100 rounded-lg text-sm text-gray-600">
          <div className="flex justify-between items-center">
            <span>
              Found {searchMeta.total_results} results 
              {searchMeta.engines_used.length > 0 && 
                ` using ${searchMeta.engines_used.join(', ')}`
              }
            </span>
            <span>
              {searchMeta.search_time.toFixed(2)}s
            </span>
          </div>
        </div>
      )}

      {/* Search Results */}
      {results.length > 0 && (
        <div className="search-results">
          <h3 className="text-lg font-semibold mb-3">Search Results</h3>
          <div className="space-y-4">
            {results.map((result, index) => (
              <div
                key={index}
                className="p-4 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex justify-between items-start mb-2">
                  <h4 className="text-base font-medium text-blue-800">
                    <a
                      href={result.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="hover:underline"
                    >
                      {result.title}
                    </a>
                  </h4>
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {result.source}
                  </span>
                </div>
                
                {result.description && (
                  <p className="text-gray-600 text-sm mb-2 line-clamp-2">
                    {result.description}
                  </p>
                )}
                
                <div className="flex justify-between items-center text-xs text-gray-500">
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-600 hover:underline truncate max-w-md"
                  >
                    {result.url}
                  </a>
                  <span className="ml-2">
                    Score: {(result.relevance_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {!isSearching && query && results.length === 0 && !error && (
        <div className="text-center py-8 text-gray-500">
          No search results found for "{query}"
        </div>
      )}
    </div>
  );
};

export default SearchComponent;