# 
<div align="center">
<pre>
  _____ _           _ _ _______                  
 / ____(_)         (_) |__   __|                 
| |  __ ___   _____ _| |_ | | _   _ _ __   ___   
| | |_ | \ \ / / _ \ | __|| || | | | '_ \ / _ \  
| |__| | |\ V /  __/ | |_ | || |_| | |_) | (_) | 
 \_____|_| \_/ \___|_|\__||_| \__, | .__/ \___/  
                               __/ | |           
                              |___/|_|           
</pre>

**Professional Bilingual Document Linter (ID + EN) 🚀**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Open Source Love](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://github.com/ellerbrock/open-source-badges/)

</div>

---

## 📖 Apa itu GiveitTypo?

Kadang capek gasi bruhuhhhhh revisi skripsi/jurnal dicoret dosen gara-gara typo atau spasi berantakan? **GiveitTypo**  buat bantu nilai kalian bruhhh. 

Ini adalah aplikasi *desktop* mandiri (Standalone App) berbasis Python yang dirancang khusus untuk memindai, menganalisis, dan memberikan laporan visual terhadap kesalahan tata tulis (PUEBI) serta salah ejaan (Typo) di dalam dokumen PDF lu. Hasil laporannya? Mirip banget sama **Turnitin**, lengkap dengan *highlight* warna dan *bounding box* di atas dokumen asli lu!

##  Fitur Andalan

* 🧠 **Hybrid 5-Layer Engine**: Nggak cuma nebak asal, mesin ini divalidasi oleh Kamus Besar Bahasa Indonesia (KBBI 133k Words), Sastrawi Root Dictionary, dan Google English Corpus. Dokumen bilingual? Sikat!
* 🎨 **Visual PDF Report ala Turnitin**: Hasil akhirnya bukan teks mentah, melainkan PDF lu yang udah di- *zoom out* rapi ke kertas A4, dibingkai, dan dikasih stabilo warna (Merah untuk Typo, Kuning untuk Format) beserta nomor index.
* ⚡ **Asynchronous Loading**: UI nggak bakal nge- *freeze* atau *Not Responding* berkat sistem *Background Worker Threading*.
* 🛠 **Custom Dictionary**: Punya istilah spesifik kampus atau singkatan gaul? Tinggal masukin ke `kamus_custom.txt` dan mesin bakal ngebaca itu sebagai kata yang sah (Whitelist).

---

## 🚀 Cara Pakai (Untuk Non-Programmer)

Buat lu yang nggak mau ribet *coding* dan cuma pengen pake aplikasinya buat ngecek skripsi:
1. Pergi ke tab **[Releases](../../releases)** di sebelah kanan halaman ini.
2. Download file **`GiveitTypo.exe`**.
3. Taruh di dalam satu folder (karena dia butuh bikin file custom dictionary).
4. *Double-click* `.exe`-nya, unggah PDF lu, dan tunggu keajaiban terjadi!

---

## 💻 Cara Install (Untuk Developer / Kontributor)

Mau ikut ngembangin kode ini? Gas, ikuti langkah ini:

**1. Clone Repository ini**
```bash
git clone [https://github.com/USERNAMEU/giveit-typo.git](https://github.com/USERNAME/giveit-typo.git)
cd giveit-typo

# GiveitTypo-Engine
Engine spell checker untuk menganalisis dokumen, skripsi, tugas makalah, tugas akhir, karya akhir bagi mahasiswa, engine tidak cukup powerfull karna keakuratanya dibawah 80% tapi cukup untuk gambaran dasar

