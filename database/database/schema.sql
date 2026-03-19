-- Создание базы данных
CREATE DATABASE beach_monitoring;

-- Подключение к базе
\c beach_monitoring;

-- Таблица пользователей (сотрудников)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    google_id VARCHAR(255) UNIQUE,
    role VARCHAR(50) DEFAULT 'employee' CHECK (role IN ('employee', 'manager')),
    calendar_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Таблица пляжных зон
CREATE TABLE beach_zones (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    polygon_data JSONB NOT NULL,
    center_lat DECIMAL(10, 8),
    center_lng DECIMAL(11, 8),
    color VARCHAR(20) DEFAULT '#FF0000',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Таблица посетителей
CREATE TABLE visitors (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER REFERENCES beach_zones(id) ON DELETE SET NULL,
    arrival_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    departure_time TIMESTAMP,
    used_sunbed BOOLEAN DEFAULT FALSE,
    used_float BOOLEAN DEFAULT FALSE,
    used_mattress BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (departure_time IS NULL OR departure_time >= arrival_time)
);

-- Таблица отчётов
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    zone_id INTEGER NOT NULL REFERENCES beach_zones(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    generated_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_data JSONB,
    google_doc_link VARCHAR(500),
    status VARCHAR(50) DEFAULT 'generated' CHECK (status IN ('generated', 'processing', 'error')),
    CHECK (end_date >= start_date)
);

-- Индексы для оптимизации
CREATE INDEX idx_visitors_arrival ON visitors(arrival_time);
CREATE INDEX idx_visitors_departure ON visitors(departure_time);
CREATE INDEX idx_visitors_zone ON visitors(zone_id);
CREATE INDEX idx_visitors_date ON visitors(DATE(arrival_time));
CREATE INDEX idx_reports_dates ON reports(start_date, end_date);
CREATE INDEX idx_reports_zone ON reports(zone_id);
CREATE INDEX idx_reports_generated ON reports(generated_at DESC);

-- Индекс для полнотекстового поиска
CREATE INDEX idx_visitors_notes ON visitors USING gin(to_tsvector('russian', COALESCE(notes, '')));

-- Функция обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для beach_zones
CREATE TRIGGER update_beach_zones_updated_at
    BEFORE UPDATE ON beach_zones
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Представление для активных посетителей
CREATE VIEW active_visitors AS
SELECT 
    v.*,
    bz.name as zone_name,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - v.arrival_time))/3600 as hours_on_beach
FROM visitors v
LEFT JOIN beach_zones bz ON v.zone_id = bz.id
WHERE v.departure_time IS NULL;

-- Функция для получения статистики за день
CREATE OR REPLACE FUNCTION get_daily_stats(p_date DATE)
RETURNS TABLE(
    zone_id INTEGER,
    zone_name VARCHAR,
    total_visitors BIGINT,
    sunbed_used BIGINT,
    float_used BIGINT,
    mattress_used BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        bz.id,
        bz.name,
        COUNT(v.id) as total_visitors,
        COUNT(v.id) FILTER (WHERE v.used_sunbed) as sunbed_used,
        COUNT(v.id) FILTER (WHERE v.used_float) as float_used,
        COUNT(v.id) FILTER (WHERE v.used_mattress) as mattress_used
    FROM beach_zones bz
    LEFT JOIN visitors v ON bz.id = v.zone_id 
        AND DATE(v.arrival_time) = p_date
    GROUP BY bz.id, bz.name;
END;
$$ LANGUAGE plpgsql;

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Сотрудники системы';
COMMENT ON TABLE beach_zones IS 'Пляжные зоны для наблюдения';
COMMENT ON TABLE visitors IS 'Посетители пляжа';
COMMENT ON TABLE reports IS 'Сгенерированные отчёты';
COMMENT ON COLUMN visitors.used_sunbed IS 'Использование шезлонга (Ш)';
COMMENT ON COLUMN visitors.used_float IS 'Использование плавсредства (П)';
COMMENT ON COLUMN visitors.used_mattress IS 'Использование матраса (М)';

-- Тестовые данные (опционально)
INSERT INTO beach_zones (name, description, polygon_data, center_lat, center_lng, color) VALUES 
('Центральный пляж', 'Основная зона пляжа с шезлонгами', 
 '[{"lat": 55.7558, "lng": 37.6173}, {"lat": 55.7559, "lng": 37.6174}, {"lat": 55.7557, "lng": 37.6175}]'::jsonb,
 55.7558, 37.6173, '#FF5733'),
('Детская зона', 'Мелкая вода, детские горки',
 '[{"lat": 55.7560, "lng": 37.6170}, {"lat": 55.7561, "lng": 37.6171}, {"lat": 55.7559, "lng": 37.6172}]'::jsonb,
 55.7560, 37.6171, '#33FF57');
