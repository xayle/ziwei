"""Parse AIR ELS file structure and try to find mlk_json."""
import hashlib, hmac, struct, math

# Read all ELS files
with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedData",  "rb") as f: data  = f.read()
with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatai", "rb") as f: idx   = f.read()
with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatak", "rb") as f: kblob = f.read()
with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatav", "rb") as f: iv    = f.read()

print(f"data: {len(data)} bytes | idx: {len(idx)} bytes | kblob: {len(kblob)} bytes | iv: {len(iv)} bytes")

# --- Parse PrivateEncryptedData as (length, value) records ---
print("\n=== PrivateEncryptedData records ===")
pos = 0
records = []
while pos < len(data):
    if pos + 4 > len(data): break
    rec_len = struct.unpack_from("<I", data, pos)[0]
    if rec_len == 0: break
    pos += 4
    if pos + rec_len > len(data): break
    rec_data = data[pos:pos+rec_len]
    records.append(rec_data)
    print(f"  @{pos-4}: len={rec_len} hex={rec_data[:32].hex()}{'...' if rec_len>32 else ''}")
    pos += rec_len

print(f"Total records in data: {len(records)}")

# --- Parse PrivateEncryptedDatai as (length, value) records ---
print("\n=== PrivateEncryptedDatai records ===")
pos = 0
idx_records = []
while pos < len(idx):
    if pos + 4 > len(idx): break
    rec_len = struct.unpack_from("<I", idx, pos)[0]
    if rec_len == 0: break
    pos += 4
    if pos + rec_len > len(idx): break
    rec_data = idx[pos:pos+rec_len]
    idx_records.append(rec_data)
    # Decode as UTF-8 if possible
    try:
        txt = rec_data.decode('utf-8')
        print(f"  @{pos-4}: len={rec_len} str={txt!r}")
    except:
        print(f"  @{pos-4}: len={rec_len} hex={rec_data[:32].hex()}")
    pos += rec_len

print(f"Total records in idx: {len(idx_records)}")

# --- Check what key names are stored ---
print("\n=== Looking for mlk_json and related keys ===")
key_candidates = ["mlk_json", "mlk_ver", "mlk_index", "mlk_c", "mlk"]
for key in key_candidates:
    for encoding in ['utf-8', 'utf-16-le', 'utf-16-be']:
        kb = key.encode(encoding)
        if kb in idx:
            print(f"FOUND key {key!r} as {encoding} in idx!")
        if kb in data:
            print(f"FOUND key {key!r} as {encoding} in data!")

# --- Try to see if any idx record decodes as UTF-16 or UTF-8 ---
print("\n=== Raw idx bytes trying UTF-16LE ---")
for i, rec in enumerate(idx_records[:5]):
    try:
        s = rec.decode('utf-16-le')
        print(f"  idx[{i}] UTF-16LE: {s!r}")
    except:
        pass
    try:
        s = rec.decode('utf-8')
        print(f"  idx[{i}] UTF-8: {s!r}")
    except:
        print(f"  idx[{i}] hex: {rec.hex()}")

# Show the PrivateEncryptedDatav raw content
print(f"\nPrivateEncryptedDatav raw: {iv.hex()}")
print(f"  As DWORD[0]: {struct.unpack_from('<I', iv, 0)[0]}")
print(f"  As DWORD[1]: {struct.unpack_from('<I', iv, 4)[0]}")
print(f"  As DWORD[2]: {struct.unpack_from('<I', iv, 8)[0]}")
