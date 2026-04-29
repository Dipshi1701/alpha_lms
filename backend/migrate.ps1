# ============================================================
# LMS Database Migration Script
# ============================================================
# Run this from the backend/ directory:
#
#   cd backend
#   .\migrate.ps1
#
# Or pass an argument:
#   .\migrate.ps1 upgrade head      <- apply all pending migrations (default)
#   .\migrate.ps1 downgrade -1      <- roll back last migration
#   .\migrate.ps1 current           <- show current migration state
#   .\migrate.ps1 history           <- show all migrations
#   .\migrate.ps1 new "your change" <- auto-generate a new migration file
# ============================================================

param(
    [string]$Command = "upgrade",
    [string]$Arg1    = "head",
    [string]$Arg2    = ""
)

# ── Find Python ───────────────────────────────────────────────
$PY = "py"   # Windows Python Launcher — works on this machine

try {
    $ver = & $PY --version 2>&1
    if ($ver -notmatch "Python") { throw }
} catch {
    Write-Error "Python not found via 'py'. Make sure Python is installed."
    exit 1
}

Write-Host "Using Python: $PY ($( & $PY --version 2>&1 ))" -ForegroundColor Cyan

# ── Install alembic if not present ────────────────────────────
$alembicCheck = & $PY -c "import alembic" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing alembic..." -ForegroundColor Yellow
    & $PY -m pip install alembic==1.13.1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to install alembic."
        exit 1
    }
}

# ── Run the migration command ─────────────────────────────────
if ($Command -eq "new") {
    # Auto-generate a new migration
    $msg = if ($Arg1) { $Arg1 } else { "new migration" }
    Write-Host "Generating new migration: '$msg'" -ForegroundColor Cyan
    & $PY -m alembic revision --autogenerate -m "$msg"
} elseif ($Arg2) {
    Write-Host "Running: alembic $Command $Arg1 $Arg2" -ForegroundColor Cyan
    & $PY -m alembic $Command $Arg1 $Arg2
} elseif ($Arg1) {
    Write-Host "Running: alembic $Command $Arg1" -ForegroundColor Cyan
    & $PY -m alembic $Command $Arg1
} else {
    Write-Host "Running: alembic $Command" -ForegroundColor Cyan
    & $PY -m alembic $Command
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nDone." -ForegroundColor Green
} else {
    Write-Host "`nMigration failed. Check the output above." -ForegroundColor Red
    exit 1
}
