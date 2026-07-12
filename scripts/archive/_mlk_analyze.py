"""Analyze the 264-byte inner content of .mlk file."""
import lzma
from collections import Counter

with open(r"d:\Users\Administrator\Desktop\文墨天机\文墨天机命例库_2026-5-23-16-42-51.mlk", "rb") as f:
    raw_file = f.read()

dec = lzma.decompress(raw_file, format=lzma.FORMAT_ALONE)
inner = bytes.fromhex(dec.decode("ascii").strip())

print("Full 264 bytes hex:")
print(inner.hex())
print()

cnt = Counter(inner)
top10 = sorted(cnt.items(), key=lambda x: -x[1])[:10]
print("Most frequent bytes:")
for b, freq in top10:
    ch = repr(chr(b)) if 32 <= b < 127 else "?"
    print(f"  0x{b:02X} ({b:3d}) {ch}: {freq} times")

print(f"\nBytes 0-1 BE={int.from_bytes(inner[:2],'big')}, LE={int.from_bytes(inner[:2],'little')}")
print(f"Bytes 0-3 BE={int.from_bytes(inner[:4],'big')}, LE={int.from_bytes(inner[:4],'little')}")
print(f"Bytes 0-4 content: {inner[:8].hex()}")

# Try: is the data just an AMF3 ByteArray object?
# AMF3 ByteArray type = 0x0C = 12
# If first byte is 0x0C followed by variable-length integer,
# then that integer is the byte count
# 0x2C = 44 in binary is 0b00101100
# AMF3 variable-length integer encoding: if MSB=0, it's 7-bit (0-127)
# 0x2C = 44, MSB=0, so this would be integer 44 directly
# Then 0xA1 would be the first byte of a 44-byte ByteArray content

# Actually, in AMF3, the variable-length-int for ByteArray:
# reading: (n << 1) | 1 = reference, or inline value
# byte 0 = 0x2C = 44 = 0b00101100
# If this is the reference flag: 44 >> 1 = 22, that's reference #22
# If this is inline: (44 - 1) / 2 = not integer...

# AMF3 variable-length integer parsing
def read_u29(data, pos):
    n = 0
    for i in range(4):
        b = data[pos + i]
        if i < 3:
            n = (n << 7) | (b & 0x7F)
            if not (b & 0x80):
                return n, pos + i + 1
        else:
            n = (n << 8) | b
            return n, pos + 4
    return n, pos + 4

# The first byte of AMF3 ByteArray stream is the type marker for the
# ByteArray object itself. For writeObject(byteArray):
# byte 0 = 0x0C (ByteArray type in AMF3)
# But our byte 0 = 0x2C, not 0x0C

# What if there's no type marker and this IS directly the bytes?
# i.e., writeBytes() was used instead of writeObject()

# Let's check: could this be a raw zlib stream starting with 0x78 after XOR?
# If zlib header starts at some offset after a custom header:
for skip in range(0, 20):
    if inner[skip] == 0x78 and inner[skip+1] in [0x9C, 0xDA, 0x01]:
        print(f"\nPossible zlib at offset {skip}!")
        import zlib
        try:
            d = zlib.decompress(inner[skip:])
            print("  zlib ok:", d[:100])
        except Exception as e:
            print(f"  zlib fail: {e}")

# Try Blowfish with various keys
try:
    from Crypto.Cipher import Blowfish
    from Crypto.Cipher import AES

    keys = [
        b"ZiWeiDesktop", b"ziwei001", b"WenMoTianJi", b"mlk", b"mlk_json",
        b"wenmo", b"ziwei", b"mlkexport", b"mlkimport",
    ]
    print("\nBlowfish ECB decryption trials:")
    for key in keys:
        try:
            cipher = Blowfish.new(key, Blowfish.MODE_ECB)
            dec_data = cipher.decrypt(inner[:264])
            printable = sum(1 for b in dec_data if 32 <= b < 127)
            pct = printable / len(dec_data) * 100
            if pct > 50:
                print(f"  Blowfish({key!r}): {pct:.0f}% printable -> {dec_data[:80]!r}")
            else:
                print(f"  Blowfish({key!r}): {pct:.0f}%")
        except Exception as e:
            print(f"  Blowfish({key!r}): error {e}")
except ImportError:
    print("pycryptodome not installed")
