import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import zipfile
import io
import streamlit as st

# === Setup ===
FONT_PATH = "font/arial.ttf"
st.set_page_config(page_title="Bulk Captioner Auto", layout="centered")
st.title("🖼️ Bulk Image Captioner (Auto Fit)")

st.write("This version automatically fits your caption inside a custom box you define, resizing text to fit each image.")

# === Uploads ===
file = st.file_uploader("📄 Upload Excel or CSV", type=["csv", "xlsx"])
uploaded_images = st.file_uploader("🖼️ Upload Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

# === Custom Box Settings ===
st.markdown("### ✏️ Text Box Dimensions (as % of image size)")
x_offset_pct = st.slider("🧭 Left offset (%)", 0, 100, 20)
y_offset_pct = st.slider("🧭 Top offset (%)", 0, 100, 30)
box_width_pct = st.slider("📏 Box width (%)", 10, 100, 60)
box_height_pct = st.slider("📏 Box height (%)", 10, 100, 40)

# === Options ===
font_color = st.color_picker("🎨 Font color", "#FFFFFF")
show_previews = st.checkbox("👁 Show image previews", value=True)
enable_download = st.checkbox("💾 Enable download (.zip)", value=True)

# === Smart Text Fitting ===
def auto_fit_text(draw, font_path, box_width, box_height, text_lines, max_font=120, min_font=10):
    for font_size in range(max_font, min_font - 1, -2):
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()

        line_heights = []
        line_widths = []
        for line in text_lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            line_widths.append(line_width)
            line_heights.append(line_height)

        total_height = sum(line_heights) + (len(text_lines) - 1) * 10
        max_width = max(line_widths)

        if total_height <= box_height and max_width <= box_width:
            return font, line_widths, line_heights
    return font, line_widths, line_heights  # fallback

# === Main Processing ===
if file and uploaded_images:
    try:
        # Read caption file
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        if 'Image Filename' not in df.columns:
            st.error("❌ Column 'Image Filename' is missing.")
            st.stop()

        uploaded_image_dict = {img.name: img for img in uploaded_images}
        output_zip = io.BytesIO()

        with zipfile.ZipFile(output_zip, 'w') as zipf:
            image_counts = {}

            for idx, row in df.iterrows():
                image_name = row['Image Filename']
                if image_name not in uploaded_image_dict:
                    st.warning(f"⚠️ Missing image: {image_name}")
                    continue

                image_counts[image_name] = image_counts.get(image_name, 0) + 1
                suffix = f"_{image_counts[image_name]}" if image_counts[image_name] > 1 else ""

                text_lines = [str(row.get('Text Line 1', '')), str(row.get('Text Line 2', ''))]
                img = Image.open(uploaded_image_dict[image_name]).convert("RGBA")
                W, H = img.size
                draw = ImageDraw.Draw(img)

                # Calculate box dimensions
                box_x = int(W * x_offset_pct / 100)
                box_y = int(H * y_offset_pct / 100)
                box_width = int(W * box_width_pct / 100)
                box_height = int(H * box_height_pct / 100)

                # Get best font that fits
                font, widths, heights = auto_fit_text(draw, FONT_PATH, box_width, box_height, text_lines)

                total_text_height = sum(heights) + (len(text_lines) - 1) * 10
                y_cursor = box_y + (box_height - total_text_height) / 2

                for i, line in enumerate(text_lines):
                    x = box_x + (box_width - widths[i]) / 2
                    draw.text((x, y_cursor), line, fill=font_color, font=font)
                    y_cursor += heights[i] + 10

                if show_previews:
                    st.image(img, caption=f"{image_name}{suffix}", use_column_width=True)

                if enable_download:
                    outname = os.path.splitext(image_name)[0] + f"{suffix}.png"
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    zipf.writestr(outname, buffer.getvalue())

        if enable_download:
            st.success("✅ All images processed.")
            st.download_button("📥 Download ZIP", output_zip.getvalue(), file_name="captioned_images.zip")

    except Exception as e:
        st.error(f"❌ Error: {e}")
