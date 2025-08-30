/**
 * Questionnaire Page
 *
 * A dynamic questionnaire component that guides users through sports and team preferences
 * with conditional logic and real-time preference storage.
 */

import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { useLocation } from 'wouter';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { ProtectedRoute } from '@/components/auth';
import {
  ChevronRight,
  ChevronLeft,
  Check,
  Star,
  Trophy,
  Users,
  Loader2,
  AlertCircle
} from 'lucide-react';
import {
  useQuestionnaireStatus,
  useAvailableSports,
  useTeamsForSports,
  useSaveSportPreferences,
  useSaveSportRankings,
  useSaveTeamPreferences
} from '@/hooks/useQuestionnaire';

interface Sport {
  id: string;
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

type QuestionnaireStep = 'sports_selection' | 'sports_ranking' | 'teams_selection' | 'completed';

export default function QuestionnairePage() {
  const { getToken } = useAuth();
  const [, setLocation] = useLocation();

  // State management
  const [currentStep, setCurrentStep] = useState<QuestionnaireStep>('sports_selection');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // User selections
  const [selectedSports, setSelectedSports] = useState<string[]>([]);
  const [rankedSports, setRankedSports] = useState<string[]>([]);
  const [selectedTeams, setSelectedTeams] = useState<{team_id: string, sport_id: string}[]>([]);

  // API hooks
  const { data: questionnaireStatus, isLoading: statusLoading } = useQuestionnaireStatus();
  const { data: sportsData, isLoading: sportsLoading, error: sportsError } = useAvailableSports();
  const teamsQuery = useTeamsForSports(Array.isArray(selectedSports) && selectedSports.length > 0 ? selectedSports : []);
  const saveSportPreferences = useSaveSportPreferences();
  const saveSportRankings = useSaveSportRankings();
  const saveTeamPreferences = useSaveTeamPreferences();

  const loading = statusLoading || sportsLoading || teamsQuery.isLoading;
  const sports = sportsData?.sports || [];
  const teams = teamsQuery.data?.teams || [];
  const status = questionnaireStatus;



  // Set current step based on status or default to sports_selection
  useEffect(() => {
    if (!statusLoading) {
      if (status) {
        if (status.is_completed) {
          setCurrentStep('completed');
        } else if (status.current_step) {
          setCurrentStep(status.current_step as QuestionnaireStep);
        } else {
          setCurrentStep('sports_selection');
        }
      } else {
        // No status available (likely not authenticated or first time), start with sports selection
        setCurrentStep('sports_selection');
      }
    }
  }, [statusLoading, status]);

  // Handle errors from API calls
  useEffect(() => {
    if (teamsQuery.isError) {
      setError('Failed to load team data');
    }
  }, [teamsQuery.isError]);

  const handleSportsSelection = async () => {
    if (!Array.isArray(selectedSports) || selectedSports.length === 0) {
      setError('Please select at least one sport');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);

      // Filter out any null/undefined values and convert selected sports to preference format
      const validSportIds = selectedSports.filter(sportId => sportId != null && sportId !== '');
      const sportPreferences = validSportIds.map((sportId) => ({
        sport_id: sportId,
        interest_level: 3,
      }));

      console.log('DEBUG: selectedSports array:', selectedSports);
      console.log('DEBUG: validSportIds array:', validSportIds);
      console.log('DEBUG: selectedSports types:', selectedSports.map(id => typeof id));
      console.log('DEBUG: sportPreferences payload:', JSON.stringify(sportPreferences, null, 2));
      await saveSportPreferences.mutateAsync(sportPreferences);

      // If user selected multiple sports, go to ranking step
      if (Array.isArray(validSportIds) && validSportIds.length > 1) {
        setRankedSports([...validSportIds]);
        setCurrentStep('sports_ranking');
      } else {
        // Single sport selected, skip ranking and go to teams
        setCurrentStep('teams_selection');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save sport preferences';
      setError(errorMessage);
      console.error('Error saving sports:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSportsRanking = async () => {
    try {
      setSubmitting(true);
      setError(null);

      await saveSportRankings.mutateAsync({ sport_rankings: rankedSports.map(id => id.toString()) });
      setCurrentStep('teams_selection');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save sport rankings';
      setError(errorMessage);
      console.error('Error saving rankings:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleTeamsSelection = async () => {
    if (!Array.isArray(selectedTeams) || selectedTeams.length === 0) {
      setError('Please select at least one team');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const teamPreferences = selectedTeams.map(team => ({
        team_id: team.team_id,
        interest_level: 3,
      }));
      await saveTeamPreferences.mutateAsync(teamPreferences);
      setCurrentStep('completed');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save team preferences';
      setError(errorMessage);
      console.error('Error saving teams:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const toggleSportSelection = (sportId: string) => {
    setSelectedSports(prev =>
      prev.includes(sportId)
        ? prev.filter(id => id !== sportId)
        : [...prev, sportId]
    );
  };

  const moveSportUp = (index: number) => {
    if (index > 0) {
      const newRanked = [...rankedSports];
      [newRanked[index], newRanked[index - 1]] = [newRanked[index - 1], newRanked[index]];
      setRankedSports(newRanked);
    }
  };

  const moveSportDown = (index: number) => {
    if (index < rankedSports.length - 1) {
      const newRanked = [...rankedSports];
      [newRanked[index], newRanked[index + 1]] = [newRanked[index + 1], newRanked[index]];
      setRankedSports(newRanked);
    }
  };

  const toggleTeamSelection = (teamId: string, sportId: string) => {
    setSelectedTeams(prev => {
      const exists = prev.find(t => t.team_id === teamId);
      if (exists) {
        return prev.filter(t => t.team_id !== teamId);
      } else {
        return [...prev, { team_id: teamId, sport_id: sportId }];
      }
    });
  };

  const renderSportsSelection = () => (
    <div className="space-y-6">
      <div className="text-center">
        <Trophy className="h-12 w-12 mx-auto mb-4 text-blue-600" />
        <h2 className="text-2xl font-bold mb-2">Choose Your Sports</h2>
        <p className="text-gray-600">Select the sports you're most interested in following</p>
      </div>

      {sportsLoading && (
        <div className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span>Loading sports...</span>
        </div>
      )}

      {sportsError && (
        <div className="flex items-center justify-center p-8 text-red-600">
          <AlertCircle className="h-6 w-6 mr-2" />
          <span>Error loading sports: {sportsError.message}</span>
        </div>
      )}

      {!sportsLoading && !sportsError && sports.length === 0 && (
        <div className="flex items-center justify-center p-8 text-gray-500">
          <span>No sports available</span>
        </div>
      )}

      {!sportsLoading && sports.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sports.map(sport => (
            <Card
              key={sport.id}
              className={`p-4 cursor-pointer transition-all hover:shadow-md ${
                selectedSports.includes(sport.id)
                  ? 'ring-2 ring-blue-500 bg-blue-50'
                  : 'hover:bg-gray-50'
              }`}
              onClick={() => toggleSportSelection(sport.id)}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold">{sport.name}</h3>
                  <p className="text-sm text-gray-600">{sport.description}</p>
                </div>
                {selectedSports.includes(sport.id) && (
                  <Check className="h-5 w-5 text-blue-600" />
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-md">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      <div className="flex justify-end">
        <Button
          onClick={handleSportsSelection}
          disabled={submitting || !Array.isArray(selectedSports) || selectedSports.length === 0}
          className="min-w-32"
        >
          {submitting ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <ChevronRight className="h-4 w-4 mr-2" />
          )}
          {submitting ? 'Saving...' : 'Continue'}
        </Button>
      </div>
    </div>
  );

  const renderSportsRanking = () => (
    <div className="space-y-6">
      <div className="text-center">
        <Star className="h-12 w-12 mx-auto mb-4 text-yellow-600" />
        <h2 className="text-2xl font-bold mb-2">Rank Your Sports</h2>
        <p className="text-gray-600">Drag to reorder your sports by preference (most favorite first)</p>
      </div>

      <div className="space-y-3 max-w-md mx-auto">
        {rankedSports.map((sportId, index) => {
          const sport = sports.find(s => s.id === sportId);
          return (
            <Card key={sportId} className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="bg-blue-100 text-blue-800 text-sm font-medium px-2 py-1 rounded">
                    #{index + 1}
                  </span>
                  <span className="font-medium">{sport?.name}</span>
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => moveSportUp(index)}
                    disabled={index === 0}
                  >
                    ↑
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => moveSportDown(index)}
                    disabled={!Array.isArray(rankedSports) || index === rankedSports.length - 1}
                  >
                    ↓
                  </Button>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {error && (
        <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-md">
          <AlertCircle className="h-4 w-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      <div className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => setCurrentStep('sports_selection')}
          disabled={submitting}
        >
          <ChevronLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <Button
          onClick={handleSportsRanking}
          disabled={submitting}
          className="min-w-32"
        >
          {submitting ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <ChevronRight className="h-4 w-4 mr-2" />
          )}
          {submitting ? 'Saving...' : 'Continue'}
        </Button>
      </div>
    </div>
  );

  const renderTeamsSelection = () => {
    const teamsBySport = teams.reduce((acc, team) => {
      if (!acc[team.sport_id]) acc[team.sport_id] = [];
      acc[team.sport_id].push(team);
      return acc;
    }, {} as Record<string, Team[]>);

    const handleTeamSelect = (teamId: string, sportId: string) => {
      if (teamId && teamId !== 'none') {
        toggleTeamSelection(teamId, sportId);
      }
    };

    return (
      <div className="space-y-6">
        <div className="text-center">
          <Users className="h-12 w-12 mx-auto mb-4 text-green-600" />
          <h2 className="text-2xl font-bold mb-2">Choose Your Teams</h2>
          <p className="text-gray-600">Select your favorite teams from your chosen sports using the dropdown menus</p>
        </div>

        {Object.entries(teamsBySport).map(([sportId, sportTeams]) => {
          const typedSportTeams = sportTeams as Team[];
          const sport = sports.find(s => s.id === sportId);
          const selectedTeamForSport = selectedTeams.find(t => t.sport_id === sportId);

          return (
            <div key={sportId} className="space-y-3">
              <h3 className="text-lg font-semibold text-gray-800">{sport?.name}</h3>
              <div className="max-w-md">
                <Select
                  value={selectedTeamForSport?.team_id || 'none'}
                  onValueChange={(value) => {
                    // Remove existing selection for this sport first
                    if (selectedTeamForSport) {
                      toggleTeamSelection(selectedTeamForSport.team_id, sportId);
                    }
                    // Add new selection if not 'none'
                    if (value !== 'none') {
                      handleTeamSelect(value, sportId);
                    }
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={`Select a ${sport?.name} team`} />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No team selected</SelectItem>
                    {typedSportTeams.map((team: Team) => (
                      <SelectItem key={team.id} value={team.id}>
                        {team.name} ({team.city})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Show selected teams for this sport */}
              {Array.isArray(selectedTeams) && selectedTeams.filter(t => t.sport_id === sportId).length > 0 && (
                <div className="mt-2">
                  <p className="text-sm text-gray-600 mb-2">Selected teams:</p>
                  <div className="flex flex-wrap gap-2">
                    {selectedTeams
                      .filter(t => t.sport_id === sportId)
                      .map(selectedTeam => {
                        const team = typedSportTeams.find((t: Team) => t.id === selectedTeam.team_id);
                        return (
                          <div key={selectedTeam.team_id} className="flex items-center gap-2 bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                            <span>{team?.name}</span>
                            <button
                              onClick={() => toggleTeamSelection(selectedTeam.team_id, sportId)}
                              className="hover:bg-green-200 rounded-full p-1"
                            >
                              ×
                            </button>
                          </div>
                        );
                      })
                    }
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {error && (
          <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-md">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={() => setCurrentStep(Array.isArray(selectedSports) && selectedSports.length > 1 ? 'sports_ranking' : 'sports_selection')}
            disabled={submitting}
          >
            <ChevronLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <Button
            onClick={handleTeamsSelection}
            disabled={submitting || !Array.isArray(selectedTeams) || selectedTeams.length === 0}
            className="min-w-32"
          >
            {submitting ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Check className="h-4 w-4 mr-2" />
            )}
            {submitting ? 'Saving...' : 'Complete'}
          </Button>
        </div>
      </div>
    );
  };

  const renderCompleted = () => (
    <div className="text-center space-y-6">
      <div className="bg-green-100 rounded-full w-20 h-20 flex items-center justify-center mx-auto">
        <Check className="h-10 w-10 text-green-600" />
      </div>
      <div>
        <h2 className="text-2xl font-bold mb-2">Welcome to Corner League!</h2>
        <p className="text-gray-600 mb-6">
          Your preferences have been saved. You'll now see personalized content based on your interests.
        </p>
        <Button onClick={() => setLocation('/')} className="min-w-32">
          Get Started
        </Button>
      </div>
    </div>
  );

  if (loading) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
            <p className="text-gray-600">Loading questionnaire...</p>
          </div>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center py-4">
              <div className="flex items-center">
                <h1 className="text-xl font-black text-black tracking-tight">
                  Corner League
                </h1>
              </div>
              <div className="text-sm text-gray-500">
                Step {currentStep === 'sports_selection' ? '1' : currentStep === 'sports_ranking' ? '2' : currentStep === 'teams_selection' ? '3' : '4'} of 3
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Card className="p-8">
            {currentStep === 'sports_selection' && renderSportsSelection()}
            {currentStep === 'sports_ranking' && renderSportsRanking()}
            {currentStep === 'teams_selection' && renderTeamsSelection()}
            {currentStep === 'completed' && renderCompleted()}
          </Card>
        </main>
      </div>
    </ProtectedRoute>
  );
}
