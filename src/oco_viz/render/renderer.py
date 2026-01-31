"""VolumeRenderer: configure once, render many frames."""

from __future__ import annotations

from typing import TYPE_CHECKING

import vtk

from oco_viz.postprocess.pipeline import PostProcessPipeline
from oco_viz.render.camera import CameraState, apply_camera
from oco_viz.render.depth import extract_depth, extract_rgb
from oco_viz.render.ground_plane import create_ground_plane
from oco_viz.render.lighting import apply_lighting
from oco_viz.render.sky_gradient import apply_sky_gradient
from oco_viz.render.transfer import TransferFunction
from oco_viz.render.volume import create_volume, numpy_to_vtk_image
from oco_viz.render.window import create_render_window

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

    from oco_viz.config.schema import AppConfig


class VolumeRenderer:
    """Configure once, render many frames."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._win: vtk.vtkRenderWindow | None = None
        self._renderer: vtk.vtkRenderer | None = None
        self._volume: vtk.vtkVolume | None = None
        self._pipeline: PostProcessPipeline | None = None

    def configure(
        self,
        tf: TransferFunction | None = None,
        *,
        lighting: bool = True,
    ) -> None:
        """Build the rendering pipeline. Call once before render_frame."""
        if tf is None:
            tf = TransferFunction.default_plume()

        self._color_tf, self._opacity_tf = tf.to_vtk()

        self._renderer = vtk.vtkRenderer()
        apply_sky_gradient(self._renderer, self._config.sky)

        if lighting:
            apply_lighting(self._renderer)

        if self._config.ground_plane.enabled:
            ground_actor = create_ground_plane(self._config.ground_plane, self._config.grid)
            self._renderer.AddActor(ground_actor)

        self._win = create_render_window(
            width=self._config.output.width,
            height=self._config.output.height,
        )
        self._win.AddRenderer(self._renderer)

        self._pipeline = PostProcessPipeline(self._config.postprocess)

    def render_frame(
        self,
        concentration: NDArray[np.float32],
        camera_state: CameraState,
    ) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
        """Render a frame from concentration data and camera state.

        Returns (rgb, depth) as float32 arrays.
        """
        if self._win is None or self._renderer is None:
            msg = "Call configure() before render_frame()"
            raise RuntimeError(msg)

        # Normalize
        max_val = concentration.max()
        normalized = concentration / max_val if max_val > 0 else concentration

        image_data = numpy_to_vtk_image(normalized)

        # Remove old volume, create new
        if self._volume is not None:
            self._renderer.RemoveVolume(self._volume)

        self._volume = create_volume(
            image_data,
            self._color_tf,
            self._opacity_tf,
            scattering=self._config.scattering,
        )
        self._renderer.AddVolume(self._volume)

        apply_camera(camera_state, self._renderer)
        self._win.Render()

        rgb = extract_rgb(self._win)
        depth = extract_depth(self._win)
        return rgb, depth

    def render_frame_postprocessed(
        self,
        concentration: NDArray[np.float32],
        camera_state: CameraState,
    ) -> NDArray[np.float32]:
        """Render and apply post-processing pipeline."""
        rgb, depth = self.render_frame(concentration, camera_state)
        if self._pipeline is not None:
            return self._pipeline.process(rgb, depth)
        return rgb

    def finalize(self) -> None:
        """Clean up VTK resources."""
        if self._win is not None:
            self._win.Finalize()
            self._win = None
