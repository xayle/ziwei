"""Compare PrivateEncryptedDatak with mlk inner data."""
import lzma

# Read mlk inner data
with open(r"d:\Users\Administrator\Desktop\文墨天机\文墨天机命例库_2026-5-23-16-42-51.mlk", "rb") as f:
    raw_file = f.read()
dec = lzma.decompress(raw_file, format=lzma.FORMAT_ALONE)
mlk_inner = bytes.fromhex(dec.decode("ascii").strip())

# Read PrivateEncryptedDatak
try:
    with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatak", "rb") as f:
        pek = f.read()
    print(f"PrivateEncryptedDatak: {len(pek)} bytes")
    print(f"First 32 hex: {pek[:32].hex()}")
    print(f"MLK inner data: {len(mlk_inner)} bytes")
    print(f"First 32 hex: {mlk_inner[:32].hex()}")
    print(f"\nIdentical: {pek == mlk_inner}")

    # If different, check XOR difference
    if pek != mlk_inner and len(pek) == len(mlk_inner):
        xor = bytes(a ^ b for a, b in zip(pek, mlk_inner))
        print(f"XOR first 32: {xor[:32].hex()}")
except PermissionError as e:
    print(f"Permission denied: {e}")
    print("Trying alternative approach...")

# Read PrivateEncryptedDatav (should be IV = 12 bytes)
try:
    with open(r"C:\Users\Administrator\AppData\Roaming\ZiWeiDesktop\ELS\PrivateEncryptedDatav", "rb") as f:
        pev = f.read()
    print(f"\nPrivateEncryptedDatav: {len(pev)} bytes = {pev.hex()}")
except PermissionError as e:
    print(f"PrivateEncryptedDatav permission denied: {e}")

# Try decrypting ELS via DPAPI + AES
# First try to read the DPAPI-protected key
import ctypes
import ctypes.wintypes

class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

def dpapi_decrypt(data: bytes, entropy: bytes = None):
    """Decrypt data using Windows DPAPI."""
    crypt32 = ctypes.WinDLL('Crypt32.dll')
    kernel32 = ctypes.WinDLL('Kernel32.dll')

    data_in = DATA_BLOB(len(data), (ctypes.c_ubyte * len(data))(*data))
    data_out = DATA_BLOB()

    if entropy:
        ent = DATA_BLOB(len(entropy), (ctypes.c_ubyte * len(entropy))(*entropy))
        ent_ptr = ctypes.byref(ent)
    else:
        ent_ptr = None

    ok = crypt32.CryptUnprotectData(
        ctypes.byref(data_in),
        None, ent_ptr, None, None, 0,
        ctypes.byref(data_out)
    )
    if ok:
        result = bytes((ctypes.c_ubyte * data_out.cbData).from_address(data_out.pbData._obj.value))
        kernel32.LocalFree(data_out.pbData)
        return result
    else:
        err = ctypes.get_last_error()
        return None, err

# Try to read PrivateEncryptedDatak via elevated PS
import subprocess
result = subprocess.run(
    ['powershell', '-Command',
     '[System.Convert]::ToBase64String([System.IO.File]::ReadAllBytes("C:\\Users\\Administrator\\AppData\\Roaming\\ZiWeiDesktop\\ELS\\PrivateEncryptedDatak"))'],
    capture_output=True, text=True
)
if result.returncode == 0 and result.stdout.strip():
    import base64
    pek_data = base64.b64decode(result.stdout.strip())
    print(f"\nPrivateEncryptedDatak read via PS: {len(pek_data)} bytes")
    print(f"First 32: {pek_data[:32].hex()}")

    # Try DPAPI decrypt with no entropy
    print("\nTrying DPAPI decrypt (no entropy)...")
    decrypted = dpapi_decrypt(pek_data)
    if isinstance(decrypted, bytes):
        print(f"Decrypted key: {decrypted.hex()}")
    else:
        print(f"Failed, error: {decrypted}")

    # Try common AIR entropies
    entropies = [
        b"ZiWeiDesktop",
        b"com.ziwei001.mlk-file",
        b"ziwei001.cn",
        b"WenMoTianJi",
        b"E5A2D037C91F4B40A96008B19715A60F",  # from SWF class name
    ]
    for ent in entropies:
        result2 = dpapi_decrypt(pek_data, ent)
        if isinstance(result2, bytes):
            print(f"Decrypted with entropy {ent!r}: {result2.hex()}")
            break
else:
    print(f"PS read failed: {result.returncode} {result.stderr[:200]}")
