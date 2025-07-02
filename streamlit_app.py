import os
import io
import zipfile
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageColor
import streamlit as st

# === Constants ===
FONT_PATH = "font/arial.ttf"
MAX_FONT_SIZE = 120
MIN_FONT_SIZE = 10

# === Page Setup ===
st.set_page_config(page_title="Bulk Captioner Auto", layout="centered")
st.title("🖼️ Bulk Image Captioner (Smart Auto-Fit + Overlay Control)")

st.write("Upload your caption file and images. Automatically wraps and fits up to 4 lines inside a customizable overlay box.")

# === Upload Inputs ===
file = st.file_uploader("📄 Upload Excel or CSV", type=["csv", "xlsx"])
uploaded_images = st.file_uploader("🖼️ Upload Images", accept_multiple_files=True, type=["jpg", "jpeg", "png"])

# === Box Controls ===
st.markdown("### 📐 Text Box Position & Size (% of image)")
x_offset_pct = st.slider("↔ Left Offset", 0, 100, 20)
y_offset_pct = st.slider("↕ Top Offset", 0, 100, 30)
box_width_pct = st.slider("🔳 Width", 10, 100, 60)
box_height_pct = st.slider("🔳 Height", 10, 100, 40)

# === Overlay Box Styling ===
st.markdown("### 🎨 Overlay Box Styling")
overlay_fill_color = st.color_picker("🟦 Fill Color", "#000000")  # Default: black
overlay_fill_alpha = st.slider("📊 Fill Transparency (0=clear, 255=solid)", 0, 255, 100)
outline_color = st.color_picker("⬜ Outline Color", "#FFFFFF")  # Default: white
outline_width = st.slider("📏 Outline Width", 0, 10, 2)

# === UI Options ===
font_color = st.color_picker("🔤 Font Color", "#FFFFFF")
show_previews = st.checkbox("👁 Show Previews", True)
enable_download = st.checkbox("💾 Enable ZIP Download", True)

# === Auto-Fit Text ===
def wrap_text_to_box(draw, font_path, box_width, box_height, raw_lines, max_font=MAX_FONT_SIZE, min_font=MIN_FONT_SIZE):
    for font_size in range(max_font, min_font - 1, -2):
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()

        wrapped_lines = []
        total_height = 0
        max_line_width = 0
        line_spacing = 10

        for raw_line in raw_lines:
            if not raw_line.strip():
                continue
            words = raw_line.strip().split()
            current_line = ""
            for word in words:
                test_line = f"{current_line} {word}".strip()
                if font.getlength(test_line) <= box_width:
                    current_line = test_line
                else:
                    wrapped_lines.append(current_line)
                    total_height += font.getbbox(current_line)[3] - font.getbbox(current_line)[1] + line_spacing
                    max_line_width = max(max_line_width, font.getlength(current_line))
                    current_line = word
            if current_line:
                wrapped_lines.append(current_line)
                total_height += font.getbbox(current_line)[3] - font.getbbox(current_line)[1] + line_spacing
                max_line_width = max(max_line_width, font.getlength(current_line))

        if total_height <= box_height and max_line_width <= box_width:
            return font, wrapped_lines

    return font, wrapped_lines

# === Main Logic ===
if file and uploaded_images:
    try:
        # Load caption data
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        df = df.fillna("")  # Fix NaN issues

        if 'Image Filename' not in df.columns:
            st.error("❌ Missing column: 'Image Filename'")
            st.stop()

        image_dict = {img.name: img for img in uploaded_images}
        output_zip = io.BytesIO()
        image_counts = {}

        with zipfile.ZipFile(output_zip, 'w') as zipf:
            for idx, row in df.iterrows():
                img_name = row['Image Filename']
                if img_name not in image_dict:
                    st.warning(f"⚠️ Missing image: {img_name}")
                    continue

                image_counts[img_name] = image_counts.get(img_name, 0) + 1
                suffix = f"_{image_counts[img_name]}" if image_counts[img_name] > 1 else ""

                text_lines = [
                    str(row.get("Text Line 1", "")),
                    str(row.get("Text Line 2", "")),
                    str(row.get("Text Line 3", "")),
                    str(row.get("Text Line 4", "")),
                ]
                text_lines = [line for line in text_lines if line.strip()]

                img = Image.open(image_dict[img_name]).convert("RGBA")
                W, H = img.size
                draw = ImageDraw.Draw(img)

                box_x = int(W * x_offset_pct / 100)
                box_y = int(H * y_offset_pct / 100)
                box_w = int(W * box_width_pct / 100)
                box_h = int(H * box_height_pct / 100)

                # === Draw overlay box
                overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
                overlay_draw = ImageDraw.Draw(overlay)

                fill_rgb = ImageColor.getrgb(overlay_fill_color)
                outline_rgb = ImageColor.getrgb(outline_color)

                overlay_draw.rectangle(
                    [(box_x, box_y), (box_x + box_w, box_y + box_h)],
                    fill=(*fill_rgb, overlay_fill_alpha),
                    outline=(*outline_rgb, 255),
                    width=outline_width
                )

                img = Image.alpha_composite(img, overlay)
                draw = ImageDraw.Draw(img)

                # === Fit and draw text
                font, wrapped_lines = wrap_text_to_box(draw, FONT_PATH, box_w, box_h, text_lines)

                line_spacing = 10
                line_heights = [font.getbbox(line)[3] - font.getbbox(line)[1] for line in wrapped_lines]
                total_height = sum(line_heights) + line_spacing * (len(wrapped_lines) - 1)
                y_cursor = box_y + (box_h - total_height) / 2

                for i, line in enumerate(wrapped_lines):
                    line_width = font.getlength(line)
                    x = box_x + (box_w - line_width) / 2
                    draw.text((x, y_cursor), line, fill=font_color, font=font)
                    y_cursor += line_heights[i] + line_spacing

                if show_previews:
                    st.image(img, caption=f"{img_name}{suffix}", use_column_width=True)

                if enable_download:
                    outname = os.path.splitext(img_name)[0] + f"{suffix}.png"
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    zipf.writestr(outname, buf.getvalue())

        if enable_download:
            st.success("✅ All images processed.")
            st.download_button("📥 Download ZIP", output_zip.getvalue(), file_name="captioned_images.zip")

    except Exception as e:
        st.error(f"❌ Error: {e}")
