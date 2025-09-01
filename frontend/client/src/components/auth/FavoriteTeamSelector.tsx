/**
 * FavoriteTeamSelector Component
 *
 * A component for selecting and managing user's favorite teams.
 * Allows users to select a sport and then choose their favorite team from that sport.
 */

import { useState, useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Heart, Loader2, Save, X } from 'lucide-react';
import { useAvailableSports, useTeamsBySport } from '@/hooks/useQuestionnaire';

interface FavoriteTeamSelectorProps {
  currentFavoriteTeams?: string[];
  onSave: (favoriteTeams: string[]) => Promise<void>;
  isEditing: boolean;
  onCancel: () => void;
}

interface UserPreferences {
  favorite_teams: string[];
  favorite_sports: string[];
  content_types: string[];
  notification_email: boolean;
  notification_push: boolean;
  notification_frequency: string;
}

export function FavoriteTeamSelector({
  currentFavoriteTeams = [],
  onSave,
  isEditing,
  onCancel
}: FavoriteTeamSelectorProps) {
  const { getToken } = useAuth();
  const [selectedSport, setSelectedSport] = useState<string>('');
  const [selectedTeams, setSelectedTeams] = useState<string[]>(currentFavoriteTeams);
  const [loading, setSaving] = useState(false);
  const [userPreferences, setUserPreferences] = useState<UserPreferences | null>(null);
  const [loadingPreferences, setLoadingPreferences] = useState(true);

  // Fetch available sports
  const { data: sports, isLoading: sportsLoading } = useAvailableSports();

  // Fetch teams for selected sport
  const { data: teams, isLoading: teamsLoading } = useTeamsBySport(selectedSport);

  // Load user preferences on component mount
  useEffect(() => {
    const loadUserPreferences = async () => {
      try {
        const token = await getToken();
        const response = await fetch('/api/auth/preferences', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const preferences = await response.json();
          setUserPreferences(preferences);
          setSelectedTeams(preferences.favorite_teams || []);
        }
      } catch (error) {
        console.error('Failed to load user preferences:', error);
      } finally {
        setLoadingPreferences(false);
      }
    };

    loadUserPreferences();
  }, [getToken]);

  // Get team name by ID
  const getTeamName = (teamId: string) => {
    if (!teams?.teams) return teamId;
    const team = teams.teams.find((t: any) => t.id === teamId);
    return team ? `${team.city} ${team.name}` : teamId;
  };

  // Get sport name by ID
  const getSportName = (sportId: string) => {
    if (!sports?.sports) return sportId;
    const sport = sports.sports.find((s: any) => s.id === sportId);
    return sport ? sport.display_name : sportId;
  };

  // Find sport for a team
  const getTeamSport = async (teamId: string) => {
    if (!sports?.sports) return null;

    for (const sport of sports.sports) {
      try {
        const token = await getToken();
        const response = await fetch(`/api/questionnaire/sports/${sport.id}/teams`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.ok) {
          const sportTeams = await response.json();
          const team = sportTeams.find((t: any) => t.id === teamId);
          if (team) {
            return sport;
          }
        }
      } catch (error) {
        console.error(`Error fetching teams for sport ${sport.id}:`, error);
      }
    }
    return null;
  };

  const handleAddTeam = (teamId: string) => {
    if (!selectedTeams.includes(teamId)) {
      setSelectedTeams([...selectedTeams, teamId]);
    }
  };

  const handleRemoveTeam = (teamId: string) => {
    setSelectedTeams(selectedTeams.filter(id => id !== teamId));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(selectedTeams);
    } catch (error) {
      console.error('Failed to save favorite teams:', error);
    } finally {
      setSaving(false);
    }
  };

  if (loadingPreferences) {
    return (
      <div className="flex items-center justify-center p-4">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span className="ml-2">Loading preferences...</span>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium flex items-center">
          <Heart className="h-4 w-4 mr-2" />
          Favorite Teams
        </h3>
        {isEditing && (
          <div className="flex gap-2">
            <Button onClick={handleSave} disabled={loading} size="sm">
              <Save className="h-4 w-4 mr-2" />
              {loading ? 'Saving...' : 'Save'}
            </Button>
            <Button onClick={onCancel} variant="outline" size="sm">
              <X className="h-4 w-4 mr-2" />
              Cancel
            </Button>
          </div>
        )}
      </div>

      {/* Current Favorite Teams */}
      {selectedTeams.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Your Favorite Teams:</h4>
          <div className="flex flex-wrap gap-2">
            {selectedTeams.map((teamId) => (
              <div
                key={teamId}
                className="flex items-center gap-2 bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
              >
                <span>{getTeamName(teamId)}</span>
                {isEditing && (
                  <button
                    onClick={() => handleRemoveTeam(teamId)}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add New Favorite Team */}
      {isEditing && (
        <Card className="p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Add Favorite Team:</h4>

          <div className="space-y-3">
            {/* Sport Selection */}
            <div>
              <label className="block text-sm text-gray-600 mb-1">Select Sport:</label>
              <Select value={selectedSport} onValueChange={setSelectedSport}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a sport" />
                </SelectTrigger>
                <SelectContent>
                  {sportsLoading ? (
                    <SelectItem value="loading" disabled>
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                      Loading sports...
                    </SelectItem>
                  ) : (
                    sports?.sports?.map((sport: any) => (
                      <SelectItem key={sport.id} value={sport.id}>
                        {sport.display_name}
                      </SelectItem>
                    ))
                  )}
                </SelectContent>
              </Select>
            </div>

            {/* Team Selection */}
            {selectedSport && (
              <div>
                <label className="block text-sm text-gray-600 mb-1">Select Team:</label>
                <Select value="" onValueChange={handleAddTeam}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a team" />
                  </SelectTrigger>
                  <SelectContent>
                    {teamsLoading ? (
                      <SelectItem value="loading" disabled>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Loading teams...
                      </SelectItem>
                    ) : (
                      teams?.teams?.filter((team: any) => !selectedTeams.includes(team.id)).map((team: any) => (
                        <SelectItem key={team.id} value={team.id}>
                          {team.city} {team.name}
                        </SelectItem>
                      ))
                    )}
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Empty State */}
      {selectedTeams.length === 0 && !isEditing && (
        <div className="text-center py-8 text-gray-500">
          <Heart className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No favorite teams selected</p>
          <p className="text-sm">Click "Edit Profile" to add your favorite teams</p>
        </div>
      )}
    </div>
  );
}
