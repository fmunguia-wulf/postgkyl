"""Generate synthetic .gkyl test files for the postgkyl test suite.

Run directly to regenerate:
    python tests/generate_test_data.py

Called automatically by conftest.py at the start of each pytest session.
Each file encodes polyOrder and basisType in its msgpack metadata block so
GData auto-populates ctx["poly_order"] and ctx["basis_type"] on load.
"""
import struct
from pathlib import Path

import msgpack
import numpy as np

_RNG = np.random.default_rng(42)

# Component counts per basis — mirrors the tables in src/postgkyl/data/dg.py
# serendipity: indexed as [ndim-1][poly_order]   (p=0 → 1 component)
_COMPS_SER = [
    [1, 2, 3, 4, 5],    # 1D
    [1, 4, 8, 12, 17],  # 2D
    [1, 8, 20, 32, 50], # 3D
]
# tensor: indexed as [ndim-1][poly_order-1]   (p starts at 1)
_COMPS_TEN = [
    [2, 3, 4, 5],       # 1D
    [4, 9, 16, 25],     # 2D
    [8, 27, 64, 125],   # 3D
]
# maximal-order: indexed as [ndim-1][poly_order-1]
_COMPS_MAX = [
    [2, 3, 4, 5],       # 1D
    [3, 6, 10, 15],     # 2D
    [4, 10, 20, 35],    # 3D
]

_COMPS = {
    "serendipity":   (_COMPS_SER, lambda p: p),
    "tensor":        (_COMPS_TEN, lambda p: p - 1),
    "maximal-order": (_COMPS_MAX, lambda p: p - 1),
}


def num_comps(basis: str, ndim: int, poly_order: int) -> int:
    table, idx_fn = _COMPS[basis]
    return table[ndim - 1][idx_fn(poly_order)]


def write_gkyl_field(
    path: Path,
    cells: list[int],
    lower: list[float],
    upper: list[float],
    values: np.ndarray,
    poly_order: int,
    basis_type: str,
    time: float = 0.0,
    frame: int = 0,
) -> None:
    """Write a minimal valid .gkyl v1 binary field file with msgpack metadata."""
    ndim = len(cells)
    nc = values.shape[-1]

    meta = msgpack.packb({
        "polyOrder": poly_order,
        "basisType": basis_type,
        "time": time,
        "frame": frame,
    })

    with open(path, "wb") as f:
        # --- version-1 header ---
        f.write(b"gkyl0")
        f.write(struct.pack("<q", 1))           # version
        f.write(struct.pack("<q", 1))           # file_type = 1 (field)
        f.write(struct.pack("<q", len(meta)))   # meta_size
        f.write(meta)

        # --- field body ---
        f.write(struct.pack("<q", 2))           # real_type = 2 → float64
        f.write(struct.pack("<q", ndim))
        for c in cells:
            f.write(struct.pack("<q", c))
        for lo in lower:
            f.write(struct.pack("<d", lo))
        for hi in upper:
            f.write(struct.pack("<d", hi))
        esznc = nc * 8                          # element_size * num_comps (bytes)
        size = int(np.prod(cells))              # total number of cells
        f.write(struct.pack("<q", esznc))
        f.write(struct.pack("<q", size))
        f.write(values.astype("<f8").tobytes()) # C-order, little-endian float64


# ---------------------------------------------------------------------------
# Configuration table
# ---------------------------------------------------------------------------

#  (stem, ndim, cells, poly_order, basis_type)
_CONFIGS: list[tuple] = [
    ("1d_ms_p1", 1, [8],       1, "serendipity"),
    ("1d_ms_p2", 1, [8],       2, "serendipity"),
    ("2d_ms_p1", 2, [8, 8],    1, "serendipity"),
    ("2d_ms_p2", 2, [8, 8],    2, "serendipity"),
    ("2d_mt_p1", 2, [8, 8],    1, "tensor"),
    ("2d_mt_p2", 2, [8, 8],    2, "tensor"),
    ("2d_mo_p1", 2, [8, 8],    1, "maximal-order"),
    ("2d_mo_p2", 2, [8, 8],    2, "maximal-order"),
    ("3d_ms_p1", 3, [4, 4, 4], 1, "serendipity"),
]


def generate_all(out_dir: Path | str) -> None:
    """Write all synthetic test files to *out_dir*."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for stem, ndim, cells, poly_order, basis_type in _CONFIGS:
        nc = num_comps(basis_type, ndim, poly_order)
        lower = [0.0] * ndim
        upper = [1.0] * ndim
        values = _RNG.standard_normal((*cells, nc))
        write_gkyl_field(
            out_dir / f"{stem}.gkyl",
            cells, lower, upper, values,
            poly_order=poly_order,
            basis_type=basis_type,
        )


if __name__ == "__main__":
    out = Path(__file__).parent / "test_data" / "generated"
    generate_all(out)
    files = sorted(out.glob("*.gkyl"))
    print(f"Generated {len(files)} files in {out}:")
    for f in files:
        print(f"  {f.name}")
