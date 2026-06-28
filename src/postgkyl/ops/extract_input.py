"""The ``extract_input`` verb — decode the input file embedded in a BP file."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

if TYPE_CHECKING:
  from postgkyl.data import GData
# end


def extract_input(data: "GData") -> str:
  """Return the decoded embedded input file, or '' when none is present."""
  encoded = data.get_input_file()
  if encoded:
    return base64.decodebytes(encoded.encode("utf-8")).decode("utf-8")
  # end
  return ""
