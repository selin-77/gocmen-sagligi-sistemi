
import os
import psycopg2
import folium
from folium.plugins import HeatMap, MarkerCluster


# --------------------------------------------------
# 1. VERITABANI AYARLARI
# --------------------------------------------------

DB_PASSWORD = os.getenv("DB_PASSWORD")

if not DB_PASSWORD:
    raise ValueError(
        "DB_PASSWORD ortam degiskeni tanimlanmamis!"
    )

DB_CONFIG = {
    "host": "localhost",
    "database": "gocmen_sagligi_db",
    "user": "postgres",
    "password": DB_PASSWORD,
    "port": "5432"
}


# --------------------------------------------------
# 2. ANA FONKSIYON
# --------------------------------------------------

def main():

    connection = None

    try:
        print("Veritabanina baglaniliyor...")

        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Konum verilerini PostGIS'ten al
        cursor.execute("""
            SELECT
                border_name,
                ST_Y(geom) AS latitude,
                ST_X(geom) AS longitude
            FROM locations
            WHERE geom IS NOT NULL;
        """)

        rows = cursor.fetchall()

        if not rows:
            print("HATA: Konum verisi bulunamadi.")
            return

        print(f"Toplam {len(rows)} konum okundu.")

        # Verileri bölgelere göre ayır
        bolgeler = {}

        for border_name, latitude, longitude in rows:
            if latitude is None or longitude is None:
                continue

            if border_name not in bolgeler:
                bolgeler[border_name] = []

            bolgeler[border_name].append(
                [latitude, longitude]
            )

        tum_koordinatlar = [
            koordinat
            for liste in bolgeler.values()
            for koordinat in liste
        ]

        if not tum_koordinatlar:
            print("HATA: Gecerli koordinat bulunamadi.")
            return

        # --------------------------------------------------
        # 3. HARITA OLUSTURMA
        # --------------------------------------------------

        print("Harita hazirlaniyor...")

        ortalama_enlem = sum(
            nokta[0] for nokta in tum_koordinatlar
        ) / len(tum_koordinatlar)

        ortalama_boylam = sum(
            nokta[1] for nokta in tum_koordinatlar
        ) / len(tum_koordinatlar)

        harita = folium.Map(
            location=[ortalama_enlem, ortalama_boylam],
            zoom_start=5,
            tiles="OpenStreetMap"
        )

        # --------------------------------------------------
        # 4. ISI HARITASI
        # --------------------------------------------------

        print("Isi haritasi olusturuluyor...")

        heatmap = folium.FeatureGroup(
            name="Genel Gocmen Yogunlugu"
        )

        HeatMap(
            tum_koordinatlar,
            radius=20,
            blur=25,
            min_opacity=0.25
        ).add_to(heatmap)

        heatmap.add_to(harita)

        # --------------------------------------------------
        # 5. BOLGE BAZLI ISI HARITALARI
        # --------------------------------------------------

        for bolge, koordinatlar in bolgeler.items():

            bolge_katmani = folium.FeatureGroup(
                name=f"{bolge} Yogunlugu",
                show=False
            )

            HeatMap(
                koordinatlar,
                radius=18,
                blur=20,
                min_opacity=0.3
            ).add_to(bolge_katmani)

            bolge_katmani.add_to(harita)

        # --------------------------------------------------
        # 6. KONUM ISARETCILERI
        # --------------------------------------------------

        marker_katmani = folium.FeatureGroup(
            name="Konum Noktalari",
            show=False
        )

        marker_cluster = MarkerCluster()

        for bolge, koordinatlar in bolgeler.items():

            for latitude, longitude in koordinatlar:

                folium.CircleMarker(
                    location=[latitude, longitude],
                    radius=2,
                    color="blue",
                    fill=True,
                    fill_opacity=0.5,
                    popup=bolge
                ).add_to(marker_cluster)

        marker_cluster.add_to(marker_katmani)
        marker_katmani.add_to(harita)

        # --------------------------------------------------
        # 7. BUTUN BOLGELERI EKRANA SIGDIR
        # --------------------------------------------------

        enlemler = [
            nokta[0] for nokta in tum_koordinatlar
        ]

        boylamlar = [
            nokta[1] for nokta in tum_koordinatlar
        ]

        harita.fit_bounds([
            [min(enlemler), min(boylamlar)],
            [max(enlemler), max(boylamlar)]
        ])

        # Katman kontrolü
        folium.LayerControl(
            collapsed=False
        ).add_to(harita)

        # --------------------------------------------------
        # 8. HARITAYI KAYDET
        # --------------------------------------------------

        dosya_adi = "gocmen_isi_haritasi.html"

        harita.save(dosya_adi)

        print("\nHARITA BASARIYLA OLUSTURULDU!")
        print("--------------------------------")

        for bolge, koordinatlar in bolgeler.items():
            print(
                f"{bolge}: {len(koordinatlar)} konum"
            )

        print("--------------------------------")
        print(f"Toplam konum: {len(tum_koordinatlar)}")
        print(f"Dosya: {dosya_adi}")

        cursor.close()

    except Exception as error:
        print("\nHATA OLUSTU:")
        print(error)

    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    main()
