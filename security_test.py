
import os
import psycopg2

print("=" * 65)
print("GOCMEN SAGLIGI SISTEMI - RLS GUVENLIK TESTLERI")
print("=" * 65)

# --------------------------------------------------
# 1. VERITABANI BAGLANTI AYARLARI
# --------------------------------------------------

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "gocmen_sagligi_db"),
    "port": os.getenv("DB_PORT", "5432"),
}

ADMIN_CONFIG = {
    **DB_CONFIG,
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

DOCTOR_A = os.getenv("DOCTOR_A_USER", "doctor_ayse")
DOCTOR_B = os.getenv("DOCTOR_B_USER", "doctor_mehmet")
ANALYST = os.getenv("ANALYST_USER", "analyst_user")
UNAUTHORIZED = os.getenv("UNAUTHORIZED_USER", "unauthorized_user")

DOCTOR_A_PASSWORD = os.getenv("DOCTOR_A_PASSWORD", "")
DOCTOR_B_PASSWORD = os.getenv("DOCTOR_B_PASSWORD", "")
ANALYST_PASSWORD = os.getenv("ANALYST_PASSWORD", "")
UNAUTHORIZED_PASSWORD = os.getenv("UNAUTHORIZED_PASSWORD", "")

# Test sonuçları: PASS, FAIL veya SKIP
results = {}


# --------------------------------------------------
# 2. YARDIMCI FONKSIYONLAR
# --------------------------------------------------

def add_result(name, status, detail=""):
    results[name] = status

    labels = {
        "PASS": "BASARILI",
        "FAIL": "BASARISIZ",
        "SKIP": "ATLANDI",
    }

    print(f"[{labels[status]}] {name}")

    if detail:
        print(f"  -> {detail}")


def connect_as(user, password):
    return psycopg2.connect(
        **DB_CONFIG,
        user=user,
        password=password
    )


def test_doctor_access(username, password, assigned_patients):
    """Bir doktorun hasta, sağlık ve konum kayıtlarını kontrol eder."""

    if not assigned_patients:
        add_result(
            f"{username} erisim testleri",
            "SKIP",
            "Doktora atanmis hasta bulunmuyor."
        )
        return

    try:
        conn = connect_as(username, password)
        cur = conn.cursor()

        # Hasta erişimi
        cur.execute("SELECT patient_id FROM patients")
        visible_patients = {row[0] for row in cur.fetchall()}

        add_result(
            f"{username} kendi hastalarini gorebiliyor",
            "PASS" if assigned_patients.issubset(visible_patients)
            else "FAIL"
        )

        add_result(
            f"{username} baska doktorun hastalarini goremiyor",
            "PASS" if visible_patients.issubset(assigned_patients)
            else "FAIL"
        )

        # Sağlık kayıtları
        cur.execute("SELECT patient_id FROM health_records")
        visible_health = {row[0] for row in cur.fetchall()}

        add_result(
            f"{username} saglik kayitlari yetkisi",
            "PASS" if visible_health.issubset(assigned_patients)
            else "FAIL"
        )

        # Konum kayıtları
        cur.execute("SELECT patient_id FROM locations")
        visible_locations = {row[0] for row in cur.fetchall()}

        add_result(
            f"{username} konum kayitlari yetkisi",
            "PASS" if visible_locations.issubset(assigned_patients)
            else "FAIL"
        )

        cur.close()
        conn.close()

    except Exception as e:
        add_result(
            f"{username} erisim testleri",
            "FAIL",
            str(e)
        )


def test_unauthorized_access(username, password):
    """Yetkisiz kullanıcının doğrudan tablo erişimini kontrol eder."""

    for table in ["patients", "health_records", "locations"]:
        conn = None

        try:
            conn = connect_as(username, password)
            cur = conn.cursor()

            cur.execute(f"SELECT * FROM {table} LIMIT 1")

            # Sorgu başarılı olduysa erişim engellenmemiştir.
            add_result(
                f"Yetkisiz kullanici {table} erisimi engellendi",
                "FAIL",
                "Kullanici tabloya erisebildi."
            )

            cur.close()

        except psycopg2.Error as e:
            if conn:
                conn.rollback()

            add_result(
                f"Yetkisiz kullanici {table} erisimi engellendi",
                "PASS",
                f"PostgreSQL hata kodu: {e.pgcode}"
            )

        except Exception as e:
            add_result(
                f"Yetkisiz kullanici {table} erisimi engellendi",
                "FAIL",
                str(e)
            )

        finally:
            if conn:
                conn.close()


# --------------------------------------------------
# TEST 1: VERITABANI BAGLANTISI
# --------------------------------------------------

print("\n[TEST 1] Veritabani baglantisi")

try:
    admin_conn = psycopg2.connect(**ADMIN_CONFIG)
    admin_conn.autocommit = True

    add_result("Veritabani baglantisi", "PASS")

except Exception as e:
    add_result("Veritabani baglantisi", "FAIL", str(e))
    raise SystemExit("Veritabani baglantisi kurulamadi.")


# --------------------------------------------------
# TEST 2: TABLO VE VERI KONTROLU
# --------------------------------------------------

print("\n[TEST 2] Tablo ve veri kontrolu")

try:
    cur = admin_conn.cursor()

    for table in ["patients", "health_records", "locations",
                  "doctor_patient_access"]:

        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]

        add_result(
            f"{table} tablosunda veri bulunuyor",
            "PASS" if count > 0 else "SKIP",
            f"Kayit sayisi: {count}"
        )

    cur.close()

