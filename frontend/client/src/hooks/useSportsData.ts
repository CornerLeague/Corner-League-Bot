// Copyright (c) 2024 Corner League Bot
// Licensed under the MIT License

/**
 * React hooks for sports data management using TanStack Query
 * Provides optimized data fetching with caching and real-time updates
 */

import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { useState, useCallback, useMemo } from 'react';
import { 
  api, 
  queryKeys, 
  cacheUtils,
  errorUtils,
  mockData,
  type ContentItem, 
  type SearchRequest, 
  type SearchResponse,
  type TrendingTerm,
  type SummaryRequest,
  type SummaryResponse,
  type UserPreferences,
  type HealthResponse,
  type PlatformStats,
  ApiError
} from '../lib/api';

// Configuration
const STALE_TIME = 5 * 60 * 1000; // 5 minutes
const CACHE_TIME = 10 * 60 * 1000; // 10 minutes
const RETRY_COUNT = 3;

// Custom hook options
interface UseSearchOptions {
  enabled?: boolean;
  staleTime?: number;
  refetchInterval?: number;
  fallbackToMock?: boolean;
}

interface UseSummaryOptions {
  enabled?: boolean;
  onSuccess?: (data: SummaryResponse) => void;
  onError?: (error: Error) => void;
}

// Health check hook
function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => api.getHealth(),
    staleTime: 30 * 1000, // 30 seconds
    retry: 1,
    refetchInterval: 60 * 1000, // Check every minute
  });
}

// Platform statistics hook
function usePlatformStats() {
  return useQuery({
    queryKey: queryKeys.stats,
    queryFn: () => api.getStats(),
    staleTime: 2 * 60 * 1000, // 2 minutes
    retry: RETRY_COUNT,
  });
}

// Content search hook with advanced options
function useSearch(request: SearchRequest, options: UseSearchOptions = {}) {
  const { 
    enabled = true, 
    staleTime = STALE_TIME, 
    refetchInterval,
    fallbackToMock = true 
  } = options;

  return useQuery({
    queryKey: queryKeys.search(request),
    queryFn: async () => {
      try {
        return await api.searchContent(request);
      } catch (error) {
        if (fallbackToMock && errorUtils.isNetworkError(error)) {
          // Fallback to mock data for development
          return {
            items: mockData.contentItems.slice(0, request.limit || 20),
            total_count: mockData.contentItems.length,
            has_more: false,
            search_time_ms: 50,
            engine: 'mock',
            from_cache: false,
          } as SearchResponse;
        }
        throw error;
      }
    },
    enabled: Boolean(enabled && (request.query || request.sports?.length || request.sources?.length)),
    staleTime,
    gcTime: CACHE_TIME,
    retry: RETRY_COUNT,
    refetchInterval,
  });
}

// Individual content item hook
function useContent(contentId: string, options?: UseQueryOptions<ContentItem>) {
  return useQuery({
    queryKey: queryKeys.content(contentId),
    queryFn: () => api.getContent(contentId),
    enabled: !!contentId,
    staleTime: STALE_TIME,
    gcTime: CACHE_TIME,
    retry: RETRY_COUNT,
    ...options,
  });
}

// Search suggestions hook with debouncing
function useSearchSuggestions(query: string, delay: number = 300) {
  const [debouncedQuery, setDebouncedQuery] = useState(query);

  // Debounce the query
  useState(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), delay);
    return () => clearTimeout(timer);
  });

  return useQuery({
    queryKey: queryKeys.suggestions(debouncedQuery),
    queryFn: () => api.getSearchSuggestions(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Trending terms hook
function useTrending(limit: number = 10) {
  return useQuery({
    queryKey: queryKeys.trending(limit),
    queryFn: async () => {
      try {
        return await api.getTrendingTerms(limit);
      } catch (error) {
        if (errorUtils.isNetworkError(error)) {
          return mockData.trendingTerms.slice(0, limit);
        }
        throw error;
      }
    },
    staleTime: 60 * 1000, // 1 minute
    gcTime: 5 * 60 * 1000, // 5 minutes
    retry: RETRY_COUNT,
    refetchInterval: 2 * 60 * 1000, // Refresh every 2 minutes
  });
}

// AI summarization hook
function useSummarization(options: UseSummaryOptions = {}) {
  const { enabled = false, onSuccess, onError } = options;
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: SummaryRequest) => api.summarizeContent(request),
    onSuccess: (data) => {
      // Cache the summary result
      queryClient.setQueryData(queryKeys.summary(data as any), data);
      onSuccess?.(data);
    },
    onError: (error) => {
      console.error('Summarization error:', error);
      onError?.(error as Error);
    },
  });
}

