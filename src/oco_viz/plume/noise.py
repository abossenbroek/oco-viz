"""Fractal Brownian motion noise for volumetric turbulence detail."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import numpy as np
import structlog
from scipy.ndimage import gaussian_filter

if TYPE_CHECKING:
    from numpy.typing import NDArray

log = structlog.get_logger()


def fbm_3d(
    shape: tuple[int, int, int],
    octaves: int = 6,
    lacunarity: float = 2.0,
    gain: float = 0.5,
    seed: int = 42,
) -> NDArray[np.float32]:
    """Generate multi-octave fractal Brownian motion noise in 3D.

    Layers Gaussian-filtered white noise at decreasing scales.  Each octave
    generates white noise, applies ``gaussian_filter`` with
    ``sigma = base_sigma / freq``, and scales by the current amplitude.
    The summed result is normalized to [0, 1].

    Parameters
    ----------
    shape:
        ``(z, y, x)`` dimensions of the output volume.
    octaves:
        Number of noise layers to sum.
    lacunarity:
        Frequency multiplier per octave.
    gain:
        Amplitude multiplier per octave (persistence).
    seed:
        Random seed for reproducibility.

    Returns
    -------
    NDArray[np.float32]
        Noise field with values in [0, 1].

    """
    rng = np.random.default_rng(seed)
    base_sigma = min(shape) / 4.0
    result = np.zeros(shape, dtype=np.float64)

    freq = 1.0
    amplitude = 1.0

    for _ in range(octaves):
        white = rng.standard_normal(shape)
        sigma = base_sigma / freq
        # Clamp sigma to at least 0.5 to avoid degenerate filtering
        sigma = max(sigma, 0.5)
        filtered = gaussian_filter(white, sigma=sigma, mode="wrap")
        result += amplitude * filtered
        freq *= lacunarity
        amplitude *= gain

    # Normalize to [0, 1]
    rmin = result.min()
    rmax = result.max()
    if rmax - rmin > 0:
        result = (result - rmin) / (rmax - rmin)
    else:
        result[:] = 0.0

    output = result.astype(np.float32)
    log.info(
        "fbm_3d generated",
        shape=shape,
        octaves=octaves,
        seed=seed,
        output_range=[round(float(output.min()), 4), round(float(output.max()), 4)],
    )
    return output


def fbm_4d(
    shape: tuple[int, int, int],
    time_slices: int,
    octaves: int = 6,
    lacunarity: float = 2.0,
    gain: float = 0.5,
    temporal_speed: float = 0.02,
    seed: int = 42,
) -> NDArray[np.float32]:
    """Generate temporally-coherent 4D fractal Brownian motion noise.

    Returns a ``(time, z, y, x)`` array.  Temporal coherence is achieved by
    linearly blending between 3D noise fields generated from adjacent integer
    seeds, weighted by the fractional part of the continuous time parameter.

    Parameters
    ----------
    shape:
        ``(z, y, x)`` spatial dimensions.
    time_slices:
        Number of time frames to generate.
    octaves:
        Number of noise layers to sum per frame.
    lacunarity:
        Frequency multiplier per octave.
    gain:
        Amplitude multiplier per octave.
    temporal_speed:
        Controls how fast the noise evolves over time.
    seed:
        Base random seed.

    Returns
    -------
    NDArray[np.float32]
        Array of shape ``(time_slices, *shape)`` with values in [0, 1].

    """
    frames: list[NDArray[np.float32]] = []

    # Pre-cache noise fields to enable blending between adjacent seeds
    cache: dict[int, NDArray[np.float32]] = {}

    for t in range(time_slices):
        continuous_t = t * temporal_speed
        seed_low = seed + int(continuous_t)
        seed_high = seed_low + 1
        frac = continuous_t - int(continuous_t)

        if seed_low not in cache:
            cache[seed_low] = fbm_3d(
                shape,
                octaves=octaves,
                lacunarity=lacunarity,
                gain=gain,
                seed=seed_low,
            )
        if seed_high not in cache:
            cache[seed_high] = fbm_3d(
                shape,
                octaves=octaves,
                lacunarity=lacunarity,
                gain=gain,
                seed=seed_high,
            )

        blended = (1.0 - frac) * cache[seed_low] + frac * cache[seed_high]
        frames.append(blended.astype(np.float32))

    return np.stack(frames, axis=0)


def curl_noise_3d(
    shape: tuple[int, int, int],
    octaves: int = 4,
    lacunarity: float = 2.0,
    gain: float = 0.5,
    seed: int = 42,
) -> tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]:
    """Compute a divergence-free 3D displacement field via the curl operator.

    Generates three independent ``fbm_3d`` scalar potentials (A, B, C) and
    returns their curl:

    .. code-block:: text

        curl = (dC/dy - dB/dz,  dA/dz - dC/dx,  dB/dx - dA/dy)

    Partial derivatives are computed with ``np.gradient``.  Each component is
    normalized to [-1, 1].

    Parameters
    ----------
    shape:
        ``(z, y, x)`` dimensions of the output volume.
    octaves:
        Number of noise layers per potential field.
    lacunarity:
        Frequency multiplier per octave.
    gain:
        Amplitude multiplier per octave.
    seed:
        Base random seed; potentials use ``seed``, ``seed+1``, ``seed+2``.

    Returns
    -------
    tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float32]]
        ``(dx, dy, dz)`` displacement fields, each in [-1, 1].

    """
    pot_a = fbm_3d(shape, octaves=octaves, lacunarity=lacunarity, gain=gain, seed=seed)
    pot_b = fbm_3d(shape, octaves=octaves, lacunarity=lacunarity, gain=gain, seed=seed + 1)
    pot_c = fbm_3d(shape, octaves=octaves, lacunarity=lacunarity, gain=gain, seed=seed + 2)

    # np.gradient returns list of gradients along each axis (z=0, y=1, x=2)
    da_dz, da_dy, _da_dx = np.gradient(pot_a.astype(np.float64))
    db_dz, _db_dy, db_dx = np.gradient(pot_b.astype(np.float64))
    _dc_dz, dc_dy, dc_dx = np.gradient(pot_c.astype(np.float64))

    # curl = (dC/dy - dB/dz, dA/dz - dC/dx, dB/dx - dA/dy)
    curl_x = dc_dy - db_dz
    curl_y = da_dz - dc_dx
    curl_z = db_dx - da_dy

    def _normalize_to_unit(arr: NDArray[np.float64]) -> NDArray[np.float32]:
        amax = np.abs(arr).max()
        if amax > 0:
            arr = arr / amax
        return arr.astype(np.float32)

    cx = _normalize_to_unit(cast("NDArray[np.float64]", curl_x))
    cy = _normalize_to_unit(cast("NDArray[np.float64]", curl_y))
    cz = _normalize_to_unit(cast("NDArray[np.float64]", curl_z))
    log.info("curl_noise_3d generated", shape=shape, octaves=octaves, seed=seed)
    return cx, cy, cz
