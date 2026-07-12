"""Try DPAPI decryption with various entropy values."""
import ctypes
import ctypes.wintypes
import hashlib, base64

class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_ubyte))
    ]

crypt32  = ctypes.WinDLL('Crypt32.dll',  use_last_error=True)
kernel32 = ctypes.WinDLL('Kernel32.dll', use_last_error=True)

def dpapi_unprotect(data: bytes, entropy: bytes = b"") -> bytes | None:
    """Attempt Windows DPAPI CryptUnprotectData."""
    # Input blob
    ptr_in  = (ctypes.c_ubyte * len(data))(*data)
    blob_in = DATA_BLOB(len(data), ptr_in)

    # Entropy blob (can be empty)
    if entropy:
        ptr_ent  = (ctypes.c_ubyte * len(entropy))(*entropy)
        blob_ent = DATA_BLOB(len(entropy), ptr_ent)
        ent_ptr  = ctypes.byref(blob_ent)
    else:
        ent_ptr = None

    blob_out = DATA_BLOB()
    desc = ctypes.c_wchar_p()

    ok = crypt32.CryptUnprotectData(
        ctypes.byref(blob_in),
        ctypes.byref(desc),
        ent_ptr,
        None,
        None,
        0,
        ctypes.byref(blob_out)
    )
    if ok:
        n = blob_out.cbData
        result = bytes(blob_out.pbData[:n])
        kernel32.LocalFree(blob_out.pbData)
        return result
    err = ctypes.get_last_error()
    return None

# Read the DPAPI blob
with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatak", "rb") as f:
    kblob = f.read()
print(f"Key blob: {len(kblob)} bytes | {kblob[:16].hex()}")

# Try with no entropy first
result = dpapi_unprotect(kblob, b"")
print(f"No entropy: {result.hex() if result else 'FAILED'}")

# Try with known entropy values
entropies = {
    "empty_bytes": b"",
    "ZiWeiDesktop": b"ZiWeiDesktop",
    "ziwei001": b"ziwei001",
    "ziwei001.cn": b"ziwei001.cn",
    "WenMoTianJi": b"WenMoTianJi",
    "com.ziwei001": b"com.ziwei001",
    "mlk_json": b"mlk_json",
    # AIR uses publisher cert hash as entropy
    "E5A2D037C91F4B40A96008B19715A60F": bytes.fromhex("E5A2D037C91F4B40A96008B19715A60F"),
    "appid_hash": hashlib.sha1(b"ZiWeiDesktop").digest(),
    "app_publisher": b"com.ziwei001.WenMoTianJi",
    # null byte entropy
    "null_bytes_16": b"\x00" * 16,
    "null_bytes_8": b"\x00" * 8,
}

for name, ent in entropies.items():
    result = dpapi_unprotect(kblob, ent)
    if result:
        print(f"SUCCESS with entropy '{name}': {result.hex()}")
    # else: print nothing for failures to avoid clutter

print("\nAll attempts done.")

# Now also inspect PrivateEncryptedData raw structure
with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedData", "rb") as f:
    enc_data = f.read()
print(f"\nPrivateEncryptedData: {len(enc_data)} bytes")
print(f"First 64 bytes: {enc_data[:64].hex()}")
print(f"Last 32 bytes:  {enc_data[-32:].hex()}")
# Check for zero padding
trailing_zeros = len(enc_data) - len(enc_data.rstrip(b'\x00'))
print(f"Trailing zero bytes: {trailing_zeros}")
print(f"Non-zero data size: {len(enc_data) - trailing_zeros}")

# Entropy
import math
freq = [0]*256
for b in enc_data:
    freq[b] += 1
entropy = -sum(f/len(enc_data)*math.log2(f/len(enc_data)) for f in freq if f > 0)
print(f"Entropy: {entropy:.3f} bits/byte")

# PrivateEncryptedDatai
with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatai", "rb") as f:
    enc_idx = f.read()
print(f"\nPrivateEncryptedDatai: {len(enc_idx)} bytes")
print(f"First 64 bytes: {enc_idx[:64].hex()}")
# Try decode as UTF-8
try:
    txt = enc_idx.decode('utf-8')
    print(f"Is UTF-8 text: YES (first 200 chars): {txt[:200]!r}")
except:
    pass
try:
    txt = enc_idx.decode('utf-16-le')
    printable = sum(1 for c in txt if 32 <= ord(c) < 127)
    if printable / len(txt) > 0.5:
        print(f"Is UTF-16-LE: YES, starts: {txt[:100]!r}")
except:
    pass
