"""Interactive transfer function tuning script.

Renders a single plume frame with the current transfer function,
saves the TF to JSON for artist iteration.

Usage:
    python scripts/tune_transfer.py --profile dev_mac --output tf.json
    python scripts/tune_transfer.py --profile dev_mac --input tf.json --output tf_v2.json
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image

from oco_viz.config import load_config
from oco_viz.data.zarr_store import write_zarr
from oco_viz.plume.gaussian import generate_sequence
from oco_viz.render.camera import FixedCamera
from oco_viz.render.renderer import VolumeRenderer
from oco_viz.render.transfer import TransferFunction


def main() -> None:
    parser = argparse.ArgumentParser(description="Transfer function tuning")
    parser.add_argument("--profile", default="dev_mac")
    parser.add_argument("--input", type=Path, default=None, help="Load existing TF JSON")
    parser.add_argument("--output", type=Path, default=Path("output/transfer_function.json"))
    parser.add_argument("--preview", type=Path, default=Path("output/tf_preview.png"))
    args = parser.parse_args()

    config = load_config(args.profile)

    # Load or create transfer function
    if args.input and args.input.exists():
        tf = TransferFunction.from_json_file(args.input)
        print(f"Loaded TF from {args.input}")
    else:
        tf = TransferFunction.default_plume()
        print("Using default plume TF")

    # Generate single-frame plume for preview
    ds = generate_sequence(config.plume, config.grid, num_timesteps=1)
    zarr_path = Path("output/tune_plume.zarr")
    write_zarr(ds, zarr_path)

    concentration = ds["concentration"].values[0]

    # Render preview
    renderer = VolumeRenderer(config)
    renderer.configure(tf)
    cam = FixedCamera(
        position=(0.0, -300.0, 200.0),
        focal_point=(0.0, 0.0, 30.0),
        view_up=(0.0, 0.0, 1.0),
    )
    state = cam.evaluate(0.0)
    rgb, _ = renderer.render_frame(concentration, state)
    renderer.finalize()

    # Save preview PNG
    args.preview.parent.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    img.save(args.preview)
    print(f"Preview: {args.preview}")

    # Save TF JSON
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tf.save_json(args.output)
    print(f"TF saved: {args.output}")

    # Verify round-trip
    loaded = TransferFunction.from_json_file(args.output)
    assert len(loaded.color_points) == len(tf.color_points)
    print("Round-trip verified")


if __name__ == "__main__":
    main()
