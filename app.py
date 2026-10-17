import json
import streamlit as st
from pipeline import read_nameplate, normalize, find_by_specs

st.set_page_config(page_title="Reparo", page_icon="🔧", layout="centered")

st.title("🔧 Reparo")
st.caption("Snap a motor nameplate → get a compatible replacement in seconds. AI vision running on AMD.")

uploaded = st.file_uploader("Upload a nameplate photo", type=["png", "jpg", "jpeg"])

if uploaded:
    # сохраняем загруженное фото во временный файл
    tmp_path = "uploaded_tmp." + uploaded.name.split(".")[-1]
    with open(tmp_path, "wb") as f:
        f.write(uploaded.getbuffer())

    st.image(uploaded, caption="Uploaded nameplate", use_container_width=True)

    with st.spinner("Reading nameplate on AMD GPU..."):
        raw = read_nameplate(tmp_path)
        part = normalize(raw)

    st.subheader("📋 Extracted specifications")
    cols = st.columns(2)
    labels = [
        ("Manufacturer", part["manufacturer"]),
        ("Model", part["model"]),
        ("Power", f"{part['power_kw']} kW" if part["power_kw"] else "—"),
        ("Speed", f"{int(part['rpm'])} rpm" if part["rpm"] else "—"),
        ("Frame size", part["frame_size"] or "—"),
        ("Mounting", part["mounting"] or "—"),
        ("Voltage", f"{part['voltage']} V" if part["voltage"] else "—"),
        ("Frequency", f"{part['frequency_hz']} Hz" if part["frequency_hz"] else "—"),
    ]
    for i, (lab, val) in enumerate(labels):
        cols[i % 2].metric(lab, val)

    with st.spinner("Searching catalog for compatible replacements..."):
        options = find_by_specs(part)

    st.divider()
    if options:
        st.success(f"✅ Found {len(options)} compatible replacement(s)")
        for o in options:
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{o['part_code']}** — {o['manufacturer']} {o['model']}")
                    st.caption("Why compatible: " + ", ".join(o["_reasons"]))
                    st.caption(f"Frame {o['frame_size']} · Mounting {o['mounting']} · "
                               f"{o['power_kw']} kW · {o['rpm']} rpm · {o['efficiency_class']}")
                with c2:
                    st.metric("Price", f"€{o['price_eur']}")
                    st.caption(f"In stock: {o['stock_qty']}")
    else:
        st.warning("⚠️ No compatible replacement found in catalog.")
        st.caption("No motor in stock matches the required power, speed, frame and mounting. "
                   "A near-match with different mounting would NOT fit — we don't suggest unsafe substitutes.")
