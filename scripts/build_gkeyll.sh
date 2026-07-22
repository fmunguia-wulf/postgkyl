#!/bin/sh
# Fetches (if needed) and builds the vendored Gkeyll `core` app as
# libg0core.so, for the gpython/ layer to bind against. Invoked automatically
# by `pip install`/`pip install -e` via setup.py, and safe to re-run by hand.
#
# gkeyll/ is a plain clone (not a git submodule) tracking branch lapack_lite_shim
# (zero external deps: no MPI/CUDA/SuperLU/Lua, LAPACK replaced by the bundled
# lapack-lite). Only core/ is needed to build libg0core.so, so moments/,
# vlasov/, gyrokinetic/, and pkpm/ (~200MB combined) are excluded via
# sparse-checkout and are never fetched, not merely deleted after the fact.
set -e

REPO_URL="https://github.com/ammarhakim/gkeyll.git"
BRANCH="lapack_lite_shim"
SPARSE_DIRS="core gkeyll install-deps machines"

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)
GKEYLL_DIR="${ROOT_DIR}/gkeyll"

if [ ! -e "${GKEYLL_DIR}/.git" ]; then
    echo "# gkeyll/ not present -- cloning ${BRANCH} (core-only, sparse + blobless)"
    rmdir "${GKEYLL_DIR}" 2>/dev/null || true
    # NOTE: `git clone --sparse <url>` (sparse-checkout init done inside clone
    # itself) hits a bug in some git versions where it passes the repo URL
    # instead of the destination directory to the sparse-checkout init step,
    # failing with "cannot change to '<url>': No such file or directory". So
    # clone plain (--no-checkout defers any file checkout) and initialize
    # sparse-checkout as its own step afterward, same as the "already present"
    # branch below.
    git clone --no-checkout --filter=blob:none --depth 1 \
        -b "${BRANCH}" "${REPO_URL}" "${GKEYLL_DIR}"
    (cd "${GKEYLL_DIR}" && git sparse-checkout init --cone && git sparse-checkout set ${SPARSE_DIRS} && git checkout "${BRANCH}")
else
    echo "# gkeyll/ already present -- ensuring sparse-checkout excludes heavy apps"
    (cd "${GKEYLL_DIR}" && git sparse-checkout init --cone >/dev/null 2>&1 || true
     git -C "${GKEYLL_DIR}" sparse-checkout set ${SPARSE_DIRS})
fi

CC="${CC:-clang}"
echo "# Configuring gkeyll core (CC=${CC}, lapack-lite, app=core)"
(cd "${GKEYLL_DIR}" && ./configure "CC=${CC}" --use-lapack-lite=yes --app=core)

echo "# Building libg0core.so"
(cd "${GKEYLL_DIR}" && make core -j"$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)")

SO_PATH="${GKEYLL_DIR}/build/core/libg0core.so"
if [ ! -f "${SO_PATH}" ]; then
    echo "error: expected ${SO_PATH} after build, but it is missing" >&2
    exit 1
fi
echo "# Built ${SO_PATH}"

# Build the _gpython extension against gkyl_gpython.h + libg0core.so. The
# gpython shim itself (core/zero/gpython.c) was just compiled INTO
# libg0core.so above -- that step is the compile-time contract check
# (GKEYLL_C_SHIM.md).
sh "${SCRIPT_DIR}/build_gpython.sh"