// User preferences hook
function useUserPreferences() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.userPreferences,
    queryFn: async () => {
      try {
        return await api.getUserPreferences();
      } catch (error) {
        if (errorUtils.isNetworkError(error)) {
          return mockData.userPreferences;
        }
        throw error;
      }
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
  });

  const mutation = useMutation({
    mutationFn: (preferences: UserPreferences) => api.updateUserPreferences(preferences),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.userPreferences, data);
    },
  });

  return {
    ...query,
    updatePreferences: mutation.mutate,
    isUpdating: mutation.isPending,
    updateError: mutation.error,
  };
}

// Convenience hooks for common content types
function useLatestNews(sports?: string[], limit: number = 20, options: UseSearchOptions = {}) {
  return useQuery({
    queryKey: queryKeys.latestNews(sports, limit),
    queryFn: async () => {
      try {
        return await api.getLatestNews(sports, limit);
      } catch (error) {
        if (options.fallbackToMock !== false && errorUtils.isNetworkError(error)) {
          return {
            items: mockData.contentItems.slice(0, limit),
            total_count: mockData.contentItems.length,
            has_more: false,
            search_time_ms: 50,
            engine: 'mock',
            from_cache: false,
          } as SearchResponse;
        }
        throw error;
      }
    },
    staleTime: options.staleTime || 2 * 60 * 1000, // 2 minutes for news
    gcTime: CACHE_TIME,
    retry: RETRY_COUNT,
    refetchInterval: options.refetchInterval || 5 * 60 * 1000, // Refresh every 5 minutes
  });
}

function useBreakingNews(limit: number = 10) {
  return useQuery({
    queryKey: queryKeys.breakingNews(limit),
    queryFn: () => api.getBreakingNews(limit),
    staleTime: 30 * 1000, // 30 seconds for breaking news
    gcTime: 2 * 60 * 1000, // 2 minutes
    retry: RETRY_COUNT,
    refetchInterval: 60 * 1000, // Refresh every minute
  });
}

