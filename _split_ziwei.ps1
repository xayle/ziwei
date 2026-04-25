$src = [System.IO.File]::ReadAllLines("d:\Users\Administrator\Desktop\c2\static\js\ziwei\main.js")
$out = "d:\Users\Administrator\Desktop\c2\static\js\ziwei"
$splits = @(
  @{from=1;   to=97;   name="constants"},
  @{from=98;  to=754;  name="render"},
  @{from=755; to=1229; name="export-cases"},
  @{from=1230;to=1571; name="compat"},
  @{from=1572;to=1822; name="glossary"},
  @{from=1823;to=2097; name="charts-svg"},
  @{from=2098;to=2766; name="panels-review"},
  @{from=2767;to=4346; name="panels-tools"}
)
foreach ($s in $splits) {
  $lines = $src[($s.from - 1)..($s.to - 1)]
  [System.IO.File]::WriteAllLines("$out\$($s.name).js", $lines, [System.Text.Encoding]::UTF8)
  Write-Host "OK: $($s.name).js  =>  $($lines.Count) lines"
}
Write-Host "Done."
