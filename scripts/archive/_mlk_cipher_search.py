"""Search for cipher name strings and key-like patterns near MLK code in SWF.
Also: look specifically for the getCipher call patterns in AVM2 bytecode."""
import re

with open(r"d:\Users\Administrator\Desktop\文墨天机\_swf_dec.bin", "rb") as f:
    swf = f.read()

# The MLK constant string "mlk_json" - find its position
mlk_json_pos = swf.find(b"mlk_json")
print(f"mlk_json @ {mlk_json_pos}")

# Hurlant crypto factory cipher names
cipher_names = [
    b"aes-cbc", b"aes-ecb", b"aes-ctr", b"aes",
    b"Blowfish-CBC", b"blowfish-cbc", b"blowfish",
    b"xtea-ecb", b"xtea-cbc", b"xtea",
    b"des-cbc", b"3des-cbc", b"3des",
    b"rc4", b"arc4",
    b"getCipher", b"getMode",
    b"SimpleAESKey", b"BlowfishKey", b"XTEAKey",
]

print("\n=== Cipher name strings in SWF ===")
for name in cipher_names:
    positions = [m.start() for m in re.finditer(re.escape(name), swf, re.IGNORECASE)]
    if positions:
        desc = f"  {name.decode(errors='replace')}: at {positions[:5]}"
        # Note how close some are to mlk_json
        near = [abs(p - mlk_json_pos) for p in positions]
        print(f"{desc} [min_dist_from_mlk_json: {min(near)}]")

# Look for any string that could be a fixed key embedded as AS3 string near MLK code
# Fixed keys in AS3 source would appear as string constants
print("\n=== All strings in ±50KB around mlk_json ===")
window_start = max(0, mlk_json_pos - 50000)
window_end   = min(len(swf), mlk_json_pos + 50000)
window = swf[window_start:window_end]

# Find all null-terminated or length-prefixed strings
# In AVM2, strings are stored as length-prefixed UTF8 in the constant pool
# But in the raw binary, we can look for 4-50 char sequences
strings_found = re.findall(rb"[\x20-\x7e]{6,60}", window)
unique_strings = sorted(set(strings_found))
# Filter to likely meaningful ones (not all numeric, not too long)
print(f"Total unique >5-char printable strings in window: {len(unique_strings)}")
print("Sample of non-trivial strings (contain letters+special):")
for s in unique_strings:
    decoded = s.decode(errors='replace')
    # Must contain at least one letter and not be pure digits/underscores
    has_letter = any(c.isalpha() for c in decoded)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?/\\~`' for c in decoded)
    if has_letter and (has_special or len(decoded) > 12):
        if not all(c in '0123456789abcdefABCDEF' for c in decoded):  # skip pure hex
            print(f"  {decoded!r}")
