import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import tkinter as tk
from tkinter import filedialog, messagebox

FONT_PATH = "arial.ttf"
FONT_SIZE = 40

class BulkImageCaptionApp:
    def __init__(self, master):
        self.master = master
        master.title("Bulk Image Captioner")

        tk.Label(master, text="Select Excel/CSV File:").grid(row=0, column=0, sticky="e")
        self.excel_path = tk.Entry(master, width=40)
        self.excel_path.grid(row=0, column=1)
        tk.Button(master, text="Browse", command=self.browse_excel).grid(row=0, column=2)

        tk.Label(master, text="Select Image Folder:").grid(row=1, column=0, sticky="e")
        self.image_folder = tk.Entry(master, width=40)
        self.image_folder.grid(row=1, column=1)
        tk.Button(master, text="Browse", command=self.browse_image_folder).grid(row=1, column=2)

        tk.Label(master, text="Select Output Folder:").grid(row=2, column=0, sticky="e")
        self.output_folder = tk.Entry(master, width=40)
        self.output_folder.grid(row=2, column=1)
        tk.Button(master, text="Browse", command=self.browse_output_folder).grid(row=2, column=2)

        tk.Button(master, text="Generate Images", command=self.generate_images, bg="green", fg="white").grid(row=3, column=1, pady=10)

    def browse_excel(self):
        file = filedialog.askopenfilename(filetypes=[("Excel/CSV files", "*.xlsx *.csv")])
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
            messagebox.showerror("Error", f"Font not found or invalid:\n{e}")
            return

        for _, row in df.iterrows():
            try:
                img_path = os.path.join(image_dir, row['Image Filename'])
                img = Image.open(img_path).convert('RGBA')
                draw = ImageDraw.Draw(img)

                W, H = img.size
                text1 = str(row.get('Text Line 1', ''))
                text2 = str(row.get('Text Line 2', ''))

                w1, h1 = draw.textsize(text1, font=font)
                w2, h2 = draw.textsize(text2, font=font)

                draw.text(((W - w1) / 2, H * 0.7), text1, fill='white', font=font)
                draw.text(((W - w2) / 2, H * 0.8), text2, fill='white', font=font)

                output_path = os.path.join(output_dir, row['Image Filename'])
                img.save(output_path)

            except Exception as e:
                print(f"Error processing {row['Image Filename']}: {e}")

        messagebox.showinfo("Done", "✅ Images generated and saved!")

if __name__ == "__main__":
    root = tk.Tk()
    app = BulkImageCaptionApp(root)
    root.mainloop()
