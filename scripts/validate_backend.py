"""Validate that a VTK offscreen backend is available."""

from oco_viz.render.backend import detect_backend
from oco_viz.render.window import create_render_window


def main() -> None:
    backend = detect_backend()
    print(f"Backend: {backend.value}")

    win = create_render_window(width=64, height=64, backend=backend)
    win.Render()
    print(f"Render window: {type(win).__name__}")
    win.Finalize()

    print("PASS")


if __name__ == "__main__":
    main()
