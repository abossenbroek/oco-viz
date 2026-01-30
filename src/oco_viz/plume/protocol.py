"""Protocol for plume generators."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    import numpy as np
    import xarray as xr
    from numpy.typing import NDArray

    from oco_viz.config.schema import GridConfig, PlumeConfig


class PlumeGenerator(Protocol):
    """Interface for plume concentration generators."""

    def generate_timestep(
        self,
        config: PlumeConfig,
        grid: GridConfig,
        time_index: int,
    ) -> NDArray[np.float32]:
        """Generate a single timestep of concentration data."""
        ...

    def generate_sequence(
        self,
        config: PlumeConfig,
        grid: GridConfig,
        num_timesteps: int,
    ) -> xr.Dataset:
        """Generate a time series of concentration data as xr.Dataset."""
        ...
