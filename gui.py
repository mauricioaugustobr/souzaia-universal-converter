#!/usr/bin/env python3
"""
SOUZAIA Universal Converter - Interface Nativa Desktop (GUI)
Aplicativo de conversão rápida e 100% autônoma para Windows sem necessidade de navegador.
"""

import os
import sys
import threading
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from core.universal_converter import UniversalConverter
from core.media_info import inspect_media, get_file_category

class SouzaiaConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SOUZAIA Universal Converter - Desktop")
        self.root.geometry("680x560")
        self.root.minsize(580, 480)

        # Apply dark theme styling
        self._configure_styles()

        self.current_file = None
        self.file_info = None
        self.is_converting = False

        self._build_ui()

    def _configure_styles(self):
        self.root.configure(bg="#0B0F19")
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure(".", background="#0B0F19", foreground="#F8FAFC", font=("Segoe UI", 10))
        self.style.configure("TLabel", background="#0B0F19", foreground="#F8FAFC")
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#818CF8")
        self.style.configure("Subheader.TLabel", font=("Segoe UI", 9), foreground="#94A3B8")
        self.style.configure("Card.TFrame", background="#131B2E", relief="flat")
        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), background="#4F46E5", foreground="#FFFFFF", borderwidth=0, padding=8)
        self.style.map("TButton", background=[("active", "#4338CA"), ("disabled", "#334155")])
        self.style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), background="#10B981", foreground="#FFFFFF", padding=10)
        self.style.map("Action.TButton", background=[("active", "#059669"), ("disabled", "#1E293B")])
        self.style.configure("TCombobox", fieldbackground="#1E293B", background="#1E293B", foreground="#F8FAFC")
        self.style.configure("Horizontal.TProgressbar", troughcolor="#1E293B", background="#6366F1", thickness=12)

    def _build_ui(self):
        # Header Frame
        header = ttk.Frame(self.root, padding=20)
        header.pack(fill="x")

        ttk.Label(header, text="SOUZAIA Universal Converter", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header, text="Alta Fidelidade • Documentos, Imagens, Áudios e Vídeos", style="Subheader.TLabel").pack(anchor="w")

        # Main Card Frame
        card = ttk.Frame(self.root, style="Card.TFrame", padding=20)
        card.pack(fill="both", expand=True, padx=20, pady=5)

        # File Selection Area
        btn_select = ttk.Button(card, text="📁 Selecionar Arquivo do Computador", command=self.select_file)
        btn_select.pack(fill="x", pady=(0, 10))

        # Selected File Info
        self.lbl_filename = ttk.Label(card, text="Nenhum arquivo selecionado", font=("Segoe UI", 11, "bold"))
        self.lbl_filename.pack(anchor="w", pady=2)

        self.lbl_filedetails = ttk.Label(card, text="Selecione um arquivo para ver as opções compatíveis", style="Subheader.TLabel")
        self.lbl_filedetails.pack(anchor="w", pady=(0, 15))

        # Target Format Selector
        fmt_frame = ttk.Frame(card, style="Card.TFrame")
        fmt_frame.pack(fill="x", pady=10)

        ttk.Label(fmt_frame, text="Converter para a extensão:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.combo_target = ttk.Combobox(fmt_frame, state="readonly", width=15)
        self.combo_target.pack(side="left", padx=10)

        # Quality Preset Selector
        qual_frame = ttk.Frame(card, style="Card.TFrame")
        qual_frame.pack(fill="x", pady=10)

        ttk.Label(qual_frame, text="Nível de Qualidade:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.combo_quality = ttk.Combobox(qual_frame, state="readonly", width=25, values=[
            "Alta Qualidade (Recomendado)",
            "Ultra / Sem Perdas (Máxima Fidelidade)",
            "Balanceado",
            "Otimizado para Web"
        ])
        self.combo_quality.current(0)
        self.combo_quality.pack(side="left", padx=10)

        # Progress Section
        self.progress_bar = ttk.Progressbar(card, style="Horizontal.TProgressbar", mode="determinate")
        self.progress_bar.pack(fill="x", pady=(20, 5))

        self.lbl_status = ttk.Label(card, text="Aguardando arquivo...", style="Subheader.TLabel")
        self.lbl_status.pack(anchor="w")

        # Action Buttons Area
        bottom_frame = ttk.Frame(self.root, padding=20)
        bottom_frame.pack(fill="x")

        self.btn_convert = ttk.Button(bottom_frame, text="⚡ CONVERTER ARQUIVO AGORA", style="Action.TButton", command=self.start_conversion)
        self.btn_convert.pack(fill="x")

        self.btn_open_folder = ttk.Button(bottom_frame, text="📂 Abrir Pasta dos Arquivos Convertidos", command=self.open_output_folder)
        self.btn_open_folder.pack(fill="x", pady=(8, 0))

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Selecione o arquivo para converter")
        if not file_path:
            return

        self.current_file = file_path
        p = Path(file_path)
        self.lbl_filename.config(text=p.name)

        try:
            self.file_info = inspect_media(file_path)
            cat = self.file_info.get('category', 'desconhecido').upper()
            size = self.file_info.get('size_formatted', '')
            details = []
            d = self.file_info.get('details', {})
            if d.get('resolution'): details.append(d['resolution'])
            if d.get('duration_formatted'): details.append(d['duration_formatted'])
            if d.get('pages'): details.append(f"{d['pages']} páginas")

            det_str = f"Categoria: {cat} • Tamanho: {size}"
            if details:
                det_str += f" • {', '.join(details)}"

            self.lbl_filedetails.config(text=det_str)

            targets = self.file_info.get('target_formats', [])
            self.combo_target['values'] = [f".{t.upper()}" for t in targets]
            if targets:
                self.combo_target.current(0)

            self.lbl_status.config(text="Pronto para converter!")
            self.progress_bar['value'] = 0

        except Exception as e:
            self.lbl_filedetails.config(text=f"Erro ao inspecionar: {str(e)}")

    def start_conversion(self):
        if not self.current_file:
            messagebox.showwarning("Atenção", "Por favor, selecione um arquivo primeiro!")
            return

        if self.is_converting:
            return

        target_str = self.combo_target.get().lstrip('.').lower()
        if not target_str:
            messagebox.showwarning("Atenção", "Por favor, selecione a extensão de destino!")
            return

        qual_idx = self.combo_quality.current()
        qual_map = {0: 'high', 1: 'ultra', 2: 'balanced', 3: 'web'}
        selected_quality = qual_map.get(qual_idx, 'high')

        self.is_converting = True
        self.btn_convert.config(state="disabled")
        self.progress_bar['value'] = 5
        self.lbl_status.config(text="Iniciando conversão...")

        output_dir = str(BASE_DIR / "outputs")

        options = {
            'quality': selected_quality,
            'image_quality': 100 if selected_quality == 'ultra' else 98,
            'audio_bitrate': '320k',
            'dpi': 300,
            'normalize': True
        }

        def worker():
            def progress_callback(pct, msg):
                self.root.after(0, lambda: self._update_progress(pct, msg))

            try:
                result = UniversalConverter.convert(
                    input_path=self.current_file,
                    output_dir=output_dir,
                    target_format=target_str,
                    options=options,
                    progress_callback=progress_callback
                )
                self.root.after(0, lambda: self._on_success(result))
            except Exception as e:
                self.root.after(0, lambda: self._on_error(str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _update_progress(self, pct, msg):
        self.progress_bar['value'] = pct
        self.lbl_status.config(text=msg)

    def _on_success(self, result):
        self.is_converting = False
        self.btn_convert.config(state="normal")
        self.progress_bar['value'] = 100
        self.lbl_status.config(text=f"Concluído com sucesso! Salvo em: {result['filename']}")

        resp = messagebox.askyesno(
            "Conversão Concluída!",
            f"O arquivo foi convertido com sucesso!\n\nSalvo como: {result['filename']}\nTamanho: {result['size_formatted']}\n\nDeseja abrir a pasta onde o arquivo foi salvo?"
        )
        if resp:
            self.open_output_folder()

    def _on_error(self, err_msg):
        self.is_converting = False
        self.btn_convert.config(state="normal")
        self.lbl_status.config(text="Falha na conversão.")
        messagebox.showerror("Erro na Conversão", f"Ocorreu um erro durante a conversão:\n\n{err_msg}")

    def open_output_folder(self):
        output_dir = str(BASE_DIR / "outputs")
        os.makedirs(output_dir, exist_ok=True)
        os.startfile(output_dir)

def main():
    root = tk.Tk()
    app = SouzaiaConverterApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
