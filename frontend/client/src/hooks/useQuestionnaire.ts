/**
 * Questionnaire API Hooks
 * 
 * Custom hooks for managing questionnaire data and API interactions
 * using React Query for caching and state management.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@clerk/clerk-react';

interface Sport {
  id: number;
  name: string;
  display_name: string;
  description: string;
  is_active: boolean;
}

interface Team {
  id: string;
  name: string;
  sport_id: string;
  city: string;
  logo_url?: string;
  is_active: boolean;
}

interface QuestionnaireStatus {
  is_completed: boolean;
  current_step?: string;
  completed_steps: string[];
  next_step?: string;
}

interface UserPreferences {
  sport_preferences: Array<{
    id: string;
    user_id: string;
    sport_id: string;
    preference_order: number;
    sport: Sport;
  }>;
  team_preferences: Array<{
    id: string;
    user_id: string;
    team_id: string;
    preference_order: number;
    team: Team;
  }>;
  questionnaire_status: {
    id: string;
    user_id: string;
    current_step?: string;
    is_completed: boolean;
    completed_steps: string[];
  };
}

interface SportPreferenceRequest {
  sport_id: number;
  interest_level: number;
}

interface SportRankingRequest {
  sport_rankings: string[];
}

interface FavoriteTeamsRequest {
  team_selections: Array<{
    team_id: string;
    sport_id: string;
  }>;
}

// Use relative API path - Vite proxy will redirect to backend
const API_BASE = '/api/questionnaire';

/**
 * Hook to get questionnaire status
 */
