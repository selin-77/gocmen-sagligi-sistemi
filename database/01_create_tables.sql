-- PostGIS Extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Patients Table
CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    passport_number VARCHAR(50),
    nationality VARCHAR(50),
    birth_date DATE,
    gender VARCHAR(10),
    phone VARCHAR(20)
);

-- Health Records Table
CREATE TABLE health_records (
    record_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(patient_id),
    disease_name VARCHAR(100),
    chronic_disease BOOLEAN,
    vaccination_status VARCHAR(50),
    risk_score INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Locations Table
CREATE TABLE locations (
    location_id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(patient_id),
    border_name VARCHAR(100),
    entry_time TIMESTAMP,
    geom GEOMETRY(Point, 4326)
);