function useGameRecaps(sports?: string[], limit: number = 15) {
  return useQuery({
    queryKey: queryKeys.gameRecaps(sports, limit),
    queryFn: () => api.getGameRecaps(sports, limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: CACHE_TIME,
    retry: RETRY_COUNT,
  });
}

function useTradingNews(limit: number = 10) {
  return useQuery({
    queryKey: queryKeys.tradingNews(limit),
    queryFn: () => api.getTradingNews(limit),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: CACHE_TIME,
    retry: RETRY_COUNT,
    refetchInterval: 3 * 60 * 1000, // Refresh every 3 minutes
  });
}

function useAnalysis(sports?: string[], limit: number = 10) {
  return useQuery({
    queryKey: queryKeys.analysis(sports, limit),
    queryFn: () => api.getAnalysis(sports, limit),
    staleTime: 10 * 60 * 1000, // 10 minutes for analysis
    gcTime: CACHE_TIME,
    retry: RETRY_COUNT,
  });
}

// Advanced search hook with pagination
function useInfiniteSearch(baseRequest: SearchRequest) {
  const queryClient = useQueryClient();

  return useQuery({
    queryKey: ['infinite-search', baseRequest],
    queryFn: async () => {
      const results = await api.searchContent(baseRequest);
      return {
        pages: [results],
        pageParams: [null],
      };
    },
    staleTime: STALE_TIME,
    gcTime: CACHE_TIME,
  });
}

// Real-time data hook with WebSocket support (placeholder)
function useRealTimeUpdates(enabled: boolean = true) {
  const queryClient = useQueryClient();

  // This would connect to WebSocket for real-time updates
  // For now, we'll use polling
  return useQuery({
    queryKey: ['real-time-updates'],
    queryFn: async () => {
      // Check for new content and invalidate relevant queries
      const stats = await api.getStats();
      
      // If there's new content, invalidate searches
      if (stats.content.articles_1h > 0) {
        cacheUtils.invalidateSearches();
      }
      
      return stats;
    },
    enabled,
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 60 * 1000, // Check every minute
  });
}

// Content interaction hooks
function useContentInteractions() {
  const queryClient = useQueryClient();

  const prefetchContent = useCallback(async (contentId: string) => {
    await cacheUtils.prefetchContent(contentId);
  }, []);

  const markAsRead = useCallback((contentId: string) => {
    // This would typically update user reading history
    console.log('Marked as read:', contentId);
  }, []);

  const shareContent = useCallback((content: ContentItem) => {
    // Share functionality
    if (navigator.share) {
      navigator.share({
        title: content.title,
        text: content.summary,
        url: content.canonical_url,
      });
    } else {
      // Fallback to clipboard
      navigator.clipboard.writeText(content.canonical_url);
    }
  }, []);

  const saveContent = useCallback((contentId: string) => {
    // This would save to user's reading list
    console.log('Saved content:', contentId);
  }, []);

  return {
    prefetchContent,
    markAsRead,
    shareContent,
    saveContent,
  };
}

// Search state management hook
function useSearchState() {
  const [searchRequest, setSearchRequest] = useState<SearchRequest>({
    query: '',
    sports: [],
    sort_by: 'relevance',
    limit: 20,
  });

  const [selectedContent, setSelectedContent] = useState<ContentItem | null>(null);
  const [summaryRequest, setSummaryRequest] = useState<SummaryRequest | null>(null);

  const updateSearch = useCallback((updates: Partial<SearchRequest>) => {
    setSearchRequest(prev => ({ ...prev, ...updates }));
  }, []);

  const clearSearch = useCallback(() => {
    setSearchRequest({
      query: '',
      sports: [],
      sort_by: 'relevance',
      limit: 20,
    });
  }, []);

  const selectContent = useCallback((content: ContentItem | null) => {
    setSelectedContent(content);
  }, []);

  const requestSummary = useCallback((request: SummaryRequest) => {
    setSummaryRequest(request);
  }, []);

  return {
    searchRequest,
    selectedContent,
    summaryRequest,
    updateSearch,
    clearSearch,
    selectContent,
    requestSummary,
  };
}

// Error handling hook
function useErrorHandler() {
  const [error, setError] = useState<Error | null>(null);

  const handleError = useCallback((error: unknown) => {
    const errorMessage = errorUtils.getErrorMessage(error);
    const errorObj = new Error(errorMessage);
    setError(errorObj);
    
    // Log error for monitoring
    console.error('Application error:', error);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const isNetworkError = useMemo(() => {
    return error && errorUtils.isNetworkError(error);
  }, [error]);

  const isServerError = useMemo(() => {
    return error && errorUtils.isServerError(error);
  }, [error]);

  return {
    error,
    handleError,
    clearError,
    isNetworkError,
    isServerError,
  };
}

// Performance monitoring hook
function usePerformanceMonitoring() {
  const [metrics, setMetrics] = useState({
    searchTime: 0,
    renderTime: 0,
    cacheHitRate: 0,
  });

  const recordSearchTime = useCallback((time: number) => {
    setMetrics(prev => ({ ...prev, searchTime: time }));
  }, []);

  const recordRenderTime = useCallback((time: number) => {
    setMetrics(prev => ({ ...prev, renderTime: time }));
  }, []);

  return {
    metrics,
    recordSearchTime,
    recordRenderTime,
  };
}

// Export all hooks
export {
  // Core data hooks
  useHealth,
  usePlatformStats,
  useSearch,
  useContent,
  useSearchSuggestions,
  useTrending,
  useSummarization,
  useUserPreferences,
  
  // Content type hooks
  useLatestNews,
  useBreakingNews,
  useGameRecaps,
  useTradingNews,
  useAnalysis,
  
  // Advanced hooks
  useInfiniteSearch,
  useRealTimeUpdates,
  useContentInteractions,
  useSearchState,
  useErrorHandler,
  usePerformanceMonitoring,
};

