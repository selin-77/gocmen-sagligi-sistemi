
import os
import time
from statistics import mean

import psycopg2


DB_CONFIG = {
    "host": "localhost",
    "database": "gocmen_sagligi_db",
    "port": 5432,
}

BASELINE_QUERY = """
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
        vaccination_status
    ORDER BY
        disease_name,
        chronic_disease,
        vaccination_status;
"""

SECURE_QUERY = """
    SELECT
        disease_name,
        chronic_disease,
        vaccination_status,
        record_count,
        average_risk_score
    FROM epidemiological_summary
    ORDER BY
        disease_name,
        chronic_disease,
        vaccination_status;
"""


def measure_query(user, password, query, label, repetitions=5):
    durations = []

    connection = psycopg2.connect(
        **DB_CONFIG,
        user=user,
        password=password,
    )

    try:
        with connection.cursor() as cursor:
            # Isınma sorgusu ölçümlere dahil edilmez.
            cursor.execute(query)
            cursor.fetchall()

            for number in range(repetitions):
                start = time.perf_counter()

                cursor.execute(query)
                rows = cursor.fetchall()

                elapsed_ms = (time.perf_counter() - start) * 1000
                durations.append(elapsed_ms)

                print(f"{label} ölçüm {number + 1}: {elapsed_ms:.2f} ms")

        return mean(durations), len(rows)

    finally:
        connection.close()


def main():
    db_password = os.getenv("DB_PASSWORD", "")
    analyst_password = os.getenv("RLS_TEST_PASSWORD", "")

    if not db_password:
        print("HATA: DB_PASSWORD ortam değişkeni tanımlı değil.")
        return

    if not analyst_password:
        print("HATA: RLS_TEST_PASSWORD ortam değişkeni tanımlı değil.")
        return

    print("=== AYNI SORGU İÇİN PERFORMANS KARŞILAŞTIRMASI ===\n")

    baseline_avg, baseline_rows = measure_query(
        user="postgres",
        password=db_password,
        query=BASELINE_QUERY,
        label="Baseline",
    )

    print()

    secure_avg, secure_rows = measure_query(
        user="analyst_test",
        password=analyst_password,
        query=SECURE_QUERY,
        label="Güvenli görünüm",
    )

    print("\n=== SONUÇLAR ===")
    print(f"Baseline ortalaması: {baseline_avg:.2f} ms")
    print(f"Güvenli görünüm ortalaması: {secure_avg:.2f} ms")
    print(f"Baseline sonuç grubu: {baseline_rows}")
    print(f"Güvenli görünüm sonuç grubu: {secure_rows}")

    if baseline_rows != secure_rows:
        print(
            "\nUYARI: Sonuç grubu sayıları farklı. "
            "Süreleri doğrudan karşılaştırmadan önce sorguları inceleyin."
        )
    elif baseline_avg > 0:
        difference = secure_avg - baseline_avg
        percent = (difference / baseline_avg) * 100

        print(f"Süre farkı: {difference:.2f} ms")
        print(f"Baseline'a göre değişim: %{percent:.2f}")

        print(
            "\nNot: Ölçümler istemciye veri aktarma ve fetch sürelerini de içerir. "
            "Sonuçlar bu test ortamına aittir; tek başına RLS maliyetini "
            "kanıtlamaz."
        )


if __name__ == "__main__":
    try:
        main()
    except psycopg2.Error as error:
        print(f"Veritabanı hatası: {error}")
