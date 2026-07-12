"""Check if any known key name hashes to the ELS index hash."""
import hashlib, hmac

# 32-byte hash from PrivateEncryptedDatai record
idx_hash = bytes.fromhex("317d6f2f9d69091a36bee5b540a8f9ee9a848a33789ec3602a8f27bf2f0b4b43")
print(f"Target hash: {idx_hash.hex()}")

# Known key candidates from SWF analysis
key_candidates = [
    "mlk_json", "mlk_ver", "mlk_index", "mlk_c",
    "mlk_c0", "mlk_c1", "mlk", "mlk_seprator",
    "ZiWeiDesktop", "ziwei001", "wenmotianji",
    "WenMoTianJi", "AppData", "database",
    "user_data", "cases", "data", "config",
    "cfg_lang", "login",
    "storeMybirth", "birth",
]

hash_fns = {
    "sha256": lambda k: hashlib.sha256(k.encode('utf-8')).digest(),
    "sha256_utf16le": lambda k: hashlib.sha256(k.encode('utf-16-le')).digest(),
    "sha1_utf8": lambda k: hashlib.sha1(k.encode('utf-8')).digest() + b'\x00'*12,  # pad to 32
    "md5_utf8": lambda k: hashlib.md5(k.encode('utf-8')).digest() + b'\x00'*16,   # pad to 32
    "sha256_with_app": lambda k: hashlib.sha256((k + ":ZiWeiDesktop").encode('utf-8')).digest(),
    "hmac_sha256_appid": lambda k: hmac.new(b"ZiWeiDesktop", k.encode('utf-8'), hashlib.sha256).digest(),
    "hmac_sha256_name": lambda k: hmac.new(b"WenMoTianJi", k.encode('utf-8'), hashlib.sha256).digest(),
}

found = False
for key in key_candidates:
    for fn_name, fn in hash_fns.items():
        h = fn(key)
        if h == idx_hash:
            print(f"MATCH! key={key!r} fn={fn_name}")
            found = True
        elif h[:16] == idx_hash[:16]:
            print(f"PARTIAL (first 16 bytes match): key={key!r} fn={fn_name}: {h.hex()}")

if not found:
    print("No direct match found.")

# Show closest matches
print("\n=== SHA-256 of key candidates ===")
for key in key_candidates:
    h = hashlib.sha256(key.encode('utf-8')).digest()
    print(f"  sha256({key!r}) = {h.hex()}")

# Now let's check: PrivateEncryptedDatav = 04 00 00 00 36 ef 66 7b 32 00 00 00
# Could be: version=4, timestamp=7b66ef36 (unix timestamp), tag_len=50
import struct, datetime
iv_raw = bytes.fromhex("0400000036ef667b32000000")
v0 = struct.unpack_from("<I", iv_raw, 0)[0]
ts = struct.unpack_from("<I", iv_raw, 4)[0]
v2 = struct.unpack_from("<I", iv_raw, 8)[0]
print(f"\nPrivateEncryptedDatav interpretation:")
print(f"  DWORD[0] = {v0} (version/type?)")
print(f"  DWORD[1] = {ts} = 0x{ts:08x}")
print(f"  As unix timestamp: {datetime.datetime.fromtimestamp(ts)}")
print(f"  DWORD[2] = {v2} (count/size?)")
