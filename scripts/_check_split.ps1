Set-Location 'd:\Users\Administrator\Desktop\c2'
foreach ($n in @('constants','render','export-cases','compat','glossary','charts-svg','panels-review','panels-tools')) {
  $l = [System.IO.File]::ReadAllLines("static\js\ziwei\$n.js")
  $first = if ($l[0].Length -gt 70) { $l[0].Substring(0,70) } else { $l[0] }
  $last  = if ($l[-1].Length -gt 70) { $l[-1].Substring(0,70) } else { $l[-1] }
  Write-Host "[$n  $($l.Count)L]"
  Write-Host "  FIRST: $first"
  Write-Host "  LAST : $last"
}
