# 🔧 Reparo

**Snap a motor nameplate → get a compatible replacement in seconds.**
AI vision running on AMD.

Reparo is built for the **AMD Developer Hackathon: ACT III** (Reinvent Commerce track).

---

## The problem

When an industrial motor fails, the production line stops — and every hour of
downtime costs money. The mechanic photographs the nameplate and sends it to a
parts supplier, where someone manually reads the photo, searches the catalog,
and — if the motor is discontinued — tries to find a compatible replacement by
spec. This takes hours. The urgent order goes to whoever answers first.

## What Reparo does

Upload a photo of a motor nameplate. Reparo:

1. **Reads the nameplate** — an AI vision model on AMD extracts manufacturer,
   model, power, speed, frame size and mounting.
2. **Searches the supplier catalog** for the exact part.
3. **Finds a compatible replacement** by specification when the original is
   discontinued or out of stock — and explains *why* it fits.
4. **Refuses unsafe substitutes** — a near-match with a different mounting type
   is NOT offered. If nothing truly fits, Reparo says so honestly.

The intelligence is in step 3–4: anyone can search by part number, but Reparo
answers the question a database can't — *"this code no longer exists, what
actually fits instead?"*

## Where AMD runs

The vision inference — reading the nameplate photo and extracting structured
specs — runs on **AMD GPUs via AMD Token Factory** (model: Qwen3.8-Flash-Next).
This is the AI workload that powers the product.

## How compatibility works

A replacement is only offered if it matches on **power, speed (±2%), frame size
and mounting**, with matching voltage and frequency. Mounting is strict — a B5
motor is never offered to replace a B3, because it physically would not fit.
This mirrors reality: in mechanics, "close enough" often means "doesn't fit".

## Tech stack

- **AMD Token Factory** — vision inference on AMD GPUs
- **Python** — matching logic
- **pandas** — catalog
- **Streamlit** — web UI

## Run it locally

\`\`\`bash
pip install -r requirements.txt
export RADEON_API_KEY="your-amd-token-factory-key"
streamlit run app.py
\`\`\`

Then open http://localhost:8501 and upload a nameplate photo.

## Project structure

- \`app.py\` — Streamlit interface
- \`pipeline.py\` — photo → specs (AMD vision) → matching
- \`matching.py\` — compatibility logic + catalog loading
- \`catalog.csv\` — motor catalog (synthetic, modeled on real IEC motor specs)

## Note on data

The catalog is synthetic, modeled on the structure of real manufacturer
catalogs (ABB, Siemens, WEG). In production, Reparo would connect to a
supplier's real inventory system and a verified cross-reference database.

## License

MIT
