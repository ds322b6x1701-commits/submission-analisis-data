# Proyek Analisis Data: Air Quality Dataset

Analisis kualitas udara di 12 stasiun pemantauan Beijing (Maret 2013 – Februari 2017)
beserta dashboard interaktif menggunakan Streamlit.

## Struktur Direktori

```
submission
├───dashboard
│   ├───main_data.csv
│   └───dashboard.py
├───data
│   └───PRSA_Data_*.csv   (12 file dataset mentah)
├───notebook.ipynb
├───README.md
├───requirements.txt
└───url.txt
```

## Setup Environment

```
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

## Menjalankan Dashboard

```
cd dashboard
streamlit run dashboard.py
```

Dashboard akan terbuka di `http://localhost:8501`.

## Isi Dashboard

1. **Tren PM2.5** – tren bulanan dan pola musiman PM2.5 per stasiun.
2. **Perbandingan Stasiun** – rata-rata PM2.5, PM10, SO2, NO2, CO, dan O3 antarstasiun.
3. **Faktor Meteorologi** – korelasi PM2.5 dengan suhu (TEMP), titik embun (DEWP), dan kecepatan angin (WSPM).
4. **Pengelompokan Stasiun** – analisis lanjutan manual grouping berdasarkan rata-rata PM2.5.
