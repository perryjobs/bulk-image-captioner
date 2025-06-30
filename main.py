import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import filedialog, messagebox

# Configuration
FONT_PATH = "arial.ttf"  # Make sure this font file is available
FONT_SIZE = 40

class BulkImageCaptionApp:
    def __init__(self, master):
        self.master = master
        master.title("Bulk Image Captioner")

        # Input Excel file
        tk.Label(master, text="Select Excel/CSV File:").grid(row=0, column=0, sticky="e")
        self.excel_path = tk.Entry(master, width=40)
        self.excel_path.grid(row=0, column=1)
        tk.Button(master, text="Browse", command=self.browse_excel).grid(row=0, column=2)

        # Image folder
        tk.Label(master, text="Select Image Folder:").grid(row=1, column=0, sticky="e")
        self.image_folder = tk.Entry(master, width=40)
        self.image_folder.grid(row=1, column=1)
        tk.Button(master, text="Browse", command=self.browse_image_folder).grid(row=1, column=2)

        # Output folder
        tk.Label(master, text="Select Output Folder:").grid(row=2, column=0, sticky="e")
        self.output_folder = tk.Entry(master, width=40)
        self.output_folder.grid(row=2, column=1)
        tk.Button(master, text="Browse", command=self.browse_output_folder).grid(row=2, column=2)

        # Generate button
        tk.Button(master, text="Generate Images", command=self.generate_images, bg="green", fg="white").grid(row=3, column=1, pady=10)

    def browse_excel(self):
        file = filedialog.askopenfilename(filetypes=[("Excel or CSV files", "*.xlsx *.csv")])
        if file:
            self.excel_path.delete(0, tk.END)
            self.excel_path.insert(0, file)

    def browse_image_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.image_folder.delete(0, tk.END)
            self.image_folder.insert(0, folder)

    def browse_output_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.delete(0, tk.END)
            self.output_folder.insert(0, folder)

    def generate_images(self):
        excel_file = self.excel_path.get()
        image_dir = self.image_folder.get()
        output_dir = self.output_folder.get()

        if not os.path.exists(excel_file) or not os.path.exists(image_dir) or not os.path.exists(output_dir):
            messagebox.showerror("Error", "Please select all valid paths.")
            return

        try:
            if excel_file.endswith('.csv'):
                df = pd.read_csv(excel_file)
            else:
                df = pd.read_excel(excel_file)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file:\n{e}")
            return

        try:
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
except Exception as e:
    messagebox.showerror("Error", f"Font not found: {FONT_PATH}\n{e}")
    return


        for _, row in df.iterrows():
            try:
                img_path = os.path.join(image_dir, row['Image Filename'])
                img