export function useQuestionnaireStatus() {
  const { getToken } = useAuth();
  
  return useQuery({
    queryKey: ['questionnaire', 'status'],
    queryFn: async (): Promise<QuestionnaireStatus> => {
      const token = await getToken();
      const response = await fetch(`${API_BASE}/status`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch questionnaire status');
      }
      
      const result = await response.json();
      
      // Handle the backend response structure: { success: true, data: {...} }
      if (result.success && result.data) {
        return result.data;
      }
      
      throw new Error('Invalid response format');
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to get available sports
 */
export function useAvailableSports() {
  const { getToken } = useAuth();
  
  return useQuery({
    queryKey: ['questionnaire', 'sports'], // Added version to invalidate cache
    queryFn: async (): Promise<{ sports: Sport[]; total_count: number }> => {
      const token = await getToken();
      const response = await fetch(`${API_BASE}/sports`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch sports');
      }
      
      const result = await response.json();
      
      // Handle the backend response structure: { success: true, data: [...] }
      if (result.success && result.data) {
        return {
          sports: result.data,
          total_count: result.data.length
        };
      }
      
      throw new Error('Invalid response format');
    },
    staleTime: 30 * 60 * 1000, // 30 minutes - sports don't change often
  });
}

/**
 * Hook to get teams for a specific sport
 */
export function useTeamsBySport(sportId: string) {
  const { getToken } = useAuth();
  
  return useQuery({
    queryKey: ['questionnaire', 'teams', sportId],
    queryFn: async (): Promise<{ teams: Team[]; total_count: number }> => {
      const token = await getToken();
      const response = await fetch(`${API_BASE}/sports/${sportId}/teams`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch teams');
      }
      
      return response.json();
    },
    enabled: !!sportId,
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
}

/**
 * Hook to get user preferences
 */
export function useUserPreferences() {
  const { getToken } = useAuth();
  
  return useQuery({
    queryKey: ['questionnaire', 'preferences'],
    queryFn: async (): Promise<UserPreferences> => {
      const token = await getToken();
      const response = await fetch(`${API_BASE}/preferences`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch user preferences');
      }
      
      return response.json();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to save sport preferences
 */
export function useSaveSportPreferences() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: SportPreferenceRequest[]) => {
      const token = await getToken();
      const response = await fetch(`${API_BASE}/sports/preferences`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        let errorMessage = 'Failed to save sport preferences';
        try {
          const error = await response.json();
          console.error('DEBUG: Full error response:', JSON.stringify(error, null, 2));
          console.error('DEBUG: Response status:', response.status);
          console.error('DEBUG: Response headers:', Object.fromEntries(response.headers.entries()));
          console.error('DEBUG: Error type:', typeof error);
          console.error('DEBUG: Error detail:', error.detail);
          console.error('DEBUG: Error message:', error.message);
          if (Array.isArray(error.detail)) {
            errorMessage = error.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
          } else if (typeof error.detail === 'object' && error.detail !== null) {
            errorMessage = JSON.stringify(error.detail);
          } else {
            errorMessage = error.detail || error.message || errorMessage;
          }
        } catch (parseError) {
          console.error('DEBUG: Failed to parse error response:', parseError);
          // If response is not JSON (e.g., HTML error page), use status text
          errorMessage = `${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const result = await response.json();
      
      // Handle the backend response structure: { success: true, data: [...] }
      if (result.success && result.data) {
        return result.data;
      }
      
      throw new Error('Invalid response format');
    },
    onSuccess: () => {
      // Invalidate related queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['questionnaire', 'status'] });
      queryClient.invalidateQueries({ queryKey: ['questionnaire', 'preferences'] });
    }
  });
}

/**
 * Hook to save sport rankings
 */
export function useSaveSportRankings() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: SportRankingRequest) => {
      const token = await getToken();
      const response = await fetch(`${API_BASE}/sports/ranking`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        let errorMessage = 'Failed to save sport rankings';
        try {
          const error = await response.json();
          console.error('DEBUG: Sport rankings error response:', JSON.stringify(error, null, 2));
          console.error('DEBUG: Sport rankings response status:', response.status);
          console.error('DEBUG: Sport rankings response headers:', Object.fromEntries(response.headers.entries()));
          console.error('DEBUG: Sport rankings error type:', typeof error);
          console.error('DEBUG: Sport rankings error detail:', error.detail);
          console.error('DEBUG: Sport rankings error message:', error.message);
          if (Array.isArray(error.detail)) {
            errorMessage = error.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
          } else if (typeof error.detail === 'object' && error.detail !== null) {
            errorMessage = JSON.stringify(error.detail);
          } else {
            errorMessage = error.detail || error.message || errorMessage;
          }
        } catch (parseError) {
          console.error('DEBUG: Failed to parse sport rankings error response:', parseError);
          // If response is not JSON (e.g., HTML error page), use status text
          errorMessage = `${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const result = await response.json();
      
      // Handle the backend response structure: { success: true, data: [...] }
      if (result.success && result.data) {
        return result.data;
      }
      
      throw new Error('Invalid response format');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['questionnaire', 'status'] });
      queryClient.invalidateQueries({ queryKey: ['questionnaire', 'preferences'] });
    }
  });
}

/**
 * Hook to save team preferences
 */
export function useSaveTeamPreferences() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: FavoriteTeamsRequest) => {
      const token = await getToken();
      const response = await fetch(`${API_BASE}/teams/preferences`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        let errorMessage = 'Failed to save team preferences';
        try {
          const error = await response.json();
          errorMessage = error.detail || error.message || errorMessage;
        } catch {
          // If response is not JSON (e.g., HTML error page), use status text
          errorMessage = `${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const result = await response.json();
      
      // Handle the backend response structure: { success: true, data: [...] }
      if (result.success && result.data) {
        return result.data;
      }
      
      throw new Error('Invalid response format');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['questionnaire', 'status'] });
      queryClient.invalidateQueries({ queryKey: ['questionnaire', 'preferences'] });
    }
  });
}

/**
 * Utility hook to get teams for multiple sports
 */
export function useTeamsForSports(sportIds: number[]) {
  const { getToken } = useAuth();
  
  // Convert sportIds to strings for API calls
  const validSportIds = (sportIds || [])
    .filter(sportId => 
      sportId && 
      typeof sportId === 'number' && 
      !isNaN(sportId)
    )
    .map(sportId => sportId.toString());
  
  return useQuery({
    queryKey: ['teams-for-sports', validSportIds],
    queryFn: async () => {
      if (validSportIds.length === 0) {
        return { teams: [] };
      }
      
      const token = await getToken();
      const teamPromises = validSportIds.map(async (sportId) => {
        const response = await fetch(`${API_BASE}/sports/${sportId}/teams`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          throw new Error(`Failed to fetch teams for sport ${sportId}`);
        }
        
        const data = await response.json();
        return data.teams || [];
      });
      
      const teamsArrays = await Promise.all(teamPromises);
      const allTeams = teamsArrays.flat();
      
      return { teams: allTeams };
    },
    enabled: validSportIds.length > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to check if questionnaire is completed
 */
export function useIsQuestionnaireCompleted() {
  const { data: status, isLoading } = useQuestionnaireStatus();
  
  return {
    isCompleted: status?.is_completed ?? false,
    isLoading,
    currentStep: status?.current_step,
    nextStep: status?.next_step
  };
}