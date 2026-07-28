# Piston Monitoring Dashboard — deploy ke Vercel

Versi deploy dari dashboard visualisasi `cylinder_timeseries_clean.csv`. File statis murni
(`index.html` + `data.json`), tidak butuh build step — `index.html` mengambil `data.json`
lewat `fetch()` saat halaman dibuka, jadi update data berikutnya tidak perlu menyentuh HTML.

## Deploy pertama kali

Vercel CLI sudah terpasang di komputer ini (`vercel --version` → 39.2.2). Yang belum:
login ke akun Vercel-mu (langkah ini interaktif, harus dijalankan sendiri lewat browser/email,
tidak bisa dilakukan otomatis).

```
cd piston-monitoring-dashboard
vercel login
vercel --prod
```

`vercel --prod` pertama kali akan menanyakan beberapa hal (set up and deploy → Y, pilih
scope/akun, link to existing project → N, nama project, root directory → `.`). Setelah itu
Vercel kasih URL production, contoh `https://piston-monitoring-dashboard.vercel.app`.

## Update data (kapan pun ada laporan baru)

```
python update_data.py
vercel --prod
```

`update_data.py` membaca ulang `dataset/processed/cylinder_timeseries_clean.csv` (satu folder
di atas) dan menulis `data.json` yang baru. `vercel --prod` mem-publish ulang — proyek yang
sama, URL yang sama, cuma datanya yang berubah. Kalau sumber datanya juga perlu dibersihkan
ulang duluan (ada laporan .xls baru), jalankan dulu `clean_cylinder_timeseries.py` di root
project sebelum `update_data.py`.

## Penting soal akses

Deployment production di Vercel **bisa diakses siapa saja yang punya link** (tidak
terindeks Google, tapi juga tidak ada gerbang login) — data operasional 3 kapal (nama kapal,
angka performa mesin) ada di dalamnya. Kalau PM-mu satu-satunya yang perlu akses dan itu
cukup, tidak perlu tindakan tambahan. Kalau mau dibatasi lebih dari sekadar "linknya tidak
disebar", opsinya:

- **Password protection bawaan Vercel** — butuh paket Pro, tinggal aktif dari dashboard Vercel
  tanpa ubah kode.
- **Gerbang password sederhana** (Edge Middleware) — bisa jalan di paket gratis, saya bisa
  buatkan kalau diminta.

## Struktur folder

```
piston-monitoring-dashboard/
├── index.html       # dashboard (fetch data.json saat dibuka)
├── data.json        # data hasil olahan, dibuat ulang oleh update_data.py
├── update_data.py    # regenerasi data.json dari dataset/processed/cylinder_timeseries_clean.csv
├── vercel.json       # header cache untuk data.json (supaya update tidak ketahan cache lama)
└── .gitignore
```
