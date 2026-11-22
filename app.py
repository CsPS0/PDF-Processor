import os
import sys
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import pikepdf

from pdf_service import (
    process_ocr,
    unlock_pdf,
    brute_force_pdf,
    get_pdf_info,
    check_dependencies,
    CHARSETS,
)
from config import load_config, save_config, AppConfig
from exceptions import OperationCancelledError

VERSION = "2.0.0"

if getattr(sys, "_MEIPASS", None):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

THEME_PATH = os.path.join(BASE_DIR, "themes", "website_theme.json")

SIDEBAR_BG = ("#14213d", "#0d1729")
SIDEBAR_ACTIVE_BG = "#1c2e50"
SIDEBAR_TEXT = "#8a9aaa"
SIDEBAR_ACTIVE_TEXT = "#fca311"
HEADER_BG = ("#14213d", "#0d1729")
CARD_BG = ("#eaeaea", "#1a2d4d")
STATUS_SUCCESS = "#2ecc71"
STATUS_ERROR = "#e74c3c"
STATUS_WARNING = "#e67e22"

LANGUAGES = {
    "English": "eng",
    "Hungarian": "hun",
    "German": "deu",
    "French": "fra",
    "Spanish": "spa",
}


class PDFProcessorApp:

    def __init__(self):
        self.config = load_config()

        ctk.set_default_color_theme(THEME_PATH)
        ctk.set_appearance_mode(self.config.theme_mode)

        self.root = ctk.CTk()
        self.root.title("PDF Processor")
        self.root.geometry("960x640")
        self.root.minsize(800, 500)

        self.cancel_event = threading.Event()
        self.is_processing = False
        self.sections = {}
        self.nav_buttons = {}
        self.current_section = None
        self.pdf_info_labels = {}

        self._build_ui()
        self._select_section("OCR")
        self.root.after(500, self._check_dependencies)

    def _build_ui(self):
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self._create_header()
        self._create_sidebar()
        self._create_content_area()
        self._create_status_bar()

        self.sections["OCR"] = self._build_ocr_section()
        self.sections["Unlock PDF"] = self._build_unlock_section()
        self.sections["Brute Force"] = self._build_bruteforce_section()
        self.sections["Settings"] = self._build_settings_section()

    def _create_header(self):
        self.header = ctk.CTkFrame(
            self.root, height=56, corner_radius=0, fg_color=HEADER_BG
        )
        self.header.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.header.grid_propagate(False)

        ctk.CTkLabel(
            self.header,
            text="  PDF Processor",
            font=("Roboto", 22, "bold"),
            text_color="#ffffff",
        ).pack(side="left", padx=(20, 0), pady=10)

        ctk.CTkLabel(
            self.header,
            text=f"v{VERSION}",
            font=("Roboto", 11),
            text_color="#5a6a7a",
        ).pack(side="left", padx=(8, 0), pady=(14, 10))

        self.theme_btn = ctk.CTkButton(
            self.header,
            text="\u25d0",
            width=40,
            height=40,
            font=("Roboto", 18),
            corner_radius=8,
            fg_color="transparent",
            hover_color="#1c2e50",
            text_color="#ffffff",
            command=self._toggle_theme,
        )
        self.theme_btn.pack(side="right", padx=16, pady=8)

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self.root, width=220, corner_radius=0, fg_color=SIDEBAR_BG
        )
        self.sidebar.grid(row=1, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        ctk.CTkLabel(
            self.sidebar,
            text="NAVIGATION",
            font=("Roboto", 10, "bold"),
            text_color="#5a6a7a",
            anchor="w",
        ).pack(fill="x", padx=20, pady=(24, 12))

        nav_items = [
            ("OCR", "Text Extraction"),
            ("Unlock PDF", "Password Unlock"),
            ("Brute Force", "Password Cracking"),
            ("Settings", "Preferences"),
        ]

        for name, subtitle in nav_items:
            container = ctk.CTkFrame(
                self.sidebar, fg_color="transparent", corner_radius=8
            )
            container.pack(fill="x", padx=10, pady=2)

            indicator = ctk.CTkFrame(
                container, width=3, corner_radius=2, fg_color="transparent"
            )
            indicator.pack(side="left", fill="y", padx=(4, 8), pady=8)

            text_frame = ctk.CTkFrame(container, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True, pady=8)

            name_lbl = ctk.CTkLabel(
                text_frame,
                text=name,
                font=("Roboto", 14, "bold"),
                text_color=SIDEBAR_TEXT,
                anchor="w",
            )
            name_lbl.pack(fill="x")

            sub_lbl = ctk.CTkLabel(
                text_frame,
                text=subtitle,
                font=("Roboto", 11),
                text_color="#5a6a7a",
                anchor="w",
            )
            sub_lbl.pack(fill="x")

            for widget in [container, text_frame, name_lbl, sub_lbl]:
                widget.bind(
                    "<Button-1>", lambda e, n=name: self._select_section(n)
                )
                widget.configure(cursor="hand2")

            self.nav_buttons[name] = {
                "container": container,
                "indicator": indicator,
                "name_label": name_lbl,
                "sub_label": sub_lbl,
            }

    def _create_content_area(self):
        self.content = ctk.CTkFrame(
            self.root, corner_radius=0, fg_color="transparent"
        )
        self.content.grid(row=1, column=1, sticky="nsew")

    def _create_status_bar(self):
        self.status_frame = ctk.CTkFrame(self.root, height=52, corner_radius=0)
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.status_frame.grid_propagate(False)

        self.progress_bar = ctk.CTkProgressBar(self.status_frame, height=4)
        self.progress_bar.pack(fill="x", padx=16, pady=(10, 0))
        self.progress_bar.set(0)

        status_row = ctk.CTkFrame(self.status_frame, fg_color="transparent")
        status_row.pack(fill="x", padx=16, pady=(6, 10))

        self.status_label = ctk.CTkLabel(
            status_row,
            text="Ready",
            font=("Roboto", 12),
            text_color=("gray50", "gray60"),
            anchor="w",
        )
        self.status_label.pack(side="left")

        self.cancel_btn = ctk.CTkButton(
            status_row,
            text="Cancel",
            width=80,
            height=28,
            font=("Roboto", 11),
            fg_color=STATUS_ERROR,
            hover_color="#c0392b",
            command=self._cancel_operation,
        )

        self.eta_label = ctk.CTkLabel(
            status_row,
            text="",
            font=("Roboto", 11),
            text_color=("gray50", "gray60"),
            anchor="e",
        )
        self.eta_label.pack(side="right")

    def _create_card(self, parent, title):
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=CARD_BG)
        card.pack(fill="x", padx=24, pady=(0, 12))

        if title:
            ctk.CTkLabel(
                card, text=title, font=("Roboto", 13, "bold"), anchor="w"
            ).pack(fill="x", padx=16, pady=(14, 4))

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=(0, 14))

        return card, content

    def _create_file_input(self, parent, label_text, string_var, browse_cmd):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=4)

        ctk.CTkLabel(
            row, text=label_text, font=("Roboto", 12), anchor="w", width=90
        ).pack(side="left")

        ctk.CTkEntry(row, textvariable=string_var, height=36).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )

        ctk.CTkButton(
            row, text="Browse", width=80, height=36, command=browse_cmd
        ).pack(side="right")

    def _build_info_row(self, parent, key):
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.pack(fill="x", padx=16, pady=(0, 14))
        content.grid_columnconfigure((0, 1, 2), weight=1)

        labels = {}

        labels["name"] = ctk.CTkLabel(
            content,
            text="No PDF selected",
            font=("Roboto", 13),
            text_color=("gray50", "gray60"),
            anchor="w",
        )
        labels["name"].grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 4))

        labels["pages"] = ctk.CTkLabel(
            content, text="", font=("Roboto", 12), anchor="w"
        )
        labels["pages"].grid(row=1, column=0, sticky="w")

        labels["size"] = ctk.CTkLabel(
            content, text="", font=("Roboto", 12), anchor="w"
        )
        labels["size"].grid(row=1, column=1, sticky="w")

        labels["encrypted"] = ctk.CTkLabel(
            content, text="", font=("Roboto", 12), anchor="w"
        )
        labels["encrypted"].grid(row=1, column=2, sticky="w")

        self.pdf_info_labels[key] = labels

    def _build_ocr_section(self):
        section = ctk.CTkScrollableFrame(
            self.content, fg_color="transparent", corner_radius=0
        )

        ctk.CTkLabel(
            section,
            text="OCR \u2014 Text Extraction",
            font=("Roboto", 20, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(24, 4))

        ctk.CTkLabel(
            section,
            text="Extract text from PDF documents using optical character recognition.",
            font=("Roboto", 13),
            text_color=("gray50", "gray60"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 20))

        _, file_content = self._create_card(section, "Select PDF")
        self.ocr_pdf_var = ctk.StringVar()
        self._create_file_input(
            file_content,
            "PDF File",
            self.ocr_pdf_var,
            lambda: self._browse_pdf(self.ocr_pdf_var, "ocr"),
        )

        info_card = ctk.CTkFrame(section, corner_radius=12, fg_color=CARD_BG)
        info_card.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(
            info_card,
            text="PDF Information",
            font=("Roboto", 13, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 4))
        self._build_info_row(info_card, "ocr")

        _, opts_content = self._create_card(section, "Options")
        opts_row = ctk.CTkFrame(opts_content, fg_color="transparent")
        opts_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            opts_row, text="Language", font=("Roboto", 12), anchor="w", width=90
        ).pack(side="left")
        self.ocr_lang_var = ctk.StringVar(
            value=self._lang_code_to_name(self.config.ocr_language)
        )
        ctk.CTkComboBox(
            opts_row,
            values=list(LANGUAGES.keys()),
            variable=self.ocr_lang_var,
            height=36,
            state="readonly",
        ).pack(side="left", fill="x", expand=True)

        _, export_content = self._create_card(section, "Export")
        self.ocr_export_var = ctk.StringVar(value=self.config.default_export_dir)
        self._create_file_input(
            export_content,
            "Export Dir",
            self.ocr_export_var,
            lambda: self._browse_dir(self.ocr_export_var),
        )

        self.ocr_btn = ctk.CTkButton(
            section,
            text="Start OCR",
            height=44,
            font=("Roboto", 15, "bold"),
            command=self._start_ocr,
        )
        self.ocr_btn.pack(fill="x", padx=24, pady=(8, 24))

        return section

    def _build_unlock_section(self):
        section = ctk.CTkScrollableFrame(
            self.content, fg_color="transparent", corner_radius=0
        )

        ctk.CTkLabel(
            section,
            text="Unlock PDF",
            font=("Roboto", 20, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(24, 4))

        ctk.CTkLabel(
            section,
            text="Unlock a password-protected PDF with a known password.",
            font=("Roboto", 13),
            text_color=("gray50", "gray60"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 20))

        _, file_content = self._create_card(section, "Select PDF")
        self.unlock_pdf_var = ctk.StringVar()
        self._create_file_input(
            file_content,
            "PDF File",
            self.unlock_pdf_var,
            lambda: self._browse_pdf(self.unlock_pdf_var, "unlock"),
        )

        info_card = ctk.CTkFrame(section, corner_radius=12, fg_color=CARD_BG)
        info_card.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(
            info_card,
            text="PDF Information",
            font=("Roboto", 13, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 4))
        self._build_info_row(info_card, "unlock")

        _, pwd_content = self._create_card(section, "Password")
        pwd_row = ctk.CTkFrame(pwd_content, fg_color="transparent")
        pwd_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            pwd_row, text="Password", font=("Roboto", 12), anchor="w", width=90
        ).pack(side="left")
        self.unlock_pwd_var = ctk.StringVar()
        ctk.CTkEntry(
            pwd_row, textvariable=self.unlock_pwd_var, show="\u2022", height=36
        ).pack(side="left", fill="x", expand=True)

        _, export_content = self._create_card(section, "Export")
        self.unlock_export_var = ctk.StringVar(value=self.config.default_export_dir)
        self._create_file_input(
            export_content,
            "Export Dir",
            self.unlock_export_var,
            lambda: self._browse_dir(self.unlock_export_var),
        )

        self.unlock_btn = ctk.CTkButton(
            section,
            text="Unlock PDF",
            height=44,
            font=("Roboto", 15, "bold"),
            command=self._start_unlock,
        )
        self.unlock_btn.pack(fill="x", padx=24, pady=(8, 24))

        return section

    def _build_bruteforce_section(self):
        section = ctk.CTkScrollableFrame(
            self.content, fg_color="transparent", corner_radius=0
        )

        ctk.CTkLabel(
            section,
            text="Brute Force",
            font=("Roboto", 20, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(24, 4))

        ctk.CTkLabel(
            section,
            text="Crack a PDF password by trying all possible combinations.",
            font=("Roboto", 13),
            text_color=("gray50", "gray60"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 20))

        _, file_content = self._create_card(section, "Select PDF")
        self.bf_pdf_var = ctk.StringVar()
        self._create_file_input(
            file_content,
            "PDF File",
            self.bf_pdf_var,
            lambda: self._browse_pdf(self.bf_pdf_var, "bruteforce"),
        )

        info_card = ctk.CTkFrame(section, corner_radius=12, fg_color=CARD_BG)
        info_card.pack(fill="x", padx=24, pady=(0, 12))
        ctk.CTkLabel(
            info_card,
            text="PDF Information",
            font=("Roboto", 13, "bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 4))
        self._build_info_row(info_card, "bruteforce")

        _, opts_content = self._create_card(section, "Cracking Options")

        charset_row = ctk.CTkFrame(opts_content, fg_color="transparent")
        charset_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            charset_row, text="Charset", font=("Roboto", 12), anchor="w", width=90
        ).pack(side="left")
        self.bf_charset_var = ctk.StringVar(value="Alphanumeric")
        ctk.CTkComboBox(
            charset_row,
            values=list(CHARSETS.keys()),
            variable=self.bf_charset_var,
            height=36,
            state="readonly",
        ).pack(side="left", fill="x", expand=True)

        length_row = ctk.CTkFrame(opts_content, fg_color="transparent")
        length_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            length_row, text="Max Length", font=("Roboto", 12), anchor="w", width=90
        ).pack(side="left")
        self.bf_length_var = ctk.StringVar(
            value=str(self.config.brute_force_max_length)
        )
        ctk.CTkEntry(
            length_row, textvariable=self.bf_length_var, height=36, width=80
        ).pack(side="left")
        ctk.CTkLabel(
            length_row,
            text="characters (1\u20138)",
            font=("Roboto", 11),
            text_color=("gray50", "gray60"),
        ).pack(side="left", padx=(8, 0))

        _, export_content = self._create_card(section, "Export")
        self.bf_export_var = ctk.StringVar(value=self.config.default_export_dir)
        self._create_file_input(
            export_content,
            "Export Dir",
            self.bf_export_var,
            lambda: self._browse_dir(self.bf_export_var),
        )

        self.bf_btn = ctk.CTkButton(
            section,
            text="Start Brute Force",
            height=44,
            font=("Roboto", 15, "bold"),
            command=self._start_bruteforce,
        )
        self.bf_btn.pack(fill="x", padx=24, pady=(8, 24))

        return section

    def _build_settings_section(self):
        section = ctk.CTkScrollableFrame(
            self.content, fg_color="transparent", corner_radius=0
        )

        ctk.CTkLabel(
            section,
            text="Settings",
            font=("Roboto", 20, "bold"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(24, 4))

        ctk.CTkLabel(
            section,
            text="Configure application preferences.",
            font=("Roboto", 13),
            text_color=("gray50", "gray60"),
            anchor="w",
        ).pack(fill="x", padx=24, pady=(0, 20))

        _, appearance_content = self._create_card(section, "Appearance")
        theme_row = ctk.CTkFrame(appearance_content, fg_color="transparent")
        theme_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            theme_row, text="Theme", font=("Roboto", 12), anchor="w", width=120
        ).pack(side="left")
        self.settings_theme_var = ctk.StringVar(value=self.config.theme_mode)
        ctk.CTkComboBox(
            theme_row,
            values=["System", "Light", "Dark"],
            variable=self.settings_theme_var,
            height=36,
            state="readonly",
            command=self._on_theme_setting_changed,
        ).pack(side="left", fill="x", expand=True)

        _, defaults_content = self._create_card(section, "Defaults")

        export_row = ctk.CTkFrame(defaults_content, fg_color="transparent")
        export_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            export_row,
            text="Export Directory",
            font=("Roboto", 12),
            anchor="w",
            width=120,
        ).pack(side="left")
        self.settings_export_var = ctk.StringVar(value=self.config.default_export_dir)
        ctk.CTkEntry(
            export_row, textvariable=self.settings_export_var, height=36
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            export_row,
            text="Browse",
            width=80,
            height=36,
            command=lambda: self._browse_dir(self.settings_export_var),
        ).pack(side="right")

        lang_row = ctk.CTkFrame(defaults_content, fg_color="transparent")
        lang_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            lang_row, text="OCR Language", font=("Roboto", 12), anchor="w", width=120
        ).pack(side="left")
        self.settings_lang_var = ctk.StringVar(
            value=self._lang_code_to_name(self.config.ocr_language)
        )
        ctk.CTkComboBox(
            lang_row,
            values=list(LANGUAGES.keys()),
            variable=self.settings_lang_var,
            height=36,
            state="readonly",
        ).pack(side="left", fill="x", expand=True)

        length_row = ctk.CTkFrame(defaults_content, fg_color="transparent")
        length_row.pack(fill="x", pady=4)
        ctk.CTkLabel(
            length_row,
            text="BF Max Length",
            font=("Roboto", 12),
            anchor="w",
            width=120,
        ).pack(side="left")
        self.settings_length_var = ctk.StringVar(
            value=str(self.config.brute_force_max_length)
        )
        ctk.CTkEntry(
            length_row, textvariable=self.settings_length_var, height=36, width=80
        ).pack(side="left")

        btn_frame = ctk.CTkFrame(section, fg_color="transparent")
        btn_frame.pack(fill="x", padx=24, pady=(8, 24))

        ctk.CTkButton(
            btn_frame,
            text="Save Settings",
            height=44,
            font=("Roboto", 15, "bold"),
            command=self._save_settings,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            btn_frame,
            text="Reset Defaults",
            height=44,
            font=("Roboto", 15, "bold"),
            fg_color="transparent",
            border_width=2,
            border_color="#fca311",
            text_color=("#fca311", "#fca311"),
            hover_color=CARD_BG,
            command=self._reset_settings,
        ).pack(side="right", fill="x", expand=True, padx=(6, 0))

        return section

    def _select_section(self, name):
        if self.is_processing:
            return

        for frame in self.sections.values():
            frame.pack_forget()
        self.sections[name].pack(fill="both", expand=True, in_=self.content)

        for nav_name, widgets in self.nav_buttons.items():
            if nav_name == name:
                widgets["container"].configure(fg_color=SIDEBAR_ACTIVE_BG)
                widgets["indicator"].configure(fg_color=SIDEBAR_ACTIVE_TEXT)
                widgets["name_label"].configure(text_color=SIDEBAR_ACTIVE_TEXT)
                widgets["sub_label"].configure(text_color=SIDEBAR_ACTIVE_TEXT)
            else:
                widgets["container"].configure(fg_color="transparent")
                widgets["indicator"].configure(fg_color="transparent")
                widgets["name_label"].configure(text_color=SIDEBAR_TEXT)
                widgets["sub_label"].configure(text_color="#5a6a7a")

        self.current_section = name

    def _browse_pdf(self, string_var, info_key):
        path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if path:
            string_var.set(path)
            self.config.add_recent_file(path)
            self._update_pdf_info(info_key, path)

    def _browse_dir(self, string_var):
        path = filedialog.askdirectory()
        if path:
            string_var.set(path)

    def _update_pdf_info(self, key, pdf_path):
        labels = self.pdf_info_labels.get(key)
        if not labels:
            return

        if not pdf_path or not os.path.isfile(pdf_path):
            labels["name"].configure(
                text="No PDF selected",
                font=("Roboto", 13),
                text_color=("gray50", "gray60"),
            )
            for k in ["pages", "size", "encrypted"]:
                labels[k].configure(text="")
            return

        try:
            info = get_pdf_info(pdf_path)
            labels["name"].configure(
                text=info["filename"],
                font=("Roboto", 13, "bold"),
                text_color=("gray10", "gray90"),
            )
            labels["pages"].configure(text=f"Pages: {info['pages']}")
            labels["size"].configure(text=f"Size: {info['size_mb']:.1f} MB")
            enc = info["encrypted"]
            labels["encrypted"].configure(
                text="Encrypted: Yes" if enc else "Encrypted: No",
                text_color=STATUS_ERROR if enc else STATUS_SUCCESS,
            )
        except Exception:
            labels["name"].configure(
                text="Error reading PDF",
                font=("Roboto", 13),
                text_color=STATUS_ERROR,
            )
            for k in ["pages", "size", "encrypted"]:
                labels[k].configure(text="")

    def _lang_code_to_name(self, code):
        for name, c in LANGUAGES.items():
            if c == code:
                return name
        return "English"

    def _set_status(self, text, color=None):
        def update():
            self.status_label.configure(text=text)
            if color:
                self.status_label.configure(text_color=color)
            else:
                self.status_label.configure(text_color=("gray50", "gray60"))

        self.root.after(0, update)

    def _set_progress(self, value):
        self.root.after(0, lambda: self.progress_bar.set(min(max(value, 0), 1)))

    def _set_eta(self, text):
        self.root.after(0, lambda: self.eta_label.configure(text=text))

    def _set_processing(self, processing):
        self.is_processing = processing

        def update():
            state = "disabled" if processing else "normal"
            for attr in ["ocr_btn", "unlock_btn", "bf_btn"]:
                btn = getattr(self, attr, None)
                if btn:
                    btn.configure(state=state)
            if processing:
                self.cancel_btn.pack(side="right", padx=(8, 0))
                self.cancel_event.clear()
            else:
                self.cancel_btn.pack_forget()
                self.eta_label.configure(text="")

        self.root.after(0, update)

    def _cancel_operation(self):
        self.cancel_event.set()
        self._set_status("Cancelling...", STATUS_WARNING)

    def _start_ocr(self):
        pdf_path = self.ocr_pdf_var.get().strip()
        export_dir = self.ocr_export_var.get().strip()

        if not pdf_path or not export_dir:
            messagebox.showwarning(
                "Missing Input", "Select a PDF file and export directory."
            )
            return

        lang_code = LANGUAGES.get(self.ocr_lang_var.get(), "eng")
        self._set_processing(True)
        self._set_status("Starting OCR...")
        self._set_progress(0)

        def run():
            try:

                def progress(current, total):
                    self._set_progress(current / total)
                    self._set_status(f"Processing page {current}/{total}...")

                output = process_ocr(
                    pdf_path,
                    export_dir,
                    lang=lang_code,
                    progress_callback=progress,
                    cancel_event=self.cancel_event,
                )
                self._set_progress(1)
                self._set_status(
                    f"OCR complete \u2192 {os.path.basename(output)}", STATUS_SUCCESS
                )
            except OperationCancelledError:
                self._set_status("OCR cancelled.", STATUS_WARNING)
                self._set_progress(0)
            except Exception as e:
                self._set_status(f"Error: {e}", STATUS_ERROR)
                self._set_progress(0)
            finally:
                self._set_processing(False)

        threading.Thread(target=run, daemon=True).start()

    def _start_unlock(self):
        pdf_path = self.unlock_pdf_var.get().strip()
        export_dir = self.unlock_export_var.get().strip()
        password = self.unlock_pwd_var.get()

        if not pdf_path or not export_dir or not password:
            messagebox.showwarning("Missing Input", "Fill in all fields.")
            return

        self._set_processing(True)
        self._set_status("Unlocking PDF...")
        self.root.after(0, lambda: self.progress_bar.configure(mode="indeterminate"))
        self.root.after(0, lambda: self.progress_bar.start())

        def run():
            try:
                output = unlock_pdf(pdf_path, password, export_dir)

                def on_success():
                    self.progress_bar.stop()
                    self.progress_bar.configure(mode="determinate")

                self.root.after(0, on_success)
                self._set_progress(1)
                self._set_status(
                    f"Unlocked \u2192 {os.path.basename(output)}", STATUS_SUCCESS
                )
            except pikepdf.PasswordError:

                def on_fail():
                    self.progress_bar.stop()
                    self.progress_bar.configure(mode="determinate")

                self.root.after(0, on_fail)
                self._set_progress(0)
                self._set_status("Incorrect password.", STATUS_ERROR)
            except Exception as e:

                def on_error():
                    self.progress_bar.stop()
                    self.progress_bar.configure(mode="determinate")

                self.root.after(0, on_error)
                self._set_progress(0)
                self._set_status(f"Error: {e}", STATUS_ERROR)
            finally:
                self._set_processing(False)

        threading.Thread(target=run, daemon=True).start()

    def _start_bruteforce(self):
        pdf_path = self.bf_pdf_var.get().strip()
        export_dir = self.bf_export_var.get().strip()

        if not pdf_path or not export_dir:
            messagebox.showwarning(
                "Missing Input", "Select a PDF file and export directory."
            )
            return

        try:
            max_length = int(self.bf_length_var.get())
            if not 1 <= max_length <= 8:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Invalid Input", "Max length must be between 1 and 8."
            )
            return

        charset = CHARSETS.get(self.bf_charset_var.get())
        self._set_processing(True)
        self._set_status("Starting brute force...")
        self._set_progress(0)

        def run():
            try:

                def progress(current, total, speed, eta):
                    self._set_progress(current / total)
                    pct = (current / total) * 100
                    self._set_status(
                        f"Brute force: {pct:.1f}%  ({current:,} / {total:,})"
                    )
                    if eta > 3600:
                        eta_str = f"{eta / 3600:.1f}h"
                    elif eta > 60:
                        eta_str = f"{eta / 60:.1f}m"
                    else:
                        eta_str = f"{eta:.0f}s"
                    self._set_eta(f"{speed:,.0f} att/s  \u00b7  ETA {eta_str}")

                password, output = brute_force_pdf(
                    pdf_path,
                    export_dir,
                    max_length=max_length,
                    charset=charset,
                    progress_callback=progress,
                    cancel_event=self.cancel_event,
                )

                if password:
                    self._set_progress(1)
                    self._set_status(
                        f"Password found: {password}", STATUS_SUCCESS
                    )
                else:
                    self._set_progress(1)
                    self._set_status("Password not found.", STATUS_WARNING)
            except OperationCancelledError:
                self._set_status("Brute force cancelled.", STATUS_WARNING)
                self._set_progress(0)
            except Exception as e:
                self._set_status(f"Error: {e}", STATUS_ERROR)
                self._set_progress(0)
            finally:
                self._set_processing(False)

        threading.Thread(target=run, daemon=True).start()

    def _toggle_theme(self):
        current = ctk.get_appearance_mode()
        new_mode = "Light" if current == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

    def _on_theme_setting_changed(self, value):
        ctk.set_appearance_mode(value)

    def _save_settings(self):
        self.config.theme_mode = self.settings_theme_var.get()
        self.config.default_export_dir = self.settings_export_var.get()
        self.config.ocr_language = LANGUAGES.get(
            self.settings_lang_var.get(), "eng"
        )
        try:
            val = int(self.settings_length_var.get())
            if 1 <= val <= 8:
                self.config.brute_force_max_length = val
        except ValueError:
            pass
        save_config(self.config)
        self._set_status("Settings saved.", STATUS_SUCCESS)

    def _reset_settings(self):
        self.config = AppConfig()
        self.settings_theme_var.set(self.config.theme_mode)
        self.settings_export_var.set(self.config.default_export_dir)
        self.settings_lang_var.set("English")
        self.settings_length_var.set(str(self.config.brute_force_max_length))
        save_config(self.config)
        ctk.set_appearance_mode(self.config.theme_mode)
        self._set_status("Settings reset to defaults.", STATUS_SUCCESS)

    def _check_dependencies(self):
        issues = check_dependencies()
        if issues:
            msg = "Missing dependencies:\n\n"
            for name, url in issues:
                msg += f"\u2022 {name}\n  {url}\n\n"
            msg += "Some features may not work correctly."
            messagebox.showwarning("Missing Dependencies", msg)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = PDFProcessorApp()
    app.run()
