import re

def validate_nric_fin(id_str: str) -> bool:
    """
    Validate a Singapore NRIC or FIN.
    
    NRIC/FIN format: 1 letter [S/T/F/G] + 7 digits + 1 checksum letter.
    Returns True if format and checksum are valid, False otherwise.
    """
    id_str = id_str.strip().upper()
    if not re.fullmatch(r"[STFG]\d{7}[A-Z]", id_str):
        return False

    prefix, digits, checksum = id_str[0], id_str[1:8], id_str[8]
    weights = [2, 7, 6, 5, 4, 3, 2]

    # 1) Compute weighted sum of digits
    total = sum(int(d) * w for d, w in zip(digits, weights))

    # 2) Add offset of 4 if prefix in T or G
    if prefix in ("T", "G"):
        total += 4

    # 3) Choose the correct checksum table
    if prefix in ("S", "T"):
        table = list("JZIHGFEDCBA")
    else:  # F or G
        table = list("XWUTRQPNMLK")

    # 4) remainder → index into table
    idx = total % 11
    return checksum == table[idx]
