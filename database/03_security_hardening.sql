-- 1. Doktor yalnızca kendisine atanmış hastaların konumlarını görebilir.
DROP POLICY IF EXISTS doctor_location_access ON public.locations;

CREATE POLICY doctor_location_access
ON public.locations
FOR SELECT
TO doctor_role
USING (
    public.doctor_can_access_patient(patient_id)
);
GRANT SELECT ON public.locations TO doctor_role;

-- 2. Doktor kendi hastasının uyruk bilgisini de görebilir.
GRANT SELECT (nationality)
ON public.patients TO doctor_role;

-- 3. Tablo sahiplerinin RLS'yi otomatik aşmasını engelle.
ALTER TABLE public.patients FORCE ROW LEVEL SECURITY;
ALTER TABLE public.health_records FORCE ROW LEVEL SECURITY;
ALTER TABLE public.locations FORCE ROW LEVEL SECURITY;
-- Analist görünümleri için ayrı ve kısıtlı sahip rolü
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles
        WHERE rolname = 'analyst_view_owner'
    ) THEN
        CREATE ROLE analyst_view_owner NOLOGIN;
    END IF;
END
$$;

-- Görünüm sahibine gerekli okuma yetkileri
GRANT SELECT ON public.patients,
                public.health_records
TO analyst_view_owner;

-- FORCE RLS nedeniyle görünüm sahibinin erişeceği satırları tanımla
DROP POLICY IF EXISTS analyst_view_patients ON public.patients;

CREATE POLICY analyst_view_patients
ON public.patients
FOR SELECT
TO analyst_view_owner
USING (true);

DROP POLICY IF EXISTS analyst_view_health ON public.health_records;

CREATE POLICY analyst_view_health
ON public.health_records
FOR SELECT
TO analyst_view_owner
USING (true);

-- Görünümlerin sahipliğini superuser olmayan role aktar
ALTER VIEW public.anonymized_patients
OWNER TO analyst_view_owner;

ALTER VIEW public.epidemiological_summary
OWNER TO analyst_view_owner;