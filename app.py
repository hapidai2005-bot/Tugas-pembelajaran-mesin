import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Monitoring Pembayaran Siswa", page_icon="💳", layout="wide")

st.title("💳 Student Payment Monitoring System")
st.caption("Dashboard monitoring pembayaran siswa/mahasiswa — data dapat diunggah melalui file Excel.")

REQUIRED_SHEETS = ["Data_Siswa", "Data_Tagihan", "Data_Pembayaran"]

def money(value):
    return "Rp " + f"{int(value or 0):,}".replace(",", ".")

def load_workbook(uploaded):
    xls = pd.ExcelFile(uploaded)
    missing = [s for s in REQUIRED_SHEETS if s not in xls.sheet_names]
    if missing:
        st.error("Sheet tidak ditemukan: " + ", ".join(missing))
        st.info("Gunakan template Excel yang disediakan, atau sesuaikan nama sheet menjadi Data_Siswa, Data_Tagihan, dan Data_Pembayaran.")
        st.stop()
    students = pd.read_excel(xls, "Data_Siswa")
    invoices = pd.read_excel(xls, "Data_Tagihan")
    payments = pd.read_excel(xls, "Data_Pembayaran")
    return students, invoices, payments

def normalize_data(students, invoices, payments):
    for df, cols in [
        (students, ["ID_Siswa"]),
        (invoices, ["ID_Tagihan", "ID_Siswa"]),
        (payments, ["ID_Tagihan", "ID_Siswa"])
    ]:
        for c in cols:
            if c in df.columns:
                df[c] = df[c].astype(str).str.strip()
    for c in ["Total_Tagihan", "Total_Dibayar", "Sisa_Tagihan"]:
        if c in invoices.columns:
            invoices[c] = pd.to_numeric(invoices[c], errors="coerce").fillna(0)
    if "Jumlah_Bayar" in payments.columns:
        payments["Jumlah_Bayar"] = pd.to_numeric(payments["Jumlah_Bayar"], errors="coerce").fillna(0)
    # Hitung ulang dari transaksi agar data pembayaran konsisten.
    if not payments.empty and {"ID_Tagihan", "Jumlah_Bayar"}.issubset(payments.columns):
        paid = payments.groupby("ID_Tagihan")["Jumlah_Bayar"].sum()
        invoices["Total_Dibayar"] = invoices["ID_Tagihan"].map(paid).fillna(0)
    else:
        invoices["Total_Dibayar"] = invoices.get("Total_Dibayar", 0)
    invoices["Sisa_Tagihan"] = (invoices["Total_Tagihan"] - invoices["Total_Dibayar"]).clip(lower=0)
    invoices["Status_Pembayaran"] = invoices.apply(
        lambda r: "Lunas" if r["Total_Tagihan"] > 0 and r["Sisa_Tagihan"] == 0
        else ("Sebagian" if r["Total_Dibayar"] > 0 else "Belum Bayar"), axis=1
    )
    return students, invoices, payments

with st.sidebar:
    st.header("⚙️ Sumber Data")
    uploaded = st.file_uploader("Unggah dataset Excel (.xlsx)", type=["xlsx"])
    st.markdown("---")
    st.markdown("**Format sheet wajib:**")
    st.write("• Data_Siswa")
    st.write("• Data_Tagihan")
    st.write("• Data_Pembayaran")
    st.markdown("---")
    st.caption("Untuk uji coba, unggah file Template_Monitoring_Pembayaran_Siswa_Dummy.xlsx.")

if uploaded is None:
    st.info("Silakan unggah file Excel dataset pembayaran pada panel sebelah kiri.")
    st.markdown("### Belum memiliki dataset?")
    st.write("Unduh template dummy berikut, kemudian unggah kembali ke aplikasi.")
    st.stop()

try:
    students, invoices, payments = load_workbook(uploaded)
    students, invoices, payments = normalize_data(students, invoices, payments)
except Exception as e:
    st.error(f"Gagal membaca file: {e}")
    st.stop()

# Filters
st.sidebar.subheader("🔎 Filter Data")
if "Tahun_Ajaran" in students.columns:
    years = ["Semua"] + sorted(students["Tahun_Ajaran"].dropna().astype(str).unique().tolist())
    selected_year = st.sidebar.selectbox("Tahun Ajaran", years)
    if selected_year != "Semua":
        students = students[students["Tahun_Ajaran"].astype(str) == selected_year]
        invoices = invoices[invoices["ID_Siswa"].isin(students["ID_Siswa"])]
if "Kelas" in students.columns:
    classes = ["Semua"] + sorted(students["Kelas"].dropna().astype(str).unique().tolist())
    selected_class = st.sidebar.selectbox("Kelas", classes)
    if selected_class != "Semua":
        students = students[students["Kelas"].astype(str) == selected_class]
        invoices = invoices[invoices["ID_Siswa"].isin(students["ID_Siswa"])]

