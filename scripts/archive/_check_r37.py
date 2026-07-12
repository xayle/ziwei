"""R37 check: no bare f-string SQL"""
import os, re

roots = ['app','routers','services']
# Pattern: f-string that contains SQL keywords followed by something that looks like a SQL query
sql_pattern = re.compile(
    r'f["\'].*?\b(SELECT\s+\w|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM|DROP\s+TABLE|TRUNCATE\b)',
    re.IGNORECASE
)
found = []
for root in roots:
    rootpath = os.path.join(r'd:\Users\Administrator\Desktop\c1', root)
    if not os.path.isdir(rootpath):
        continue
    for dirpath, _, files in os.walk(rootpath):
        for fname in files:
            if not fname.endswith('.py'):
                continue
            path = os.path.join(dirpath, fname)
            with open(path, encoding='utf-8', errors='ignore') as fp:
                for i, line in enumerate(fp, 1):
                    if sql_pattern.search(line):
                        found.append(f'{path}:{i}: {line.strip()}')

if found:
    print('R37 FAIL: bare f-string SQL found:')
    for x in found:
        print('  ', x)
else:
    print('R37 PASS: no bare f-string SQL found')
