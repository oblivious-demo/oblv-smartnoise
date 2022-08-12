from .base import EXPORT_TYPES
from .MWEM import MWEM
from .DPCTGAN import DPCTGAN
from .MTS import MTS
from .PATECTGAN import PATECTGAN

DPModelSelect = {
    "MWEM": MWEM,
    "DPCTGAN": DPCTGAN,
    "PATECTGAN":PATECTGAN
}