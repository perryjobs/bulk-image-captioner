# 🖼️ Bulk Image Captioner (Streamlit App)

This is a web-based image captioning tool built with **Streamlit**. It lets you overlay multiple lines of text from a CSV/Excel file onto images — with custom fonts, box positions, styling, and a downloadable ZIP of results.

---

## 🚀 Features

✅ Upload JPEG/PNG images  
✅ Upload a CSV or Excel file with captions  
✅ Support for **Text Line 1–4**  
✅ Auto-center text box  
✅ Global or per-image box dimensions and offsets  
✅ Custom font picker from `/font` folder  
✅ Font color and scale  
✅ Box background color, border color, and transparency  
✅ Preview images inline  
✅ Export all images as ZIP (PNG format)  

---

## 📂 Folder Structure

bulk-image-captioner/
├── streamlit_app.py ← Main app file
├── font/ ← Place your .ttf/.otf font files here
│ ├── arial.ttf
│ └── roboto.ttf
├── requirements.txt
├── README.md
└── output_images/ captions.xlsx

---

## 📥 CSV/Excel Format

Required column:
- `Image Filename` — must match one of your uploaded image filenames

Optional caption lines:
- `Text Line 1`
- `Text Line 2`
- `Text Line 3`
- `Text Line 4`

Example:

```csv
Image Filename,Text Line 1,Text Line 2
image1.jpg,Welcome to the Event,Enjoy your stay
image2.jpg,Celebrating Success,With You Always


## How to Use

1. Clone this repo or download ZIP
2. Install dependencies:
   ```bash
   pip install -r requirements.txt

Start the app

streamlit run streamlit_app.py

## License

This project is licensed under the [MIT License](LICENSE).

