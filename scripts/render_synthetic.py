"""Render synthetic plume frames to PNG."""

import argparse
from pathlib import Path

import numpy as np
import vtk

from oco_viz.config import load_config
from oco_viz.plume.gaussian import generate_timestep
from oco_viz.render.transfer import TransferFunction
from oco_viz.render.volume import create_volume, numpy_to_vtk_image
from oco_viz.render.window import create_render_window


def render_frame(
    concentration: np.ndarray,
    output_path: Path,
    width: int,
    height: int,
    scattering_config: object,
) -> None:
    """Render a single concentration field to a PNG file."""
    # Normalize concentration to [0, 1] for transfer function
    max_val = concentration.max()
    normalized = concentration / max_val if max_val > 0 else concentration

    image_data = numpy_to_vtk_image(normalized.astype(np.float32))

    tf = TransferFunction.default_plume()
    color_tf, opacity_tf = tf.to_vtk()

    volume = create_volume(image_data, color_tf, opacity_tf, scattering=scattering_config)

    renderer = vtk.vtkRenderer()
    renderer.AddVolume(volume)
    renderer.SetBackground(0.1, 0.1, 0.15)
    renderer.ResetCamera()
    renderer.GetActiveCamera().Elevation(30)
    renderer.GetActiveCamera().Azimuth(45)
    renderer.ResetCameraClippingRange()

    win = create_render_window(width=width, height=height)
    win.AddRenderer(renderer)
    win.Render()

    w2i = vtk.vtkWindowToImageFilter()
    w2i.SetInput(win)
    w2i.Update()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(output_path))
    writer.SetInputConnection(w2i.GetOutputPort())
    writer.Write()

    win.Finalize()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render synthetic plume frames")
    parser.add_argument("--profile", default="dev_mac", help="Config profile name")
    parser.add_argument("--num-frames", type=int, default=1, help="Number of frames")
    args = parser.parse_args()

    config = load_config(args.profile)
    frames_dir = Path(config.output.frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)

    for i in range(args.num_frames):
        concentration = generate_timestep(config.plume, config.grid, time_index=i)
        output_path = frames_dir / f"frame_{i:06d}.png"
        print(f"Rendering frame {i}/{args.num_frames} -> {output_path}")
        render_frame(
            concentration,
            output_path,
            config.output.width,
            config.output.height,
            config.scattering,
        )

    print(f"Done. {args.num_frames} frames in {frames_dir}")


if __name__ == "__main__":
    main()
