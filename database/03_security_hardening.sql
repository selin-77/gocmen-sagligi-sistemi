
-- =====================================================
-- GÖÇMEN SAĞLIĞI SİSTEMİ
-- 03 - SECURITY HARDENING
-- =====================================================


-- 1. DOKTOR ROLÜNÜ OLUŞTUR

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles
        WHERE rolname = 'doctor_role'
    ) THEN
        CREATE ROLE doctor_role NOLOGIN;
    END IF;
END
$$;


-- 2. HER DOKTOR İÇİN AYRI POSTGRESQL HESABI OLUŞTUR

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles
        WHERE rolname = 'doctor_test'
    ) THEN
        CREATE ROLE doctor_test LOGIN;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_roles
        WHERE rolname = 'doctor_test2'
    ) THEN
        CREATE ROLE doctor_test2 LOGIN;
    END IF;
END
$$;


-- 3. DOKTOR HESAPLARINI doctor_role GRUBUNA EKLE

GRANT doctor_role TO doctor_test;
GRANT doctor_role TO doctor_test2;


-- 4. DOKTORLARIN YALNIZCA ATANMIŞ HASTALARIN
-- KONUM BİLGİLERİNİ GÖREBİLMESİ

DROP POLICY IF EXISTS doctor_location_access
ON public.locations;

CREATE POLICY doctor_location_access
ON public.locations
FOR SELECT
TO doctor_role
USING (
    public.doctor_can_access_patient(patient_id)
);

GRANT SELECT ON public.locations TO doctor_role;


-- 5. DOKTORLARIN HASTALARIN UYRUK BİLGİSİNİ
-- GÖREBİLMESİ

GRANT SELECT (nationality)
ON public.patients
TO doctor_role;


-- 6. RLS GÜVENLİĞİ
-- Tablo sahipleri için FORCE ROW LEVEL SECURITY uygula.

ALTER TABLE public.patients
FORCE ROW LEVEL SECURITY;

ALTER TABLE public.health_records
FORCE ROW LEVEL SECURITY;

ALTER TABLE public.locations
FORCE ROW LEVEL SECURITY;


-- 7. YÖNETİCİ VE TABLO SAHİBİ RLS DAVRANIŞI
-- PostgreSQL superuser ve BYPASSRLS rollerinin
-- RLS politikalarını aşabildiği unutulmamalıdır.
-- FORCE ROW LEVEL SECURITY superuser hesaplarını engellemez.

SELECT
    rolname,
    rolsuper,
    rolbypassrls
FROM pg_roles
WHERE rolname IN (
    'postgres',
    'doctor_test',
    'doctor_test2',
    'analyst_test'
);


-- 8. ANALİST GÖRÜNÜMLERİ İÇİN AYRI SAHİP ROLÜ

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


-- 9. ANALİST GÖRÜNÜM SAHİBİNE GEREKLİ OKUMA YETKİLERİ

GRANT SELECT ON public.patients,
                public.health_records
TO analyst_view_owner;


-- 10. FORCE RLS NEDENİYLE GÖRÜNÜM SAHİBİNE
-- GEREKLİ RLS POLİTİKALARINI TANIMLA

DROP POLICY IF EXISTS analyst_view_patients
ON public.patients;

CREATE POLICY analyst_view_patients
ON public.patients
FOR SELECT
TO analyst_view_owner
USING (true);


DROP POLICY IF EXISTS analyst_view_health
ON public.health_records;

CREATE POLICY analyst_view_health
ON public.health_records
FOR SELECT
TO analyst_view_owner
USING (true);


-- 11. EPİDEMİYOLOJİK ÖZET GÖRÜNÜMÜNÜN SAHİPLİĞİ

ALTER VIEW public.epidemiological_summary
OWNER TO analyst_view_owner;


-- 12. ANONİMLEŞTİRİLMİŞ HASTA GÖRÜNÜMÜNÜ GÜNCELLE

DROP VIEW IF EXISTS public.anonymized_patients;

CREATE VIEW public.anonymized_patients AS
SELECT
    CASE
        WHEN first_name IS NOT NULL
        THEN LEFT(first_name, 1) || '***'
        ELSE '***'
    END AS first_name,

    '***'::text AS last_name,

    '***'::text AS passport_number,

    nationality,

    CASE
        WHEN birth_date IS NULL THEN 'Bilinmiyor'
        WHEN EXTRACT(YEAR FROM age(CURRENT_DATE, birth_date)) < 18 THEN '0-17'
        WHEN EXTRACT(YEAR FROM age(CURRENT_DATE, birth_date)) < 30 THEN '18-29'
        WHEN EXTRACT(YEAR FROM age(CURRENT_DATE, birth_date)) < 45 THEN '30-44'
        WHEN EXTRACT(YEAR FROM age(CURRENT_DATE, birth_date)) < 60 THEN '45-59'
        ELSE '60+'
    END AS age_group,

    gender,

    '***'::text AS phone

FROM public.patients;


-- 13. ANONİMLEŞTİRİLMİŞ GÖRÜNÜMÜN SAHİPLİĞİ

ALTER VIEW public.anonymized_patients
OWNER TO analyst_view_owner;


-- 14. ANALİSTLERE GÖRÜNÜMLER İÇİN OKUMA YETKİSİ VER

GRANT SELECT
ON public.anonymized_patients
TO analyst_role;

GRANT SELECT
ON public.epidemiological_summary
TO analyst_role;


-- =====================================================
-- SECURITY HARDENING
-- =====================================================
