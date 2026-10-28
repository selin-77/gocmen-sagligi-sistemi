
import os
import time
import psycopg2


def get_connection():
    """Baseline uygulamasının veritabanı bağlantısı."""
    return psycopg2.connect(
        host="localhost",
        database="gocmen_sagligi_db",
        user="postgres",
        password=os.getenv("DB_PASSWORD", ""),
        port=5432,
    )
def request_data(user_role, requested_data):
    """Veri isteğini uygulama katmanında yetkilendirir."""
    if not authorize(user_role, requested_data):
        print(f"ERİŞİM REDDEDİLDİ: {user_role} -> {requested_data}")
        return None

    if requested_data == "health_summary":
        return get_patient_summary()

    if requested_data == "health_records":
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT record_id, disease_name FROM health_records LIMIT 5;"
                )
                return cursor.fetchall()
        finally:
            connection.close()

    if requested_data == "patients":
        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT patient_id, first_name, last_name FROM patients LIMIT 5;"
                )
                return cursor.fetchall()
        finally:
            connection.close()

def get_patient_summary():
    """Baseline için temel hasta istatistiklerini getirir."""
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            start = time.perf_counter()

            cursor.execute("SELECT COUNT(*) FROM patients;")
            patient_count = cursor.fetchone()[0]

            cursor.execute("""
                SELECT
                    disease_name,
                    COUNT(*) AS record_count
                FROM health_records
                GROUP BY disease_name
                ORDER BY disease_name;
            """)
            disease_summary = cursor.fetchall()

            elapsed_ms = (time.perf_counter() - start) * 1000

        return patient_count, disease_summary, elapsed_ms

    finally:
        connection.close()


def authorize(user_role, requested_data):
    """
    Baseline yaklaşımında uygulama katmanında manuel yetkilendirme.
    Bu kontrol tek başına veritabanı güvenliği sağlamaz.
    """
    permissions = {
        "doctor": {"patients", "health_records"},
        "analyst": {"health_summary"},
    }

    return requested_data in permissions.get(user_role, set())


def main():
    print("=== BASELINE: Klasik Referans Yöntem ===")

    # Uygulama katmanındaki manuel yetkilendirme testleri
    print("\nUygulama katmanında erişim testleri:")

    doctor_result = request_data("doctor", "health_records")
    print(f"Doktor sağlık kayıtlarına erişebildi: {doctor_result is not None}")

    analyst_result = request_data("analyst", "health_summary")
    print(f"Analist özete erişebildi: {analyst_result is not None}")

    request_data("analyst", "patients")
    request_data("unauthorized", "patients")

    # Yetki kontrolünden geçen analist isteği
    summary_result = request_data("analyst", "health_summary")
    patient_count, disease_summary, elapsed_ms = summary_result
    print("\nBaseline sorgu sonuçları:")
    print(f"Toplam hasta sayısı: {patient_count}")
    print(f"Sorgu süresi: {elapsed_ms:.2f} ms")
    print("Hastalıklara göre kayıt sayıları:")
    for disease, count in disease_summary:
        print(f"- {disease}: {count}")


if __name__ == "__main__":
    main()
