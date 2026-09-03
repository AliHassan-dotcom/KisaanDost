-- Kisaan Dost PostgreSQL Schema Definition (Phase 12)
-- Minimum supported version: PostgreSQL 14+

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50),
    district VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_district ON users (district);

-- 2. Crop Scans Table
CREATE TABLE IF NOT EXISTS crop_scans (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    image_path VARCHAR(500) NOT NULL,
    predicted_disease VARCHAR(255) NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    model_version VARCHAR(50) DEFAULT 'v2' NOT NULL,
    district VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_crop_scans_user_id ON crop_scans (user_id);
CREATE INDEX IF NOT EXISTS idx_crop_scans_district ON crop_scans (district);

-- 3. Weather Cache Table
CREATE TABLE IF NOT EXISTS weather_cache (
    id VARCHAR(36) PRIMARY KEY,
    district VARCHAR(100) NOT NULL,
    temperature_2m DOUBLE PRECISION,
    relative_humidity_2m DOUBLE PRECISION,
    precipitation DOUBLE PRECISION DEFAULT 0.0,
    wind_speed_10m DOUBLE PRECISION,
    status VARCHAR(50) DEFAULT 'live' NOT NULL,
    source_url VARCHAR(500),
    retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_weather_cache_district ON weather_cache (district);

-- 4. Market Prices Table
CREATE TABLE IF NOT EXISTS market_prices (
    id VARCHAR(36) PRIMARY KEY,
    price_date VARCHAR(20) NOT NULL,
    province VARCHAR(100) DEFAULT 'Punjab' NOT NULL,
    district VARCHAR(100),
    market_name VARCHAR(100) NOT NULL,
    market_id_or_source_label VARCHAR(100),
    commodity_name VARCHAR(100) NOT NULL,
    commodity_id INTEGER,
    variety VARCHAR(100),
    min_price_pkr DOUBLE PRECISION,
    max_price_pkr DOUBLE PRECISION,
    fqp_price_pkr DOUBLE PRECISION,
    quantity DOUBLE PRECISION,
    unit VARCHAR(50) DEFAULT '100 Kg' NOT NULL,
    source_name VARCHAR(100) DEFAULT 'AMIS Punjab' NOT NULL,
    source_url VARCHAR(500),
    source_displayed_date VARCHAR(50),
    retrieved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    data_status VARCHAR(50) DEFAULT 'live' NOT NULL,
    validation_status VARCHAR(50) DEFAULT 'pass' NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_prices_date ON market_prices (price_date);
CREATE INDEX IF NOT EXISTS idx_market_prices_market ON market_prices (market_name);
CREATE INDEX IF NOT EXISTS idx_market_prices_commodity ON market_prices (commodity_name);
CREATE INDEX IF NOT EXISTS idx_market_prices_district ON market_prices (district);

-- 5. User Preferences Table
CREATE TABLE IF NOT EXISTS user_preferences (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE REFERENCES users (id) ON DELETE CASCADE,
    selected_crops JSONB DEFAULT '[]'::jsonb NOT NULL,
    primary_district VARCHAR(100) DEFAULT 'Lahore District' NOT NULL,
    primary_market VARCHAR(100) DEFAULT 'Lahore' NOT NULL,
    alert_types JSONB DEFAULT '["weather", "market", "advisory"]'::jsonb NOT NULL,
    notification_channels JSONB DEFAULT '["in_app", "local"]'::jsonb NOT NULL,
    threshold_settings JSONB DEFAULT '{}'::jsonb NOT NULL,
    fcm_config_status VARCHAR(50) DEFAULT 'not_configured' NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id ON user_preferences (user_id);

-- 6. Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    body_urdu TEXT,
    severity VARCHAR(50) DEFAULT 'info' NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    read_at TIMESTAMP WITH TIME ZONE,
    source_attribution VARCHAR(255) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications (user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications (created_at);

-- 7. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users (id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    status_code INTEGER NOT NULL,
    ip_address VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs (created_at);

-- 8. Migration Metadata Table
CREATE TABLE IF NOT EXISTS migration_metadata (
    id VARCHAR(36) PRIMARY KEY,
    migration_name VARCHAR(100) NOT NULL,
    migrated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    source_json_snapshot_hash VARCHAR(64) NOT NULL,
    row_counts JSONB DEFAULT '{}'::jsonb NOT NULL,
    status VARCHAR(50) DEFAULT 'success' NOT NULL
);
