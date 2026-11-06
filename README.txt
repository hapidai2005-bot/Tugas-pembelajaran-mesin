# Sistem Monitoring Pembayaran Siswa — Streamlit

## Isi folder
- `app.py` : aplikasi Streamlit
- `requirements.txt` : pustaka yang diperlukan

## Cara menjalankan di Windows
1. Pastikan Python sudah terpasang.
2. Simpan file Excel template dummy pada komputer.
3. Buka Command Prompt pada folder aplikasi.
4. Jalankan:
   `py -m pip install -r requirements.txt`
5. Jalankan aplikasi:
   `py -m streamlit run app.py`
6. Browser akan membuka aplikasi. Unggah file Excel pada panel kiri.

## Format Excel
File harus memiliki tiga sheet:
- `Data_Siswa`
- `Data_Tagihan`
- `Data_Pembayaran`

Nama kolom utama:
- Data_Siswa: `ID_Siswa`, `NIS`, `Nama_Siswa`, `Kelas`, `Tahun_Ajaran`, `Status_Siswa`
- Data_Tagihan: `ID_Tagihan`, `ID_Siswa`, `Total_Tagihan`
- Data_Pembayaran: `ID_Pembayaran`, `ID_Tagihan`, `ID_Siswa`, `Jumlah_Bayar`

Aplikasi menghitung ulang total dibayar dari transaksi pada sheet Data_Pembayaran.
Data pada template yang disertakan adalah data dummy/fiktif.
