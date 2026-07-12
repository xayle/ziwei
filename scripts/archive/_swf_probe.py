"""
Decompress ZWS (LZMA-compressed SWF) and search for string constants
that might be used as encryption key for .mlk files.
"""
import lzma, struct, sys, re

swf_path = r"d:\Users\Administrator\Desktop\文墨天机\App.swf"

with open(swf_path, "rb") as f:
    swf = f.read()

print(f"SWF size: {len(swf)} bytes")
magic = swf[:3]
print(f"Magic: {magic}")

# ZWS = LZMA compressed SWF
# Layout: ZWS(3) + version(1) + uncompressed_size(4) + compressed_len(4) + lzma_data
assert magic == b"ZWS", f"Not a ZWS SWF: {magic}"

version = swf[3]
uncompressed_size = struct.unpack_from("<I", swf, 4)[0]
compressed_len = struct.unpack_from("<I", swf, 8)[0]

print(f"Version: {version}")
print(f"Uncompressed size: {uncompressed_size}")
print(f"Compressed len: {compressed_len}")

# LZMA data starts at offset 12
# In ZWS, the LZMA stream is stored WITHOUT the uncompressed_size field
# We need to reconstruct a valid LZMA alone stream:
#   props (5 bytes) + uncompressed_size (8 bytes LE) + compressed_data
lzma_payload = swf[12:]  # props(5) + compressed_data

# Reconstruct LZMA alone stream header
props = lzma_payload[:5]
compressed_data = lzma_payload[5:]

# Build LZMA alone stream:
#   properties (5 bytes) + uncompressed_size (8 bytes LE) + data
inner_size = uncompressed_size - 8  # don't count the SWF header
lzma_stream = props + struct.pack("<Q", inner_size) + compressed_data

print(f"Decompressing SWF...")
try:
    decompressed = lzma.decompress(lzma_stream, format=lzma.FORMAT_ALONE)
    print(f"Decompressed: {len(decompressed)} bytes")

    # Search for string constants that look like keys/secrets
    # Look for printable ASCII strings of length 8-64
    strings = re.findall(rb"[\x20-\x7e]{8,64}", decompressed)
    print(f"\nFound {len(strings)} ASCII strings (8-64 chars)")

    # Filter for crypto-related strings
    key_patterns = [b"key", b"Key", b"KEY", b"secret", b"Secret", b"encrypt",
                    b"Encrypt", b"mlk", b"MLK", b"cipher", b"Cipher",
                    b"wenmo", b"WenMo", b"ziwei", b"ZiWei", b"salt", b"Salt"]

    print("\n=== Potentially crypto-related strings ===")
    for s in strings:
        sl = s.lower()
        if any(p.lower() in sl for p in key_patterns):
            print(f"  {s!r}")

    # Also look for hex-encoded strings or base64 that might be keys
    print("\n=== Strings that look like hex keys (32+ hex chars) ===")
    for s in strings:
        if re.match(rb"^[0-9a-fA-F]{32,}$", s):
            print(f"  {s!r}")

    # Save decompressed SWF for further analysis
    out_path = r"d:\Users\Administrator\Desktop\文墨天机\_decompressed_swf.bin"
    with open(out_path, "wb") as f:
        f.write(b"FWS" + bytes([version]) + struct.pack("<I", uncompressed_size) + decompressed)
    print(f"\nDecompressed SWF saved to: {out_path}")

except Exception as e:
    print(f"Decompression failed: {e}")
    # Try alternative: maybe the 4 bytes at offset 8 are part of LZMA stream
    print("Trying alternative LZMA layout...")
    try:
        dec2 = lzma.decompress(swf[12:], format=lzma.FORMAT_ALONE)
        print("Alt OK:", len(dec2))
    except Exception as e2:
        print(f"Alt also failed: {e2}")
