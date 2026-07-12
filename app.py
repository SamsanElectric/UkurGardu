import math
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="UkurGardu", page_icon="⚡", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
DATA_FILE = DATA_DIR / "pengukuran_gardu.csv"
LINE_VOLTAGE = 380  # tegangan fasa-fasa sisi sekunder trafo distribusi (Volt)
TRAFO_SIZES = [25, 50, 100, 160, 200, 250, 315, 400, 630]

COLUMNS = [
    "TIMESTAMP", "TANGGAL", "ID", "KODE UNIT", "UNIT", "PENYULANG", "NOMOR GARDU",
    "LWBP/WBP", "KAPASITAS TRAFO KVA", "JUMLAH JURUSAN",
    "R INDUK", "S INDUK", "T INDUK", "N INDUK",
    "R JURUSAN 1", "S JURUSAN 1", "T JURUSAN 1", "N JURUSAN 1",
    "R JURUSAN 2", "S JURUSAN 2", "T JURUSAN 2", "N JURUSAN 2",
    "R JURUSAN 3", "S JURUSAN 3", "T JURUSAN 3", "N JURUSAN 3",
    "R JURUSAN 4", "S JURUSAN 4", "T JURUSAN 4", "N JURUSAN 4",
    "COS Q", "% TIDAK SEIMBANG", "% BEBAN TRAFO", "KAPASITAS DERATING",
    "PETUGAS", "KETERANGAN",
]


def ensure_data_file():
    DATA_DIR.mkdir(exist_ok=True)
    if not DATA_FILE.exists():
        pd.DataFrame(columns=COLUMNS).to_csv(DATA_FILE, index=False)


def load_data() -> pd.DataFrame:
    ensure_data_file()
    return pd.read_csv(DATA_FILE, dtype=str).fillna("")


def append_row(row: dict):
    df = load_data()
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)


def arus_nominal_trafo(kva: float) -> float:
    return kva * 1000 / (math.sqrt(3) * LINE_VOLTAGE)


def persen_tidak_seimbang(r: float, s: float, t: float) -> float:
    rata = (r + s + t) / 3
    if rata == 0:
        return 0.0
    return abs(max(r, s, t) - rata) / rata * 100


def persen_beban_trafo(r: float, s: float, t: float, kva: float) -> float:
    if kva == 0:
        return 0.0
    rata = (r + s + t) / 3
    return rata / arus_nominal_trafo(kva) * 100


def kapasitas_derating(r: float, s: float, t: float, kva: float) -> float:
    maks = max(r, s, t)
    if maks == 0:
        return kva
    rata = (r + s + t) / 3
    return kva * rata / maks


def buat_id(kode_unit: str, nomor_gardu: str, waktu: datetime) -> str:
    return f"{kode_unit}.{nomor_gardu}-{waktu.strftime('%Y%m%d')}-{waktu.strftime('%H%M%S')}"


st.title("⚡ UkurGardu — Input Pengukuran Gardu Distribusi")

tab_input, tab_data = st.tabs(["📝 Input Pengukuran", "📊 Data & Unduh"])

