"""The ``extract_input`` verb — decode the input file embedded in a BP file."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def extract_input(data: "GData") -> str:
  """Decode the input file embedded in a Gkeyll output file.

  Gkeyll output files (e.g. BP files) may carry the original simulation input
  file as a base64-encoded string. This returns the decoded text.

  Args:
    data: GData
      The dataset whose embedded input file is decoded.

  Returns:
    The decoded input-file text as a ``str``, or an empty string when no input
    file is embedded.
  """
  encoded = data.get_input_file()
  if encoded:
    return base64.decodebytes(encoded.encode("utf-8")).decode("utf-8")
  # end
  return ""
