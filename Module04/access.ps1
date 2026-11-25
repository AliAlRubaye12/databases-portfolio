# Task 4: access control without a server (Windows / PowerShell version of the workbook's chmod steps).
# Run from the repo root with:  powershell -ExecutionPolicy Bypass -File Module04/access.ps1
# On Linux/macOS the file-level steps are `chmod 444 Module04/edge.db` and `chmod 644 Module04/edge.db`.
$db = 'Module04/edge.db'

'== 1. a view exposes a safe subset to report readers'
sqlite3 $db "DROP VIEW IF EXISTS machine_health; CREATE VIEW machine_health AS
  SELECT s.machine_id, s.metric, MAX(r.value) AS peak, COUNT(*) AS n
  FROM sensor s JOIN reading r USING(sensor_id) GROUP BY s.machine_id, s.metric;"
sqlite3 -header -column $db "SELECT * FROM machine_health;"

''
'== 2. read-only at the file level (Windows read-only attribute = chmod 444)'
Set-ItemProperty $db -Name IsReadOnly -Value $true
"IsReadOnly: $((Get-Item $db).IsReadOnly)"
'-- reading still works:'
sqlite3 $db "SELECT COUNT(*) AS readings FROM reading;"
'-- writing must fail:'
sqlite3 $db "DELETE FROM reading;" 2>&1 | ForEach-Object { "$_" }

''
'== 3. read-only at the connection level (file is writable again)'
Set-ItemProperty $db -Name IsReadOnly -Value $false
sqlite3 "file:$($db)?mode=ro" "SELECT COUNT(*) AS readings FROM reading;"
'-- mode=ro: writing must fail:'
sqlite3 "file:$($db)?mode=ro" "DELETE FROM reading;" 2>&1 | ForEach-Object { "$_" }
'-- PRAGMA query_only: the connection refuses writes too:'
sqlite3 $db "PRAGMA query_only = ON; DELETE FROM reading;" 2>&1 | ForEach-Object { "$_" }

''
'== 4. write access restored for further work'
"IsReadOnly: $((Get-Item $db).IsReadOnly)"
sqlite3 $db "SELECT COUNT(*) AS readings_still_there FROM reading;"
