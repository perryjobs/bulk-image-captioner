import io, os, glob, zipfile
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageColor
import streamlit as st

# ── CONSTANTS ───────────────────────────────────────────────
MAX_FONT_SIZE = 120
MIN_FONT_SIZE = 10
LINE_SPACING = 10

# ── PAGE SETUP ──────────────────────────────────────────────
st.set_page_config(page_title="Bulk Captioner", layout="wide")
st.title("🖼️ Bulk Image Captioner")
st.write(
    "Upload a CSV/Excel file and matching images. Overlay up to **4 lines** of "
    "text on each image with custom fonts, colors, box position, and styling. "
    "Download all captioned images as a ZIP."
)

# ── FILE UPLOADS ─────────────────────────────────────────────
cap_file        = st.file_uploader("📄 Captions (CSV or Excel)", ["csv", "xlsx"])
uploaded_images = st.file_uploader(
    "🖼️ Upload Images (JPG/PNG)", type=["jpg", "jpeg", "png"], accept_multiple_files=True
)

# ── SIDEBAR : Font, Overlay, Global Box ─────────────────────
with st.sidebar:
    st.header("🖋 Font & Text")
    font_files = glob.glob("font/*.ttf") + glob.glob("font/*.otf")
    font_opts  = {os.path.basename(f): f for f in font_files}
    if not font_opts:
        st.error("Add .ttf/.otf files to /font folder.")
        st.stop()

    font_name   = st.selectbox("Font Family", list(font_opts.keys()))
    FONT_PATH   = font_opts[font_name]
    font_color  = st.color_picker("Font Color", "#FFFFFF")
    font_scale  = st.slider("Font Scale (%)", 80, 200, 100)

    st.header("🖌 Overlay Box")
    fill_color     = st.color_picker("Fill Color", "#000000")
    fill_alpha     = st.slider("Fill Transparency", 0, 255, 100)
    outline_color  = st.color_picker("Outline Color", "#FFFFFF")
    outline_width  = st.slider("Outline Width (px)", 0, 10, 2)

    st.header("📦 Global Box")
    use_global_box = st.checkbox("Use same box for all images", True)
    g_box_w  = st.number_input("Box Width (px)",  10, 2000, 400)
    g_box_h  = st.number_input("Box Height (px)", 10, 2000, 200)
    g_off_x  = st.number_input("X Offset (±px)", -2000, 2000, 0)
    g_off_y  = st.number_input("Y Offset (±px)", -2000, 2000, 0)

    st.header("⚙️ Other Settings")
    show_prev = st.checkbox("👁 Show Previews", True)
    zip_out   = st.checkbox("💾 Enable ZIP Download", True)
    max_previews = st.number_input("Max Image Previews (0=all)", 0, 100, 20)

# ── TEXT WRAP ────────────────────────────────────────────────
def wrap_and_fit(draw, font_path, box_w, box_h, lines,
                 max_sz=MAX_FONT_SIZE, min_sz=MIN_FONT_SIZE):
    for sz in range(max_sz, min_sz - 1, -2):
        try:
            fnt = ImageFont.truetype(font_path, sz)
        except:
            fnt = ImageFont.load_default()

        wrapped, tot_h, max_w = [], 0, 0
        for raw in lines:
            if not raw.strip(): continue
            words, cur = raw.split(), ""
            for w in words:
                test = f"{cur} {w}".strip()
                if fnt.getlength(test) <= box_w:
                    cur = test
                else:
                    wrapped.append(cur)
                    tot_h += fnt.getbbox(cur)[3]-fnt.getbbox(cur)[1] + LINE_SPACING
                    max_w = max(max_w, fnt.getlength(cur))
                    cur = w
            if cur:
                wrapped.append(cur)
                tot_h += fnt.getbbox(cur)[3]-fnt.getbbox(cur)[1] + LINE_SPACING
                max_w = max(max_w, fnt.getlength(cur))

        if wrapped and tot_h-LINE_SPACING <= box_h and max_w <= box_w:
            return fnt, wrapped
    return fnt, wrapped  # fallback

