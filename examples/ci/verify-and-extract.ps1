param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Archive,
    [Parameter(Position = 1)]
    [string]$Output = "extracted",
    [Parameter(Position = 2)]
    [ValidateSet("ok", "low", "medium", "high", "critical")]
    [string]$MaxRisk = "low"
)

$ErrorActionPreference = "Stop"

function Invoke-Pagonic {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    & pagonic @Arguments
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Invoke-Pagonic @("verify", $Archive, "--max-risk", $MaxRisk)
Invoke-Pagonic @("safe-extract", $Archive, $Output, "--allow-risk", $MaxRisk, "--dry-run")
Invoke-Pagonic @("safe-extract", $Archive, $Output, "--allow-risk", $MaxRisk)
