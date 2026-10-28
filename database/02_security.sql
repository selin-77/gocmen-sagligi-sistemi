
-- Göçmen Sağlığı Sistemi: Rol Bazlı Güvenlik ve RLS
-- PostgreSQL 15+
-- Bu dosyayı veritabanı yöneticisi yetkisiyle çalıştırın.

RESET ROLE;

-- 1. Güvenlik rolleri
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'doctor_role'
    ) THEN
        CREATE ROLE doctor_role NOLOGIN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'analyst_role'
    ) THEN
        CREATE ROLE analyst_role NOLOGIN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'unauthorized_role'
    ) THEN
        CREATE ROLE unauthorized_role NOLOGIN;
    END IF;
END
$$;

-- 2. Ham tablolardaki rol izinlerini sınırla
REVOKE ALL ON TABLE patients, health_records, locations
FROM PUBLIC, doctor_role, analyst_role, unauthorized_role;

-- 3. Satır düzeyinde güvenliği etkinleştir
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE locations ENABLE ROW LEVEL SECURITY;

-- 4. Doktor politikaları
DROP POLICY IF EXISTS doctor_health_access ON health_records;
CREATE POLICY doctor_health_access
ON health_records
FOR SELECT
TO doctor_role
USING (true);

DROP POLICY IF EXISTS doctor_patient_access ON patients;
CREATE POLICY doctor_patient_access
ON patients
FOR SELECT
TO doctor_role
USING (true);

-- Doktor sağlık kayıtlarını okuyabilir
GRANT SELECT ON TABLE health_records TO doctor_role;

-- Doktor yalnızca temel hasta bilgilerini okuyabilir
GRANT SELECT (patient_id, first_name, last_name)
ON TABLE patients TO doctor_role;

-- 5. Analist için toplulaştırılmış epidemiyolojik görünüm
CREATE OR REPLACE VIEW epidemiological_summary AS
SELECT
    disease_name,
    chronic_disease,
    vaccination_status,
    COUNT(*) AS record_count,
    ROUND(AVG(risk_score), 2) AS average_risk_score
FROM health_records
GROUP BY
    disease_name,
    chronic_disease,
    vaccination_status;

-- Görünümün erişimini açıkça sınırla
REVOKE ALL ON epidemiological_summary
FROM PUBLIC, doctor_role, analyst_role, unauthorized_role;

GRANT SELECT ON epidemiological_summary TO analyst_role;

-- Not: Doktor politikaları tüm satırlara izin verir.
-- Hastaya özel satır kısıtlaması için ek eşleştirme gerekir.
-- Uygulama kullanıcıları için ayrıca LOGIN rolleri tanımlanmalıdır.
-- 6. Kişisel bilgileri maskeleyen görünüm
CREATE OR REPLACE VIEW anonymized_patients AS
SELECT
    patient_id,
    LEFT(first_name, 1) || '***' AS first_name,
    '***' AS last_name,
    '***' AS passport_number,
    nationality,
    birth_date,
    gender,
    '***' AS phone
FROM patients;

-- Yetkisiz erişimi kapat, yalnızca analiste izin ver
REVOKE ALL ON anonymized_patients
FROM PUBLIC, doctor_role, analyst_role, unauthorized_role;

GRANT SELECT ON anonymized_patients TO analyst_role;

-- 7. Sağlık kaydı oluşturulurken tarih alanını otomatik doldur
CREATE OR REPLACE FUNCTION set_health_record_created_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.created_at IS NULL THEN
        NEW.created_at := CURRENT_TIMESTAMP;
    END IF;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_health_record_created_at
ON health_records;

CREATE TRIGGER trg_health_record_created_at
BEFORE INSERT ON health_records
FOR EACH ROW
EXECUTE FUNCTION set_health_record_created_at();