valid_ids = set(students["ID_Siswa"].astype(str)) if "ID_Siswa" in students.columns else set()
invoices = invoices[invoices["ID_Siswa"].astype(str).isin(valid_ids)]
total_students = students["ID_Siswa"].nunique() if "ID_Siswa" in students.columns else len(students)

# Status siswa berdasarkan seluruh tagihan dalam filter
status_per_student = invoices.groupby("ID_Siswa")["Status_Pembayaran"].apply(
    lambda s: "Lunas" if len(s) and (s == "Lunas").all()
    else ("Belum Bayar" if (s == "Belum Bayar").all() else "Belum Lunas")
)
lunas = int((status_per_student == "Lunas").sum())
belum_lunas = int((status_per_student != "Lunas").sum())
belum_bayar = int((status_per_student == "Belum Bayar").sum())
sebagian_atau_campuran = max(0, belum_lunas - belum_bayar)
total_tagihan = invoices["Total_Tagihan"].sum()
total_dibayar = invoices["Total_Dibayar"].sum()
tunggakan = invoices["Sisa_Tagihan"].sum()
persen_lunas = (lunas / total_students * 100) if total_students else 0

st.subheader("Ringkasan Pembayaran")
c1,c2,c3,c4 = st.columns(4)
c1.metric("Total Siswa", f"{total_students:,}".replace(",", "."))
c2.metric("Siswa Lunas", f"{lunas:,}".replace(",", "."), f"{(lunas/total_students*100 if total_students else 0):.1f}%")
c3.metric("Belum Lunas", f"{belum_lunas:,}".replace(",", "."), f"{(belum_lunas/total_students*100 if total_students else 0):.1f}%")
c4.metric("Belum Bayar", f"{belum_bayar:,}".replace(",", "."))

c5,c6,c7 = st.columns(3)
c5.metric("Total Tagihan", money(total_tagihan))
c6.metric("Total Pembayaran", money(total_dibayar))
c7.metric("Total Tunggakan", money(tunggakan))

left, right = st.columns(2)
with left:
    st.markdown("#### Komposisi status tagihan")
    status_counts = invoices["Status_Pembayaran"].value_counts().reindex(["Lunas","Sebagian","Belum Bayar"], fill_value=0).reset_index()
    status_counts.columns = ["Status", "Jumlah Tagihan"]
    fig = px.pie(status_counts, names="Status", values="Jumlah Tagihan", hole=0.45)
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.markdown("#### Pembayaran berdasarkan kelas")
    if "Kelas" in students.columns:
        class_map = students[["ID_Siswa","Kelas"]].drop_duplicates()
        class_data = invoices.merge(class_map, on="ID_Siswa", how="left").groupby("Kelas", as_index=False).agg(
            Total_Tagihan=("Total_Tagihan","sum"), Total_Dibayar=("Total_Dibayar","sum")
        )
        fig2 = px.bar(class_data, x="Kelas", y=["Total_Dibayar","Total_Tagihan"], barmode="group")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Kolom Kelas belum tersedia pada Data_Siswa.")

st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📋 Status Siswa", "🧾 Data Tagihan", "💰 Riwayat Pembayaran"])

with tab1:
    st.markdown("#### Daftar status pembayaran per siswa")
    detail = students.copy()
    detail["Status_Siswa_Pembayaran"] = detail["ID_Siswa"].astype(str).map(status_per_student).fillna("Belum Ada Tagihan")
    if "Nama_Siswa" in detail.columns:
        search = st.text_input("Cari nama atau NIS siswa")
        if search:
            mask = detail.astype(str).apply(lambda col: col.str.contains(search, case=False, na=False)).any(axis=1)
            detail = detail[mask]
    st.dataframe(detail, use_container_width=True, hide_index=True)
    csv = detail.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Unduh status siswa (CSV)", csv, "status_siswa.csv", "text/csv")

with tab2:
    st.markdown("#### Rincian tagihan")
    status_filter = st.multiselect("Filter status tagihan", ["Lunas","Sebagian","Belum Bayar"], default=["Lunas","Sebagian","Belum Bayar"])
    inv_view = invoices[invoices["Status_Pembayaran"].isin(status_filter)].copy()
    st.dataframe(inv_view, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Unduh data tagihan (CSV)", inv_view.to_csv(index=False).encode("utf-8-sig"),
                       "data_tagihan.csv", "text/csv")

with tab3:
    st.markdown("#### Riwayat transaksi pembayaran")
    st.dataframe(payments, use_container_width=True, hide_index=True)
    st.download_button("⬇️ Unduh riwayat pembayaran (CSV)", payments.to_csv(index=False).encode("utf-8-sig"),
                       "riwayat_pembayaran.csv", "text/csv")

st.caption("Catatan: status siswa dihitung lunas jika seluruh tagihan pada data/filter yang sedang ditampilkan telah lunas. Pastikan satu baris Data_Tagihan mewakili satu tagihan.")
