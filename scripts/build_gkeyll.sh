#!/bin/sh
# Build the existing producer checkout, obtaining it only when absent.
# Local edits are built as-is; updating upstream is a separate operation.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)
GKEYLL_DIR="${ROOT_DIR}/gkeyll"
if [ ! -e "${GKEYLL_DIR}/.git" ]; then
    sh "${SCRIPT_DIR}/update_gkeyll.sh"
fi

CC="${CC:-cc}"
echo "# Configuring gkeyll core (CC=${CC}, lapack-lite, app=core)"
(cd "${GKEYLL_DIR}" && ./configure "CC=${CC}" --use-lapack-lite=yes --app=core)

ARCH_FLAGS="${ARCH_FLAGS:-}"
export ARCH_FLAGS

echo "# Building libg0core.so (ARCH_FLAGS=${ARCH_FLAGS:-<none -- compiler default>})"
if [ -z "${BUILD_JOBS:-}" ]; then
    BUILD_JOBS=$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2)
    BUILD_JOBS=$((BUILD_JOBS > 1 ? BUILD_JOBS / 2 : 1))
fi
(cd "${GKEYLL_DIR}" && make core "ARCH_FLAGS=${ARCH_FLAGS}" \
    -j"${BUILD_JOBS}")

SO_PATH="${GKEYLL_DIR}/build/core/libg0core.so"
if [ ! -f "${SO_PATH}" ]; then
    echo "error: expected ${SO_PATH} after build, but it is missing" >&2
    exit 1
fi
echo "# Built ${SO_PATH}"
