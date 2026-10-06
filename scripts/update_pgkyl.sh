#!/usr/bin/env bash
# Update an installed source checkout using the active Python environment.
set -euo pipefail

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ROOT_DIR=$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)
GKEYLL_DIR="${ROOT_DIR}/gkeyll"
PYTHON="${PYTHON:-python}"

INSTALL_OPTIONS=()
if [[ "$#" -eq 1 && "$1" == "--editable" ]]; then
    INSTALL_OPTIONS+=(--editable)
elif [[ "$#" -ne 0 ]]; then
    echo "usage: $0 [--editable]" >&2
    exit 2
fi

if [[ ! -e "${GKEYLL_DIR}/.git" ]]; then
    echo "error: gkeyll/ is missing; install Postgkyl from source first (see README.md)" >&2
    exit 1
fi
if ! git -C "${GKEYLL_DIR}" diff --quiet || \
   ! git -C "${GKEYLL_DIR}" diff --cached --quiet; then
    echo "error: gkeyll/ has tracked modifications; commit or stash them before updating" >&2
    exit 1
fi

echo "# Updating Postgkyl from the current branch's upstream"
git -C "${ROOT_DIR}" pull --ff-only

# Fetch explicitly; ordinary installs only build the existing producer.
sh "${SCRIPT_DIR}/update_gkeyll.sh"
echo "# Rebuilding Gkeyll and gpython, and reinstalling Postgkyl"
POSTGKYL_SKIP_GKEYLL_BUILD=0 "${PYTHON}" -m pip install \
    ${INSTALL_OPTIONS[@]+"${INSTALL_OPTIONS[@]}"} "${ROOT_DIR}"
"${PYTHON}" -c 'from postgkyl import gpython; gpython.require()'
echo "# Postgkyl update complete"
