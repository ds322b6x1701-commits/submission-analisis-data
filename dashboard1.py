from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from matplotlib.patches import Patch

# ------------------------------------------------------------------
# Konfigurasi
# ------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Kualitas Udara Beijing",
    page_icon="🌫️",
    layout="wide",
)
sns.set_theme(style="whitegrid")

DATA_PATH = Path(__file__).parent / "main_data.csv.gz"
POLUTAN = ["PM2.5", "PM10", "SO2", "NO2", "CO", "O3"]
METEO = ["TEMP", "DEWP", "WSPM"]
BULAN_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
    7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}
MERAH, ABU = "#D62728", "#D3D3D3"
WARNA_KATEGORI = {"Rendah": "#2CA02C", "Sedang": "#FF9F1C", "Tinggi": "#D62728"}


def nama_bulan(ts):
    return f"{BULAN_ID[ts.month]} {ts.year}"


# ------------------------------------------------------------------
# Data
# ------------------------------------------------------------------
@st.cache_data
def load_data():
    return pd.read_csv(
        DATA_PATH,
        compression="gzip",
        parse_dates=["datetime"]
    )


df = load_data()
min_date = df["datetime"].min().date()
max_date = df["datetime"].max().date()
semua_stasiun = sorted(df["station"].unique())

# ------------------------------------------------------------------
# Sidebar (filter)
# ------------------------------------------------------------------
with st.sidebar:
    st.header("Filter Data")
    rentang = st.date_input(
        "Rentang waktu",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    stasiun_dipilih = st.multiselect(
        "Stasiun (untuk tab 2–4)",
        options=semua_stasiun,
        default=semua_stasiun,
    )
    st.caption("Sumber data: Air Quality Dataset (12 stasiun Beijing, Mar 2013 – Feb 2017).")

# date_input mengembalikan 1 tanggal saat pengguna baru memilih tanggal awal
if not isinstance(rentang, (tuple, list)) or len(rentang) != 2:
    st.info("Pilih tanggal akhir pada filter rentang waktu.")
    st.stop()
if not stasiun_dipilih:
    st.warning("Pilih minimal satu stasiun.")
    st.stop()

start_date, end_date = rentang
tanggal = df["datetime"].dt.date
df_waktu = df[(tanggal >= start_date) & (tanggal <= end_date)]
df_f = df_waktu[df_waktu["station"].isin(stasiun_dipilih)]

if df_f.empty:
    st.warning("Tidak ada data pada filter yang dipilih.")
    st.stop()

# ------------------------------------------------------------------
# Header + ringkasan
# ------------------------------------------------------------------
st.title("🌫️ Dashboard Kualitas Udara Beijing")
st.caption(f"Periode: {start_date:%d %b %Y} – {end_date:%d %b %Y} · {len(stasiun_dipilih)} stasiun")

rata_stasiun = df_f.groupby("station")["PM2.5"].mean().sort_values(ascending=False)
c1, c2, c3 = st.columns(3)
c1.metric("Rata-rata PM2.5", f"{df_f['PM2.5'].mean():.1f} µg/m³")
c2.metric("Stasiun PM2.5 tertinggi", rata_stasiun.index[0], f"{rata_stasiun.iloc[0]:.1f} µg/m³", delta_color="off")
c3.metric("Stasiun PM2.5 terendah", rata_stasiun.index[-1], f"{rata_stasiun.iloc[-1]:.1f} µg/m³", delta_color="off")

tab1, tab2, tab3, tab4 = st.tabs([
    "1. Tren PM2.5",
    "2. Perbandingan Stasiun",
    "3. Faktor Meteorologi",
    "4. Pengelompokan Stasiun",
])

# ------------------------------------------------------------------
# Tab 1 – Pertanyaan 1: tren bulanan PM2.5
# ------------------------------------------------------------------
with tab1:
    st.subheader("Bagaimana tren bulanan PM2.5 dan kapan puncaknya?")
    default_idx = semua_stasiun.index("Aotizhongxin") if "Aotizhongxin" in semua_stasiun else 0
    stasiun_q1 = st.selectbox("Stasiun", semua_stasiun, index=default_idx)

    data_q1 = df_waktu[df_waktu["station"] == stasiun_q1]
    tren = data_q1.set_index("datetime")["PM2.5"].resample("MS").mean().dropna()

    if tren.empty:
        st.warning("Tidak ada data untuk stasiun dan periode ini.")
    else:
        puncak_tgl, puncak_nilai = tren.idxmax(), tren.max()

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(tren.index, tren.values, color="#B0B0B0", marker="o", markersize=4)
        ax.scatter(puncak_tgl, puncak_nilai, color=MERAH, s=120, zorder=5)
        ax.annotate(
            f"Puncak: {nama_bulan(puncak_tgl)}\n{puncak_nilai:.1f} µg/m³",
            xy=(puncak_tgl, puncak_nilai),
            xytext=(-110, -10),
            textcoords="offset points",
            arrowprops=dict(arrowstyle="->", color=MERAH),
            color=MERAH,
            fontsize=11,
            ha="center",
        )
        ax.set_title(
            f"PM2.5 di {stasiun_q1} mencapai puncak pada {nama_bulan(puncak_tgl)}",
            fontsize=14,
        )
        ax.set_xlabel("Bulan")
        ax.set_ylabel("Rata-rata PM2.5 (µg/m³)")
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        # Pola musiman: rata-rata per bulan kalender
        musiman = (
            data_q1.groupby(data_q1["datetime"].dt.month)["PM2.5"].mean().reindex(range(1, 13))
        )
        bulan_tertinggi = musiman.idxmax()
        warna = [MERAH if m == bulan_tertinggi else ABU for m in musiman.index]

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.bar([BULAN_ID[m][:3] for m in musiman.index], musiman.values, color=warna)
        ax.set_title(
            f"Pola musiman: PM2.5 rata-rata tertinggi pada bulan {BULAN_ID[bulan_tertinggi]}",
            fontsize=14,
        )
        ax.set_ylabel("Rata-rata PM2.5 (µg/m³)")
        ax.grid(axis="x", visible=False)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.info(
            f"Di **{stasiun_q1}**, rata-rata bulanan PM2.5 tertinggi terjadi pada "
            f"**{nama_bulan(puncak_tgl)}** ({puncak_nilai:.1f} µg/m³). "
            f"Secara musiman, bulan **{BULAN_ID[bulan_tertinggi]}** paling tinggi "
            f"({musiman.max():.1f} µg/m³) dan **{BULAN_ID[musiman.idxmin()]}** paling rendah "
            f"({musiman.min():.1f} µg/m³)."
        )

# ------------------------------------------------------------------
# Tab 2 – Pertanyaan 2: perbandingan polutan antarstasiun
# ------------------------------------------------------------------
with tab2:
    st.subheader("Stasiun mana yang memiliki rata-rata polutan tertinggi?")

    fig, axes = plt.subplots(3, 2, figsize=(16, 15))
    for i, kolom in enumerate(POLUTAN):
        ax = axes[i // 2, i % 2]
        data_plot = df_f.groupby("station")[kolom].mean().sort_values(ascending=False)
        warna = [MERAH] + [ABU] * (len(data_plot) - 1)
        ax.bar(data_plot.index, data_plot.values, color=warna)
        ax.set_title(f"{kolom} tertinggi di {data_plot.index[0]} ({data_plot.iloc[0]:.1f})", fontsize=13)
        ax.set_ylabel(f"Rata-rata {kolom} (µg/m³)")
        ax.tick_params(axis="x", rotation=90)
        ax.grid(axis="x", visible=False)
    fig.suptitle("Perbandingan Rata-rata Polutan Antarstasiun", fontsize=16)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    ringkasan = df_f.groupby("station")[POLUTAN].mean().round(2)
    with st.expander("Lihat tabel rata-rata per stasiun"):
        st.dataframe(ringkasan)

    tertinggi = {k: ringkasan[k].idxmax() for k in POLUTAN}
    st.info(
        "Stasiun tertinggi per polutan: "
        + ", ".join(f"**{k}** → {v}" for k, v in tertinggi.items())
        + "."
    )

# ------------------------------------------------------------------
# Tab 3 – Pertanyaan 3: hubungan PM2.5 dengan meteorologi
# ------------------------------------------------------------------
with tab3:
    st.subheader("Seberapa kuat hubungan suhu, titik embun, dan angin dengan PM2.5?")
    korelasi = df_f[["PM2.5"] + METEO].corr()

    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(korelasi, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
    ax.set_title("Korelasi PM2.5 dengan Variabel Meteorologi", fontsize=13)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    kor_pm = korelasi["PM2.5"].drop("PM2.5")
    terkuat = kor_pm.abs().idxmax()
    st.info(
        f"Variabel dengan korelasi terkuat terhadap PM2.5 adalah **{terkuat}** "
        f"(r = {kor_pm[terkuat]:.2f}). Semua korelasi relatif lemah "
        f"(|r| ≤ {kor_pm.abs().max():.2f}), sehingga ketiga variabel ini belum cukup "
        "menjelaskan variasi PM2.5."
    )

# ------------------------------------------------------------------
# Tab 4 – Analisis lanjutan: manual grouping
# ------------------------------------------------------------------
with tab4:
    st.subheader("Pengelompokan stasiun berdasarkan rata-rata PM2.5 (Manual Grouping)")
    st.caption(
        "Batas kategori ditentukan untuk proyek ini (bukan standar resmi): "
        "Rendah ≤ 50, Sedang 50–75, Tinggi > 75 µg/m³."
    )

    grup = df_f.groupby("station")["PM2.5"].mean().reset_index()
    grup["Kategori"] = pd.cut(
        grup["PM2.5"], bins=[0, 50, 75, float("inf")], labels=["Rendah", "Sedang", "Tinggi"]
    )
    grup = grup.sort_values("PM2.5", ascending=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(grup["station"], grup["PM2.5"], color=grup["Kategori"].map(WARNA_KATEGORI).astype(str))
    for i, v in enumerate(grup["PM2.5"]):
        ax.text(v + 0.5, i, f"{v:.2f}", va="center", fontsize=10)
    ax.axvline(50, color="gray", linestyle="--", linewidth=1)
    ax.axvline(75, color="gray", linestyle="--", linewidth=1)
    ax.set_xlim(0, grup["PM2.5"].max() * 1.12)
    ax.set_xlabel("Rata-rata PM2.5 (µg/m³)")
    ax.set_title("Pengelompokan Stasiun Berdasarkan Rata-rata PM2.5", fontsize=14)
    ax.grid(axis="y", visible=False)
    ax.legend(
        handles=[Patch(color=c, label=k) for k, c in WARNA_KATEGORI.items()],
        title="Kategori",
        loc="lower right",
    )
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    jumlah = grup["Kategori"].value_counts()
    st.info(
        " · ".join(f"**{k}**: {int(jumlah.get(k, 0))} stasiun" for k in ["Rendah", "Sedang", "Tinggi"])
    )

st.caption("Proyek Analisis Data · Air Quality Dataset")