except Exception as e:
    add_result("Tablo ve veri kontrolu", "FAIL", str(e))


# --------------------------------------------------
# TEST 3: DOKTOR-HASTA ESLESTIRMELERI
# --------------------------------------------------

print("\n[TEST 3] Doktor-hasta eslestirmeleri")

doctor_a_patients = set()
doctor_b_patients = set()

try:
    cur = admin_conn.cursor()

    cur.execute("""
        SELECT patient_id
        FROM doctor_patient_access
        WHERE doctor_username = %s
    """, (DOCTOR_A,))

    doctor_a_patients = {row[0] for row in cur.fetchall()}

    cur.execute("""
        SELECT patient_id
        FROM doctor_patient_access
        WHERE doctor_username = %s
    """, (DOCTOR_B,))

    doctor_b_patients = {row[0] for row in cur.fetchall()}

    add_result(
        "Doktor A hasta atamalari",
        "PASS" if doctor_a_patients else "SKIP",
        f"{len(doctor_a_patients)} hasta atanmis."
    )

    add_result(
        "Doktor B hasta atamalari",
        "PASS" if doctor_b_patients else "SKIP",
        f"{len(doctor_b_patients)} hasta atanmis."
    )

    different_patients = (
        len(doctor_a_patients - doctor_b_patients) > 0
        and len(doctor_b_patients - doctor_a_patients) > 0
    )

    add_result(
        "Doktorlar arasinda farkli hasta atamalari",
        "PASS" if different_patients else "SKIP"
    )

    cur.close()

except Exception as e:
    add_result("Doktor-hasta eslestirmeleri", "FAIL", str(e))


# --------------------------------------------------
# TEST 4: DOKTOR A ERISIM TESTLERI
# --------------------------------------------------

print("\n[TEST 4] Doktor A erisim kontrolu")

test_doctor_access(
    DOCTOR_A,
    DOCTOR_A_PASSWORD,
    doctor_a_patients
)


# --------------------------------------------------
# TEST 5: DOKTOR B ERISIM TESTLERI
# --------------------------------------------------

print("\n[TEST 5] Doktor B erisim kontrolu")

test_doctor_access(
    DOCTOR_B,
    DOCTOR_B_PASSWORD,
    doctor_b_patients
)


# --------------------------------------------------
# TEST 6: YETKISIZ KULLANICI TESTI
# --------------------------------------------------

print("\n[TEST 6] Yetkisiz kullanici erisim testi")

test_unauthorized_access(
    UNAUTHORIZED,
    UNAUTHORIZED_PASSWORD
)


