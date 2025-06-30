import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import zipfile
import io
import streamlit as st

# Constants
FONT_PATH = "font/arial.ttf"
DEFAULT_FONT_RATIO = 0.05  # 5% of image height

st.set_page_config(page_title="Bulk Image Captioner", layout="centered")
st.title("🖼️ Bulk Image Captioner")

st.write("Upload your caption file and images. We'll overlay the text and let you preview and/or download the results.")

# === Uploads ===
file = st.file_uploader("📄 Upload Excel or CSV", type=["csv", "xlsx"])
uploaded_images = st.file_uploader("🖼️ Upload Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

# === Global Options ===
show_previews = st.checkbox("👁 Show image previews", value=True)
enable_download = st.checkbox("💾 Enable download of captioned images", value=True)
text_alignment = st.selectbox("📍 Text vertical position", ["Top", "Middle", "Bottom"])
font_color = st.color_picker("🎨 Pick font color", "#FFFFFF")  # Default: white

if file and uploaded_images:
    try:
        # Load caption file
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        if 'Image Filename' not in df.columns:
            st.error("❌ Your file must contain a column named 'Image Filename'")
            st.stop()

        # Preload uploaded images into dict
        uploaded_image_dict = {img.name: img for img in uploaded_images}
        output_zip = io.BytesIO()

        with zipfile.ZipFile(output_zip, 'w') as zipf:
            image_counts = {}  # Track versioned outputs

            for idx, row in df.iterrows():
                image_name = row['Image Filename']
                if image_name not in uploaded_image_dict:
                    st.warning(f"⚠️ Image not found: {image_name}")
                    continue

                # Track usage count for renaming
                image_counts[image_name] = image_counts.get(image_name, 0) + 1
                version_suffix = f"_{image_counts[image_name]}" if image_counts[image_name] > 1 else ""

                # Get text
                text1 = str(row.get('Text Line 1', ''))
                text2 = str(row.get('Text Line 2', ''))

                # Load image
                img = Image.open(uploaded_image_dict[image_name]).convert("RGBA")
                draw = ImageDraw.Draw(img)
                W, H = img.size

                # Font size recommendation
                recommended_font_size = int(H * DEFAULT_FONT_RATIO)
                user_font_size = st.slider(
                    f"🔤 Font size for {image_name} ({W}x{H}) use #{image_counts[image_name]}",
                    10, int(H * 0.2), recommended_font_size, key=f"{image_name}_{idx}"
                )

                # Load font
                try:
                    font = ImageFont.truetype(FONT_PATH, user_font_size)
                except:
                    font = ImageFont.load_default()

                # Measure text
                bbox1 = font.getbbox(text1)
                w1, h1 = bbox1[2] - bbox1[0], bbox1[3] - bbox1[1]

                bbox2 = font.getbbox(text2)
                w2, h2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]

                # Vertical alignment
                if text_alignment == "Top":
                    y1 = H * 0.05
                    y2 = y1 + h1 + 10
                elif text_alignment == "Bottom":
                    y2 = H * 0.95 - h2
                    y1 = y2 - h1 - 10
                else:  # Middle
                    total_height = h1 + h2 + 10
                    y1 = (H - total_height) / 2
                    y2 = y1 + h1 + 10

                # Draw text centered horizontally
                draw.text(((W - w1) / 2, y1), text1, fill=font_color, font=font)
                draw.text(((W - w2) / 2, y2), text2, fill=font_color, font=font)

                # === Show Preview ===
                if show_previews:
                    st.image(img, caption=f"{image_name}{version_suffix}", use_column_width=True)

                # === Save Image ===
                if enable_download:
                    output_name = os.path.splitext(image_name)[0] + f"{version_suffix}.png"
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format="PNG")
                    zipf.writestr(output_name, img_bytes.getvalue())

        # === Download ZIP ===
        if enable_download:
            st.success("✅ All images processed!")
            st.download_button("📥 Download All Images (.zip)", output_zip.getvalue(), file_name="captioned_images.zip")

    except Exception as e:
        st.error(f"❌ Something went wrong:\n\n{e}")
