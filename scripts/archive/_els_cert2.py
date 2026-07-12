"""Extract X.509 cert from signatures.xml and compute Publisher ID."""
import base64, hashlib, re, ctypes, ctypes.wintypes

# Read signatures.xml
with open(r"D:\Users\Administrator\Desktop\文墨天机\META-INF\signatures.xml", "rb") as f:
    sig_xml = f.read()

# Extract X.509 certificate (strip whitespace between XML tags)
cert_b64 = re.findall(rb'<X509Certificate>([\s\S]+?)</X509Certificate>', sig_xml)[0]
cert_b64 = re.sub(rb'\s+', b'', cert_b64)
cert_der = base64.b64decode(cert_b64)
print(f"Certificate DER: {len(cert_der)} bytes")
sha1_cert  = hashlib.sha1(cert_der).digest()
sha256_cert = hashlib.sha256(cert_der).digest()
print(f"SHA-1:   {sha1_cert.hex()}")
print(f"SHA-256: {sha256_cert.hex()}")

# Adobe AIR Publisher ID: base64url of SHA1 of DER cert (no padding)
publisher_id = base64.urlsafe_b64encode(sha1_cert).decode().rstrip('=')
print(f"Publisher ID: {publisher_id}")

# --- DPAPI decrypt helper ---
class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]
crypt32  = ctypes.WinDLL('Crypt32.dll',  use_last_error=True)
kernel32 = ctypes.WinDLL('Kernel32.dll', use_last_error=True)

def dpapi_unprotect(data: bytes, entropy: bytes = b"") -> bytes | None:
    ptr_in = (ctypes.c_ubyte * len(data))(*data)
    blob_in = DATA_BLOB(len(data), ptr_in)
    if entropy:
        ptr_ent = (ctypes.c_ubyte * len(entropy))(*entropy)
        blob_ent = DATA_BLOB(len(entropy), ptr_ent)
        ent_ptr = ctypes.byref(blob_ent)
    else:
        ent_ptr = None
    blob_out = DATA_BLOB()
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), None, ent_ptr, None, None, 0, ctypes.byref(blob_out))
    if ok:
        result = bytes(blob_out.pbData[:blob_out.cbData])
        kernel32.LocalFree(blob_out.pbData)
        return result
    return None

with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatak", "rb") as f:
    kblob = f.read()

# Key entropy candidates
entropies = {
    "sha1_cert (20 bytes)": sha1_cert,
    "sha256_cert (32 bytes)": sha256_cert,
    "publisher_id_ascii": publisher_id.encode('ascii'),
    "publisher_id_nullterm": publisher_id.encode('ascii') + b'\x00',
    "sha1_hex_upper": sha1_cert.hex().upper().encode(),
    "sha1_hex_lower": sha1_cert.hex().lower().encode(),
    "ZiWeiDesktop_sha1": (b"ZiWeiDesktop" + sha1_cert),
    "sha1 + ZiWeiDesktop": (sha1_cert + b"ZiWeiDesktop"),
    "publisherID:ZiWeiDesktop": (publisher_id + ":ZiWeiDesktop").encode(),
    "empty": b"",
}

print("\n=== DPAPI attempts ===")
for name, ent in entropies.items():
    result = dpapi_unprotect(kblob, ent)
    if result:
        print(f"SUCCESS '{name}': {result.hex()[:64]}")
    else:
        err = ctypes.get_last_error()
        print(f"FAIL    '{name}' err={err}")

# Check ELS index hash
with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatai", "rb") as f:
    idx_data = f.read()
idx_hash = idx_data[4:36]  # first record: 4 + 32 bytes
print(f"\nELS index SHA-256 hash: {idx_hash.hex()}")

# Check if hash = SHA-256 of (key_name) with optional hmac/salt
test_keys = ["mlk_json", "mlk_ver", "mlk_index", "mlk_c", "mlkData", "mlkMaxRowsNum"]
for k in test_keys:
    for enc in ['utf-8', 'utf-16-le']:
        kb = k.encode(enc)
        h1 = hashlib.sha256(kb).digest()
        h2 = hashlib.sha256(publisher_id.encode() + kb).digest()
        h3 = hashlib.sha256(kb + publisher_id.encode()).digest()
        h4 = hashlib.sha256(sha1_cert + kb).digest()
        for label, h in [("sha256", h1), ("sha256(pub+k)", h2), ("sha256(k+pub)", h3), ("sha256(sha1+k)", h4)]:
            if h == idx_hash:
                print(f"\nINDEX HASH MATCH! fn={label} key={k!r} enc={enc}")