with tab_input:
    with st.form("form_pengukuran", clear_on_submit=True):
        st.subheader("Identitas Gardu")
        col1, col2, col3 = st.columns(3)
        with col1:
            tanggal = st.date_input("Tanggal Pengukuran", value=date.today(), format="DD/MM/YYYY")
            kode_unit = st.text_input("Kode Unit", placeholder="cth. PGK").strip().upper()
        with col2:
            unit = st.text_input("Unit", placeholder="cth. KUPRIK")
            penyulang = st.text_input("Penyulang")
        with col3:
            nomor_gardu = st.text_input("Nomor Gardu", placeholder="cth. GD01.4105560").strip().upper()
            petugas = st.text_input("Petugas Pengukur")

        col4, col5, col6 = st.columns(3)
        with col4:
            lwbp_wbp = st.selectbox("LWBP / WBP", ["LWBP", "WBP"])
        with col5:
            kapasitas_trafo = st.selectbox("Kapasitas Trafo (kVA)", TRAFO_SIZES, index=2)
        with col6:
            jumlah_jurusan = st.number_input("Jumlah Jurusan", min_value=1, max_value=4, value=2, step=1)

        st.subheader("Arus Induk (Ampere)")
        c1, c2, c3, c4 = st.columns(4)
        r_induk = c1.number_input("R Induk", min_value=0.0, step=0.1)
        s_induk = c2.number_input("S Induk", min_value=0.0, step=0.1)
        t_induk = c3.number_input("T Induk", min_value=0.0, step=0.1)
        n_induk = c4.number_input("N Induk", min_value=0.0, step=0.1)

        st.subheader("Arus per Jurusan (Ampere)")
        jurusan_data = {}
        for i in range(1, int(jumlah_jurusan) + 1):
            st.markdown(f"**Jurusan {i}**")
            c1, c2, c3, c4 = st.columns(4)
            jurusan_data[i] = (
                c1.number_input(f"R Jurusan {i}", min_value=0.0, step=0.1, key=f"r{i}"),
                c2.number_input(f"S Jurusan {i}", min_value=0.0, step=0.1, key=f"s{i}"),
                c3.number_input(f"T Jurusan {i}", min_value=0.0, step=0.1, key=f"t{i}"),
                c4.number_input(f"N Jurusan {i}", min_value=0.0, step=0.1, key=f"n{i}"),
            )

        cos_q = st.number_input("COS Q", min_value=0.0, max_value=1.0, value=0.9, step=0.01)
        keterangan = st.text_area("Keterangan (opsional)")

        submitted = st.form_submit_button("💾 Simpan Pengukuran")

    if submitted:
        if not kode_unit or not penyulang or not nomor_gardu:
            st.error("Kode Unit, Penyulang, dan Nomor Gardu wajib diisi.")
        else:
            now = datetime.now()
            row = {c: "" for c in COLUMNS}
            row.update({
                "TIMESTAMP": now.strftime("%d/%m/%Y %H.%M.%S"),
                "TANGGAL": tanggal.strftime("%d/%m/%Y"),
                "ID": buat_id(kode_unit, nomor_gardu, now),
                "KODE UNIT": kode_unit,
                "UNIT": unit,
                "PENYULANG": penyulang,
                "NOMOR GARDU": nomor_gardu,
                "LWBP/WBP": lwbp_wbp,
                "KAPASITAS TRAFO KVA": kapasitas_trafo,
                "JUMLAH JURUSAN": int(jumlah_jurusan),
                "R INDUK": r_induk, "S INDUK": s_induk, "T INDUK": t_induk, "N INDUK": n_induk,
                "COS Q": cos_q,
                "PETUGAS": petugas,
                "KETERANGAN": keterangan,
                "% TIDAK SEIMBANG": f"{round(persen_tidak_seimbang(r_induk, s_induk, t_induk))}%",
                "% BEBAN TRAFO": f"{round(persen_beban_trafo(r_induk, s_induk, t_induk, kapasitas_trafo))}%",
                "KAPASITAS DERATING": round(kapasitas_derating(r_induk, s_induk, t_induk, kapasitas_trafo)),
            })
            for i, (r, s, t, n) in jurusan_data.items():
                row[f"R JURUSAN {i}"] = r
                row[f"S JURUSAN {i}"] = s
                row[f"T JURUSAN {i}"] = t
                row[f"N JURUSAN {i}"] = n

            append_row(row)
            st.success(f"Pengukuran gardu {nomor_gardu} tersimpan dengan ID {row['ID']}.")
            st.json({
                "% TIDAK SEIMBANG": row["% TIDAK SEIMBANG"],
                "% BEBAN TRAFO": row["% BEBAN TRAFO"],
                "KAPASITAS DERATING": row["KAPASITAS DERATING"],
            })

with tab_data:
    df = load_data()
    st.subheader(f"Riwayat Pengukuran ({len(df)} data)")

    colf1, colf2 = st.columns(2)
    cari_gardu = colf1.text_input("Cari Nomor Gardu / Penyulang")
    cari_unit = colf2.text_input("Cari Unit")

    filtered = df.copy()
    if cari_gardu:
        mask = filtered["NOMOR GARDU"].str.contains(cari_gardu, case=False, na=False) | \
               filtered["PENYULANG"].str.contains(cari_gardu, case=False, na=False)
        filtered = filtered[mask]
    if cari_unit:
        filtered = filtered[filtered["UNIT"].str.contains(cari_unit, case=False, na=False)]

    st.dataframe(filtered, use_container_width=True)

    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Unduh Data (CSV)", csv_bytes, "pengukuran_gardu.csv", "text/csv")
