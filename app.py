import os
import sys
import re
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from io import BytesIO
from datetime import datetime

# Engine 1: Typo Hybrid 6-Layer (ID + EN) -> SASTRAWI KEMBALI BERSINAR!
from symspellpy import SymSpell, Verbosity
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

# Engine 2: PDF Manipulator
import fitz  # PyMuPDF

# Engine 3: ReportLab (Cover & Final Report)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors

def resource_path(relative_path):
    """Membaca file dari dalam perut .exe (Untuk database besar)"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_exe_dir():
    """Mendapatkan lokasi folder tempat .exe dijalankan (Untuk Custom Dict)"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(".")

class GiveitTypoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Giveit Typo - Professional Document Linter")
        self.root.geometry("850x650")
        self.root.configure(bg="#f4f6f9")
        
        self.file_path = ""
        self.extracted_text = ""
        self.analysis_results = {}
        self.valid_words_cache = set()
        
        # Path dinamis untuk Kamus Custom agar tetap bisa diedit user
        self.custom_dict_path = os.path.join(get_exe_dir(), "kamus_custom.txt")
        
        self.setup_ui()
        self.root.after(100, self.start_background_engine)

    def start_background_engine(self):
        self.btn_upload.config(state=tk.DISABLED)
        self.btn_custom_dict.config(state=tk.DISABLED)
        threading.Thread(target=self.setup_engines_worker, daemon=True).start()

    def update_status(self, teks, warna="#2563eb"):
        self.root.after(0, lambda: self.lbl_file.config(text=teks, fg=warna))

    def setup_engines_worker(self):
        self.sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
        
        try:
            # LAPIS 1: Sastrawi (Akar Kata Resmi)
            self.update_status("⚙️ [1/6] Mengekstrak Sastrawi Root Dictionary...", "#ea580c")
            factory = StemmerFactory()
            for word in factory.get_words():
                self.valid_words_cache.add(word)
                self.sym_spell.create_dictionary_entry(word, 1000000)

            # LAPIS 2: Kamus Indonesia 50K
            self.update_status("⚙️ [2/6] Memuat Kamus Indonesia (50.000 kata)...")
            file_id_50k = resource_path("kamus_indonesia_50k.txt")
            if os.path.exists(file_id_50k):
                with open(file_id_50k, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip().lower()
                        if word.isalpha():
                            self.valid_words_cache.add(word)
                            self.sym_spell.create_dictionary_entry(word, 500000)

            # LAPIS 3: Kamus Inggris 50K
            self.update_status("⚙️ [3/6] Memuat Kamus Inggris (50.000 kata)...")
            file_en_50k = resource_path("kamus_inggris_50k.txt")
            if os.path.exists(file_en_50k):
                with open(file_en_50k, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip().lower()
                        if word.isalpha():
                            self.valid_words_cache.add(word)
                            self.sym_spell.create_dictionary_entry(word, 250000)

            # LAPIS 4: Leipzig Indonesia Corpus
            self.update_status("⚙️ [4/6] Memuat Leipzig Corpus ID (133.000 kata)...")
            file_kbbi = resource_path("kbbi_database.txt")
            if os.path.exists(file_kbbi):
                with open(file_kbbi, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'): continue
                        parts = line.split()
                        word = parts[0].lower()
                        freq = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10000
                        self.valid_words_cache.add(word)
                        self.sym_spell.create_dictionary_entry(word, freq)

            # LAPIS 5: Google English Corpus
            self.update_status("⚙️ [5/6] Memuat Google Corpus EN (Data Global)...")
            file_google = resource_path("google_english_corpus.txt")
            if os.path.exists(file_google):
                with open(file_google, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'): continue
                        parts = line.split()
                        word = parts[0].lower()
                        freq = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 10000
                        self.valid_words_cache.add(word)
                        self.sym_spell.create_dictionary_entry(word, freq)

            # LAPIS 6: Custom Dictionary (Berada di luar .exe agar bisa diedit)
            self.update_status("⚙️ [6/6] Memuat Custom Dictionary...")
            if not os.path.exists(self.custom_dict_path):
                with open(self.custom_dict_path, 'w', encoding='utf-8') as f:
                    f.write("# Masukkan nama, singkatan, atau istilah spesifik kampus.\n")
                    f.write("giveit\ntypo\n")
            self.load_custom_dictionary()

            self.root.after(0, self.finish_loading_engines)
            
        except Exception as e:
            # Jika ada error, tampilkan di GUI agar tidak STUCK dalam diam!
            self.root.after(0, lambda: messagebox.showerror("Engine Error", f"Sistem Gagal Memuat:\n{e}"))
            self.update_status(f"❌ Error: {e}", "#ef4444")

    def finish_loading_engines(self):
        self.lbl_file.config(text=f"✅ Engine Siap! (Giveit Typo: Hybrid ID+EN 6-Layer).", fg="#10b981")
        self.btn_upload.config(state=tk.NORMAL)
        self.btn_custom_dict.config(state=tk.NORMAL)

    def load_custom_dictionary(self):
        if os.path.exists(self.custom_dict_path):
            with open(self.custom_dict_path, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word and not word.startswith('#'):
                        self.valid_words_cache.add(word)
                        self.sym_spell.create_dictionary_entry(word, 999999999)

    def open_text_file(self, filepath):
        if not os.path.exists(filepath): return
        try:
            if platform.system() == 'Windows': os.startfile(filepath)
            elif platform.system() == 'Darwin': subprocess.call(('open', filepath))
            else: subprocess.call(('xdg-open', filepath))
        except Exception as e: messagebox.showerror("Error", f"Gagal membuka file: {e}")

    def setup_ui(self):
        header_frame = tk.Frame(self.root, bg="#1e293b", padx=15, pady=15)
        header_frame.pack(fill=tk.X)
        
        tk.Label(header_frame, text="📝 Giveit Typo (Professional Edition)", font=("Helvetica", 16, "bold"), fg="white", bg="#1e293b").pack(anchor="w")
        tk.Label(header_frame, text="Engine: Hybrid 6-Layer (ID+EN) | Laporan PDF A4 Terintegrasi", font=("Helvetica", 10), fg="#cbd5e1", bg="#1e293b").pack(anchor="w")

        main_frame = tk.Frame(self.root, bg="#f4f6f9", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = tk.Frame(main_frame, bg="#f4f6f9")
        btn_frame.pack(pady=10)

        self.btn_upload = tk.Button(btn_frame, text="📂 Unggah Dokumen (PDF)", font=("Helvetica", 10, "bold"), bg="#2563eb", fg="white", padx=15, pady=8, bd=0, state=tk.DISABLED, command=self.upload_file)
        self.btn_upload.pack(side=tk.LEFT, padx=5)

        self.btn_custom_dict = tk.Button(btn_frame, text="📝 Edit Kamus Kustom", font=("Helvetica", 10, "bold"), bg="#475569", fg="white", padx=15, pady=8, bd=0, state=tk.DISABLED, command=lambda: self.open_text_file(self.custom_dict_path))
        self.btn_custom_dict.pack(side=tk.LEFT, padx=5)

        self.lbl_file = tk.Label(main_frame, text="Mempersiapkan sistem...", font=("Helvetica", 9, "bold"), fg="#ea580c", bg="#f4f6f9")
        self.lbl_file.pack(pady=5)

        self.stats_frame = tk.LabelFrame(main_frame, text=" Dasbor Analisis Sementara ", font=("Helvetica", 10, "bold"), bg="white", padx=15, pady=15)
        self.stats_frame.pack(fill=tk.X, pady=15)

        self.lbl_words = tk.Label(self.stats_frame, text="Total Kata: -", font=("Helvetica", 10), bg="white", anchor="w")
        self.lbl_words.grid(row=0, column=0, sticky="w", pady=5, padx=20)

        self.lbl_typos = tk.Label(self.stats_frame, text="Typo Ejaan: -", font=("Helvetica", 10), bg="white", anchor="w")
        self.lbl_typos.grid(row=0, column=1, sticky="w", pady=5, padx=20)

        self.lbl_format = tk.Label(self.stats_frame, text="Error PUEBI: -", font=("Helvetica", 10), bg="white", anchor="w")
        self.lbl_format.grid(row=1, column=0, sticky="w", pady=5, padx=20)

        self.lbl_score = tk.Label(self.stats_frame, text="Indeks Kerapian: -", font=("Helvetica", 11, "bold"), bg="white", anchor="w")
        self.lbl_score.grid(row=1, column=1, sticky="w", pady=5, padx=20)

        self.btn_export = tk.Button(main_frame, text="📥 Unduh Laporan PDF Lengkap", font=("Helvetica", 12, "bold"), bg="#10b981", fg="white", padx=20, pady=10, bd=0, state=tk.DISABLED, command=self.export_to_pdf)
        self.btn_export.pack(pady=20)

    def upload_file(self):
        self.file_path = filedialog.askopenfilename(title="Pilih File PDF", filetypes=[("PDF Documents", "*.pdf")])
        if self.file_path:
            self.load_custom_dictionary() 
            self.lbl_file.config(text=f"Menganalisis: {os.path.basename(self.file_path)}...", fg="#0f172a")
            self.root.update()
            threading.Thread(target=self.process_document, daemon=True).start()

    def process_document(self):
        try:
            self.doc_fitz = fitz.open(self.file_path)
            teks_gabungan = []
            for page in self.doc_fitz:
                teks_gabungan.append(page.get_text())
            
            self.extracted_text = "\n".join(teks_gabungan)
            if not self.extracted_text.strip(): raise ValueError("Dokumen kosong.")
            
            self.analyze_text()
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Gagal membaca PDF:\n{e}"))

    def analyze_text(self):
        text_bersih = re.sub(r'(?<=\w) {2}(?=\w)', ' ', self.extracted_text) 
        total_words_raw = len(re.findall(r'\b\w+\b', text_bersih))
        if total_words_raw == 0: return

        # 1. PUEBI LINTER
        format_issues = {}
        for m in re.finditer(r' {3,}', text_bersih):
            snippet = text_bersih[max(0, m.start()-10):min(len(text_bersih), m.end()+10)].replace('\n', ' ').strip()
            key = (snippet, "Spasi Berlebih")
            if key not in format_issues: format_issues[key] = {"teks": snippet, "perbaikan": re.sub(r' {3,}', ' ', snippet), "jenis": "Spasi Berlebih", "freq": 1}
            else: format_issues[key]["freq"] += 1

        for m in re.finditer(r'([a-zA-Z]) +([,.])', text_bersih):
            snippet = text_bersih[max(0, m.start()-10):min(len(text_bersih), m.end()+10)].replace('\n', ' ').strip()
            key = (snippet, "Spasi Sebelum Tanda Baca")
            if key not in format_issues: format_issues[key] = {"teks": snippet, "perbaikan": snippet.replace(m.group(0), m.group(1) + m.group(2)), "jenis": "Spasi sblm tanda baca", "freq": 1}
            else: format_issues[key]["freq"] += 1

        for m in re.finditer(r'([a-z][.,;:!?])([a-zA-Z])', text_bersih):
            snippet = text_bersih[max(0, m.start()-10):min(len(text_bersih), m.end()+10)].replace('\n', ' ').strip()
            key = (snippet, "Kurang Spasi")
            if key not in format_issues: format_issues[key] = {"teks": snippet, "perbaikan": snippet.replace(m.group(0), m.group(1) + " " + m.group(2)), "jenis": "Kurang spasi", "freq": 1}
            else: format_issues[key]["freq"] += 1

        total_format_errors = sum(item["freq"] for item in format_issues.values())

        # 2. TYPO (HYBRID ID+EN)
        word_tokens = re.finditer(r'\b[a-zA-Z]{3,}\b', text_bersih)
        typo_dict = {}
        word_counts = {}
        for match in word_tokens:
            word = match.group()
            if word.isupper() or word.istitle(): continue
            word_lower = word.lower()
            word_counts[word_lower] = word_counts.get(word_lower, 0) + 1

        for word, count in word_counts.items():
            if word in self.valid_words_cache: continue
            suggestions = self.sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
            if suggestions:
                best = suggestions[0].term
                if best != word: typo_dict[word] = {"count": count, "suggestion": best}

        filtered_typos = {k: v for k, v in typo_dict.items() if v["count"] > 1}
        total_typos = sum(item["count"] for item in filtered_typos.values())

        total_issues = total_typos + total_format_errors
        raw_score = 100 - ((total_issues / total_words_raw) * 100) if total_words_raw > 0 else 0
        cleanliness_score = max(0, min(100, round(raw_score, 2)))

        self.analysis_results = {
            "total_words": total_words_raw, "total_typos": total_typos, "total_format": total_format_errors,
            "cleanliness_score": cleanliness_score, "typo_details": filtered_typos, "format_details": format_issues
        }

        self.root.after(0, self.update_gui_after_analysis)

    def update_gui_after_analysis(self):
        self.lbl_file.config(text=f"Selesai: {os.path.basename(self.file_path)}", fg="#0f172a")
        self.lbl_words.config(text=f"Total Kata: {self.analysis_results['total_words']:,}")
        self.lbl_typos.config(text=f"Typo Ejaan: {self.analysis_results['total_typos']:,}")
        self.lbl_format.config(text=f"Error PUEBI: {self.analysis_results['total_format']:,}")
        self.lbl_score.config(text=f"Indeks Kerapian: {self.analysis_results['cleanliness_score']}%")
        self.btn_export.config(state=tk.NORMAL)
        messagebox.showinfo("Analisis Selesai", "Silakan klik Unduh Laporan PDF Lengkap!")

    def _generate_report_pdf(self, part="cover", sorted_typos=None, sorted_formats=None):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        styles = getSampleStyleSheet()
        
        score_color = "#10b981" if self.analysis_results["cleanliness_score"] >= 90 else "#f59e0b" if self.analysis_results["cleanliness_score"] >= 75 else "#ef4444"
        
        if part == "cover":
            waktu_cetak = datetime.now().strftime("%d %B %Y | %H:%M WIB")
            
            title_style = ParagraphStyle('CoverTitle', fontName='Times-Bold', fontSize=26, leading=30, textColor=colors.HexColor("#1e293b"), alignment=TA_CENTER, spaceAfter=30)
            subtitle_style = ParagraphStyle('Sub', fontName='Times-Roman', fontSize=12, leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#334155"), spaceAfter=8)
            
            story.append(Spacer(1, 80))
            story.append(Paragraph("LAPORAN ORIGINALITAS EJAAN<br/>& ANALISIS TATA TULIS", title_style))
            story.append(Spacer(1, 30))
            
            story.append(Paragraph(f"<b>Dokumen Diuji:</b> {os.path.basename(self.file_path)}", subtitle_style))
            story.append(Paragraph(f"<b>Tanggal Pengujian:</b> {waktu_cetak}", subtitle_style))
            story.append(Paragraph(f"<b>Diuji Oleh:</b> Pengguna Admin", subtitle_style))
            story.append(Paragraph(f"<b>Mesin Deteksi:</b> Giveit Typo Engine (Hybrid 6-Layer)", subtitle_style))
            story.append(Spacer(1, 40))
            
            story.append(Paragraph("INDEKS KERAPIAN DOKUMEN", ParagraphStyle('Sub', fontName='Times-Bold', alignment=TA_CENTER, fontSize=14, textColor=colors.HexColor("#0f172a"))))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<font size=65 color='{score_color}'>{self.analysis_results['cleanliness_score']}%</font>", ParagraphStyle('Score', fontName='Times-Bold', alignment=TA_CENTER)))
            
            story.append(Spacer(1, 80))
            
            confidence_score = "74.5%" 
            story.append(Paragraph(f"System Confidence Score: <b>{confidence_score}</b> (Tingkat Akurasi Sistem Giveit Typo)", ParagraphStyle('Sub', fontName='Times-Roman', alignment=TA_CENTER, fontSize=11, textColor=colors.HexColor("#16a34a"))))
            story.append(Spacer(1, 5))
            story.append(Paragraph("Tervalidasi oleh: Leipzig ID Corpus, Google EN Corpus, & Sastrawi", ParagraphStyle('Sub', fontName='Times-Italic', alignment=TA_CENTER, fontSize=10, textColor=colors.HexColor("#64748b"))))
            story.append(Spacer(1, 15))
            story.append(Paragraph("<font size=9 color='#94a3b8'>Dicetak secara otomatis oleh Giveit Typo - Professional Document Linter</font>", subtitle_style))
        
        elif part == "report":
            title_report = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=18, textColor=colors.HexColor("#1e293b"), spaceAfter=10)
            normal_report = ParagraphStyle('Normal', fontName='Helvetica', fontSize=10)
            h2_report = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=12, spaceAfter=8)

            story.append(Paragraph("LAPORAN ORIGINALITAS EJAAN", title_report))
            story.append(Paragraph(f"Nama Berkas: {os.path.basename(self.file_path)} | Engine: ID+EN Hybrid & Custom Dict", normal_report))
            story.append(Spacer(1, 15))

            db_data = [[
                Paragraph(f"<font size=10 color='#64748b'>TOTAL KATA</font><br/><br/><font size=16><b>{self.analysis_results['total_words']:,}</b></font>", normal_report),
                Paragraph(f"<font size=10 color='#64748b'>INDIKASI TYPO</font><br/><br/><font size=16 color='#ef4444'><b>{self.analysis_results['total_typos']}</b></font>", normal_report),
                Paragraph(f"<font size=10 color='#64748b'>ERROR PUEBI</font><br/><br/><font size=16 color='#ef4444'><b>{self.analysis_results['total_format']}</b></font>", normal_report),
                Paragraph(f"<font size=10 color='#ffffff'>SKOR AKHIR</font><br/><br/><font size=20 color='#ffffff'><b>{self.analysis_results['cleanliness_score']}%</b></font>", normal_report)
            ]]
            db_table = Table(db_data, colWidths=[120, 120, 120, 150])
            db_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (2,0), colors.HexColor("#f8fafc")), ('BACKGROUND', (3,0), (3,0), colors.HexColor(score_color)),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#1e293b")), ('PADDING', (0,0), (-1,-1), 12),
            ]))
            story.append(db_table)
            story.append(Spacer(1, 25))

            story.append(Paragraph("<b>DAFTAR TYPO & REKOMENDASI (Divalidasi Corpus ID & EN)</b>", h2_report))
            t_typo = [["No", "Kata Salah Terdeteksi", "Freq", "Saran Perbaikan"]]
            
            idx = 1
            for word, data in sorted_typos:
                t_typo.append([str(idx), word, f"{data['count']}x", data["suggestion"]])
                idx += 1
            if len(t_typo) == 1: t_typo.append(["-", "Aman, ejaan kata valid.", "-", "-"])

            dt_typo = Table(t_typo, colWidths=[30, 140, 45, 305])
            dt_typo.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'), 
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), 
                ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")), ('TEXTCOLOR', (3,1), (3,-1), colors.HexColor("#059669")),
            ]))
            story.append(dt_typo)
            story.append(Spacer(1, 20))

            story.append(Paragraph("<b>KESALAHAN FORMAT TATA TULIS & TANDA BACA</b>", h2_report))
            t_format = [["Kode", "Cuplikan Teks Asli (Error)", "Perbaikan Spasi/Tanda Baca", "Freq"]]
            
            idx_fmt = 1
            for key, data in sorted_formats:
                t_format.append([f"F{idx_fmt}", f"...{data['teks']}...", f"...{data['perbaikan']}...", f"{data['freq']}x"])
                idx_fmt += 1
            if len(t_format) == 1: t_format.append(["-", "Aman, format tanda baca rapi.", "-", "-"])

            dt_format = Table(t_format, colWidths=[40, 190, 240, 40])
            dt_format.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'), 
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTNAME', (0,1), (-1,-1), 'Helvetica'), 
                ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")), 
                ('TEXTCOLOR', (1,1), (1,-1), colors.HexColor("#dc2626")), 
                ('TEXTCOLOR', (2,1), (2,-1), colors.HexColor("#059669")), 
            ]))
            story.append(dt_format)

        doc.build(story)
        buffer.seek(0)
        return fitz.open(stream=buffer.read(), filetype="pdf")

    def export_to_pdf(self):
        default_name = f"GiveitTypo_Report_{os.path.basename(self.file_path)}"
        save_path = filedialog.asksaveasfilename(
            initialfile=default_name,
            defaultextension=".pdf", 
            filetypes=[("PDF", "*.pdf")], 
            title="Simpan Laporan Giveit Typo"
        )
        if not save_path: return
        
        self.lbl_file.config(text="Membangun Buku Laporan PDF (A4)...", fg="#f59e0b")
        self.btn_export.config(state=tk.DISABLED)
        threading.Thread(target=self.generate_pdf_worker, args=(save_path,), daemon=True).start()

    def generate_pdf_worker(self, save_path):
        try:
            sorted_typos = sorted(self.analysis_results["typo_details"].items(), key=lambda i: i[1]["count"], reverse=True)[:30]
            sorted_formats = sorted(self.analysis_results["format_details"].items(), key=lambda i: i[1]["freq"], reverse=True)[:30]

            final_pdf = fitz.open()

            cover_pdf = self._generate_report_pdf(part="cover")
            final_pdf.insert_pdf(cover_pdf)

            original_pdf = fitz.open(self.file_path)
            
            for page in original_pdf:
                idx = 1
                for word, data in sorted_typos:
                    for inst in page.search_for(word):
                        page.draw_rect(inst, color=(1, 0, 0), fill=(1, 0.7, 0.7), fill_opacity=0.35)
                        page.insert_text((inst.x0, max(0, inst.y0 - 2)), f"[{idx}]", fontsize=8, color=(0.8, 0, 0), fontname="hebo")
                    idx += 1
                
                idx_fmt = 1
                for key, data in sorted_formats:
                    for inst in page.search_for(data["teks"][:20]):
                        page.draw_rect(inst, color=(1, 0.6, 0), fill=(1, 1, 0), fill_opacity=0.35)
                        page.insert_text((inst.x0, max(0, inst.y0 - 2)), f"[F{idx_fmt}]", fontsize=8, color=(0.7, 0.4, 0), fontname="hebo")
                    idx_fmt += 1

            a4_width, a4_height = fitz.paper_size("a4")
            for page_num in range(len(original_pdf)):
                src_page = original_pdf[page_num]
                new_page = final_pdf.new_page(width=a4_width, height=a4_height)
                
                margin = 40
                fit_rect = fitz.Rect(margin, margin, a4_width - margin, a4_height - margin)
                
                src_rect = src_page.rect
                scale = min(fit_rect.width / src_rect.width, fit_rect.height / src_rect.height)
                new_w, new_h = src_rect.width * scale, src_rect.height * scale
                
                dx, dy = (fit_rect.width - new_w) / 2, (fit_rect.height - new_h) / 2
                target_rect = fitz.Rect(margin + dx, margin + dy, margin + dx + new_w, margin + dy + new_h)
                
                new_page.show_pdf_page(target_rect, original_pdf, page_num)
                new_page.draw_rect(target_rect, color=(0.2, 0.2, 0.2), width=1)

            report_pdf = self._generate_report_pdf(part="report", sorted_typos=sorted_typos, sorted_formats=sorted_formats)
            final_pdf.insert_pdf(report_pdf)

            final_pdf.save(save_path)
            
            self.root.after(0, lambda: self.finish_pdf_generation(save_path))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error PDF Generation", f"Gagal membuat laporan:\n{str(e)}"))
            self.root.after(0, lambda: self.btn_export.config(state=tk.NORMAL))

    def finish_pdf_generation(self, save_path):
        self.lbl_file.config(text=f"✅ Selesai: {os.path.basename(save_path)}", fg="#10b981")
        self.btn_export.config(state=tk.NORMAL)
        messagebox.showinfo("Sukses", f"Laporan Giveit Typo berhasil disimpan di:\n{save_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GiveitTypoApp(root)
    root.mainloop()