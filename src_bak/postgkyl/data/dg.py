import numpy as np
import os.path
import tables

from postgkyl.data.computeDerivativeMatrices import createDerivativeMatrix
from postgkyl.data.computeInterpolationMatrices import createInterpMatrix
from postgkyl.data.mapping import c2p_grid

# from postgkyl.data.recovData import recovC0Fn, recovC1Fn, recovEdFn

path = os.path.dirname(os.path.realpath(__file__))

num_nodesSerendipity = np.array([
    [1, 2, 3, 4, 5],
    [1, 4, 8, 12, 17],
    [1, 8, 20, 32, 50],
    [1, 16, 48, 80, 136],
    [1, 32, 112, 192, 352],
    [1, 64, 256, 448, 880]])

num_nodesMaximal = np.array([
    [2, 3, 4, 5],
    [3, 6, 10, 15],
    [4, 10, 20, 35],
    [5, 15, 35, 70],
    [6, 21, 56, 126],
    [7, 28, 84, 210]])

num_nodesTensor = np.array([
    [2, 3, 4, 5],
    [4, 9, 16, 25],
    [8, 27, 64, 125],
    [16, 81, 256, 625],
    [32, 343, 1024, 3125],
    [64, 729, 4096, 15625]])

num_nodesGkHybrid = np.array([1, 6, 12, 24, 48])
num_nodeshybrid = np.array([1, 6, 12, 24, 48])


def _get_basis_p(num_dim, num_comp):
  basis, poly_order = None, None
  idx = np.argwhere(num_nodesSerendipity[num_dim - 1, :] == num_comp).squeeze()
  if idx.ndim == 0 and idx:
    basis = "serendipity"
    poly_order = idx
  # end
  idx = np.argwhere(num_nodesTensor[num_dim - 1, :] == num_comp).squeeze()
  if idx.ndim == 0 and idx:
    basis = "tensor"
    poly_order = idx + 1
  # end
  if basis is None:
    raise ValueError(
        "Could not infer the basis: got {:d} "
        "component(s) for a {:d}D grid, which matches no supported serendipity "
        "or tensor basis. The mapc2p file likely does not match the dataset "
        "(e.g. a 1D geometry applied to {:d}D data).".format(
            num_comp, num_dim, num_dim)
    )
  # end
  return basis, poly_order

def _getnum_nodes(dim, poly_order, basis_type):
  if basis_type.lower() == "serendipity":
    num_nodes = num_nodesSerendipity[dim - 1, poly_order]
  elif basis_type.lower() == "maximal-order":
    num_nodes = num_nodesMaximal[dim - 1, poly_order - 1]
  elif basis_type.lower() == "tensor":
    num_nodes = num_nodesTensor[dim - 1, poly_order - 1]
  elif basis_type.lower() == "gkhybrid":
    num_nodes = num_nodesGkHybrid[dim - 1]
  elif basis_type.lower() == "hybrid":
    num_nodes = num_nodeshybrid[dim - 1]
  else:
    raise NameError(
        "GInterp: Basis '{:s}' is not supported!\n"
        "Supported basis are currently 'ns' (Nodal Serendipity),"
        " 'ms' (Modal Serendipity), 'mt' (Modal Tensor product),"
        " 'mo' (Modal maximal Order), 'gkhybrid' (Modal GkHybrid),"
        " and 'hybrid' (Modal PKPM hybrid)".format(basis_type)
    )
  # end
  return num_nodes

def get_num_basis(dim, poly_order, basis_type) -> int:
  # Return the number of nodes for a dimensionality, basis type and poly order.
  return _getnum_nodes(dim, poly_order, basis_type)

