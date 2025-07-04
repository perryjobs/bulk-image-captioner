import io, os, zipfile
import pandas as pd
from PIL import Image, ImageDraw, ImageFont, ImageColor
import streamlit as st

# ── CONSTANTS ──────────────────────────────────────────────────────────────────
FONT_PATH        = "font/arial.ttf"       # put any .ttf you prefer in /font
MAX_FONT_SIZE    = 120
MIN_FONT_SIZE    = 10
LINE_SPACING_PX  = 10                     # gap between wrapped lines

# ── PAGE SET‑UP ────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Bulk Captioner (Pixels + Center + Offset)",
                   layout="centered")
st.title("🖼️ Bulk Image Captioner – Centred Box + Offset + Font Scale")
st.write(
    "Upload an Excel/CSV with **Image Filename** + up to **Text Line 1‑4**.  "
    "Choose box size, optional pixel offsets, overlay colours & font scale. "
    "Text auto‑wraps and fits the box."
)

# ── FILE UPLOADS ───────────────────────────────────────────────────────────────
cap_file        = st.file_uploader("📄  Captions (Excel or CSV)", ["csv", "xlsx"])
uploaded_images = st.file_uploader("🖼  Images (JPG/PNG)",  ["jpg", "jpeg", "png"],
                                   accept_multiple_files=True)

# ── GLOBAL VISUAL OPTIONS ──────────────────────────────────────────────────────
st.markdown("### 🎨 Overlay Box & Font")
overlay_fill_color  = st.color_picker("Fill Colour",    "#000000")
overlay_fill_alpha  = st.slider     ("Fill Transparency (0 = clear, 255 = solid)",
                                     0, 255, 100)
outline_color       = st.color_picker("Outline Colour", "#FFFFFF")
outline_width       = st.slider     ("Outline Width (px)", 0, 10, 2)
font_color          = st.color_picker("Font Colour",   "#FFFFFF")
font_scale_pct      = st.slider("🔠 Font Scale (%)", 80, 200, 100)

show_previews  = st.checkbox("👁 Show Previews", True)
enable_zip     = st.checkbox("💾 Enable ZIP Download", True)

# ── TEXT‑FIT FUNCTION ──────────────────────────────────────────────────────────
def wrap_and_fit(draw, font_path, box_w, box_h, raw_lines,
                 max_size, min_size=MIN_FONT_SIZE):
    """Return (font_object, wrapped_lines) that fit inside box (pixel)."""
    for size in range(max_size, min_size - 1, -2):
        try:  font = ImageFont.truetype(font_path, size)
        except: font = ImageFont.load_default()
        wrapped, tot_h, max_w = [], 0, 0
        for raw in raw_lines:
            if not raw.strip():  continue
            words, cur = raw.split(), ""
            for w in words:
                test = f"{cur} {w}".strip()
                if font.getlength(test) <= box_w:
                    cur = test
                else:
                    wrapped.append(cur)
                    tot_h += font.getbbox(cur)[3] - font.getbbox(cur)[1] + LINE_SPACING_PX
                    max_w = max(max_w, font.getlength(cur))
                    cur = w
            if cur:
                wrapped.append(cur)
                tot_h += font.getbbox(cur)[3] - font.getbbox(cur)[1] + LINE_SPACING_PX
                max_w = max(max_w, font.getlength(cur))
        if wrapped and tot_h - LINE_SPACING_PX <= box_h and max_w <= box_w:
            return font, wrapped
    return font, wrapped  # minimal size fallback

