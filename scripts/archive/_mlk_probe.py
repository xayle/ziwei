"""Probe .mlk file format - temporary diagnostic script."""
import lzma, zipfile, zlib, sys

mlk_path = r"d:\Users\Administrator\Desktop\文墨天机\文墨天机命例库_2026-5-23-16-42-51.mlk"
if len(sys.argv) > 1:
    mlk_path = sys.argv[1]

with open(mlk_path, "rb") as f:
    data = f.read()

print(f"Size: {len(data)} bytes")
h = " ".join(f"{b:02X}" for b in data[:32])
print(f"Header hex: {h}")

# --- LZMA alone ---
try:
    dec = lzma.decompress(data, format=lzma.FORMAT_ALONE)
    print(f"[OK] LZMA alone: {len(dec)} bytes")
    print(repr(dec[:400]))
    sys.exit(0)
except Exception as e:
    print(f"LZMA alone: {e}")

# --- LZMA auto ---
try:
    dec = lzma.decompress(data)
    print(f"[OK] LZMA auto: {len(dec)} bytes")
    print(repr(dec[:400]))
    sys.exit(0)
except Exception as e:
    print(f"LZMA auto: {e}")

# --- zlib ---
try:
    dec = zlib.decompress(data)
    print(f"[OK] zlib: {len(dec)} bytes")
    print(repr(dec[:400]))
    sys.exit(0)
except Exception as e:
    print(f"zlib: {e}")

# --- zlib skip 2-byte header (raw deflate) ---
try:
    dec = zlib.decompress(data[2:], -15)
    print(f"[OK] raw deflate: {len(dec)} bytes")
    print(repr(dec[:400]))
    sys.exit(0)
except Exception as e:
    print(f"raw deflate: {e}")

# --- ZIP ---
try:
    z = zipfile.ZipFile(mlk_path)
    print("[OK] ZIP archive contents:")
    for n in z.namelist():
        info = z.getinfo(n)
        print(f"  {n} ({info.file_size} bytes)")
    sys.exit(0)
except Exception as e:
    print(f"ZIP: {e}")

# --- raw bytes fallback ---
print("\nAll decompression attempts failed. Full raw bytes:")
print(data.hex())
