"""Extract X.509 cert from signatures.xml and compute Publisher ID (used as DPAPI entropy)."""
import base64, hashlib, struct
from lxml import etree
import re

# Read signatures.xml
with open(r"D:\Users\Administrator\Desktop\文墨天机\META-INF\signatures.xml", "rb") as f:
    sig_xml = f.read()

# Extract X.509 certificate (strip whitespace between XML tags)
cert_b64 = re.findall(rb'<X509Certificate>([\s\S]+?)</X509Certificate>', sig_xml)[0]
cert_b64 = cert_b64.replace(b' ', b'').replace(b'\n', b'').replace(b'\r', b'').replace(b'\t', b'')
cert_der = base64.b64decode(cert_b64)
print(f"Certificate DER: {len(cert_der)} bytes")
print(f"SHA-1 fingerprint:   {hashlib.sha1(cert_der).hexdigest()}")
print(f"SHA-256 fingerprint: {hashlib.sha256(cert_der).hexdigest()}")
print(f"MD5 fingerprint:     {hashlib.md5(cert_der).hexdigest()}")

# Adobe AIR Publisher ID: SHA1 of the stripped DER, then base64url-encoded
# From AIR SDK source code
sha1_cert = hashlib.sha1(cert_der).digest()
publisher_id = base64.urlsafe_b64encode(sha1_cert).decode().rstrip('=')
print(f"\nPublisher ID (base64url of SHA1): {publisher_id}")
# Microsoft format: strip padding
print(f"Publisher ID (no padding): {publisher_id}")

# Try DPAPI with cert SHA1 as entropy
import ctypes, ctypes.wintypes

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

crypt32  = ctypes.WinDLL('Crypt32.dll',  use_last_error=True)
kernel32 = ctypes.WinDLL('Kernel32.dll', use_last_error=True)

def dpapi_unprotect(data: bytes, entropy: bytes = b"") -> bytes | None:
    ptr_in  = (ctypes.c_ubyte * len(data))(*data)
    blob_in = DATA_BLOB(len(data), ptr_in)
    if entropy:
        ptr_ent  = (ctypes.c_ubyte * len(entropy))(*entropy)
        blob_ent = DATA_BLOB(len(entropy), ptr_ent)
        ent_ptr  = ctypes.byref(blob_ent)
    else:
        ent_ptr = None
    blob_out = DATA_BLOB()
    desc = ctypes.c_wchar_p()
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(blob_in), ctypes.byref(desc), ent_ptr,
        None, None, 0, ctypes.byref(blob_out))
    if ok:
        n = blob_out.cbData
        result = bytes(blob_out.pbData[:n])
        kernel32.LocalFree(blob_out.pbData)
        return result
    return None

with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatak", "rb") as f:
    kblob = f.read()

# Try various certificate-derived entropies
entropies = {
    "sha1_cert": sha1_cert,
    "sha256_cert": hashlib.sha256(cert_der).digest(),
    "publisher_id_utf8": publisher_id.encode('utf-8'),
    "sha1_cert_hex": hashlib.sha1(cert_der).hexdigest().encode('utf-8'),
    "cert_sha1_upper": hashlib.sha1(cert_der).hexdigest().upper().encode('utf-8'),
    "sha1_cert + \\0": sha1_cert + b'\x00',
    "publisher_id_utf8_null": publisher_id.encode('utf-8') + b'\x00',
}

print("\n=== DPAPI decryption attempts ===")
for name, ent in entropies.items():
    result = dpapi_unprotect(kblob, ent)
    if result:
        print(f"SUCCESS with entropy='{name}': {result.hex()}")
    else:
        err = ctypes.get_last_error()
        print(f"FAILED  entropy='{name}' err={err}")

# Also try with the SHA-1 as hex string
# AIR uses the publisher certificate to derive publisherID
# The publisherID is used as the storage directory name in ELS
# Check the actual ELS directory path
import os
els_parent = "C:\\Users\\Administrator\\AppData\\Roaming\\ZiWeiDesktop\\ELS"
print(f"\nELS directory exists: {os.path.exists(els_parent)}")
# In AIR, the ELS directory is at: <appStorageDir>/<appID>/<publisherID>/ELS
# But for older AIR desktop apps, it's just <appStorageDir>
print(f"ELS path: {els_parent}")
print(f"Publisher ID would create path: {els_parent}")

# Also try to see if publisher_id is used as ELS encryption entropy for the data record
# Looking at the sole 32-byte index record
with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatai", "rb") as f:
    idx_data = f.read()[:36]  # First record: 4-byte len + 32 bytes

idx_hash = idx_data[4:36]
print(f"\nELS index hash (32 bytes): {idx_hash.hex()}")

# Check if it's SHA-256 of any known key with publisherID prefix
candidates = [
    ("publisherID + mlk_json", publisher_id.encode() + b"mlk_json"),
    ("mlk_json + publisherID", b"mlk_json" + publisher_id.encode()),
    ("sha1_cert + mlk_json", sha1_cert + b"mlk_json"),
    ("mlk_json", b"mlk_json"),
    ("ZiWeiDesktop + mlk_json", b"ZiWeiDesktop:mlk_json"),
]
for name, data in candidates:
    h = hashlib.sha256(data).digest()
    if h == idx_hash:
        print(f"INDEX HASH MATCH: {name}")
    else:
        print(f"  sha256({name!r}) = {h.hex()[:16]}...")
