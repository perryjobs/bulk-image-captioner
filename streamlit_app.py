import io, os, glob, zipfile
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageColor
import streamlit as st

# ── CONSTANTS ───────────────────────────────────────────────
MAX_FONT_SIZE = 120
MIN_FONT_SIZE = 10
LINE_SPACING = 10

# ── PAGE SETUP ──────────────────────────────────────────────
st.set_page_config(page_title="Bulk Captioner", layout="centered")
st.title("🖼️ Bulk Image Captioner")
st.write("Upload captions + images. Auto-caption with 1–4 lines of text, custom fonts, box position, colors, ZIP download.")

# ── FILE UPLOADS ─────────────────────────────────────────────
cap_file = st.file_uploader("📄 Captions (CSV or Excel)", ["csv", "xlsx"])
uploaded_images = st.file_uploader("🖼️ Upload Images (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

# ── FONT PICKER ─────────────────────────────────────────────
st.markdown("### 🔠 Font and Styling")

# Detect font files in /font
font_files = glob.glob("font/*.ttf") + glob.glob("font/*.otf")
font_options = {os.path.basename(f): f for f in font_files}
if not font_options:
    st.error("❌ No fonts found in /font folder. Please add .ttf or .otf files.")
    st.stop()

selected_font_name = st.selectbox("🔤 Font Family", list(font_options.keys()))
selected_font_path = font_options[selected_font_name]

font_color = st.color_picker("🎨 Font Color", "#FFFFFF")
font_scale_pct = st.slider("🔡 Font Scale (%)", 80, 200, 100)

# ── OVERLAY BOX STYLING ─────────────────────────────────────
st.markdown("### 🖌️ Overlay Box Styling")

overlay_fill_color = st.color_picker("🟦 Box Fill Color", "#000000")
overlay_fill_alpha = st.slider("📊 Box Fill Transparency (0=clear, 255=solid)", 0, 255, 100)
outline_color = st.color_picker("⬜ Box Outline Color", "#FFFFFF")
outline_width = st.slider("📏 Outline Width (px)", 0, 10, 2)

# ── GLOBAL BOX SETTINGS ─────────────────────────────────────
st.markdown("### 📦 Global Box Settings")
use_global_box = st.checkbox("✅ Use same box size & offset for all images", value=True)

global_box_w = st.number_input("Global Box Width (px)", min_value=10, max_value=2000, value=400)
global_box_h = st.number_input("Global Box Height (px)", min_value=10, max_value=2000, value=200)
global_x_offset = st.number_input("Global X Offset (±px)", -2000, 2000, 0)
global_y_offset = st.number_input("Global Y Offset (±px)", -2000, 2000, 0)

show_previews = st.checkbox("👁 Show Previews", True)
enable_zip = st.checkbox("💾 Enable ZIP Download", True)

# ── TEXT WRAP + FIT ─────────────────────────────────────────
def wrap_and_fit(draw, font_path, box_w, box_h, raw_lines,
                 max_size, min_size=MIN_FONT_SIZE):
    for size in range(max_size, min_size - 1, -2):
        try:
            font = ImageFont.truetype(font_path, size)
        except:
            font = ImageFont.load_default()

        wrapped, total_height, max_line_width = [], 0, 0
        for raw in raw_lines:
            if not raw.strip(): continue
            words, current_line = raw.strip().split(), ""
            for word in words:
                test = f"{current_line} {word}".strip()
                if font.getlength(test) <= box_w:
                    current_line = test
                else:
                    wrapped.append(current_line)
                    total_height += font.getbbox(current_line)[3] - font.getbbox(current_line)[1] + LINE_SPACING
                    max_line_width = max(max_line_width, font.getlength(current_line))
                    current_line = word
            if current_line:
                wrapped.append(current_line)
                total_height += font.getbbox(current_line)[3] - font.getbbox(current_line)[1] + LINE_SPACING
                max_line_width = max(max_line_width, font.getlength(current_line))

        if wrapped and total_height - LINE_SPACING <= box_h and max_line_width <= box_w:
            return font, wrapped
    return font, wrapped

# ── MAIN PROCESSING ─────────────────────────────────────────
if cap_file and uploaded_images:
    try:
        df = pd.read_csv(cap_file) if cap_file.name.endswith(".csv") else pd.read_excel(cap_file)
        df = df.fillna("")

        if 'Image Filename' not in df.columns:
            st.error("❌ Missing column: 'Image Filename'")
            st.stop()

        image_dict = {img.name: img for img in uploaded_images}
        zip_buffer = io.BytesIO()
        reuse_counts = {}

        for idx, row in df.iterrows():
            img_name = row["Image Filename"]
            if img_name not in image_dict:
                st.warning(f"⚠️ Missing image: {img_name}")
                continue

            # Text lines
            lines = [str(row.get(f"Text Line {n}", "")) for n in range(1, 5)]
            lines = [line for line in lines if line.strip()]

            img = Image.open(image_dict[img_name]).convert("RGBA")
            W, H = img.size
            unique_key = f"{img_name}_{idx}"

            if use_global_box:
                box_w = global_box_w
                box_h = global_box_h
                x_offset = global_x_offset
                y_offset = global_y_offset
            else:
                st.markdown(f"### 🖼 Box Settings for: {img_name} (row {idx}, {W}×{H})")
                box_w = st.number_input("Box Width (px)", 10, W, 400, key=f"bw_{unique_key}")
                box_h = st.number_input("Box Height (px)", 10, H, 200, key=f"bh_{unique_key}")
                x_offset = st.number_input("X Offset (±px)", -W, W, 0, key=f"ox_{unique_key}")
                y_offset = st.number_input("Y Offset (±px)", -H, H, 0, key=f"oy_{unique_key}")

            box_x = (W - box_w) // 2 + x_offset
            box_y = (H - box_h) // 2 + y_offset

            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            odraw = ImageDraw.Draw(overlay)
            fill_rgb = ImageColor.getrgb(overlay_fill_color)
            outline_rgb = ImageColor.getrgb(outline_color)

            odraw.rectangle(
                [(box_x, box_y), (box_x + box_w, box_y + box_h)],
                fill=(*fill_rgb, overlay_fill_alpha),
                outline=(*outline_rgb, 255),
                width=outline_width
            )

            img = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)

            base_font, wrapped_lines = wrap_and_fit(draw, selected_font_path, box_w, box_h, lines, MAX_FONT_SIZE)
            scaled_size = max(MIN_FONT_SIZE, int(base_font.size * font_scale_pct / 100))
            font, wrapped_lines = wrap_and_fit(draw, selected_font_path, box_w, box_h, lines, scaled_size)

            line_heights = [font.getbbox(line)[3] - font.getbbox(line)[1] for line in wrapped_lines]
            total_text_height = sum(line_heights) + LINE_SPACING * (len(line_heights) - 1)
            y_cursor = box_y + (box_h - total_text_height) // 2

            for i, line in enumerate(wrapped_lines):
                x = box_x + (box_w - font.getlength(line)) // 2
                draw.text((x, y_cursor), line, fill=font_color, font=font)
                y_cursor += line_heights[i] + LINE_SPACING

            if show_previews:
                st.image(img.convert("RGB"), caption=f"{img_name} (Row {idx})", use_column_width=True)

            if enable_zip:
                reuse_counts[img_name] = reuse_counts.get(img_name, 0) + 1
                suffix = f"_{reuse_counts[img_name]}" if reuse_counts[img_name] > 1 else ""
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                with zipfile.ZipFile(zip_buffer, "a") as zipf:
                    zipf.writestr(os.path.splitext(img_name)[0] + suffix + ".png", buf.getvalue())

        if enable_zip and zip_buffer.getvalue():
            st.download_button("📦 Download ZIP", zip_buffer.getvalue(), file_name="captioned_images.zip")

    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")
