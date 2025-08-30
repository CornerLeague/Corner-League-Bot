-- Migration: Create questionnaire tables for user sports preferences
-- Created: 2024-01-17
-- Description: Creates tables for sports, teams, user preferences, and questionnaire tracking

-- Create sports table
CREATE TABLE IF NOT EXISTS sports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    has_teams BOOLEAN NOT NULL DEFAULT true,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create index on sports for performance
CREATE INDEX IF NOT EXISTS idx_sports_active_order ON sports(is_active, display_order);
CREATE INDEX IF NOT EXISTS idx_sports_slug ON sports(slug);

-- Create teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sport_id UUID NOT NULL REFERENCES sports(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    city VARCHAR(100),
    abbreviation VARCHAR(10),
    league VARCHAR(50),
    conference VARCHAR(50),
    division VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT true,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(sport_id, slug)
);

-- Create indexes on teams for performance
CREATE INDEX IF NOT EXISTS idx_teams_sport_id ON teams(sport_id);
CREATE INDEX IF NOT EXISTS idx_teams_active ON teams(is_active);
CREATE INDEX IF NOT EXISTS idx_teams_league ON teams(league);
CREATE INDEX IF NOT EXISTS idx_teams_slug ON teams(sport_id, slug);

-- Create user sport preferences table
CREATE TABLE IF NOT EXISTS user_sport_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL, -- Clerk user ID
    sport_id UUID NOT NULL REFERENCES sports(id) ON DELETE CASCADE,
    preference_order INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, sport_id)
);

-- Create indexes on user sport preferences
CREATE INDEX IF NOT EXISTS idx_user_sport_prefs_user_id ON user_sport_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sport_prefs_order ON user_sport_preferences(user_id, preference_order);

-- Create user team preferences table
CREATE TABLE IF NOT EXISTS user_team_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL, -- Clerk user ID
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    preference_order INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, team_id)
);

-- Create indexes on user team preferences
CREATE INDEX IF NOT EXISTS idx_user_team_prefs_user_id ON user_team_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_team_prefs_order ON user_team_preferences(user_id, preference_order);

-- Create questionnaire responses table for tracking individual answers
CREATE TABLE IF NOT EXISTS questionnaire_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL, -- Clerk user ID
    question_type VARCHAR(50) NOT NULL, -- 'sports_selection', 'sports_ranking', 'teams_selection'
    question_data JSONB, -- Store question context
    answer_data JSONB NOT NULL, -- Store the actual answer
    step_order INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes on questionnaire responses
CREATE INDEX IF NOT EXISTS idx_questionnaire_responses_user_id ON questionnaire_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_questionnaire_responses_type ON questionnaire_responses(question_type);
CREATE INDEX IF NOT EXISTS idx_questionnaire_responses_user_step ON questionnaire_responses(user_id, step_order);

-- Create user questionnaire status table for tracking completion
CREATE TABLE IF NOT EXISTS user_questionnaire_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL UNIQUE, -- Clerk user ID
    is_completed BOOLEAN NOT NULL DEFAULT false,
    current_step VARCHAR(50), -- Current step in questionnaire
    completed_steps TEXT[], -- Array of completed step names
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes on user questionnaire status
CREATE INDEX IF NOT EXISTS idx_user_questionnaire_status_user_id ON user_questionnaire_status(user_id);
CREATE INDEX IF NOT EXISTS idx_user_questionnaire_status_completed ON user_questionnaire_status(is_completed);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_sports_updated_at BEFORE UPDATE ON sports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teams_updated_at BEFORE UPDATE ON teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_sport_preferences_updated_at BEFORE UPDATE ON user_sport_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_team_preferences_updated_at BEFORE UPDATE ON user_team_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_questionnaire_responses_updated_at BEFORE UPDATE ON questionnaire_responses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_questionnaire_status_updated_at BEFORE UPDATE ON user_questionnaire_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data for testing (optional)
-- This will be replaced by the seed script

COMMIT;