def _loadInterpMatrix(dim, poly_order, basis_type, interp, read, modal, c2p=False):
  if (interp is not None and read is None) or c2p:
    if interp is None:
      interp = poly_order + 1
    # end
    mat = createInterpMatrix(dim, poly_order, basis_type, interp, modal, c2p)
    return mat
  elif basis_type == "tensor":
    mat = createInterpMatrix(dim, poly_order, "tensor", poly_order + 1, True, c2p)
    return mat
  elif basis_type == "gkhybrid":
    mat = createInterpMatrix(dim, poly_order, "gkhybrid", poly_order + 1, True, c2p)
    return mat
  elif basis_type == "hybrid":
    mat = createInterpMatrix(dim, poly_order, "hybrid", poly_order + 1, True, c2p)
    return mat
  else:
    # Load interpolation matrix from the pre-computed HDF5 file.
    varid = "xformMatrix%i%i" % (dim, poly_order)
    if modal == False and basis_type.lower() == "serendipity":
      fileName = path + "/xformMatricesNodalSerendipity.h5"
    elif modal and basis_type.lower() == "serendipity":
      fileName = path + "/xformMatricesModalSerendipity.h5"

    elif modal and basis_type.lower() == "maximal-order":
      fileName = path + "/xformMatricesModalMaximal.h5"
    else:
      raise NameError(
          "GInterp: Basis {:s} is not supported!\n"
          "Supported basis are currently 'ns' (Nodal Serendipity), "
          "'ms' (Modal Serendipity), and 'mo' (Modal Maximal Order)".format(basis_type)
      )
    # end
    fh = tables.open_file(fileName)
    mat = fh.root.matrices._v_children[varid].read()
    fh.close()
    return mat.transpose()
  # end


def _loadDerivativeMatrix(dim, poly_order, basis_type, interp, read, modal=True):
  if interp is not None and read is None:
    mat = createDerivativeMatrix(dim, poly_order, basis_type, interp, modal)
    return mat
  else:
    interp = poly_order + 1
    mat = createDerivativeMatrix(dim, poly_order, basis_type, interp, modal)
    return mat
  # end


def _makeMesh(num_interp, Xc, xlo=None, xup=None, gridType=None):
  nx = Xc.shape[0] - 1  # expecting nodal mesh
  meshOut = np.zeros(num_interp * nx + 1)
  if gridType is None or gridType == "uniform":
    if xlo is None or xup is None:
      xlo = Xc[0]
      xup = Xc[-1]
    # end
    meshOut = np.linspace(xlo, xup, num_interp*nx + 1)
  elif gridType == "mapped":
    # subdivide every cell in Xc into num_interp cells.
    for i in range(nx):
      dx = (Xc[i + 1] - Xc[i]) / num_interp
      for j in range(num_interp):
        meshOut[i*num_interp + j] = Xc[i] + j*dx
      # end
    # end
    # add the last node.
    dx = (Xc[-1] - Xc[-2]) / num_interp
    meshOut[nx*num_interp] = Xc[nx - 1] + num_interp*dx
  # end
  return meshOut


def _make1Dgrids(num_interp, Xc, num_dims, gridType=None):
  # build a list of 1D arrays, each containing the grid in that dimension.
  gridOut = list()
  if gridType is None or gridType == "uniform":
    gridOut = [_makeMesh(num_interp[d], Xc[d]) for d in range(num_dims)]
  elif gridType == "mapped":
    # back out 1D arrays from Xc.
    for d in range(num_dims):
      currSlices = [0] * num_dims
      currSlices[-1 - d] = np.s_[:]
      gridOut.append(_makeMesh(num_interp[d], Xc[d][tuple(currSlices)], gridType=gridType))
    # end
  # end
  return gridOut


