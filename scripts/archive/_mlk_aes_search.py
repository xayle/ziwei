"""Try AES decryption with MD5 of common strings as key.
Also tries known string patterns as AES-128 key directly."""
import lzma, hashlib
from Crypto.Cipher import AES

with open(r"d:\Users\Administrator\Desktop\文墨天机\文墨天机命例库_2026-5-23-16-42-51.mlk", "rb") as f:
    raw_file = f.read()

dec = lzma.decompress(raw_file, format=lzma.FORMAT_ALONE)
inner = bytes.fromhex(dec.decode("ascii").strip())
print(f"Inner data: {len(inner)} bytes, first 16: {inner[:16].hex()}")

# Candidates for key derivation
raw_candidates = [
    "ZiWeiDesktop", "ziwei001", "ziwei001.cn", "WenMoTianJi",
    "mlk_json", "mlk", "mlk_ver", "wenmo", "wenmotianji",
    "mlkexport", "mlkimport", "ZiWei", "com.ziwei001",
    "com.ziwei001.mlk-file",
]

def check_aes(mode_name, cipher_fn, data, expected_prefix=None):
    """Try decryption and check if result looks like JSON or AMF3."""
    try:
        result = cipher_fn(data)
    except Exception as e:
        return None, str(e)

    # Check for JSON start
    json_chars = sum(1 for b in result[:20] if chr(b) in '{}[]"abcdefghijklmnopqrstuvwxyz0123456789_-: ')
    printable = sum(1 for b in result if 32 <= b < 127)

    return result, f"{printable/len(result)*100:.0f}% printable, json_chars={json_chars}"

print("\n=== AES-ECB with MD5 keys ===")
for candidate in raw_candidates:
    key = hashlib.md5(candidate.encode()).digest()  # 16-byte MD5
    cipher = AES.new(key, AES.MODE_ECB)
    block = cipher.decrypt(inner[:16])
    printable = sum(1 for b in block if 32 <= b < 127)
    if printable > 8:
        print(f"MD5({candidate!r}) key={key.hex()}: {block!r}")

print("\n=== AES-ECB with SHA1[:16] keys ===")
for candidate in raw_candidates:
    key = hashlib.sha1(candidate.encode()).digest()[:16]  # first 16 of SHA1
    cipher = AES.new(key, AES.MODE_ECB)
    block = cipher.decrypt(inner[:16])
    printable = sum(1 for b in block if 32 <= b < 127)
    if printable > 8:
        print(f"SHA1[:16]({candidate!r}) key={key.hex()}: {block!r}")

print("\n=== AES-ECB with first 16 bytes of SWF-extracted strings ===")
# Extract all 16-byte (or 32-byte) strings from SWF that look like hex keys
import re
with open(r"d:\Users\Administrator\Desktop\文墨天机\_swf_dec.bin", "rb") as f:
    swf = f.read()

hex_keys_16 = set(re.findall(rb"[0-9a-fA-F]{32}(?![0-9a-fA-F])", swf))
print(f"Found {len(hex_keys_16)} pure 16-byte hex strings in SWF")
for hk in list(hex_keys_16)[:30]:
    key = bytes.fromhex(hk.decode())
    cipher = AES.new(key, AES.MODE_ECB)
    block = cipher.decrypt(inner[:16])
    printable = sum(1 for b in block if 32 <= b < 127)
    if printable > 8:
        print(f"key={hk.decode()}: {block!r}")
