import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { apiClient, ApiError, type ApiPaths, type OperationRequestBody, type OperationResponse } from '../lib/api-client';

// Type helpers for React Query
type HttpMethod = 'get' | 'post' | 'put' | 'delete' | 'patch';

type PathsWithMethod<TMethod extends HttpMethod> = {
  [TPath in keyof ApiPaths]: ApiPaths[TPath] extends { [K in TMethod]: any }
    ? TPath
    : never;
}[keyof ApiPaths];

// Query hook for GET requests
export function useApiQuery<TPath extends PathsWithMethod<'get'>>(
  path: TPath,
  options?: {
    params?: any;
    query?: any;
    headers?: Record<string, string>;
  },
  queryOptions?: Omit<UseQueryOptions<OperationResponse<TPath, 'get'>, ApiError>, 'queryKey' | 'queryFn'>
) {
  return useQuery({
    queryKey: [path, options?.params, options?.query],
    queryFn: () => apiClient.get(path, options),
    ...queryOptions,
  });
}

// Mutation hook for POST requests
export function useApiMutation<TPath extends PathsWithMethod<'post'>>(
  path: TPath,
  options?: UseMutationOptions<
    OperationResponse<TPath, 'post'>,
    ApiError,
    {
      params?: any;
      query?: any;
      body?: OperationRequestBody<TPath, 'post'>;
      headers?: Record<string, string>;
    }
  >
) {
  return useMutation({
    mutationFn: (variables) => apiClient.post(path, variables),
    ...options,
  });
}

// Mutation hook for PUT requests
export function useApiPutMutation<TPath extends PathsWithMethod<'put'>>(
  path: TPath,
  options?: UseMutationOptions<
    OperationResponse<TPath, 'put'>,
    ApiError,
    {
      params?: any;
      query?: any;
      body?: OperationRequestBody<TPath, 'put'>;
      headers?: Record<string, string>;
    }
  >
) {
  return useMutation({
    mutationFn: (variables) => apiClient.put(path, variables),
    ...options,
  });
}

// Mutation hook for DELETE requests
export function useApiDeleteMutation<TPath extends PathsWithMethod<'delete'>>(
  path: TPath,
  options?: UseMutationOptions<
    OperationResponse<TPath, 'delete'>,
    ApiError,
    {
      params?: any;
      query?: any;
      headers?: Record<string, string>;
    }
  >
) {
  return useMutation({
    mutationFn: (variables) => apiClient.delete(path, variables),
    ...options,
  });
}

// Specific API hooks for common operations
export function useUserProfile() {
  return useApiQuery('/api/auth/me');
}

export function useUserPreferences() {
  return useApiQuery('/api/auth/preferences');
}

export function useUpdateUserPreferences() {
  const queryClient = useQueryClient();
  
  return useApiPutMutation('/api/auth/preferences', {
    onSuccess: () => {
      // Invalidate and refetch user preferences
      queryClient.invalidateQueries({ queryKey: ['/api/auth/preferences'] });
    },
  });
}

export function useSearchContent() {
  return useApiMutation('/api/search');
}

export function useGetContent(contentId: string, enabled = true) {
  return useApiQuery(
    '/api/content/{content_id}',
    { params: { content_id: contentId } },
    { enabled: enabled && !!contentId }
  );
}

export function useTrendingTerms(limit = 10) {
  return useApiQuery(
    '/api/trending',
    { query: { limit } }
  );
}

export function useHealthCheck() {
  return useApiQuery('/api/health');
}

export function usePlatformStats() {
  return useApiQuery('/api/stats');
}

export function useQuestionnaireSports() {
  return useApiQuery('/api/questionnaire/sports');
}

export function useQuestionnaireTeams(sportId: string, enabled = true) {
  return useApiQuery(
    '/api/questionnaire/sports/{sport_id}/teams',
    { params: { sport_id: sportId } },
    { enabled: enabled && !!sportId }
  );
}

export function useQuestionnaireStatus() {
  return useApiQuery('/api/questionnaire/status');
}

export function useUserQuestionnairePreferences() {
  return useApiQuery('/api/questionnaire/preferences');
}

export function useSubmitSportPreferences() {
  const queryClient = useQueryClient();
  
  return useApiMutation('/api/questionnaire/sports/preferences', {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/questionnaire/status'] });
      queryClient.invalidateQueries({ queryKey: ['/api/questionnaire/preferences'] });
    },
  });
}

export function useSubmitTeamPreferences() {
  const queryClient = useQueryClient();
  
  return useApiMutation('/api/questionnaire/teams/preferences', {
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/questionnaire/status'] });
      queryClient.invalidateQueries({ queryKey: ['/api/questionnaire/preferences'] });
    },
  });
}

// Auth hooks
export function useUserStats() {
  return useApiQuery('/api/auth/stats');
}

export function useDeleteAccount() {
  return useApiDeleteMutation('/api/auth/me');
}

// Error boundary helper
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

// Query key factory for consistent cache management
export const queryKeys = {
  auth: {
    me: () => ['/api/auth/me'] as const,
    preferences: () => ['/api/auth/preferences'] as const,
    stats: () => ['/api/auth/stats'] as const,
  },
  questionnaire: {
    sports: () => ['/api/questionnaire/sports'] as const,
    teams: (sportId: string) => ['/api/questionnaire/sports/{sport_id}/teams', { sport_id: sportId }] as const,
    status: () => ['/api/questionnaire/status'] as const,
    preferences: () => ['/api/questionnaire/preferences'] as const,
  },
  content: {
    item: (contentId: string) => ['/api/content/{content_id}', { content_id: contentId }] as const,
    search: (query: any) => ['/api/search', query] as const,
  },
  platform: {
    health: () => ['/api/health'] as const,
    stats: () => ['/api/stats'] as const,
    trending: (limit: number) => ['/api/trending', { limit }] as const,
  },
} as const;