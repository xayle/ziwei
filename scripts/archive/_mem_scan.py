"""
在进程内存中搜索解密后的mlk数据。
用法: python _mem_scan.py <pid_or_auto>
"""
import ctypes
import ctypes.wintypes
import sys
import struct
import json
import re
import subprocess
import time
import os

# Windows API constants
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_READABLE = 0x02 | 0x04 | 0x20 | 0x40  # READONLY | READWRITE | EXECUTE_READ | EXECUTE_READWRITE

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.wintypes.DWORD),
        ("Protect", ctypes.wintypes.DWORD),
        ("Type", ctypes.wintypes.DWORD),
    ]

def find_pid(name_fragment):
    """Find PID by process name fragment."""
    import subprocess
    result = subprocess.run(
        ['tasklist', '/FO', 'CSV', '/NH'],
        capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        parts = line.strip('"').split('","')
        if len(parts) >= 2 and name_fragment.lower() in parts[0].lower():
            try:
                return int(parts[1])
            except:
                pass
    return None

def scan_process_memory(pid, patterns):
    """Scan process memory for patterns."""
    handle = kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid
    )
    if not handle:
        print(f"OpenProcess failed: {ctypes.get_last_error()}")
        return []

    results = []
    address = 0
    mbi = MEMORY_BASIC_INFORMATION()

    while True:
        ret = kernel32.VirtualQueryEx(
            handle, ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi)
        )
        if not ret:
            break

        if (mbi.State == MEM_COMMIT and
            mbi.Protect & PAGE_READABLE and
            mbi.Protect != 0x100 and  # not GUARD
            mbi.RegionSize > 0):

            buf = ctypes.create_string_buffer(mbi.RegionSize)
            bytes_read = ctypes.c_size_t(0)
            ok = kernel32.ReadProcessMemory(
                handle, ctypes.c_void_p(mbi.BaseAddress),
                buf, mbi.RegionSize, ctypes.byref(bytes_read)
            )
            if ok and bytes_read.value > 0:
                data = buf.raw[:bytes_read.value]
                for pat in patterns:
                    pat_bytes = pat.encode('utf-8') if isinstance(pat, str) else pat
                    idx = 0
                    while True:
                        pos = data.find(pat_bytes, idx)
                        if pos == -1:
                            break
                        # Extract surrounding context
                        start = max(0, pos - 50)
                        end = min(len(data), pos + 500)
                        ctx = data[start:end]
                        results.append({
                            'addr': hex(mbi.BaseAddress + pos),
                            'pattern': pat if isinstance(pat, str) else pat.decode(errors='replace'),
                            'context': ctx
                        })
                        idx = pos + 1

        # Advance to next region
        next_addr = (mbi.BaseAddress or 0) + mbi.RegionSize
        if next_addr <= address:
            break
        address = next_addr

    kernel32.CloseHandle(handle)
    return results

if __name__ == '__main__':
    # Find the ZiWei desktop app
    pid = find_pid('文墨天机')
    if not pid:
        pid = find_pid('adl.exe')
    if not pid:
        pid = find_pid('ZiWeiDesktop')

    if not pid:
        print("App not running. Starting it now...")
        proc = subprocess.Popen(
            [r'D:\Users\Administrator\Desktop\文墨天机\文墨天机.exe'],
            shell=True
        )
        time.sleep(8)  # Wait for app to load
        pid = find_pid('adl')
        if not pid:
            pid = find_pid('文墨天机')
        if not pid:
            # search all processes
            result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True)
            print("Running processes:")
            for line in result.stdout.splitlines()[:30]:
                print(line)
            sys.exit(1)

    print(f"Scanning PID: {pid}")

    patterns = [
        'mlk_json',
        'mlk_ver',
        '|$|',
        '"cases"',
        '"birth"',
        '"name"',
        '"sex"',
        '"gl"',
        '"nl"',
        'birth_raw',
        'solar_time',
    ]

    print("Scanning memory... (this may take a minute)")
    results = scan_process_memory(pid, patterns)

    if not results:
        print("No matches found")
    else:
        print(f"Found {len(results)} matches")
        seen_contexts = set()
        for r in results:
            ctx_str = r['context'][:100].hex()
            if ctx_str not in seen_contexts:
                seen_contexts.add(ctx_str)
                print(f"\n=== Pattern: {r['pattern']!r} @ {r['addr']} ===")
                # Try to decode as UTF-8 or UTF-16
                for encoding in ['utf-8', 'utf-16-le', 'utf-16-be']:
                    try:
                        decoded = r['context'].decode(encoding, errors='replace')
                        # Show only printable range
                        printable = ''.join(c if ord(c) > 31 and ord(c) < 127 else '.' for c in decoded)
                        if printable.count('.') / len(printable) < 0.5:
                            print(f"  [{encoding}]: {printable[:200]}")
                    except:
                        pass
