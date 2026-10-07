$ErrorActionPreference='Stop'
Set-ExecutionPolicy -Scope Process Bypass -Force
& (Join-Path $PSScriptRoot 'scripts\run-local.ps1')
