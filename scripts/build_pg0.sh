#!/bin/sh
# Builds the _g0py CPython extension into src/postgkyl/ffi/_g0py.so
# (GKEYLL_C_SHIM.md). The pg0 shim itself lives in the gkeyll repo
# (core/zero/gkyl_pg0.h + core/zero/pg0.c) and is compiled INTO
# libg0core.so by gkeyll's own build — that compile step is the contract
# check: any core API drift fails there, at the producer. This script only
# compiles the extension against gkyl_pg0.h (opaque handles + scalars) and
# links the shim symbols from libg0core.so; a stale header/library pairing
# is caught at import by the PG0_API_VERSION handshake.
#
# Requires a built gkeyll/build/core/libg0core.so (scripts/build_gkeyll.sh,
# which invokes this script as its final step). Safe to re-run by hand.
set -e

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)
GKEYLL_DIR="${ROOT_DIR}/gkeyll"
LIB_DIR="${GKEYLL_DIR}/build/core"
CSRC_DIR="${ROOT_DIR}/src/postgkyl/ffi/csrc"
OUT="${ROOT_DIR}/src/postgkyl/ffi/_g0py.so"

if [ ! -f "${LIB_DIR}/libg0core.so" ]; then
    echo "error: ${LIB_DIR}/libg0core.so not found; run scripts/build_gkeyll.sh first" >&2
    exit 1
fi
if [ ! -f "${GKEYLL_DIR}/core/zero/gkyl_pg0.h" ]; then
    echo "error: gkeyll/core/zero/gkyl_pg0.h not found; this gkeyll tree lacks the pg0 shim" >&2
    exit 1
fi

PYTHON="${PYTHON:-python3}"
PY_INCLUDES=$("${PYTHON}" -c "import sysconfig; print(sysconfig.get_path('include'))")
NUMPY_INCLUDE=$("${PYTHON}" -c "import numpy; print(numpy.get_include())")

CC="${CC:-clang}"
echo "# Building _g0py extension (CC=${CC}) -> ${OUT}"
"${CC}" -O2 -g -fPIC -shared \
    "${CSRC_DIR}/_g0pymodule.c" \
    -I "${GKEYLL_DIR}/core/zero" \
    -I "${PY_INCLUDES}" \
    -I "${NUMPY_INCLUDE}" \
    -L "${LIB_DIR}" -lg0core -Wl,-rpath,"${LIB_DIR}" \
    -o "${OUT}"
echo "# Built ${OUT}"
