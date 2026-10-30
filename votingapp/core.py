import hashlib, hmac, re
# Exact substrings from the brief. NOTE: 2025 uses 25L1SE, other years use LSE (preserved as written).
ELIGIBLE = ["23L1CS","23L1FT","23L1CY","23L1SE","23L1LB","24L1CS","24L1FT","24L1CY","24L1SE","24L1LB",
            "25L1CS","25L1FT","25L1CY","25L1SE","25L1LB","26L1CS","26L1FT","26L1CY","26L1SE","26L1LB"]

def norm_matric(m):
    return re.sub(r"\s+", "", str(m or "")).upper()

def is_eligible(matric):
    m = norm_matric(matric)
    return any(s in m for s in ELIGIBLE)

def normalize_phone(p):
    """Return +234XXXXXXXXXX or None."""
    d = re.sub(r"\D", "", str(p or ""))
    if d.startswith("234") and len(d) == 13: d = d[3:]
    elif d.startswith("0") and len(d) == 11: d = d[1:]
    if len(d) == 10 and d[0] in "789": return "+234" + d
    return None

def phone_hash(phone, pepper):
    return hmac.new(pepper.encode(), phone.encode(), hashlib.sha256).hexdigest()
