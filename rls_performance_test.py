
import os
import time
import psycopg2
from statistics import mean


def main():
    password = os.getenv("RLS_TEST_PASSWORD", "")

    if not password:
        password = os.getenv("DB_PASSWORD", "")

    if not password:
        print("HATA: RLS_TEST_PASSWORD veya DB_PASSWORD tanımlı değil.")
        return

    durations = []

    connection = psycopg2.connect(
        host="localhost",
        database="gocmen_sagligi_db",
        user="analyst_test",
        password=password,
        port=5432,
    )

    try:
        with connection.cursor() as cursor:
            # Isınma sorgusu; ölçümlere dahil edilmez.
            cursor.execute("SELECT * FROM epidemiological_summary;")
            cursor.fetchall()

            # Aynı sorguyu 5 kez ölç.
            for i in range(5):
                start = time.perf_counter()

                cursor.execute("SELECT * FROM epidemiological_summary;")
                results = cursor.fetchall()

                elapsed_ms = (time.perf_counter() - start) * 1000
                durations.append(elapsed_ms)

                print(f"Ölçüm {i + 1}: {elapsed_ms:.2f} ms")

        print("\n--- RLS GÜVENLİ GÖRÜNÜM PERFORMANS TESTİ ---")
        print("Veritabanı rolü: analyst_test")
        print(f"Sonuç grubu sayısı: {len(results)}")
        print(f"Ortalama sorgu süresi: {mean(durations):.2f} ms")

    finally:
        connection.close()


if __name__ == "__main__":
    try:
        main()
    except psycopg2.Error as error:
        print(f"Veritabanı hatası: {error}")
