# Start Genesis: the local server in one window, the companion (Eve or Adam) in another.
#   .\start.ps1             carry on in the existing world
#   .\start.ps1 -NewWorld   start again from the darkness (the old world is deleted)
#   .\start.ps1 -Text       type to the companion instead of talking
param([switch]$NewWorld, [switch]$Text)

$root = $PSScriptRoot
$python = "D:\voice-assistant\.venv\Scripts\python.exe"

$serverArgs = @("-NoExit", "-ExecutionPolicy", "Bypass", "-File", "$root\tools\server.ps1")
if ($NewWorld) {
    $serverArgs += "-NewWorld"
    Remove-Item "$root\companion\state.json" -ErrorAction SilentlyContinue -Confirm:$false
}
Start-Process powershell -ArgumentList $serverArgs

Write-Host "Waiting for the server..."
do { Start-Sleep -Seconds 2; & $python -I "$root\tools\rcon.py" "list" 2>$null | Out-Null } until ($LASTEXITCODE -eq 0)

$bridgeArgs = @("-NoExit", "-Command", "& '$python' '$root\companion\bridge.py'" + $(if ($Text) { " --text" } else { "" }))
Start-Process powershell -ArgumentList $bridgeArgs

Write-Host ""
Write-Host "Ready. In the Minecraft launcher choose the 'Genesis VR' profile and press Play,"
Write-Host "then Multiplayer -> Genesis. Stand on the gold stone to be Adam or the diamond stone to be Eve."
