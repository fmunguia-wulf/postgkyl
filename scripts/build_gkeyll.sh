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

CC="${CC:-cc}"

# gkeyll's own ./configure defaults ARCH_FLAGS to `-march=native`, baking
# in whatever ISA extensions the BUILD machine happens to expose. On
# x86_64 that can select AVX-512 codegen, and GCC (verified on 13 and 14,
# independent of -O level or -ffast-math -- clang is unaffected) has a real
# auto-vectorization bug that silently miscomputes at least one Gkeyll DG
# kernel (ker/bin_op/binop_cross_mul_*_gkhyb_p1.c) when targeting AVX-512.
# Because CI runners (and contributors' own machines) are whatever hardware
# they happen to be, `-march=native` turns this into a silent,
# host-dependent correctness bug rather than a build failure: some hosts
# expose AVX-512 and miscompile, others don't and are fine -- indistinguishable
# from flakiness.
#
# Fix: pin to a portable, standardized microarchitecture level instead of
# auto-detecting. `x86-64-v3` (AVX2 + FMA + BMI2, no AVX-512) is universally
# available on any x86_64 CPU from the last decade-plus, avoids the buggy
# code path entirely on every compiler, and -- unlike `-march=native` --
# produces the same binary regardless of which machine builds it. There is
# no equivalent portable-level spec on other architectures and no evidence
# of an equivalent bug there, so non-x86_64 hosts are left on the
# compiler's own default (empty ARCH_FLAGS) rather than guessing.
#
# Anyone who wants maximum-performance native codegen (and accepts the
# tradeoff) can still get it with `ARCH_FLAGS=-march=native ./setup.py ...`
# or `ARCH_FLAGS=-march=native scripts/build_gkeyll.sh` -- this default only
# applies when the caller hasn't set ARCH_FLAGS themselves.
if [ -z "${ARCH_FLAGS+set}" ]; then
    case "$(uname -m)" in
        x86_64|amd64)
            ARCH_FLAGS="-march=x86-64-v3"
            ;;
        *)
            ARCH_FLAGS=""
            ;;
    esac
fi

echo "# Configuring gkeyll core (CC=${CC}, ARCH_FLAGS=${ARCH_FLAGS:-<compiler default>}, lapack-lite, app=core)"
(cd "${GKEYLL_DIR}" && ./configure "CC=${CC}" "ARCH_FLAGS=${ARCH_FLAGS}" --use-lapack-lite=yes --app=core)

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
