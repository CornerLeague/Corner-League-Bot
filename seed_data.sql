-- Seed test data for sports media platform

-- Insert test sources
INSERT INTO sources (id, name, domain, base_url, source_type, rss_url, is_active, created_at, updated_at) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'ESPN', 'espn.com', 'https://espn.com', 'rss', 'https://espn.com/rss', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440002', 'The Athletic', 'theathletic.com', 'https://theathletic.com', 'rss', 'https://theathletic.com/rss', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440003', 'NFL.com', 'nfl.com', 'https://nfl.com', 'rss', 'https://nfl.com/rss', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440004', 'Bleacher Report', 'bleacherreport.com', 'https://bleacherreport.com', 'rss', 'https://bleacherreport.com/rss', true, NOW(), NOW()),
('550e8400-e29b-41d4-a716-446655440005', 'MLB.com', 'mlb.com', 'https://mlb.com', 'rss', 'https://mlb.com/rss', true, NOW(), NOW());

-- Insert test content items
INSERT INTO content_items (id, title, summary, canonical_url, original_url, source_id, sports_keywords, content_type, published_at, created_at, updated_at, quality_score, content_hash) VALUES
('660e8400-e29b-41d4-a716-446655440001',
 'Dodgers Win World Series in Dramatic Fashion',
 'The Los Angeles Dodgers defeated the Yankees 4-1 in the World Series, with Mookie Betts leading the charge with clutch hitting throughout the series.',
 'https://example.com/dodgers-world-series-win',
 'https://example.com/dodgers-world-series-win',
 '550e8400-e29b-41d4-a716-446655440001',
 '["dodgers", "world series", "mookie betts", "baseball", "mlb", "yankees", "championship"]',
 'article',
 NOW() - INTERVAL '1 day',
 NOW(),
 NOW(),
 0.95,
 'hash001'),

('660e8400-e29b-41d4-a716-446655440002',
 'Lakers Trade Rumors Heat Up Before Deadline',
 'The Los Angeles Lakers are reportedly exploring trade options to bolster their roster for a playoff push, with several role players mentioned in discussions.',
 'https://example.com/lakers-trade-rumors',
 'https://example.com/lakers-trade-rumors',
 '550e8400-e29b-41d4-a716-446655440002',
 '["lakers", "nba", "trade deadline", "lebron james", "anthony davis", "basketball"]',
 'article',
 NOW() - INTERVAL '2 hours',
 NOW(),
 NOW(),
 0.88,
 'hash002'),

('660e8400-e29b-41d4-a716-446655440003',
 'Rams Prepare for Playoff Push with Key Additions',
 'The Los Angeles Rams have made several key acquisitions as they prepare for the NFL playoffs, strengthening both their offensive and defensive units.',
 'https://example.com/rams-playoff-preparation',
 'https://example.com/rams-playoff-preparation',
 '550e8400-e29b-41d4-a716-446655440003',
 '["rams", "nfl", "playoffs", "sean mcvay", "bobby wagner", "football"]',
 'article',
 NOW() - INTERVAL '4 hours',
 NOW(),
 NOW(),
 0.92,
 'hash003'),

('660e8400-e29b-41d4-a716-446655440004',
 'Kings Make Coaching Change Mid-Season',
 'The Sacramento Kings have fired their head coach and named an interim replacement as the team struggles to meet expectations this season.',
 'https://example.com/kings-coaching-change',
 'https://example.com/kings-coaching-change',
 '550e8400-e29b-41d4-a716-446655440004',
 '["kings", "nba", "coaching change", "mike brown", "alvin gentry", "basketball", "sacramento"]',
 'article',
 NOW() - INTERVAL '6 hours',
 NOW(),
 NOW(),
 0.85,
 'hash004'),

('660e8400-e29b-41d4-a716-446655440005',
 'Dodgers Sign Star Pitcher to Record Contract',
 'The Los Angeles Dodgers have signed Japanese pitcher Yoshinobu Yamamoto to a record-breaking 12-year, $325 million contract.',
 'https://example.com/dodgers-yamamoto-signing',
 'https://example.com/dodgers-yamamoto-signing',
 '550e8400-e29b-41d4-a716-446655440005',
 '["dodgers", "yoshinobu yamamoto", "mlb", "baseball", "free agency", "contract", "pitcher"]',
 'article',
 NOW() - INTERVAL '8 hours',
 NOW(),
 NOW(),
 0.93,
 'hash005'),

('660e8400-e29b-41d4-a716-446655440006',
 'UCLA Basketball Upsets Top-Ranked Duke',
 'UCLA''s basketball team pulled off a stunning upset victory over #1 ranked Duke in a thrilling overtime game at Pauley Pavilion.',
 'https://example.com/ucla-upsets-duke',
 'https://example.com/ucla-upsets-duke',
 '550e8400-e29b-41d4-a716-446655440001',
 '["ucla", "duke", "college basketball", "upset", "jaylen clark", "pauley pavilion"]',
 'article',
 NOW() - INTERVAL '12 hours',
 NOW(),
 NOW(),
 0.90,
 'hash006');

-- Insert test users
INSERT INTO users (id, email, username, full_name, created_at, updated_at) VALUES
('770e8400-e29b-41d4-a716-446655440001', 'test@example.com', 'testuser', 'Test User', NOW(), NOW());

-- Insert test ingestion jobs (checking required columns first)
-- Note: ingestion_jobs table requires job_type column
INSERT INTO ingestion_jobs (id, source_id, job_type, status, started_at, completed_at, items_processed, created_at, updated_at) VALUES
('880e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'rss_crawl', 'completed', NOW() - INTERVAL '1 day', NOW() - INTERVAL '23 hours', 25, NOW(), NOW()),
('880e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440002', 'rss_crawl', 'completed', NOW() - INTERVAL '12 hours', NOW() - INTERVAL '11 hours', 18, NOW(), NOW()),
('880e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440003', 'rss_crawl', 'running', NOW() - INTERVAL '2 hours', NULL, 12, NOW(), NOW());
