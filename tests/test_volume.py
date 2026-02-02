"""Tests for VTK volume rendering utilities."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from oco_viz.config.schema import ScatteringConfig
from oco_viz.render.transfer import TransferFunction
from oco_viz.render.volume import (
    create_volume,
    make_gaussian_blob,
    numpy_to_vtk_image,
    render_blob_to_png,
)


def test_make_gaussian_blob_shape():
    blob = make_gaussian_blob((60, 100, 100))
    assert blob.shape == (60, 100, 100)
    assert blob.dtype == np.float32


def test_make_gaussian_blob_values():
    blob = make_gaussian_blob()
    assert blob.min() >= 0.0
    assert blob.max() <= 1.0
    assert blob.max() > 0.9


def test_numpy_to_vtk_image():
    data = np.random.default_rng(42).random((10, 20, 30), dtype=np.float32)
    image = numpy_to_vtk_image(data)
    dims = image.GetDimensions()
    assert dims == (30, 20, 10)


def test_numpy_to_vtk_image_default_spacing():
    data = np.random.default_rng(42).random((10, 20, 30), dtype=np.float32)
    image = numpy_to_vtk_image(data)
    assert image.GetSpacing() == (1.0, 1.0, 1.0)


def test_numpy_to_vtk_image_custom_spacing():
    data = np.random.default_rng(42).random((10, 20, 30), dtype=np.float32)
    spacing = (1000.0, 1000.0, 500.0)
    image = numpy_to_vtk_image(data, spacing=spacing)
    assert image.GetSpacing() == spacing


def test_create_volume_without_scattering():
    blob = make_gaussian_blob((10, 20, 20))
    image_data = numpy_to_vtk_image(blob)
    tf = TransferFunction.default_plume()
    color_tf, opacity_tf = tf.to_vtk()
    volume = create_volume(image_data, color_tf, opacity_tf)
    assert volume.GetMapper() is not None
    assert volume.GetProperty().GetShade() == 1


def test_create_volume_with_scattering():
    blob = make_gaussian_blob((10, 20, 20))
    image_data = numpy_to_vtk_image(blob)
    tf = TransferFunction.default_plume()
    color_tf, opacity_tf = tf.to_vtk()

    scattering = ScatteringConfig(
        global_illumination_reach=0.7,
        volumetric_scattering_blending=1.0,
        anisotropy=0.5,
        jittering=True,
        shade=True,
    )

    volume = create_volume(image_data, color_tf, opacity_tf, scattering=scattering)
    mapper = volume.GetMapper()
    assert mapper.GetGlobalIlluminationReach() == pytest.approx(0.7, abs=1e-6)
    assert mapper.GetVolumetricScatteringBlending() == pytest.approx(1.0, abs=1e-6)
    assert volume.GetProperty().GetScatteringAnisotropy() == pytest.approx(0.5, abs=1e-6)
    assert volume.GetProperty().GetShade() == 1


def test_create_volume_sample_distance():
    blob = make_gaussian_blob((10, 20, 20))
    image_data = numpy_to_vtk_image(blob)
    tf = TransferFunction.default_plume()
    color_tf, opacity_tf = tf.to_vtk()

    scattering = ScatteringConfig(sample_distance=0.25)
    volume = create_volume(image_data, color_tf, opacity_tf, scattering=scattering)
    mapper = volume.GetMapper()
    assert mapper.GetSampleDistance() == pytest.approx(0.25, abs=1e-6)
    assert mapper.GetAutoAdjustSampleDistances() == 0


@pytest.mark.skipci
def test_render_blob_to_png(tmp_path):
    output = tmp_path / "test_blob.png"
    render_blob_to_png(output, width=256, height=256, shape=(30, 50, 50))
    assert output.exists()
    assert output.stat().st_size > 1024

    img = Image.open(output)
    assert img.size == (256, 256)
    arr = np.array(img)
    assert arr.max() > 10


@pytest.mark.skipci
def test_render_blob_to_output_dir():
    output = Path("output/test_blob.png")
    output.parent.mkdir(parents=True, exist_ok=True)
    render_blob_to_png(output, width=512, height=512)
    assert output.exists()
    assert output.stat().st_size > 1024

    img = Image.open(output)
    assert img.size == (512, 512)
    arr = np.array(img)
    assert arr.max() > 10
