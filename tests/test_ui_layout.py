from audit_tools_bundle.app import calculate_window_geometry


def test_window_geometry_fits_14_inch_work_area():
    assert calculate_window_geometry((0, 0, 1280, 680)) == (1152, 612, 64, 34)


def test_window_geometry_never_exceeds_small_work_area():
    width, height, x, y = calculate_window_geometry((10, 20, 710, 500))
    assert (width, height) == (700, 480)
    assert (x, y) == (10, 20)