# ── MAIN ─────────────────────────────────────────────────────
if cap_file and uploaded_images:
    try:
        df = (pd.read_csv(cap_file) if cap_file.name.endswith(".csv")
              else pd.read_excel(cap_file)).fillna("")

        if "Image Filename" not in df.columns:
            st.error("Column **Image Filename** missing.")
            st.stop()

        img_dict   = {img.name: img for img in uploaded_images}
        zip_buffer = io.BytesIO()
        reuse_cnt  = {}
        shown      = 0

        for idx, row in df.iterrows():
            img_name = row["Image Filename"]
            if img_name not in img_dict:
                st.warning(f"⚠ Image not uploaded: {img_name}")
                continue

            # Caption lines
            txt_lines = [str(row.get(f"Text Line {n}", "")) for n in range(1, 5)]
            txt_lines = [t for t in txt_lines if t.strip()]

            # Open image
            im  = Image.open(img_dict[img_name]).convert("RGBA")
            W, H = im.size
            key  = f"{img_name}_{idx}"  # unique per row

            # Box size / offset
            if use_global_box:
                box_w, box_h = g_box_w, g_box_h
                off_x, off_y = g_off_x, g_off_y
            else:
                st.markdown(f"#### Box for **{img_name}** (row {idx})")
                col1, col2 = st.columns(2)
                box_w = col1.number_input("Width", 10, W, 400, key=f"bw_{key}")
                box_h = col2.number_input("Height", 10, H, 200, key=f"bh_{key}")
                col3, col4 = st.columns(2)
                off_x = col3.number_input("Offset X", -W, W, 0, key=f"ox_{key}")
                off_y = col4.number_input("Offset Y", -H, H, 0, key=f"oy_{key}")

            box_x = (W - box_w) // 2 + off_x
            box_y = (H - box_h) // 2 + off_y

            # Overlay box
            overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
            odraw   = ImageDraw.Draw(overlay)
            odraw.rectangle(
                [(box_x, box_y), (box_x+box_w, box_y+box_h)],
                fill=(*ImageColor.getrgb(fill_color), fill_alpha),
                outline=(*ImageColor.getrgb(outline_color), 255),
                width=outline_width,
            )
            im = Image.alpha_composite(im, overlay)
            draw = ImageDraw.Draw(im)

            # Fit text
            base_font, wrapped = wrap_and_fit(
                draw, FONT_PATH, box_w, box_h, txt_lines, MAX_FONT_SIZE
            )
            scaled_sz = max(MIN_FONT_SIZE, int(base_font.size * font_scale / 100))
            font, wrapped = wrap_and_fit(
                draw, FONT_PATH, box_w, box_h, txt_lines, scaled_sz
            )

            # Draw text centered
            heights = [font.getbbox(t)[3]-font.getbbox(t)[1] for t in wrapped]
            tot_h   = sum(heights) + LINE_SPACING*(len(heights)-1)
            y_cur   = box_y + (box_h - tot_h)//2
            for h, line in zip(heights, wrapped):
                x = box_x + (box_w - font.getlength(line))//2
                draw.text((x, y_cur), line, fill=font_color, font=font)
                y_cur += h + LINE_SPACING

            if show_prev and (max_previews == 0 or shown < max_previews):
                st.image(im.convert("RGB"), caption=f"{img_name} (row {idx})", use_column_width=True)
                shown += 1

            if zip_out:
                reuse_cnt[img_name] = reuse_cnt.get(img_name, 0) + 1
                suf = f"_{reuse_cnt[img_name]}" if reuse_cnt[img_name] > 1 else ""
                buf = io.BytesIO()
                im.save(buf, format="PNG")
                with zipfile.ZipFile(zip_buffer, "a") as zf:
                    zf.writestr(os.path.splitext(img_name)[0] + suf + ".png", buf.getvalue())

        if zip_out and zip_buffer.getvalue():
            st.download_button("📦 Download ZIP", zip_buffer.getvalue(), "captioned_images.zip")

    except Exception as e:
        st.error(f"❌ Error: {e}")
