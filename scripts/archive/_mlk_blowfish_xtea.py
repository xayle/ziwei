"""Comprehensive decryption attempt: Blowfish-CBC and XTEA with embedded IV.
Structure hypothesis: [8-byte IV] [256-byte cipher blocks]"""
import lzma, struct, hashlib
from Crypto.Cipher import Blowfish, AES, DES3

with open(r"d:\Users\Administrator\Desktop\文墨天机\文墨天机命例库_2026-5-23-16-42-51.mlk", "rb") as f:
    raw_file = f.read()
dec = lzma.decompress(raw_file, format=lzma.FORMAT_ALONE)
inner = bytes.fromhex(dec.decode("ascii").strip())
print(f"Inner: {len(inner)} bytes | {inner[:16].hex()}")

# Hypothesis: first 8 bytes = Blowfish IV, rest = ciphertext
iv8   = inner[:8]    # 8-byte potential IV
ct256 = inner[8:]    # 256 bytes = 32 Blowfish blocks
iv16  = inner[:16]   # 16-byte potential AES IV
ct248 = inner[16:]   # 248 bytes (not AES-CBC aligned, so skip)
# ALL 264 bytes as Blowfish-ECB (264/8=33 blocks, aligned)
ct264 = inner        # 33 Blowfish blocks

def is_json_like(data: bytes, min_pct=0.75) -> bool:
    """Check if decrypted data looks like JSON."""
    printable = sum(1 for b in data if 32 <= b < 127)
    if printable / len(data) < min_pct:
        return False
    # Check for JSON-like start after stripping junk
    for start in range(min(16, len(data))):
        if data[start:start+1] in (b'{', b'[', b'"'):
            return True
    return False

def try_blowfish(key: bytes, mode_label: str, iv: bytes, ct: bytes):
    """Try Blowfish decryption and check result."""
    if len(key) < 4:
        key = (key * 8)[:8]
    try:
        if len(iv) > 0:
            cipher = Blowfish.new(key, Blowfish.MODE_CBC, iv)
        else:
            cipher = Blowfish.new(key, Blowfish.MODE_ECB)
        pt = cipher.decrypt(ct)
        if is_json_like(pt):
            print(f"\n*** MATCH: Blowfish-{mode_label} key={key!r} ***")
            print(f"  Plaintext: {pt[:100]}")
            return True
    except Exception as e:
        pass
    return False

def try_3des(key: bytes, iv: bytes, ct: bytes):
    """Try 3DES-CBC."""
    try:
        k = (key * 4)[:24]
        cipher = DES3.new(k, DES3.MODE_CBC, iv[:8])
        pt = cipher.decrypt(ct)
        if is_json_like(pt):
            print(f"\n*** MATCH: 3DES-CBC key={key!r} ***")
            print(f"  Plaintext: {pt[:100]}")
            return True
    except:
        pass
    return False

def xtea_dec(v: bytes, key: bytes) -> bytes:
    """Decrypt 8-byte XTEA block with 16-byte key."""
    v0, v1 = struct.unpack('>II', v)
    k = list(struct.unpack('>4I', (key*4)[:16]))
    delta, mask = 0x9e3779b9, 0xFFFFFFFF
    s = (delta * 32) & mask
    for _ in range(32):
        v1 = (v1 - (((v0<<4 ^ v0>>5) + v0) ^ (s + k[s>>11 & 3]))) & mask
        s  = (s - delta) & mask
        v0 = (v0 - (((v1<<4 ^ v1>>5) + v1) ^ (s + k[s & 3])))     & mask
    return struct.pack('>II', v0, v1)

def xtea_dec_le(v: bytes, key: bytes) -> bytes:
    """Decrypt 8-byte XTEA block (little-endian)."""
    v0, v1 = struct.unpack('<II', v)
    k = list(struct.unpack('<4I', (key*4)[:16]))
    delta, mask = 0x9e3779b9, 0xFFFFFFFF
    s = (delta * 32) & mask
    for _ in range(32):
        v1 = (v1 - (((v0<<4 ^ v0>>5) + v0) ^ (s + k[s>>11 & 3]))) & mask
        s  = (s - delta) & mask
        v0 = (v0 - (((v1<<4 ^ v1>>5) + v1) ^ (s + k[s & 3])))     & mask
    return struct.pack('<II', v0, v1)

def try_xtea(key16: bytes, iv8: bytes, ct: bytes, le=False):
    """Try XTEA-CBC."""
    dec_fn = xtea_dec_le if le else xtea_dec
    prev = iv8
    result = bytearray()
    try:
        for i in range(0, len(ct), 8):
            block = ct[i:i+8]
            dec_block = dec_fn(block, key16)
            result.extend(bytes(a^b for a,b in zip(dec_block, prev)))
            prev = block
    except:
        return False
    result = bytes(result)
    if is_json_like(result):
        label = 'XTEA-CBC-LE' if le else 'XTEA-CBC-BE'
        print(f"\n*** MATCH: {label} key={key16.hex()} ***")
        print(f"  Plaintext: {result[:100]}")
        return True
    return False

# Key candidates
raw_strs = [
    "ZiWeiDesktop", "ziwei001", "ziwei001.cn", "WenMoTianJi",
    "wenmotianji", "mlk_json", "mlk", "mlkexport",
    "com.ziwei001", "zw2013", "zwajiu", "zwajiu2",
    "ziwei", "zwpan", "zwmlk", "mlkkey",
    "12345678", "password", "mlk_key",
    # Try reversed app ID
    "потопиseW iZ",  # reversed ZiWeiDesktop
]

key_candidates = []
for s in raw_strs:
    b = s.encode('utf-8')
    key_candidates.append(('utf8:'+s, b))
    # MD5 of the string (16 bytes)
    key_candidates.append(('md5:'+s, hashlib.md5(b).digest()))
    # First 16 of SHA1
    key_candidates.append(('sha1_16:'+s, hashlib.sha1(b).digest()[:16]))

print(f"\nTrying {len(key_candidates)} keys × 4 cipher modes")

for label, key in key_candidates:
    # 1. Blowfish-CBC with embedded 8-byte IV
    try_blowfish(key, f"CBC(iv8)", iv8, ct256)
    # 2. Blowfish-ECB on all 264 bytes
    try_blowfish(key, "ECB(264)", b"", ct264)
    # 3. XTEA-CBC BE
    key16 = (key*4)[:16]
    try_xtea(key16, iv8, ct256, le=False)
    # 4. XTEA-CBC LE
    try_xtea(key16, iv8, ct256, le=True)

print("\nDone.")
