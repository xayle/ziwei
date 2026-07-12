"""Search for potential crypto keys: pushbyte sequences of 8/16/24/32 bytes
that are NON-printable (likely random/binary key material) near MLK code."""
with open(r"d:\Users\Administrator\Desktop\文墨天机\_swf_dec.bin", "rb") as f:
    dec = f.read()

# Find tight pushbyte sequences (consecutive, no interleaved ops)
# These are the most likely to be direct key encoding
results = []
i = 0
while i < len(dec) - 2:
    if dec[i] == 0x24:  # pushbyte
        seq = []
        j = i
        while j < len(dec) - 1 and dec[j] == 0x24:
            seq.append(dec[j+1])
            j += 2
        if len(seq) in (8, 12, 16, 24, 32):
            sb = bytes(seq)
            printable = sum(1 for b in sb if 32 <= b < 127)
            printable_pct = printable / len(sb)
            # Only keep non-printable ones (likely key material, not text)
            if printable_pct < 0.5:
                results.append((i, sb))
        i = j
    else:
        i += 1

print(f"Found {len(results)} potential key-length pushbyte sequences (non-printable)")
seen = set()
for pos, key_bytes in results:
    if key_bytes in seen:
        continue
    seen.add(key_bytes)
    printable_pct = sum(1 for b in key_bytes if 32 <= b < 127) / len(key_bytes) * 100
    print(f"@{pos}: len={len(key_bytes)} printable={printable_pct:.0f}%  hex={key_bytes.hex()}")
    # Show context: what MLK-related strings are within 5000 bytes?
    import re
    ctx_start = max(0, pos - 3000)
    ctx_end = min(len(dec), pos + 3000)
    ctx = dec[ctx_start:ctx_end]
    if b"mlk" in ctx.lower() or b"MLK" in ctx:
        print("  ** NEAR MLK CODE **")
    strings = re.findall(rb"[\x20-\x7e]{6,40}", ctx)
    nearby = [s.decode("ascii","replace") for s in strings
              if b"WenMoTianJiK" not in s and len(s) < 40]
    if nearby:
        print(f"  Near strings: {nearby[:5]}")
