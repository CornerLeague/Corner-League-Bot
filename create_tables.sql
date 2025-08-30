-- Create basic tables for the sports media platform

-- Sources table
CREATE TABLE IF NOT EXISTS sources (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL UNIQUE,
    base_url VARCHAR(500) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    crawl_frequency INTEGER DEFAULT 3600,
    is_active BOOLEAN DEFAULT true,
    robots_txt_url VARCHAR(500),
    sitemap_url VARCHAR(500),
    rss_url VARCHAR(500),
    quality_tier INTEGER DEFAULT 2,
    reputation_score FLOAT DEFAULT 0.5,
    success_rate FLOAT DEFAULT 1.0,
    avg_response_time FLOAT DEFAULT 0.0,
    language VARCHAR(10) DEFAULT 'en',
    country VARCHAR(10),
    sports_focus JSONB,
    content_selectors JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_crawled TIMESTAMP
);

-- Content items table
CREATE TABLE IF NOT EXISTS content_items (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    source_id VARCHAR(36) REFERENCES sources(id),
    original_url VARCHAR(1000) NOT NULL,
    canonical_url VARCHAR(1000) NOT NULL UNIQUE,
    content_hash VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    text TEXT,
    byline VARCHAR(200),
    summary TEXT,
    published_at TIMESTAMP,
    language VARCHAR(10) DEFAULT 'en',
    word_count INTEGER DEFAULT 0,
    image_url VARCHAR(1000),
    sports_keywords JSONB,
    entities JSONB,
    content_type VARCHAR(50),
    quality_score FLOAT DEFAULT 0.0,
    relevance_score FLOAT DEFAULT 0.0,
    engagement_score FLOAT DEFAULT 0.0,
    extraction_status VARCHAR(20) DEFAULT 'pending',
    last_extracted TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    last_error TEXT,
    is_active BOOLEAN DEFAULT true,
    is_duplicate BOOLEAN DEFAULT false,
    is_spam BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    username VARCHAR(50) UNIQUE,
    full_name VARCHAR(200),
    avatar_url VARCHAR(500),
    favorite_teams JSONB,
    favorite_sports JSONB,
    content_preferences JSONB,
    notification_settings JSONB,
    quality_threshold FLOAT DEFAULT 0.6,
    personalization_score FLOAT DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

-- Ingestion jobs table
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    source_id VARCHAR(36) REFERENCES sources(id),
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    items_discovered INTEGER DEFAULT 0,
    items_processed INTEGER DEFAULT 0,
    items_successful INTEGER DEFAULT 0,
    items_failed INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds FLOAT,
    result_summary JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sources_domain ON sources(domain);
CREATE INDEX IF NOT EXISTS idx_sources_active_tier ON sources(is_active, quality_tier);
CREATE INDEX IF NOT EXISTS idx_content_published ON content_items(published_at);
CREATE INDEX IF NOT EXISTS idx_content_quality ON content_items(quality_score);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

SELECT 'Tables created successfully!' as result;
