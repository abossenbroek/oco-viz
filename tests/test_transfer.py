from oco_viz.render.transfer import ControlPoint, TransferFunction


def test_json_round_trip():
    tf = TransferFunction.default_plume()
    json_str = tf.to_json()
    tf2 = TransferFunction.from_json(json_str)
    assert len(tf2.color_points) == len(tf.color_points)
    assert len(tf2.opacity_points) == len(tf.opacity_points)
    for a, b in zip(tf.color_points, tf2.color_points, strict=True):
        assert a == b
    for a, b in zip(tf.opacity_points, tf2.opacity_points, strict=True):
        assert a == b


def test_to_vtk_returns_correct_types():
    tf = TransferFunction.default_plume()
    color_tf, opacity_tf = tf.to_vtk()
    assert color_tf.GetSize() == len(tf.color_points)
    assert opacity_tf.GetSize() == len(tf.opacity_points)


def test_control_point_frozen():
    cp = ControlPoint(scalar=0.5, r=1.0, g=0.5, b=0.0, opacity=0.3)
    assert cp.scalar == 0.5
    assert cp.r == 1.0


def test_save_and_load_json(tmp_path):
    tf = TransferFunction.default_plume()
    path = tmp_path / "tf.json"
    tf.save_json(path)
    tf2 = TransferFunction.from_json_file(path)
    assert len(tf2.color_points) == len(tf.color_points)


def test_empty_transfer_function():
    tf = TransferFunction()
    color_tf, opacity_tf = tf.to_vtk()
    assert color_tf.GetSize() == 0
    assert opacity_tf.GetSize() == 0
