from matching import find_part, resolve
import json

def show(title, part_code):
    print("=" * 50)
    print(title, "->", part_code)
    target = find_part(part_code)
    if not target:
        print("  not found in catalog")
        return
    res = resolve(target)
    print("  decision:", res["decision"])
    if res["decision"] == "replacements":
        for o in res["options"]:
            print(f"    - {o['part_code']} ({o['manufacturer']}) "
                  f"{o['price_eur']}eur stock {o['stock_qty']} | "
                  f"{', '.join(o['_reasons'])}")
    elif res["decision"] == "in_stock":
        print(f"    {res['part']['part_code']} in stock")

show("Discontinued, has replacement", "ABB-M2QA90L4A")
show("Discontinued, cross-brand matches", "Siemens-1LA7096-4AA")
show("Discontinued, NO replacement", "Bonfiglioli-BN80B6")
show("Active, in stock", "ABB-M3BP90LB4")