def _interpOnMesh(cMat, qIn, nInterpIn, basis_type, c2p=False):
  numCells = np.array(qIn.shape)
  # last entry is indexing nodes, get rid of it
  numCells = numCells[:-1]
  num_dims = int(len(numCells))
  num_interp = np.array([max(nInterpIn, 2)] * num_dims)
  if basis_type == "gkhybrid":
    # 1x1v, 1x2v, 2x2v, 3x2v cases, with p=2 in the first velocity dim.
    vpardir = (1 if (num_dims == 2 or num_dims == 3)
        else (2 if num_dims == 4 else (3 if num_dims == 5 else 99)))
    num_interp[vpardir] = nInterpIn + 1
  # end
  if basis_type == "hybrid":
    num_interp[-1] = nInterpIn + 1
  # end
  if c2p:
    qOut = np.zeros(numCells*(num_interp - 1) + 1, np.float64)
  else:
    qOut = np.zeros(numCells*num_interp, np.float64)
  # end
  # move the node index from last to the first
  qIn = np.moveaxis(qIn, -1, 0)
  # Main loop
  for n in range(np.prod(num_interp)):
    # https://docs.scipy.org/doc/numpy/reference/generated/numpy.tensordot.html
    temp = np.tensordot(cMat[n, :], qIn, axes=1)
    # decompose n to i,j,k,... indices based on the number of dimensions
    startIdx = np.unravel_index(n, num_interp, order="F")
    # define multi-D qOut slices
    if c2p:
      idxs = [slice(int(startIdx[i]), int(numCells[i]*(num_interp[i] - 1) + startIdx[i]),
                  num_interp[i] - 1)
         for i in range(num_dims)]
    else:
      idxs = [slice(int(startIdx[i]), int(numCells[i]*num_interp[i]), num_interp[i])
          for i in range(num_dims)]
    # end
    qOut[tuple(idxs)] = temp
  # end
  return np.array(qOut)


def interp_c2p_conf_grid(map_data, num_interp=None, read=None) -> list:
  """Interpolate a configuration-space mapping field onto node coordinates.

  ``map_data`` is a coordinate-mapping :class:`GData` whose components pack the
  physical coordinate of every node (one block of DG coefficients per
  dimension). This interpolates each block onto the refined mesh, returning a
  list of ``map_dim`` full N-D node-coordinate arrays. Because every coordinate
  is interpolated over all of the map's dimensions, this supports general
  *curvilinear* maps (e.g. a rotation), not just separable ones.

  ``num_interp`` is the number of interpolation points per cell; when omitted it
  defaults to the mapping basis ``poly_order + 1``. The resulting node count per
  dimension is ``cells * num_interp + 1``, matching a field interpolated at the
  same ``num_interp``.
  """
  map_dim = map_data.get_num_dims()
  blocks = c2p_grid(map_data.get_values(), map_dim)
  num_comp = blocks[0].shape[-1]
  basis, poly_order = _get_basis_p(map_dim, num_comp)
  if num_interp is None:
    num_interp = poly_order + 1
  # end
  cMat = _loadInterpMatrix(map_dim, poly_order, basis, num_interp, read, True, True)
  return [_interpOnMesh(cMat, blocks[d], num_interp + 1, basis, True)
      for d in range(map_dim)]


