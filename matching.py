import pandas as pd

CATALOG = pd.read_csv("catalog.csv")

def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

def find_part(part_code):
    """Точный поиск по артикулу."""
    hit = CATALOG[CATALOG["part_code"].str.lower() == str(part_code).lower()]
    if len(hit) == 0:
        return None
    return hit.iloc[0].to_dict()

def is_compatible(target, cand):
    """
    Совместима ли деталь cand как замена target.
    Жёсткие поля (должны совпадать): мощность, обороты (±2%), крепление,
    типоразмер, вольтаж, частота. Иначе — не подходит.
    """
    reasons = []
    ok = True

    # мощность — строго равна
    tp, cp = _num(target["power_kw"]), _num(cand["power_kw"])
    if tp != cp:
        ok = False
    else:
        reasons.append(f"same power {cp} kW")

    # обороты — допуск ±2% (разные бренды дают 1450 vs 1460)
    tr, cr = _num(target["rpm"]), _num(cand["rpm"])
    if tr and cr and abs(tr - cr) / tr <= 0.02:
        reasons.append(f"matching speed ~{cr} rpm")
    else:
        ok = False

    # крепление — строго (твой кейс с B3 vs B5)
    if str(target["mounting"]) == str(cand["mounting"]):
        reasons.append(f"same mounting {cand['mounting']}")
    else:
        ok = False

    # типоразмер — строго
    if str(target["frame_size"]) == str(cand["frame_size"]):
        reasons.append(f"same frame {cand['frame_size']}")
    else:
        ok = False

    # вольтаж и частота — мягко: несовпадение блокирует, но отсутствие данных (None) — нет
    tv, cv = target.get("voltage"), cand.get("voltage")
    if tv and cv and str(tv) not in str(cv) and str(cv) not in str(tv):
        ok = False
    tf, cf = target.get("frequency_hz"), cand.get("frequency_hz")
    if tf and cf and str(_num(tf)) != str(_num(cf)):
        ok = False

    return ok, reasons

def find_replacements(target):
    """Список совместимых доступных замен, отсортированных по наличию и цене."""
    results = []
    for _, row in CATALOG.iterrows():
        cand = row.to_dict()
        if cand["part_code"] == target["part_code"]:
            continue
        if str(cand["status"]) != "active":
            continue
        if _num(cand["stock_qty"]) is None or _num(cand["stock_qty"]) <= 0:
            continue
        ok, reasons = is_compatible(target, cand)
        if ok:
            cand["_reasons"] = reasons
            results.append(cand)
    results.sort(key=lambda c: (-_num(c["stock_qty"]), _num(c["price_eur"])))
    return results

def resolve(target):
    """
    Главная функция. Принимает деталь (dict с характеристиками),
    возвращает решение: in_stock / replacements / no_replacement.
    """
    # есть ли сама деталь в наличии?
    in_cat = find_part(target.get("part_code", "")) if target.get("part_code") else None
    if in_cat and str(in_cat["status"]) == "active" and _num(in_cat["stock_qty"]) > 0:
        return {"decision": "in_stock", "part": in_cat}

    # ищем замены по характеристикам
    reps = find_replacements(in_cat if in_cat else target)
    if reps:
        return {"decision": "replacements", "original": in_cat or target, "options": reps}

    return {"decision": "no_replacement", "original": in_cat or target}
