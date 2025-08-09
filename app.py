import customtkinter as ctk
from tkinter import filedialog
import threading
import time
import pytesseract
from pdf2image import convert_from_path
import os
import pikepdf
import itertools
import string

import sys

class PDFProcessor:
    def __init__(self):
        # Set appearance and theme
        ctk.set_appearance_mode("System")  # Modes: "System", "Dark", "Light"

        # Conditional theme path for PyInstaller
        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
        else:
            bundle_dir = os.path.dirname(os.path.abspath(__file__))

        theme_path = os.path.join(bundle_dir, "themes", "website_theme.json")
        ctk.set_default_color_theme(theme_path)

        self.root = ctk.CTk()
        self.root.title("PDF Processing Application")
        self.root.geometry("600x500")

        # Notebook (TabView)
        self.notebook = ctk.CTkTabview(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Tabs
        self.notebook.add("OCR")
        self.notebook.add("Unlock PDF")

        self.ocr_tab = self.notebook.tab("OCR")
        self.unlock_tab = self.notebook.tab("Unlock PDF")

        # UI elements
        self.setup_ocr_tab()
        self.setup_unlock_tab()

        # Status and progress
        self.progress_bar = ctk.CTkProgressBar(self.root, mode="indeterminate")
        self.progress_bar.pack(pady=10, fill="x")
        self.status_label = ctk.CTkLabel(self.root, text="")
        self.status_label.pack()

    def setup_ocr_tab(self):
        frame = ctk.CTkFrame(self.ocr_tab)
        frame.pack(pady=20)

        # File selection
        ctk.CTkLabel(frame, text="Select PDF File:").grid(row=0, column=0, padx=5, pady=5)
        self.ocr_file_path = ctk.CTkEntry(frame, width=300)
        self.ocr_file_path.grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(frame, text="Browse", command=lambda: self.select_file(self.ocr_file_path)).grid(row=0, column=2, padx=5, pady=5)

        # Export path
        ctk.CTkLabel(frame, text="Export Path:").grid(row=1, column=0, padx=5, pady=5)
        self.ocr_export_path = ctk.CTkEntry(frame, width=300)
        self.ocr_export_path.grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(frame, text="Browse", command=lambda: self.select_export_path(self.ocr_export_path)).grid(row=1, column=2, padx=5, pady=5)

        # Process button
        ctk.CTkButton(self.ocr_tab, text="Start OCR", command=self.process_pdf).pack(pady=10)

    def setup_unlock_tab(self):
        frame = ctk.CTkFrame(self.unlock_tab)
        frame.pack(pady=20)

        # File selection
        ctk.CTkLabel(frame, text="Select PDF File:").grid(row=0, column=0, padx=5, pady=5)
        self.unlock_file_path = ctk.CTkEntry(frame, width=300)
        self.unlock_file_path.grid(row=0, column=1, padx=5, pady=5)
        ctk.CTkButton(frame, text="Browse", command=lambda: self.select_file(self.unlock_file_path)).grid(row=0, column=2, padx=5, pady=5)

        # Export path
        ctk.CTkLabel(frame, text="Export Path:").grid(row=1, column=0, padx=5, pady=5)
        self.unlock_export_path = ctk.CTkEntry(frame, width=300)
        self.unlock_export_path.grid(row=1, column=1, padx=5, pady=5)
        ctk.CTkButton(frame, text="Browse", command=lambda: self.select_export_path(self.unlock_export_path)).grid(row=1, column=2, padx=5, pady=5)

        # Password entry
        ctk.CTkLabel(frame, text="Password:").grid(row=2, column=0, padx=5, pady=5)
        self.password_entry = ctk.CTkEntry(frame, width=300, show="*")
        self.password_entry.grid(row=2, column=1, padx=5, pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(self.unlock_tab)
        button_frame.pack(pady=10)
        ctk.CTkButton(button_frame, text="Unlock with Password", command=self.unlock_pdf_with_password).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Brute Force Unlock", command=self.brute_force_pdf).pack(side="left", padx=5)

    def select_file(self, entry_widget):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        entry_widget.delete(0, "end")
        entry_widget.insert(0, file_path)

    def select_export_path(self, entry_widget):
        export_path = filedialog.askdirectory()
        entry_widget.delete(0, "end")
        entry_widget.insert(0, export_path)

    def process_pdf(self):
        def run_task():
            self.progress_bar.start()
            pdf_path = self.ocr_file_path.get()
            export_path = self.ocr_export_path.get()

            if not pdf_path or not export_path:
                self.status_label.configure(text="Please select a file and export path!")
                self.progress_bar.stop()
                return

            try:
                images = convert_from_path(pdf_path)
                extracted_text = ""
                for i, img in enumerate(images):
                    extracted_text += f"Page {i+1}:\n{pytesseract.image_to_string(img)}\n"
                    extracted_text += "=" * 50 + "\n"

                output_file = os.path.join(export_path, "extracted_text.txt")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(extracted_text)

                self.status_label.configure(text=f"Process completed! Saved to {output_file}")
            except Exception as e:
                self.status_label.configure(text=f"Error: {str(e)}")
            finally:
                self.progress_bar.stop()

        self.status_label.configure(text="Processing...")
        threading.Thread(target=run_task).start()

    def unlock_pdf_with_password(self):
        def run_task():
            self.progress_bar.start()
            pdf_path = self.unlock_file_path.get()
            password = self.password_entry.get()
            export_path = self.unlock_export_path.get()

            if not pdf_path or not export_path or not password:
                self.status_label.configure(text="Please select a file, export path, and provide a password!")
                self.progress_bar.stop()
                return

            try:
                pdf = pikepdf.open(pdf_path, password=password)
                unlocked_pdf_path = os.path.join(export_path, "unlocked.pdf")
                pdf.save(unlocked_pdf_path)
                self.status_label.configure(text=f"PDF unlocked and saved to {unlocked_pdf_path}")
            except pikepdf.PasswordError:
                self.status_label.configure(text="Incorrect password!")
            except Exception as e:
                self.status_label.configure(text=f"An error occurred: {str(e)}")
            finally:
                self.progress_bar.stop()

        self.status_label.configure(text="Unlocking PDF...")
        threading.Thread(target=run_task).start()

    def brute_force_pdf(self):
        def run_task():
            self.progress_bar.start()
            pdf_path = self.unlock_file_path.get()
            export_path = self.unlock_export_path.get()

            if not pdf_path or not export_path:
                self.status_label.configure(text="Please select a file and export path!")
                self.progress_bar.stop()
                return

            characters = string.ascii_letters + string.digits
            found = False

            try:
                for length in range(1, 5):
                    for password_tuple in itertools.product(characters, repeat=length):
                        password = ''.join(password_tuple)
                        try:
                            pdf = pikepdf.open(pdf_path, password=password)
                            unlocked_pdf_path = os.path.join(export_path, "unlocked.pdf")
                            pdf.save(unlocked_pdf_path)
                            self.status_label.configure(text=f"PDF unlocked with password '{password}' and saved to {unlocked_pdf_path}")
                            found = True
                            break
                        except pikepdf.PasswordError:
                            continue
                    if found:
                        break

                if not found:
                    self.status_label.configure(text="Failed to unlock PDF with brute force.")
            except Exception as e:
                self.status_label.configure(text=f"An error occurred: {str(e)}")
            finally:
                self.progress_bar.stop()

        self.status_label.configure(text="Starting brute force...")
        threading.Thread(target=run_task).start()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PDFProcessor()
    app.run()
