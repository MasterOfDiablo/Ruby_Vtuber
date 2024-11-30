-- Game Sessions
CREATE TABLE IF NOT EXISTS game_sessions (
    session_id CHAR(36) PRIMARY KEY,
    game_name VARCHAR(255) NOT NULL,
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    game_mode VARCHAR(50),
    difficulty VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    session_summary JSON,
    achievements JSON,
    notable_events JSON
) ENGINE=InnoDB;

-- Game Events
CREATE TABLE IF NOT EXISTS game_events (
    event_id CHAR(36) PRIMARY KEY,
    session_id CHAR(36),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    event_data JSON,
    impact_score FLOAT,
    FOREIGN KEY (session_id) REFERENCES game_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Stream Sessions
CREATE TABLE IF NOT EXISTS stream_sessions (
    session_id CHAR(36) PRIMARY KEY,
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    title VARCHAR(255),
    category VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    game_session_id CHAR(36),
    viewer_stats JSON,
    highlight_moments JSON,
    session_metrics JSON,
    FOREIGN KEY (game_session_id) REFERENCES game_sessions(session_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Viewer Interactions
CREATE TABLE IF NOT EXISTS viewer_interactions (
    interaction_id CHAR(36) PRIMARY KEY,
    session_id CHAR(36),
    viewer_id CHAR(36),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    interaction_type VARCHAR(100) NOT NULL,
    message TEXT,
    sentiment_score FLOAT,
    impact_level INT,
    context_tags JSON,
    FOREIGN KEY (session_id) REFERENCES stream_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Viewer Profiles
CREATE TABLE IF NOT EXISTS viewer_profiles (
    viewer_id CHAR(36) PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    first_seen TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP NULL,
    interaction_summary JSON,
    preferences JSON,
    engagement_metrics JSON,
    relationship_level INT
) ENGINE=InnoDB;

-- Performance Analytics
CREATE TABLE IF NOT EXISTS performance_analytics (
    analytic_id CHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metric_type VARCHAR(50) NOT NULL,
    time_period_start TIMESTAMP NOT NULL,
    time_period_end TIMESTAMP NOT NULL,
    metric_data JSON,
    insights JSON
) ENGINE=InnoDB;

-- Learning History
CREATE TABLE IF NOT EXISTS learning_history (
    entry_id CHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    category VARCHAR(50) NOT NULL,
    learned_pattern JSON,
    application_results JSON,
    effectiveness_score FLOAT
) ENGINE=InnoDB;

-- Stream Highlights
CREATE TABLE IF NOT EXISTS stream_highlights (
    highlight_id CHAR(36) PRIMARY KEY,
    session_id CHAR(36),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    highlight_type VARCHAR(100) NOT NULL,
    description TEXT,
    viewer_impact JSON,
    significance_score FLOAT,
    FOREIGN KEY (session_id) REFERENCES stream_sessions(session_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Create indexes for better query performance
CREATE INDEX idx_game_events_session ON game_events(session_id);
CREATE INDEX idx_game_events_type ON game_events(event_type);
CREATE INDEX idx_viewer_interactions_session ON viewer_interactions(session_id);
CREATE INDEX idx_viewer_interactions_viewer ON viewer_interactions(viewer_id);
CREATE INDEX idx_viewer_interactions_type ON viewer_interactions(interaction_type);
CREATE INDEX idx_stream_highlights_session ON stream_highlights(session_id);
CREATE INDEX idx_performance_analytics_type ON performance_analytics(metric_type);
CREATE INDEX idx_learning_history_category ON learning_history(category);

-- Create fulltext search index for viewer messages
CREATE FULLTEXT INDEX idx_viewer_interactions_message ON viewer_interactions(message);
