import hashlib, hmac, re
# Exact prefixes from the brief. NOTE: for L1, 2025 uses 25L1SE while other years use LSE (preserved as written).
ELIGIBLE_L1 = ["23L1CS","23L1FT","23L1CY","23LSE","23L1LI","24L1CS","24L1FT","24L1CY","24LSE","24L1LI",
               "25L1CS","25L1FT","25L1CY","25L1SE","25L1LI","26L1CS","26L1FT","26L1CY","26LSE","26L1LI"]
# L2 mirrors L1 with L2 in place of L1 (same years, same departments). L2 Software Engineering is written consistently as L2SE.
ELIGIBLE_L2 = ["23L2CS","23L2FT","23L2CY","23L2SE","23L2LI","24L2CS","24L2FT","24L2CY","24L2SE","24L2LI",
               "25L2CS","25L2FT","25L2CY","25L2SE","25L2LI","26L2CS","26L2FT","26L2CY","26L2SE","26L2LI"]
ELIGIBLE = ELIGIBLE_L1 + ELIGIBLE_L2   # both levels share one voting system: 40 groups x 300 = 12,000 matrics

def norm_matric(m):
    return re.sub(r"\s+", "", str(m or "")).upper()

MAX_SERIAL = 300   # each department group is numbered 0001 to 0300 only

def is_eligible(matric, admin_matric=""):
    """STRICT roll: exactly <prefix><4-digit serial 0001-0300>, e.g. 23L1CS0001 ... 26L2LI0300 (40 groups x 300 = 12,000 matrics: L1 and L2).
    Anything else is refused: no extra characters, no 0000, no 0301+, no 3-digit serials. Only the configured admin matric is exempt."""
    m = norm_matric(matric)
    if admin_matric and m == norm_matric(admin_matric): return True
    for p in ELIGIBLE:
        if m.startswith(p):
            serial = m[len(p):]
            return len(serial) == 4 and serial.isascii() and serial.isdigit() and 1 <= int(serial) <= MAX_SERIAL
    return False

def normalize_phone(p):
    """Return +234XXXXXXXXXX or None."""
    d = re.sub(r"\D", "", str(p or ""))
    if d.startswith("234") and len(d) == 13: d = d[3:]
    elif d.startswith("0") and len(d) == 11: d = d[1:]
    if len(d) == 10 and d[0] in "789": return "+234" + d
    return None

def phone_hash(phone, pepper):
    return hmac.new(pepper.encode(), phone.encode(), hashlib.sha256).hexdigest()
