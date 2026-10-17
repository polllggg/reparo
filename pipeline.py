import os
import re
import json
import base64
from openai import OpenAI
from matching import CATALOG, is_compatible, _num

client = OpenAI(
    base_url="https://developer.amd.com.cn/radeon/api/v1",
    api_key=os.environ["RADEON_API_KEY"],
)

PROMPT = (
    "You are reading the nameplate of a European three-phase electric motor. "
    "Look carefully and extract EVERY field. Return ONLY valid JSON, no extra text, "
    "with exactly these keys:\n"
    "  manufacturer (brand, e.g. ABB, Siemens, WEG)\n"
    "  model (full type designation exactly as printed, e.g. 'M2QA 90L 4A')\n"
    "  power_kw (number in kilowatts, e.g. 1.5)\n"
    "  rpm (number, the r/min value, e.g. 1450)\n"
    "  frame_size (IEC frame, e.g. 90L, 100L, 132M, 80)\n"
    "  mounting (mounting code, e.g. B3, B5, B14 — read this carefully, it matters)\n"
    "  voltage (e.g. 400)\n"
    "  frequency_hz (number; European motors are almost always 50)\n"
    "Rules: read digits and letters precisely. If a field is truly not visible, use null. "
    "Do NOT invent a model name — copy it exactly. "
    "If you see 'Hz' assume 50 unless another number is clearly printed."
)

def _call(img_b64, ext):
    resp = client.chat.completions.create(
        model="Qwen3.8-Flash-Next",
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/{ext};base64,{img_b64}"}},
            ],
        }],
        response_format={"type": "json_object"},
        reasoning_effort="none",
        temperature=0,
        max_tokens=1500,
    )
    return resp.choices[0].message.content

def read_nameplate(image_path, retries=2):
    with open(image_path, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    ext = "jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else "png"
    last_err = None
    for attempt in range(retries + 1):
        content = _call(img_b64, ext)
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            last_err = e
            # пробуем вытащить JSON из текста, если модель обернула его
            m = re.search(r"\{.*\}", content, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group())
                except json.JSONDecodeError:
                    pass
    raise last_err

def normalize(raw):
    def num(v):
        if v is None:
            return None
        m = re.search(r"[\d.]+", str(v))
        return float(m.group()) if m else None
    freq = num(raw.get("frequency_hz"))
    if freq is None:
        freq = 50.0  # европейский мотор по умолчанию
    return {
        "manufacturer": raw.get("manufacturer"),
        "model": raw.get("model"),
        "power_kw": num(raw.get("power_kw")),
        "rpm": num(raw.get("rpm")),
        "frame_size": str(raw.get("frame_size")).strip() if raw.get("frame_size") else None,
        "mounting": str(raw.get("mounting")).strip().upper() if raw.get("mounting") else None,
        "voltage": str(num(raw.get("voltage"))).replace(".0", "") if raw.get("voltage") else None,
        "frequency_hz": str(freq).replace(".0", ""),
    }

def find_by_specs(part):
    results = []
    for _, row in CATALOG.iterrows():
        cand = row.to_dict()
        if str(cand["status"]) != "active" or _num(cand["stock_qty"]) <= 0:
            continue
        ok, reasons = is_compatible(part, cand)
        if ok:
            cand["_reasons"] = reasons
            results.append(cand)
    results.sort(key=lambda c: (-_num(c["stock_qty"]), _num(c["price_eur"])))
    return results

def run(image_path):
    raw = read_nameplate(image_path)
    part = normalize(raw)
    options = find_by_specs(part)
    if options:
        return {"decision": "replacements", "scanned": part, "options": options}
    return {"decision": "no_replacement", "scanned": part}

if __name__ == "__main__":
    import sys
    img = sys.argv[1] if len(sys.argv) > 1 else "test.png"
    result = run(img)
    print("\nSCANNED:", json.dumps(result["scanned"], ensure_ascii=False))
    print("DECISION:", result["decision"])
    for o in result.get("options", []):
        print(f"  - {o['part_code']} €{o['price_eur']} | {', '.join(o['_reasons'])}")
