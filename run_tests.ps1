# PowerShell Test Runner for KnowShift (Windows)
# Usage:
#   .\run_tests.ps1               -> unit + integration (default)
#   .\run_tests.ps1 unit
#   .\run_tests.ps1 integration
#   .\run_tests.ps1 all
#   .\run_tests.ps1 demo
#   .\run_tests.ps1 perf
#   .\run_tests.ps1 frontend
#   .\run_tests.ps1 coverage

param(
    [string]$Mode = "default"
)

$ErrorActionPreference = "Stop"

$BackendDir  = "knowshift-backend"
$FrontendDir = "knowshift-frontend"
$TestApiUrl  = $env:TEST_API_URL ?? "http://localhost:8000"

function Write-Header {
    Write-Host ""
    Write-Host "╔══════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║       KnowShift Test Runner v1.0         ║" -ForegroundColor Cyan
    Write-Host "╚══════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host "Mode: $Mode  |  API: $TestApiUrl" -ForegroundColor Gray
    Write-Host ""
}

function Run-BackendTests {
    param([string]$Label, [string[]]$Args)
    Write-Host "▶ $Label" -ForegroundColor Cyan
    Push-Location $BackendDir
    try {
        python -m pytest @Args
        if ($LASTEXITCODE -ne 0) { throw "$Label failed (exit code $LASTEXITCODE)" }
        Write-Host "✅ $Label passed" -ForegroundColor Green
    } finally {
        Pop-Location
    }
    Write-Host ""
}

function Run-FrontendTests {
    Write-Host "▶ Frontend Tests (Vitest)" -ForegroundColor Cyan
    Push-Location $FrontendDir
    try {
        npm run test:run
        if ($LASTEXITCODE -ne 0) { throw "Frontend tests failed" }
        Write-Host "✅ Frontend tests passed" -ForegroundColor Green
    } finally {
        Pop-Location
    }
    Write-Host ""
}

Write-Header

switch ($Mode.ToLower()) {

    "unit" {
        Run-BackendTests "Unit Tests" @(
            "tests/unit/", "-v", "--tb=short", "-m", "unit"
        )
    }

    "integration" {
        Run-BackendTests "Integration Tests" @(
            "tests/integration/", "-v", "--tb=short", "-m", "integration"
        )
    }

    "default" {
        Run-BackendTests "Unit Tests" @(
            "tests/unit/", "-v", "--tb=short", "-m", "unit"
        )
        Run-BackendTests "Integration Tests" @(
            "tests/integration/", "-v", "--tb=short", "-m", "integration"
        )
    }

    "all" {
        Run-BackendTests "Unit Tests" @(
            "tests/unit/", "-v", "--tb=short", "-m", "unit"
        )
        Run-BackendTests "Integration Tests" @(
            "tests/integration/", "-v", "--tb=short", "-m", "integration"
        )
        Run-BackendTests "E2E Tests" @(
            "tests/e2e/", "-v", "--tb=short", "-m", "e2e", "--timeout=120"
        )
    }

    "demo" {
        Write-Host "⚠  Ensure API is running at $TestApiUrl" -ForegroundColor Yellow
        $env:TEST_API_URL = $TestApiUrl
        Run-BackendTests "Demo Validation" @(
            "tests/demo/", "-v", "-s", "--tb=short", "-m", "demo", "--timeout=120"
        )
    }

    "perf" {
        Write-Host "⚠  Performance tests take several minutes" -ForegroundColor Yellow
        $env:TEST_API_URL = $TestApiUrl
        Run-BackendTests "Performance Benchmarks" @(
            "tests/performance/", "-v", "-s", "--tb=short", "-m", "performance", "--timeout=180"
        )
    }

    "frontend" {
        Run-FrontendTests
    }

    "coverage" {
        Run-BackendTests "Coverage Report" @(
            "tests/unit/", "tests/integration/",
            "-m", "unit or integration",
            "--cov=app",
            "--cov-report=html:coverage_report",
            "--cov-report=term-missing",
            "--cov-fail-under=60",
            "-q"
        )
        Write-Host "Coverage report: $BackendDir\coverage_report\index.html" -ForegroundColor Green
    }

    default {
        Write-Host "Unknown mode: $Mode" -ForegroundColor Red
        Write-Host "Valid modes: unit, integration, default, all, demo, perf, frontend, coverage"
        exit 1
    }
}

Write-Host "✅ All selected tests passed!" -ForegroundColor Green
