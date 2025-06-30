import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import zipfile
import io
import streamlit as st

# Font settings
FONT_PATH = "font/arial.ttf"
FONT_SIZE = 40

st.set_page_config(page_title="Bulk Image Captioner", layout="centered")
st.title("🖼️ Bulk Image Captioner")
st.write("Upload an Excel or CSV file with captions and a set of images. This tool will overlay the text and let you download the modified images.")

# Upload Excel or CSV
file = st.file_uploader("📄 Upload Excel or CSV file", type=["csv", "xlsx"])
uploaded_images = st.file_uploader("🖼️ Upload images", accept_multiple_files=True, type=["jpg", "png", "jpeg"])

if file and uploaded_images:
    try:
        # Read Excel or CSV
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        if 'Image Filename' not in df.columns:
            st.error("Your file must contain a column named 'Image Filename'")
            st.stop()

        # Load font
        try:
            font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        except:
            font = ImageFont.load_default()

        output_zip = io.BytesIO()
        with zipfile.ZipFile(output_zip, 'w') as zipf:
            for img_file in uploaded_images:
                matching_row = df[df['Image Filename'] == img_file.name]
                if matching_row.empty:
                    continue

                text1 = str(matching_row.iloc[0].get('Text Line 1', ''))
                text2 = str(matching_row.iloc[0].get('Text Line 2', ''))

                img = Image.open(img_file).convert('RGBA')
                draw = ImageDraw.Draw(img)
                W, H = img.size

                w1, h1 = draw.textsize(text1, font=font)
                w2, h2 = draw.textsize(text2, font=font)

                draw.text(((W - w1) / 2, H * 0.7), text1, fill='white', font=font)
                draw.text(((W - w2) / 2, H * 0.8), text2, fill='white', font=font)

                # Save to memory
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                zipf.writestr(img_file.name, img_bytes.getvalue())

        st.success("✅ Done! Download your processed images below.")
        st.download_button("📥 Download ZIP", data=output_zip.getvalue(), file_name="captioned_images.zip")

    except Exception as e:
        st.error(f"Something went wrong: {e}")
