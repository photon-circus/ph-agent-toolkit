"""Model-provider adapters."""

from .lm_studio import call_lm_studio, strip_code_fence

__all__ = ["call_lm_studio", "strip_code_fence"]
