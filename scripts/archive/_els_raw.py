"""Detailed examination of ELS raw files."""
import struct, hashlib

def read_nonzero(path):
    with open(path, "rb") as f:
        data = f.read()
    # Find the last non-zero byte
    last_nz = len(data)
    while last_nz > 0 and data[last_nz-1] == 0:
        last_nz -= 1
    return data[:last_nz], data

main_nz, main_full = read_nonzero(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedData")
idx_nz,  idx_full  = read_nonzero(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatai")

print(f"PrivateEncryptedData : {len(main_full)} total, {len(main_nz)} non-zero")
print(f"PrivateEncryptedDatai: {len(idx_full)} total, {len(idx_nz)} non-zero")
print(f"\n--- PrivateEncryptedData non-zero hex ---")
print(' '.join(f'{b:02x}' for b in main_nz))
print(f"\n--- PrivateEncryptedDatai non-zero hex ---")
print(' '.join(f'{b:02x}' for b in idx_nz))
print(f"\n--- PrivateEncryptedDatai non-zero ASCII attempt ---")
try:
    print(idx_nz.decode('utf-8'))
except:
    try:
        print(idx_nz.decode('utf-16-le'))
    except:
        print("(not decodable as text)")

# How many DWORD-length records fit in each?
print("\n--- Try parse as DWORD-prefixed records ---")
for name, data in [("data", main_nz), ("idx", idx_nz)]:
    pos = 0
    recs = []
    while pos + 4 <= len(data):
        rec_len = struct.unpack_from("<I", data, pos)[0]
        pos += 4
        if rec_len == 0 or pos + rec_len > len(data):
            # Try big-endian
            rec_len = struct.unpack_from(">I", data, pos-4)[0]
            if rec_len == 0 or pos + rec_len > len(data):
                break
        recs.append((pos-4, rec_len, data[pos:pos+rec_len]))
        pos += rec_len
    print(f"\n{name} has {len(recs)} records (LE parse):")
    for offset, rlen, rdata in recs:
        print(f"  @{offset}: len={rlen} | {rdata[:32].hex()}")