# ── MAIN PROCESSING ────────────────────────────────────────────────────────────
if cap_file and uploaded_images:
    try:
        df = (pd.read_csv(cap_file) if cap_file.name.endswith(".csv")
              else pd.read_excel(cap_file)).fillna("")

        assert "Image Filename" in df.columns, "Column 'Image Filename' missing."

        img_dict = {img.name: img for img in uploaded_images}
        zip_buffer = io.BytesIO()
        reuse_counter = {}

        for _, row in df.iterrows():
            img_name = row["Image Filename"]
            if img_name not in img_dict:
                st.warning(f"⚠ Image not uploaded: {img_name}")
                continue

            # ► Collect caption lines
            lines = [str(row.get(f"Text Line {n}", "")) for n in range(1, 5)]
            lines = [l for l in lines if l.strip()]

            # ► Open image & dimensions
            im  = Image.open(img_dict[img_name]).convert("RGBA")
            W, H = im.size

            # ► Box size controls (per‑image)
            st.markdown(f"### 📐 Box for **{img_name}** ({W}×{H}px)")
            box_w = st.number_input(f"Width (px) – {img_name}", 10, W, 400,
                                    key=f"bw_{img_name}")
            box_h = st.number_input(f"Height (px) – {img_name}", 10, H, 200,
                                    key=f"bh_{img_name}")
            x_offset = st.number_input(f"X Offset (px, +right / ‑left) – {img_name}",
                                       -W, W, 0, key=f"ox_{img_name}")
            y_offset = st.number_input(f"Y Offset (px, +down / ‑up) – {img_name}",
                                       -H, H, 0, key=f"oy_{img_name}")

            # ► Centre + offset
            box_x = (W - box_w)//2 + x_offset
            box_y = (H - box_h)//2 + y_offset

            # ► Draw overlay box
            fill_rgb, out_rgb = map(ImageColor.getrgb,
                                    [overlay_fill_color, outline_color])
            overlay = Image.new("RGBA", im.size, (0,0,0,0))
            odraw   = ImageDraw.Draw(overlay)
            odraw.rectangle(
                [(box_x, box_y), (box_x+box_w, box_y+box_h)],
                fill=(*fill_rgb, overlay_fill_alpha),
                outline=(*out_rgb, 255),
                width=outline_width
            )
            im = Image.alpha_composite(im, overlay)
            draw = ImageDraw.Draw(im)

            # ► Auto‑fit base size
            base_font, wrapped = wrap_and_fit(
                draw, FONT_PATH, box_w, box_h, lines, MAX_FONT_SIZE
            )

            # ► Apply user font‑scale (try bigger/smaller but keep fit)
            scaled_size = max(MIN_FONT_SIZE,
                              int(base_font.size * font_scale_pct/100))
            font, wrapped = wrap_and_fit(
                draw, FONT_PATH, box_w, box_h, lines,
                max_size=scaled_size, min_size=MIN_FONT_SIZE
            )

            # ► Vertical centring
            lh = [font.getbbox(t)[3]-font.getbbox(t)[1] for t in wrapped]
            total_h = sum(lh) + LINE_SPACING_PX*(len(lh)-1)
            y_cursor = box_y + (box_h - total_h)//2

            for idx, t in enumerate(wrapped):
                x = box_x + (box_w - font.getlength(t))//2
                draw.text((x, y_cursor), t, fill=font_color, font=font)
                y_cursor += lh[idx] + LINE_SPACING_PX

            # ► Preview
            if show_previews:
                st.image(im.convert("RGB"), caption=img_name, use_column_width=True)

            # ► ZIP save
            if enable_zip:
                reuse_counter[img_name] = reuse_counter.get(img_name, 0) + 1
                suffix = f"_{reuse_counter[img_name]}" if reuse_counter[img_name]>1 else ""
                with zipfile.ZipFile(zip_buffer, "a") as zf:
                    buf = io.BytesIO()
                    im.save(buf, format="PNG")
                    zf.writestr(os.path.splitext(img_name)[0]+suffix+".png",
                                buf.getvalue())

        if enable_zip and zip_buffer.getvalue():
            st.download_button("📥 Download ZIP", zip_buffer.getvalue(),
                               "captioned_images.zip")

    except Exception as e:
        st.error(f"❌ Error → {e}")
