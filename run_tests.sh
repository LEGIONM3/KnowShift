#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  run_tests.sh — KnowShift Phase 5 Test Runner
#  Usage:
#    bash run_tests.sh            → unit + integration (default)
#    bash run_tests.sh all        → unit + integration + e2e
#    bash run_tests.sh unit       → unit only
#    bash run_tests.sh demo       → demo validation only
#    bash run_tests.sh perf       → performance benchmarks only
#    bash run_tests.sh frontend   → Vitest frontend suite
# ─────────────────────────────────────────────────────────────────

set -euo pipefail
cd "$(dirname "$0")"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

MODE="${1:-default}"
BACKEND_DIR="knowshift-backend"
FRONTEND_DIR="knowshift-frontend"
TEST_API_URL="${TEST_API_URL:-http://localhost:8000}"

printf "\n${BOLD}${CYAN}╔══════════════════════════════════════════╗${RESET}\n"
printf "${BOLD}${CYAN}║       KnowShift Test Runner v1.0         ║${RESET}\n"
printf "${BOLD}${CYAN}╚══════════════════════════════════════════╝${RESET}\n"
printf "Mode: ${BOLD}%s${RESET}  |  API: ${BOLD}%s${RESET}\n\n" "$MODE" "$TEST_API_URL"

# ─── Helper ──────────────────────────────────────────────────────
run_backend() {
  local label="$1"; shift
  printf "${BOLD}${CYAN}▶ %s${RESET}\n" "$label"
  cd "$BACKEND_DIR"
  if python -m pytest "$@"; then
    printf "${GREEN}✅ %s passed${RESET}\n\n" "$label"
  else
    printf "${RED}❌ %s failed${RESET}\n\n" "$label"
    cd ..
    exit 1
  fi
  cd ..
}

# ─── Modes ───────────────────────────────────────────────────────
case "$MODE" in

  unit)
    run_backend "Unit Tests" tests/unit/ -v --tb=short -m unit

    ;;

  integration)
    run_backend "Integration Tests" tests/integration/ -v --tb=short -m integration

    ;;

  default)
    run_backend "Unit Tests"        tests/unit/        -v --tb=short -m unit
    run_backend "Integration Tests" tests/integration/ -v --tb=short -m integration

    ;;

  all)
    run_backend "Unit Tests"        tests/unit/        -v --tb=short -m unit
    run_backend "Integration Tests" tests/integration/ -v --tb=short -m integration
    run_backend "E2E Tests"         tests/e2e/         -v --tb=short -m e2e --timeout=120 \
      -x  # stop on first failure for E2E

    ;;

  demo)
    printf "${YELLOW}⚠  Make sure the API is running at %s${RESET}\n\n" "$TEST_API_URL"
    run_backend "Demo Validation" tests/demo/ -v -s --tb=short -m demo --timeout=120

    ;;

  perf)
    printf "${YELLOW}⚠  Performance tests take several minutes${RESET}\n\n"
    run_backend "Performance Benchmarks" tests/performance/ -v -s --tb=short -m performance --timeout=180

    ;;

  frontend)
    printf "${BOLD}${CYAN}▶ Frontend Tests (Vitest)${RESET}\n"
    cd "$FRONTEND_DIR"
    if npm run test:run; then
      printf "${GREEN}✅ Frontend tests passed${RESET}\n\n"
    else
      printf "${RED}❌ Frontend tests failed${RESET}\n\n"
      exit 1
    fi
    cd ..

    ;;

  coverage)
    printf "${BOLD}${CYAN}▶ Full Coverage Report${RESET}\n"
    cd "$BACKEND_DIR"
    python -m pytest tests/unit/ tests/integration/ \
      -m "unit or integration" \
      --cov=app \
      --cov-report=html:coverage_report \
      --cov-report=term-missing \
      --cov-fail-under=60 \
      -q
    cd ..
    printf "${GREEN}✅ Coverage report: %s/coverage_report/index.html${RESET}\n" "$BACKEND_DIR"

    ;;

  *)
    printf "${RED}Unknown mode: %s${RESET}\n" "$MODE"
    printf "Valid modes: unit, integration, default, all, demo, perf, frontend, coverage\n"
    exit 1
    ;;

esac

printf "${BOLD}${GREEN}✅ All selected tests passed!${RESET}\n\n"
