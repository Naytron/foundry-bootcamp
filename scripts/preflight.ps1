$ErrorActionPreference = 'Stop'

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3.12 "$PSScriptRoot\preflight.py" @args
} else {
    & python "$PSScriptRoot\preflight.py" @args
}
exit $LASTEXITCODE
