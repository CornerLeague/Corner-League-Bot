/**
 * UserProfile Component
 *
 * A comprehensive user profile component that displays user information,
 * preferences, and provides access to account management features.
 */

import { useUser, useAuth } from '@clerk/clerk-react';
import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  User,
  Settings,
  Bell,
  Shield,
  Activity,
  Calendar,
  Mail,
  Phone,
  MapPin,
  Edit3,
  Save,
  X
} from 'lucide-react';
import { FavoriteTeamSelector } from './FavoriteTeamSelector';

interface UserPreferences {
  emailNotifications: boolean;
  pushNotifications: boolean;
  sportsInterests: string[];
  preferredLanguage: string;
  timezone: string;
  favorite_teams: string[];
}

export function UserProfile() {
  const { user, isLoaded } = useUser();
  const { getToken } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [preferences, setPreferences] = useState<UserPreferences>({
    emailNotifications: true,
    pushNotifications: false,
    sportsInterests: [],
    preferredLanguage: 'en',
    timezone: 'UTC',
    favorite_teams: []
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isLoaded && user) {
      loadUserPreferences();
    }
  }, [isLoaded, user]);

  const loadUserPreferences = async () => {
    try {
      const token = await getToken();
      const response = await fetch('/api/auth/preferences', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPreferences({
          emailNotifications: data.notification_email ?? true,
          pushNotifications: data.notification_push ?? false,
          sportsInterests: data.favorite_sports ?? [],
          preferredLanguage: 'en',
          timezone: 'UTC',
          favorite_teams: data.favorite_teams ?? []
        });
      }
    } catch (error) {
      console.error('Failed to load user preferences:', error);
    }
  };

  const savePreferences = async () => {
    setLoading(true);
    try {
      const token = await getToken();
      const response = await fetch('/api/auth/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          favorite_teams: preferences.favorite_teams,
          favorite_sports: preferences.sportsInterests,
          notification_email: preferences.emailNotifications,
          notification_push: preferences.pushNotifications
        })
      });

      if (response.ok) {
        setIsEditing(false);
      } else {
        throw new Error('Failed to save preferences');
      }
    } catch (error) {
      console.error('Failed to save preferences:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isLoaded || !user) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-pulse">Loading profile...</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Profile Header */}
      <Card className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-16 w-16 rounded-full bg-blue-100 flex items-center justify-center">
              {user.imageUrl ? (
                <img
                  src={user.imageUrl}
                  alt={user.fullName || 'User'}
                  className="h-16 w-16 rounded-full object-cover"
                />
              ) : (
                <User className="h-8 w-8 text-blue-600" />
              )}
            </div>
            <div>
              <h1 className="text-2xl font-bold">
                {user.fullName || user.username || 'User'}
              </h1>
              <p className="text-gray-600">{user.primaryEmailAddress?.emailAddress}</p>
              <p className="text-sm text-gray-500">
                Member since {new Date(user.createdAt!).toLocaleDateString()}
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            onClick={() => setIsEditing(!isEditing)}
            disabled={loading}
          >
            {isEditing ? (
              <>
                <X className="h-4 w-4 mr-2" />
                Cancel
              </>
            ) : (
              <>
                <Edit3 className="h-4 w-4 mr-2" />
                Edit Profile
              </>
            )}
          </Button>
        </div>
      </Card>

      {/* Contact Information */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <Mail className="h-5 w-5 mr-2" />
          Contact Information
        </h2>
        <div className="space-y-3">
          <div className="flex items-center space-x-3">
            <Mail className="h-4 w-4 text-gray-400" />
            <span>{user.primaryEmailAddress?.emailAddress}</span>
            {user.primaryEmailAddress?.verification?.status === 'verified' && (
              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                Verified
              </span>
            )}
          </div>
          {user.primaryPhoneNumber && (
            <div className="flex items-center space-x-3">
              <Phone className="h-4 w-4 text-gray-400" />
              <span>{user.primaryPhoneNumber.phoneNumber}</span>
            </div>
          )}
        </div>
      </Card>

      {/* Preferences */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center">
            <Settings className="h-5 w-5 mr-2" />
            Preferences
          </h2>
          {isEditing && (
            <Button onClick={savePreferences} disabled={loading}>
              <Save className="h-4 w-4 mr-2" />
              {loading ? 'Saving...' : 'Save Changes'}
            </Button>
          )}
        </div>

        <div className="space-y-4">
          {/* Notifications */}
          <div>
            <h3 className="font-medium mb-2 flex items-center">
              <Bell className="h-4 w-4 mr-2" />
              Notifications
            </h3>
            <div className="space-y-2 ml-6">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={preferences.emailNotifications}
                  onChange={(e) => setPreferences(prev => ({
                    ...prev,
                    emailNotifications: e.target.checked
                  }))}
                  disabled={!isEditing}
                  className="rounded"
                />
                <span>Email notifications</span>
              </label>
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={preferences.pushNotifications}
                  onChange={(e) => setPreferences(prev => ({
                    ...prev,
                    pushNotifications: e.target.checked
                  }))}
                  disabled={!isEditing}
                  className="rounded"
                />
                <span>Push notifications</span>
              </label>
            </div>
          </div>

          {/* Language & Region */}
          <div>
            <h3 className="font-medium mb-2">Language & Region</h3>
            <div className="space-y-2 ml-6">
              <div>
                <label className="block text-sm text-gray-600 mb-1">Language</label>
                <select
                  value={preferences.preferredLanguage}
                  onChange={(e) => setPreferences(prev => ({
                    ...prev,
                    preferredLanguage: e.target.value
                  }))}
                  disabled={!isEditing}
                  className="border rounded px-3 py-1 text-sm"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">Timezone</label>
                <select
                  value={preferences.timezone}
                  onChange={(e) => setPreferences(prev => ({
                    ...prev,
                    timezone: e.target.value
                  }))}
                  disabled={!isEditing}
                  className="border rounded px-3 py-1 text-sm"
                >
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern Time</option>
                  <option value="America/Chicago">Central Time</option>
                  <option value="America/Denver">Mountain Time</option>
                  <option value="America/Los_Angeles">Pacific Time</option>
                </select>
              </div>
            </div>
          </div>

          {/* Favorite Teams */}
           <div>
             <FavoriteTeamSelector
                currentFavoriteTeams={preferences.favorite_teams}
                onSave={async (teams: string[]) => {
                  setPreferences(prev => ({
                    ...prev,
                    favorite_teams: teams
                  }));
                  await savePreferences();
                }}
                isEditing={isEditing}
                onCancel={() => setIsEditing(false)}
              />
           </div>
        </div>
      </Card>

      {/* Account Security */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <Shield className="h-5 w-5 mr-2" />
          Account Security
        </h2>
        <div className="space-y-3">
          <Button variant="outline" className="w-full justify-start">
            <Settings className="h-4 w-4 mr-2" />
            Manage Account Settings
          </Button>
          <Button variant="outline" className="w-full justify-start">
            <Activity className="h-4 w-4 mr-2" />
            View Login Activity
          </Button>
        </div>
      </Card>
    </div>
  );
}
