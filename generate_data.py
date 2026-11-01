
import os
import random
from datetime import date, timedelta, datetime

import psycopg2
from psycopg2.extras import execute_values


# --------------------------------------------------
# AYARLAR
# --------------------------------------------------

DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_CONFIG = {
    "host": "localhost",
    "database": "gocmen_sagligi_db",
    "user": "postgres",
    "password": DB_PASSWORD,
    "port": "5432"
}

TOTAL_PATIENTS = 20000

DOCTORS = ["doctor_ayse", "doctor_mehmet"]

FIRST_NAMES = [
    "Ahmet", "Mehmet", "Ali", "Mustafa", "Hasan",
    "Fatma", "Ayşe", "Zeynep", "Elif", "Meryem",
    "Yusuf", "Ömer", "Hüseyin", "Emine", "Hatice"
]

LAST_NAMES = [
    "Yılmaz", "Demir", "Kaya", "Şahin", "Çelik",
    "Aydın", "Arslan", "Doğan", "Özdemir", "Kılıç"
]

NATIONALITIES = [
    "Suriye", "Afganistan", "Irak", "İran",
    "Pakistan", "Somali"
]

DISEASES = [
    "Diyabet", "Hipertansiyon", "Astım",
    "Kalp Hastalığı", "Tüberküloz", "Yok"
]

VACCINATIONS = [
    "Tamamlandı", "Eksik", "Başlanmadı"
]

# Temsili sınır bölgeleri: boylam, enlem
BORDER_POINTS = [
    (26.56, 41.68),  # Edirne çevresi
    (36.16, 36.20),  # Hatay çevresi
    (37.12, 36.72),  # Kilis çevresi
    (42.45, 37.50),  # Şırnak çevresi
    (43.05, 39.70)   # Ağrı çevresi
]

BORDER_NAMES = [
    "Edirne",
    "Hatay",
    "Kilis",
    "Şırnak",
    "Ağrı"
]


# --------------------------------------------------
# VERİ ÜRETİMİ
# --------------------------------------------------

def generate_patient(index):
    return (
        random.choice(FIRST_NAMES),
        random.choice(LAST_NAMES),
        f"SYN-2026-{index:06d}",
        random.choice(NATIONALITIES),
        date(
            random.randint(1960, 2015),
            random.randint(1, 12),
            random.randint(1, 28)
        ),
        random.choice(["Kadın", "Erkek"]),
        f"05{random.randint(100000000, 999999999)}"
    )


def generate_health_record(patient_id):
    disease = random.choice(DISEASES)

    return (
        patient_id,
        disease,
        disease != "Yok",
        random.choice(VACCINATIONS),
        random.randint(1, 100)
    )


def generate_location(patient_id):
    index = random.randrange(len(BORDER_POINTS))
    longitude, latitude = BORDER_POINTS[index]

    # Noktanın çevresinde küçük rastgele konum farklılıkları
    longitude += random.uniform(-0.15, 0.15)
    latitude += random.uniform(-0.15, 0.15)

    entry_time = datetime.now() - timedelta(
        days=random.randint(1, 1000)
    )

    return (
        patient_id,
        BORDER_NAMES[index],
        entry_time,
        longitude,
        latitude
    )


# --------------------------------------------------
# VERİTABANINA KAYIT
# --------------------------------------------------

def main():

    if not DB_PASSWORD:
        print("HATA: DB_PASSWORD ortam değişkeni tanımlanmamış.")
        return

    connection = None

    try:
        print("Veritabanına bağlanılıyor...")

        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Yanlışlıkla ikinci kez veri eklenmesini önle
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM patients),
                (SELECT COUNT(*) FROM health_records),
                (SELECT COUNT(*) FROM locations)
        """)

        counts = cursor.fetchone()

        if any(counts):
            print("Tablolarda zaten veri var. Tekrar ekleme yapılmadı.")
            print("Mevcut kayıt sayıları:", counts)
            return

        print("20.000 hasta verisi hazırlanıyor...")

        patients = [
            generate_patient(i)
            for i in range(1, TOTAL_PATIENTS + 1)
        ]

        execute_values(
            cursor,
            """
            INSERT INTO patients
            (first_name, last_name, passport_number, nationality,
             birth_date, gender, phone)
            VALUES %s
            RETURNING patient_id
            """,
            patients,
            page_size=1000,
            fetch=True
        )

        # Eklenen hastaların ID değerlerini al
        patient_ids = [
            row[0]
            for row in cursor.fetchall()
        ]

        print(f"{len(patient_ids)} hasta eklendi.")

        # Sağlık kayıtları
        print("Sağlık kayıtları oluşturuluyor...")

        health_records = [
            generate_health_record(patient_id)
            for patient_id in patient_ids
        ]

        execute_values(
            cursor,
            """
            INSERT INTO health_records
            (patient_id, disease_name, chronic_disease,
             vaccination_status, risk_score)
            VALUES %s
            """,
            health_records,
            page_size=1000
        )

        print(f"{len(health_records)} sağlık kaydı eklendi.")

        # Konum kayıtları
        print("Konum kayıtları oluşturuluyor...")

        locations = [
            generate_location(patient_id)
            for patient_id in patient_ids
        ]

        execute_values(
            cursor,
            """
            INSERT INTO locations
            (patient_id, border_name, entry_time, geom)
            VALUES %s
            """,
            [
                (
                    patient_id,
                    border_name,
                    entry_time,
                    longitude,
                    latitude
                )
                for (
                    patient_id,
                    border_name,
                    entry_time,
                    longitude,
                    latitude
                ) in locations
            ],
            template="""
                (%s, %s, %s,
                 ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            """,
            page_size=1000
        )

        print(f"{len(locations)} konum kaydı eklendi.")

        # Doktorlara hasta atama
        print("Doktor-hasta yetkileri oluşturuluyor...")

        doctor_assignments = []

        for index, patient_id in enumerate(patient_ids):
            doctor_username = (
                DOCTORS[0]
                if index < len(patient_ids) // 2
                else DOCTORS[1]
            )

            doctor_assignments.append(
                (doctor_username, patient_id)
            )

        execute_values(
            cursor,
            """
            INSERT INTO doctor_patient_access
            (doctor_username, patient_id)
            VALUES %s
            """,
            doctor_assignments,
            page_size=1000
        )

        connection.commit()

        print("\nVERİ ÜRETİMİ BAŞARILI!")
        print("------------------------------")
        print("Hasta sayısı: 20.000")
        print("Sağlık kaydı: 20.000")
        print("Konum kaydı: 20.000")
        print("Doktor hasta ataması: 20.000")
        print("Ayşe doktor: 10.000 hasta")
        print("Mehmet doktor: 10.000 hasta")

    except Exception as error:
        if connection:
            connection.rollback()

        print("\nHATA OLUŞTU:")
        print(error)

    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    main()
