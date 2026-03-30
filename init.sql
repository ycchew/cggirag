-- CGGI Database Initialization Script

-- Create countries table
CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    region VARCHAR(100),
    income_group VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create CGGI reports table
CREATE TABLE IF NOT EXISTS cggi_reports (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    country_id INTEGER REFERENCES countries(id),
    overall_rank INTEGER,
    overall_score DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(year, country_id)
);

-- Create pillars table
CREATE TABLE IF NOT EXISTS pillars (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indicators table
CREATE TABLE IF NOT EXISTS indicators (
    id SERIAL PRIMARY KEY,
    pillar_id INTEGER REFERENCES pillars(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES cggi_reports(id),
    indicator_id INTEGER REFERENCES indicators(id),
    value DECIMAL(10, 4),
    rank INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_cggi_reports_year ON cggi_reports(year);
CREATE INDEX IF NOT EXISTS idx_cggi_reports_country ON cggi_reports(country_id);
CREATE INDEX IF NOT EXISTS idx_metrics_report ON metrics(report_id);
CREATE INDEX IF NOT EXISTS idx_metrics_indicator ON metrics(indicator_id);