def interp_c2p_vel_grid(map_data, num_interp=None, read=None) -> list:
  """Interpolate a velocity-space mapping field onto node coordinates.

  ``map_data`` is a velocity coordinate-mapping :class:`GData`; each velocity
  dimension's coordinate is taken to depend only on its own index (a separable
  map), so each is interpolated independently in 1D. Returns a list of
  ``map_dim`` 1D node-coordinate arrays.

  ``num_interp`` may be a scalar (applied to every dimension) or a per-dimension
  sequence; when omitted it defaults to the mapping basis ``poly_order + 1``.
  Per-dimension control matters for hybrid bases, where the parallel-velocity
  direction carries one extra interpolation point.
  """
  raw = map_data.get_values()
  map_dim = map_data.get_num_dims()
  num_comps = raw.shape[-1]
  num_coeff = int(num_comps // map_dim)
  basis, poly_order = _get_basis_p(1, num_coeff)
  coords = []
  for d in range(map_dim):
    if num_interp is None:
      ni = poly_order + 1
    elif np.ndim(num_interp) == 0:
      ni = int(num_interp)
    else:
      ni = int(num_interp[d])
    # end
    idx = [0] * (map_dim + 1)
    idx[d] = slice(None)
    idx[-1] = slice(d * num_coeff, (d + 1) * num_coeff)
    block = raw[tuple(idx)]
    cMat = _loadInterpMatrix(1, poly_order, basis, ni, read, True, True)
    coords.append(_interpOnMesh(cMat, block, ni + 1, basis, True))
  # end
  return coords


class GInterp(object):
  """Postgkyl base class for DG data manipulation.

  This class should not be used on its own! Currently supported
  child classes are:
    - GInterpNodal
    - GInterpModal

  Init Args:
    data (GData): Data to work with
    num_nodes (int): Number of nodes
  """

  def __init__(self, data, num_nodes):
    self.data = data
    self.num_nodes = num_nodes
    self.numEqns = data.get_num_comps() / num_nodes
    self.num_dims = data.get_num_dims()
    self.Xc = data.get_grid()
    self.gridType = data.get_grid_type()

  def _getRawNodal(self, component):
    q = self.data.get_values()
    numEqns = self.numEqns
    shp = [q.shape[i] for i in range(self.num_dims)]
    shp.append(self.num_nodes)
    rawData = np.zeros(shp, np.float64)
    for n in range(self.num_nodes):
      rawData[..., n] = q[..., int(component + n * numEqns)]
    # end
    return rawData

  def _getRawModal(self, component):
    q = self.data.get_values()
    shp = [q.shape[i] for i in range(self.num_dims)]
    shp.append(self.num_nodes)
    rawData = np.zeros(shp, np.float64)
    lo = int(component * self.num_nodes)
    up = int(lo + self.num_nodes)
    rawData = q[..., lo:up]
    return rawData


class GInterpNodal(GInterp):
  """Postgkyl class for nodal DG data manipulation.

  After the initializations, GInterpNodal object provides the
  interpolate and differentiate methods.  These return grid and
  values by default but could be used to directly push the result
  back onto the GData object with the overwrite=True flag.

  Parent: GInterp

  Example:
    import postgkyl
    data = postgkyl.GData('file.h5')
    dg = postgkyl.GInterpNodal(data, 2, 'ns')
    grid, values = dg.interpolate()
  """

  def __init__(self, data, poly_order, basis_type, num_interp=None, read=None):
    """Initialize a nodal DG interpolator.

    Args:
      data (GData): Gkeyll dataset (holding DG basis coefficients) to
        operate on.
      poly_order (int): Order of the polynomial approximation (e.g. 1
        or 2).
      basis_type (str): Short code specifying the nodal basis. The only
        supported value is 'ns' (nodal Serendipity), which is expanded
        internally to 'serendipity'. Any other value is passed through
        unchanged and must already match a name understood by the
        underlying matrix loaders.
      num_interp (int, optional): Number of interpolation points per
        dimension. Defaults to None, in which case poly_order + 1 points
        are used.
      read (optional): When None (the default), interpolation matrices
        are computed on the fly if num_interp is set; otherwise
        pre-computed matrices are read from the bundled HDF5 files. Used
        to force reading of the stored matrices rather than recomputing.
    """
    self.num_dims = data.get_num_dims()
    self.poly_order = poly_order
    self.basis_type = basis_type
    if basis_type == "ns":
      self.basis_type = "serendipity"
    # end

    self.num_interp = num_interp
    self.read = read
    num_nodes = _getnum_nodes(self.num_dims, self.poly_order, self.basis_type)
    GInterp.__init__(self, data, num_nodes)

  def interpolate(self, comp=0, overwrite=False, stack=False):
    """Interpolate nodal DG coefficients onto a finer grid.

    Args:
      comp (int | tuple[int, ...] | slice): Component(s) to interpolate.
        An int selects a single component; a tuple selects the listed
        components; a slice selects components from comp.start up to (but
        not including) comp.stop. Interpolated components are stacked
        along the last axis of the returned values. Defaults to 0.
      overwrite (bool): When True, push the interpolated (grid, values)
        back onto the GData object via data.push and return None. When
        False (the default), return the (grid, values) tuple instead.
      stack (bool): DEPRECATED alias for overwrite. If True, it sets
        overwrite=True and prints a deprecation warning. Defaults to
        False.

    Returns:
      tuple | None: When overwrite (or stack) is False, a (grid, values)
        tuple where grid is a list of 1D numpy arrays (one per
        dimension) and values is the interpolated N-D numpy array.
        Returns None when overwrite is True.
    """
    if stack:
      overwrite = stack
      print("Deprecation warning: The 'stack' parameter is going to be replaced with 'overwrite'")
    # end
    cMat = _loadInterpMatrix(self.num_dims, self.poly_order, self.basis_type,
        self.num_interp, self.read, False)
    if isinstance(comp, int):
      q = self._getRawNodal(comp)
      values = _interpOnMesh(cMat, q, self.num_interp, self.basis_type)[..., np.newaxis]
    elif isinstance(comp, tuple):
      q = self._getRawNodal(comp[0])
      values = _interpOnMesh(cMat, q, self.num_interp, self.basis_type)[..., np.newaxis]
      for c in comp[1:]:
        q = self._getRawNodal(c)
        values = np.append(values,
            _interpOnMesh(cMat, q, self.num_interp, self.basis_type)[..., np.newaxis],
            axis=-1)
      # end
    elif isinstance(comp, slice):
      q = self._getRawNodal(comp.start)
      values = _interpOnMesh(cMat, q, self.num_interp, self.basis_type)[..., np.newaxis]
      for c in range(comp.start + 1, comp.stop):
        q = self._getRawNodal(c)
        values = np.append(
            values,
            _interpOnMesh(cMat, q, self.num_interp, self.basis_type)[..., np.newaxis],
            axis=-1,
        )
      # end
    # end

    num_interp = [int(round(cMat.shape[0] ** (1.0 / self.num_dims)))] * self.num_dims
    grid = _make1Dgrids(num_interp, self.Xc, self.num_dims)
    if overwrite:
      self.data.push(grid, values)
    else:
      return grid, values
    # end

  def differentiate(self, direction, comp=0, overwrite=False, stack=False):
    """Compute the derivative of nodal DG data on a finer grid.

    Args:
      direction (int | None): Index of the axis along which to take the
        derivative. When None, derivatives in all directions are
        computed and stacked.
      comp (int): Component to differentiate. Defaults to 0.
      overwrite (bool): When True, push the resulting (grid, values)
        back onto the GData object via data.push and return None. When
        False (the default), return the (grid, values) tuple instead.
      stack (bool): DEPRECATED alias for overwrite. If True, it sets
        overwrite=True and prints a deprecation warning. Defaults to
        False.

    Returns:
      tuple | None: When overwrite (or stack) is False, a (grid, values)
        tuple where grid is a list of 1D numpy arrays (one per
        dimension) and values is the differentiated N-D numpy array.
        Returns None when overwrite is True.
    """
    if stack:
      overwrite = stack
      print("Deprecation warning: The 'stack' parameter is going to be replaced with 'overwrite'")
    # end
    q = self._getRawNodal(comp)
    cMat = _loadDerivativeMatrix(self.num_dims, self.poly_order, self.basis_type,
        self.num_interp, self.read, False)
    if direction is not None:
      values = (
          _interpOnMesh(cMat[:, :, direction], q, self.num_interp, self.basis_type)
          * 2
          / (self.Xc[direction][1] - self.Xc[direction][0]))
      values = values[..., np.newaxis]
    else:
      values = np.zeros(q.shape, self.num_dims)
      for i in range(self.num_dims):
        values[:, i] = _interpOnMesh(cMat[:, :, i], q, self.num_interp, self.basis_type)
        values[:, i] *= 2 / (self.Xc[i][1] - self.Xc[i][0])
      # end
    # end

    num_interp = [int(round(cMat.shape[0] ** (1.0 / self.num_dims)))] * self.num_dims
    grid = _make1Dgrids(num_interp, self.Xc, self.num_dims)
    if overwrite:
      self.data.push(grid, values)
    else:
      return grid, values
    # end


class GInterpModal(GInterp):
  """Postgkyl class for modal DG data manipulation.

  After the initializations, GInterpModal object provides the
  interpolate and differentiate methods.  These return grid and
  values by default but could be used to directly push the result
  back onto the GData object with the overwrite=True flag.

  Parent: GInterp

  Example:
    import postgkyl
    data = postgkyl.GData('file.bp')
    dg = postgkyl.GInterpModal(data, 2, 'ms')
    grid, values = dg.interpolate()
  """

  def __init__(self, data, poly_order=None, basis_type=None, num_interp=None,
      periodic=False, read=None):
    """Initialize a modal DG interpolator.

    Args:
      data (GData): Gkeyll dataset (holding DG basis coefficients) to
        operate on.
      poly_order (int, optional): Order of the polynomial approximation.
        Defaults to None, in which case the value stored in the file's
        context (data.ctx["poly_order"]) is used; a ValueError is raised
        if neither is available.
      basis_type (str, optional): Short code specifying the modal basis.
        Recognized codes are 'ms' (modal Serendipity), 'mo' (modal
        maximal-order), 'mt' (modal tensor product), 'gkhyb' (modal
        GkHybrid), and 'pkpmhyb' (modal PKPM hybrid); these are expanded
        internally to 'serendipity', 'maximal-order', 'tensor',
        'gkhybrid', and 'hybrid', respectively. Defaults to None, in
        which case data.ctx["basis_type"] is used; a ValueError is
        raised if neither is available. Note: for 1D data a 'hybrid'
        basis is automatically downgraded to 'serendipity'.
      num_interp (int, optional): Number of interpolation points per
        dimension. Defaults to None, in which case poly_order + 1 points
        are used.
      periodic (bool): Whether the domain is periodic. Stored on the
        object and consumed by recovery-style routines. Defaults to
        False.
      read (optional): When None (the default), interpolation matrices
        are computed on the fly if num_interp is set; otherwise
        pre-computed matrices are read from the bundled HDF5 files. Used
        to force reading of the stored matrices rather than recomputing.
    """
    self.num_dims = data.get_num_dims()
    if poly_order is not None:
      self.poly_order = poly_order
    elif data.ctx.get("poly_order"):
      self.poly_order = data.ctx["poly_order"]
    else:
      raise ValueError(
        "GInterpNodal: polynomial order is neither specified nor stored in the output file")
    # end
    if basis_type:
      if basis_type == "ms":
        self.basis_type = "serendipity"
      elif basis_type == "mo":
        self.basis_type = "maximal-order"
      elif basis_type == "mt":
        self.basis_type = "tensor"
      elif basis_type == "gkhyb":
        self.basis_type = "gkhybrid"
      elif basis_type == "pkpmhyb":
        self.basis_type = "hybrid"
      # end
    elif data.ctx.get("basis_type"):
      self.basis_type = data.ctx["basis_type"]
    else:
      raise ValueError(
        "GInterpModal: basis type is neither specified nor stored in the output file")
    # end

    # PKPM hybrid base expects 2+ dimensions with the last one being
    # the parallel velocity. This allows to specify 'pkpmhyb' basis
    # and work with 1x1v and 1x data simulataneously.
    if self.num_dims == 1 and self.basis_type == "hybrid":
      self.basis_type = "serendipity"
    # end

    self.periodic = periodic

    # XXX This was introduced with the c2p but I can't see the importance of the extra
    # condition and seem to unecessarily limit the capabilities. The c2p test cases
    # still seems to produce correct results. -- P.C.
    # if num_interp is not None and self.poly_order > 1:
    if num_interp:
      self.num_interp = num_interp
    else:
      self.num_interp = self.poly_order + 1
    # end
    self.read = read
    num_nodes = _getnum_nodes(self.num_dims, self.poly_order, self.basis_type)
    GInterp.__init__(self, data, num_nodes)

  def interpolate(self, comp=0, overwrite=False, stack=False):
    """Interpolate modal DG coefficients onto a finer nodal grid.

    Builds a uniform refined grid, including the 'gkhybrid'/'hybrid' bases
    that use an extra interpolation point in the relevant velocity direction.
    Coordinate (computational-to-physical) mappings are applied separately,
    after interpolation, via the ``map`` verb.

    Args:
      comp (int | tuple[int, ...] | slice): Component(s) to interpolate.
        An int selects a single component; a tuple selects the listed
        components; a slice selects components from comp.start up to (but
        not including) comp.stop. Interpolated components are stacked
        along the last axis of the returned values. Defaults to 0.
      overwrite (bool): When True, push the interpolated (grid, values)
        back onto the GData object via data.push and return None. When
        False (the default), return the (grid, values) tuple instead.
      stack (bool): DEPRECATED alias for overwrite. If True, it sets
        overwrite=True and prints a deprecation warning. Defaults to
        False.

    Returns:
      tuple | None: When overwrite (or stack) is False, a (grid, values)
        tuple where grid is a list of 1D numpy arrays (one per
        dimension) and values is the interpolated N-D numpy array.
        Returns None when overwrite is True.
    """
    if stack:
      overwrite = stack
      print("Deprecation warning: The 'stack' parameter is going to be replaced with 'overwrite'")
    # end
    cMat = _loadInterpMatrix(self.num_dims, self.poly_order, self.basis_type,
        self.num_interp, self.read, True)
    if isinstance(comp, int):
      q = self._getRawModal(comp)
      values = _interpOnMesh(cMat, q, self.num_interp, self.basis_type)[..., np.newaxis]
    elif isinstance(comp, tuple):
      q = self._getRawModal(comp[0])
      values = _interpOnMesh(cMat, q, self.num_interp, self.basis_type)[..., np.newaxis]
      for c in comp[1:]:
        q = self._getRawModal(c)
        values = np.append(values,
            _interpOnMesh(cMat, q, self.num_interp, self.basis_type)[..., np.newaxis],
            axis=-1)
      # end
    elif isinstance(comp, slice):
      q = self._getRawModal(comp.start)
      values = _interpOnMesh(cMat, q, self.num_interp, self.basis_type)[..., np.newaxis]
      for c in range(comp.start + 1, comp.stop):
        q = self._getRawModal(c)
        values = np.append(values,
            _interpOnMesh(cMat, q, self.num_interp, self.basis_type)[..., np.newaxis],
            axis=-1)
      # end
    # end
    if self.basis_type == "gkhybrid":
      # 1x1v, 1x2v, 2x2v, 3x2v cases, with p=2 in the first velocity dim.
      vpardir = (1 if (self.num_dims == 2 or self.num_dims == 3)
          else (2 if self.num_dims == 4 else (3 if self.num_dims == 5 else 99)))
      num_interp = [self.num_interp] * self.num_dims
      num_interp[vpardir] = self.num_interp + 1
    elif self.basis_type == "hybrid":
      num_interp = [self.num_interp] * self.num_dims
      num_interp[-1] = self.num_interp + 1
    else:
      num_interp = [int(round(cMat.shape[0] ** (1.0 / self.num_dims)))] * self.num_dims
    # end

    grid = _make1Dgrids(num_interp, self.Xc, self.num_dims, None)

    if overwrite:
      self.data.push(grid, values)
    else:
      return grid, values
    # end

  def interpolateGrid(self, overwrite=False):
    """Interpolate only the grid (node coordinates) onto a finer mesh.

    Unlike interpolate, this operates solely on the grid, building a uniform
    refined grid. Coordinate (computational-to-physical) mappings are applied
    separately via the ``map`` verb.

    Args:
      overwrite (bool): When True, set the new grid on the GData object
        via data.set_grid and return None. When False (the default),
        return the computed grid instead.

    Returns:
      list | None: When overwrite is False, the grid as a list of numpy
        arrays (one per dimension). Returns None when overwrite is True.
    """
    num_interp = [self.num_interp] * self.num_dims
    grid = _make1Dgrids(num_interp, self.Xc, self.num_dims, self.gridType)

    if overwrite:
      self.data.set_grid(grid)
    else:
      return grid
    # end

  def differentiate(self, direction=None, comp=0, overwrite=False, stack=False):
    """Compute the derivative of modal DG data on a finer grid.

    Args:
      direction (int | None): Index of the axis along which to take the
        derivative. When None (the default), derivatives in all
        directions are computed and stacked along the last axis.
      comp (int): Component to differentiate. Defaults to 0.
      overwrite (bool): When True, push the resulting (grid, values)
        back onto the GData object via data.push and return None. When
        False (the default), return the (grid, values) tuple instead.
      stack (bool): DEPRECATED alias for overwrite. If True, it sets
        overwrite=True and prints a deprecation warning. Defaults to
        False.

    Returns:
      tuple | None: When overwrite (or stack) is False, a (grid, values)
        tuple where grid is a list of 1D numpy arrays (one per
        dimension) and values is the differentiated N-D numpy array.
        Returns None when overwrite is True.
    """
    if stack:
      overwrite = stack
      print("Deprecation warning: The 'stack' parameter is going to be replaced with 'overwrite'")
    # end
    q = self._getRawModal(comp)
    cMat = _loadDerivativeMatrix(self.num_dims, self.poly_order, self.basis_type,
        self.num_interp, self.read, True)
    if direction is not None:
      values = (_interpOnMesh(cMat[:, :, direction], q, self.num_interp, self.basis_type)*2
          / (self.Xc[direction][1] - self.Xc[direction][0]))
      values = values[..., np.newaxis]
    else:
      values = _interpOnMesh(cMat[..., 0], q, self.num_interp, self.basis_type)
      values /= self.Xc[0][1] - self.Xc[0][0]
      values = values[..., np.newaxis]
      for i in range(1, self.num_dims):
        values = np.append(values,
            _interpOnMesh(cMat[..., i], q, self.num_interp, self.basis_type)[..., np.newaxis],
            axis=self.num_dims)
        values[..., i] *= 2 / (self.Xc[i][1] - self.Xc[i][0])
      # end
    # end

    num_interp = [int(round(cMat.shape[0] ** (1.0 / self.num_dims)))] * self.num_dims
    grid = _make1Dgrids(num_interp, self.Xc, self.num_dims, self.gridType)
    if overwrite:
      self.data.push(grid, values)
    else:
      return grid, values
    # end

  # def recovery(self, comp=0, c1=False, overwrite=False, stack=False):
  #   if stack:
  #     overwrite = stack
  #     print(
  #         "Deprecation warning: The 'stack' parameter is going to be replaced with 'overwrite'"
  #     )
  #   # end
  #   if isinstance(comp, int):
  #     q = self._getRawModal(comp)
  #   else:
  #     raise ValueError("recovery: only 'int' comp implemented so far")
  #   # end
  #   if self.num_dims > 1:
  #     raise ValueError("recovery: only 1D implemented so far")
  #   # end

  #   if self.num_interp is not None:
  #     N = self.num_interp
  #   else:
  #     N = 100
  #   # end

  #   numCells = self.data.get_num_cells()
  #   grid = [
  #       np.linspace(self.Xc[int(d)][0], self.Xc[int(d)][-1], int(numCells * N + 1))
  #       for d in range(self.num_dims)
  #   ]

  #   values = np.zeros(numCells * N)
  #   dx = self.Xc[0][1] - self.Xc[0][0]

  #   xC = np.linspace(-1, 1, N, endpoint=False) * dx / 2
  #   xL = np.linspace(-1, 0, N, endpoint=False) * dx
  #   xR = np.linspace(0, 1, N, endpoint=False) * dx

  #   if self.periodic:
  #     if c1:
  #       values[:N] = recovC1Fn[self.poly_order - 1](xC, q[0], q[-1], q[1], dx)
  #       values[-N:] = recovC1Fn[self.poly_order - 1](xC, q[-1], q[-2], q[0], dx)
  #     else:
  #       values[:N] = recovC0Fn[self.poly_order - 1](xC, q[0], q[-1], q[1], dx)
  #       values[-N:] = recovC0Fn[self.poly_order - 1](xC, q[-1], q[-2], q[0], dx)
  #     # end
  #   else:
  #     values[:N] = recovEdFn[self.poly_order - 1](xL, q[0], q[1], dx)
  #     values[-N:] = recovEdFn[self.poly_order - 1](xR, q[-2], q[-1], dx)
  #   # end
  #   for j in range(1, numCells[0] - 1):
  #     if c1:
  #       values[j * N : (j + 1) * N] = recovC1Fn[self.poly_order - 1](
  #           xC, q[j], q[j - 1], q[j + 1], dx
  #       )
  #     else:
  #       values[j * N : (j + 1) * N] = recovC0Fn[self.poly_order - 1](
  #           xC, q[j], q[j - 1], q[j + 1], dx
  #       )
  #     # end
  #   # end

  #   values = values[..., np.newaxis]
  #   if overwrite:
  #     self.data.push(grid, values)
  #   else:
  #     return grid, values
  #   # end
