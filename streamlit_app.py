import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import zipfile
import io
import streamlit as st

# Constants
FONT_PATH = "font/arial.ttf"
MAX_FONT_SIZE = 100
MIN_FONT_SIZE = 10

st.set_page_config(page_title="Smart Image Captioner", layout="centered")
st.title("🤖 Auto-Fit Image Captioner")

st.write("Upload your caption file and images. The app will auto-fit captions into the image's center region.")

# Uploads
file = st.file_uploader("📄 Upload Excel or CSV", type=["csv", "xlsx"])
uploaded_images = st.file_uploader("🖼️ Upload Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

show_previews = st.checkbox("👁 Show image previews", value=True)
enable_download = st.checkbox("💾 Enable download", value=True)
font_color = st.color_picker("🎨 Font color", "#FFFFFF")  # white

# Helper: Auto-fit font inside a given box
def get_fitting_font(text_lines, draw, box_width, box_height):
    for font_size in range(MAX_FONT_SIZE, MIN_FONT_SIZE - 1, -1):
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except:
            font = ImageFont.load_default()

        total_height = 0
        max_width = 0
        for line in text_lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            total_height += line_height + 10
            max_width = max(max_width, line_width)

        if total_height <= box_height and max_width <= box_width:
            return font
    return ImageFont.load_default()

if file and uploaded_images:
    try:
        # Load caption file
        df = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)

        if 'Image Filename' not in df.columns:
            st.error("❌ 'Image Filename' column is missing")
            st.stop()

        # Load images to dict
        image_map = {img.name: img for img in uploaded_images}
        output_zip = io.BytesIO()
        image_counts = {}

        with zipfile.ZipFile(output_zip, 'w') as zipf:
            for idx, row in df.iterrows():
                img_name = row['Image Filename']
                if img_name not in image_map:
                    continue

                text1 = str(row.get('Text Line 1', ''))
                text2 = str(row.get('Text Line 2', ''))

                image_counts[img_name] = image_counts.get(img_name, 0) + 1
                suffix = f"_{image_counts[img_name]}" if image_counts[img_name] > 1 else ""

                img = Image.open(image_map[img_name]).convert("RGBA")
                draw = ImageDraw.Draw(img)
                W, H = img.size

                # Default centered box (60% width/height)
                box_x0 = int(W * 0.2)
                box_y0 = int(H * 0.35)
                box_x1 = int(W * 0.8)
                box_y1 = int(H * 0.65)
                box_width = box_x1 - box_x0
                box_height = box_y1 - box_y0

                # Auto-fit font
                font = get_fitting_font([text1, text2], draw, box_width, box_height)

                # Measure again to center inside box
                bbox1 = font.getbbox(text1)
                w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]

                bbox2 = font.getbbox(text2)
                w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]

                total_height = h1 + h2 + 10
                y_start = box_y0 + (box_height - total_height) / 2

                draw.text((box_x0 + (box_width - w1) / 2, y_start), text1, fill=font_color, font=font)
                draw.text((box_x0 + (box_width - w2) / 2, y_start + h1 + 10), text2, fill=font_color, font=font)

                # Preview
                if show_previews:
                    st.image(img, caption=f"{img_name}{suffix}", use_column_width=True)

                # Save if enabled
                if enable_download:
                    output_name = os.path.splitext(img_name)[0] + f"{suffix}.png"
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    zipf.writestr(output_name, img_bytes.getvalue())

        if enable_download:
            st.success("✅ Done!")
            st.download_button("📥 Download ZIP", data=output_zip.getvalue(), file_name="captioned_images.zip")

    except Exception as e:
        st.error(f"Something went wrong:\n\n{e}")
