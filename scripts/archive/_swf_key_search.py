"""Search for pushbyte sequences in AVM2 bytecode that might represent encryption keys."""
with open(r"d:\Users\Administrator\Desktop\文墨天机\_swf_dec.bin", "rb") as f:
    dec = f.read()

found_sequences = []
for i in range(len(dec) - 32):
    count = 0
    bytes_seq = []
    j = i
    while j < len(dec) - 1 and j < i + 200 and count < 40:
        if dec[j] == 0x24:  # pushbyte
            val = dec[j+1]
            bytes_seq.append(val)
            j += 2
            count += 1
        elif dec[j] in [0x2C, 0x27, 0x26, 0x4f, 0x41, 0x20, 0x60, 0xd0, 0xd1, 0x48]:
            j += 1
        elif dec[j] == 0x25:  # pushshort (2 bytes operand)
            j += 3
        else:
            break
    if count >= 8:
        found_sequences.append((i, bytes(bytes_seq)))

print(f"Found {len(found_sequences)} sequences of 8+ pushbyte instructions")
seen = set()
for start, seq in found_sequences:
    if seq in seen:
        continue
    seen.add(seq)
    printable = sum(1 for b in seq if 32 <= b < 127)
    is_asc = seq.decode("ascii", errors="replace")
    print(f"@{start}: len={len(seq)} hex={seq.hex()}")
    if printable > len(seq) * 0.4:
        print(f"  ascii: {is_asc}")