# --------------------------------------------------
# TEST 7: ANALIST ANONIMLESTIRME TESTI
# --------------------------------------------------

print("\n[TEST 7] Analist anonimlestirme kontrolu")

analyst_conn = None

try:
    analyst_conn = connect_as(ANALYST, ANALYST_PASSWORD)
    analyst_cur = analyst_conn.cursor()

    analyst_cur.execute("""
        SELECT
            first_name,
            last_name,
            passport_number,
            phone
        FROM anonymized_patients
    """)

    rows = analyst_cur.fetchall()

    if not rows:
        add_result(
            "Analist kisisel bilgileri maskelenmis goruyor",
            "SKIP",
            "Anonimlestirme gorunumunde kayit bulunmuyor."
        )
    else:
        masking_success = all(
            row[0] is not None
            and row[0].endswith("***")
            and row[1] == "***"
            and row[2] == "***"
            and row[3] == "***"
            for row in rows
        )

        add_result(
            "Analist kisisel bilgileri maskelenmis goruyor",
            "PASS" if masking_success else "FAIL",
            f"Kontrol edilen kayit: {len(rows)}"
        )

    analyst_cur.close()

except Exception as e:
    add_result("Analist anonimlestirme testi", "FAIL", str(e))

finally:
    if analyst_conn:
        analyst_conn.close()


# --------------------------------------------------
# TEST 8: ANALIST HAM VERI ERISIMI
# --------------------------------------------------

print("\n[TEST 8] Analist ham veri erisim kontrolu")

try:
    analyst_conn = connect_as(ANALYST, ANALYST_PASSWORD)
    analyst_cur = analyst_conn.cursor()

    analyst_cur.execute("SELECT * FROM patients LIMIT 1")

    add_result(
        "Analist ham hasta tablosuna erisemiyor",
        "FAIL",
        "Analist ham tabloya erisebildi."
    )

    analyst_cur.close()

except psycopg2.Error as e:
    if analyst_conn:
        analyst_conn.rollback()

    add_result(
        "Analist ham hasta tablosuna erisemiyor",
        "PASS",
        f"PostgreSQL hata kodu: {e.pgcode}"
    )

except Exception as e:
    add_result(
        "Analist ham veri erisim testi",
        "FAIL",
        str(e)
    )

finally:
    if analyst_conn:
        analyst_conn.close()


# --------------------------------------------------
# TEST 9: ANALIST EPIDEMIYOLOJIK OZET
# --------------------------------------------------

print("\n[TEST 9] Analist epidemiyolojik ozet")

try:
    analyst_conn = connect_as(ANALYST, ANALYST_PASSWORD)
    analyst_cur = analyst_conn.cursor()

    analyst_cur.execute("""
        SELECT *
        FROM epidemiological_summary
        LIMIT 5
    """)

    summary_rows = analyst_cur.fetchall()

    add_result(
        "Analist epidemiyolojik ozet gorebiliyor",
        "PASS" if summary_rows else "SKIP",
        f"Getirilen kayit: {len(summary_rows)}"
    )

    analyst_cur.close()

except Exception as e:
    add_result("Analist epidemiyolojik ozet", "FAIL", str(e))

finally:
    if analyst_conn:
        analyst_conn.close()


# --------------------------------------------------
# SONUC VE BASARI METRIGI
# --------------------------------------------------

print("\n" + "=" * 65)
print("GUVENLIK TEST RAPORU")
print("=" * 65)

total = len(results)
success_count = sum(1 for status in results.values() if status == "PASS")
fail_count = sum(1 for status in results.values() if status == "FAIL")
skip_count = sum(1 for status in results.values() if status == "SKIP")

for name, status in results.items():
    print(f"{name}: {status}")

executed = success_count + fail_count

success_rate = (
    success_count / executed * 100
    if executed else 0
)

print("-" * 65)
print(f"Toplam test kriteri       : {total}")
print(f"Basarili test             : {success_count}")
print(f"Basarisiz test            : {fail_count}")
print(f"Atlanan test              : {skip_count}")
print(f"Test basari orani         : %{success_rate:.2f}")
print("=" * 65)

admin_conn.close()
