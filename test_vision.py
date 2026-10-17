import os
import base64
from openai import OpenAI

client = OpenAI(
    base_url="https://developer.amd.com.cn/radeon/api/v1",
    api_key=os.environ["RADEON_API_KEY"],
)

with open("test.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

resp = client.chat.completions.create(
    model="Qwen3.8-Flash-Next",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "This is a photo of an equipment nameplate. "
                        "Extract the technical data and return ONLY valid JSON "
                        "with keys: manufacturer, model, type, voltage, power, "
                        "rpm, frequency, serial_number, country. "
                        "If a field is not visible, use null."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                },
            ],
        }
    ],
    response_format={"type": "json_object"},
    max_tokens=500,
)

print(resp.choices[0].message.content)
