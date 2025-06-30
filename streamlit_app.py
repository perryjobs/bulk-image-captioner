import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import zipfile
import io
import streamlit as st

# Defaults
FONT_PATH = "font/arial.ttf"
DEFAULT_FONT_RATIO = 0.05  # 5% of image height

st.set_page_config(page_title="Bulk Image Captioner", layout="centered")
st.title("🖼️ Bulk Image Captioner")
st.write("Upload your caption file and images. We'll overlay the text and let you download the results.")

file = st.file_uploader("📄 Upload Excel or CSV", type=["csv", "xlsx"])
uploaded_images = st.file_uploader("🖼️ Upload Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

show_previews = st.checkbox("📌 Show image dimensions & recommended font sizes", value=True)

if file and uploaded_images:
    try:
        # Load caption file
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        if 'Image Filename' not in df.columns:
            st.error("Your file must contain a column named 'Image Filename'")
            st.stop()

        output_zip = io.BytesIO()

        with zipfile.ZipFile(output_zip, 'w') as zipf:
            for img_file in uploaded_images:
                matching_row = df[df['Image Filename'] == img_file.name]
                if matching_row.empty:
                    continue

                text1 = str(matching_row.iloc[0].get('Text Line 1', ''))
                text2 = str(matching_row.iloc[0].get('Text Line 2', ''))

                img = Image.open(img_file).convert("RGBA")
                draw = ImageDraw.Draw(img)
                W, H = img.size

                # Calculate recommended font size
                recommended_font_size = int(H * DEFAULT_FONT_RATIO)
                user_font_size = st.slider(
                    f"Font size for {img_file.name} (Image: {W}x{H})",
                    min_value=10,
                    max_value=int(H * 0.2),
                    value=recommended_font_size,
                    key=img_file.name
                )

                # Load font
                try:
                    font = ImageFont.truetype(FONT_PATH, user_font_size)
                except:
                    font = ImageFont.load_default()

                # Get text sizes
                bbox1 = font.getbbox(text1)
                w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]

                bbox2 = font.getbbox(text2)
                w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]

                # Draw text
                draw.text(((W - w1) / 2, H * 0.7), text1, fill="white", font=font)
                draw.text(((W - w2) / 2, H * 0.8), text2, fill="white", font=font)

                # Preview image (optional)
                if show_previews:
                    st.image(img, caption=f"{img_file.name} ({W}×{H}) | Font size: {user_font_size}", use_column_width=True)

                # Save to memory
                img_bytes = io.BytesIO()
                img.save(img_bytes, format="PNG")
                zipf.writestr(img_file.name, img_bytes.getvalue())

        st.success("✅ All images processed!")
        st.download_button("📥 Download All Captioned Images (.zip)", output_zip.getvalue(), file_name="captioned_images.zip")

    except Exception as e:
        st.error(f"Something went wrong:\n\n{e}")
