from __future__ import annotations

import io
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from src import contrast, mockup, skeleton
from src.image_processor import ImageProcessor


# ── Device & browser mockups ─────────────────────────────────────────
def _source(size: tuple[int, int] = (800, 600)) -> Image.Image:
    return Image.new("RGB", size, (200, 60, 60))


@pytest.mark.parametrize("device", sorted(mockup.DEVICES))
def test_mockup_renders_every_device(device: str) -> None:
    """Every frame renders at the requested width with its declared aspect ratio."""
    spec = mockup.DEVICES[device]
    frame = mockup.render(_source(), device, width=400)

    assert frame.width == 400
    expected_h = round(400 * spec.frame_size[1] / spec.frame_size[0])
    assert abs(frame.height - expected_h) <= 1
    assert frame.mode == "RGBA"


def test_mockup_native_size_and_transparent_corners() -> None:
    """Without a width the frame keeps native size and rounded (transparent) corners."""
    frame = mockup.render(_source(), "iphone")
    assert frame.size == mockup.DEVICES["iphone"].frame_size
    assert frame.getpixel((0, 0))[3] == 0


def test_mockup_background_flattens_corners() -> None:
    """A background colour fills in behind the rounded body."""
    frame = mockup.render(_source(), "iphone", width=200, background="#00ff00")
    assert frame.getpixel((0, 0))[:3] == (0, 255, 0)
    assert frame.getpixel((0, 0))[3] == 255


def test_mockup_unknown_device_and_bad_color() -> None:
    with pytest.raises(ValueError):
        mockup.render(_source(), "nope")
    with pytest.raises(ValueError):
        mockup.render(_source(), "iphone", background="zzz")
    with pytest.raises(ValueError):
        mockup.render(_source(), "iphone", background="#12345")


@pytest.mark.parametrize("fmt", ["png", "jpeg", "jpg", "webp"])
def test_mockup_render_bytes_formats(fmt: str) -> None:
    data = mockup.render_bytes(_source(), "browser", width=320, output_format=fmt)
    with Image.open(io.BytesIO(data)) as img:
        assert img.width == 320
        assert img.format == ("JPEG" if fmt in ("jpeg", "jpg") else fmt.upper())


def test_mockup_short_hex_background() -> None:
    """Short hex expands; the corner is background, modulo resampling of the round body."""
    frame = mockup.render(_source(), "tablet", width=120, background="0f0")
    r, g, b = frame.getpixel((0, 0))[:3]
    assert (r, b) == (0, 0)
    assert g > 240


def test_list_devices_metadata() -> None:
    devices = mockup.list_devices()
    assert {d["id"] for d in devices} == set(mockup.DEVICES)
    for entry in devices:
        assert entry["frame"]["width"] > 0
        assert entry["aspect_ratio"] > 0


# ── Wireframe / skeleton placeholders ────────────────────────────────
@pytest.mark.parametrize("preset", skeleton.PRESETS)
@pytest.mark.parametrize("theme", ["light", "dark"])
def test_skeleton_renders_every_preset(preset: str, theme: str) -> None:
    img = skeleton.render(preset, 400, 300, theme=theme)
    assert img.size == (400, 300)
    # A wireframe must actually draw something on top of the background.
    assert len(img.getcolors(maxcolors=1 << 16)) > 1


def test_skeleton_theme_backgrounds_differ() -> None:
    light = skeleton.render("grid", 200, 200, theme="light")
    dark = skeleton.render("grid", 200, 200, theme="dark")
    assert light.getpixel((1, 1)) != dark.getpixel((1, 1))


def test_skeleton_row_and_column_overrides() -> None:
    default = skeleton.render("grid", 300, 300)
    custom = skeleton.render("grid", 300, 300, rows=4, cols=4)
    assert default.tobytes() != custom.tobytes()

    rows_default = skeleton.render("list", 300, 300)
    rows_custom = skeleton.render("list", 300, 300, rows=8)
    assert rows_default.tobytes() != rows_custom.tobytes()

    form_default = skeleton.render("form", 300, 300)
    form_custom = skeleton.render("form", 300, 300, rows=5)
    assert form_default.tobytes() != form_custom.tobytes()


def test_skeleton_invalid_preset_and_theme() -> None:
    with pytest.raises(ValueError):
        skeleton.render("nope", 100, 100)
    with pytest.raises(ValueError):
        skeleton.render("card", 100, 100, theme="neon")


@pytest.mark.parametrize("fmt", ["png", "jpeg", "webp"])
def test_skeleton_render_bytes_formats(fmt: str) -> None:
    data = skeleton.render_bytes("card", 200, 150, output_format=fmt)
    with Image.open(io.BytesIO(data)) as img:
        assert img.size == (200, 150)
        assert img.format == fmt.upper()


def test_list_presets_metadata() -> None:
    assert {p["id"] for p in skeleton.list_presets()} == set(skeleton.PRESETS)


# ── Contrast / text safety ───────────────────────────────────────────
def test_relative_luminance_endpoints() -> None:
    assert contrast.relative_luminance((0, 0, 0)) == 0.0
    assert contrast.relative_luminance((255, 255, 255)) == pytest.approx(1.0)


def test_contrast_ratio_black_on_white() -> None:
    assert contrast.contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0)
    assert contrast.contrast_ratio((255, 255, 255), (255, 255, 255)) == pytest.approx(1.0)


def test_analyze_dark_image_prefers_white_text() -> None:
    report = contrast.analyze(Image.new("RGB", (90, 90), (10, 10, 10)))
    assert report["text_color"] == "#ffffff"
    assert report["recommended_text_color"] == "#ffffff"
    assert report["safe_for_text"] is True
    assert report["suggested_scrim"] == 0.0
    assert len(report["regions"]) == 9
    assert report["regions"][0]["region"] == "top-left"
    assert report["regions"][0]["rating"] == "AAA"


def test_analyze_light_image_prefers_black_text() -> None:
    report = contrast.analyze(Image.new("RGB", (90, 90), (250, 250, 250)))
    assert report["recommended_text_color"] == "#000000"
    # White-on-white is the default question here, and it fails badly.
    assert report["safe_for_text"] is False


def test_parse_color_accepts_short_and_long_hex() -> None:
    assert contrast.parse_color("#f00") == (255, 0, 0)
    assert contrast.parse_color("00ff00") == (0, 255, 0)
    for bad in ("", "#12345", "zzzzzz"):
        with pytest.raises(ValueError):
            contrast.parse_color(bad)


def test_analyze_mid_grey_needs_a_scrim() -> None:
    """White text over mid grey fails AA, so a scrim is required."""
    report = contrast.analyze(Image.new("RGB", (90, 90), (128, 128, 128)))
    assert report["safe_for_text"] is False
    assert 0.0 < report["suggested_scrim"] <= 1.0
    assert report["regions"][0]["rating"] in ("fail", "AA-large")
    # Black text clears AA on the same image, which is what the recommendation says.
    black_report = contrast.analyze(
        Image.new("RGB", (90, 90), (128, 128, 128)), text_color="#000000"
    )
    assert black_report["safe_for_text"] is True
    assert report["recommended_text_color"] == "#000000"


def test_analyze_custom_grid_names_and_validation() -> None:
    report = contrast.analyze(Image.new("RGB", (80, 80), (0, 0, 0)), grid=2)
    assert [r["region"] for r in report["regions"]] == ["r1c1", "r1c2", "r2c1", "r2c2"]
    with pytest.raises(ValueError):
        contrast.analyze(Image.new("RGB", (10, 10)), grid=0)


def test_required_scrim_saturates_at_one() -> None:
    """White text on white can never reach AA, so the scrim maxes out."""
    assert contrast.required_scrim((255, 255, 255), (255, 255, 255), target=21.0) == 1.0
    assert contrast.required_scrim((0, 0, 0), (255, 255, 255)) == 0.0


def test_analyze_worst_region_is_the_lowest_contrast_cell() -> None:
    img = Image.new("RGB", (90, 90), (0, 0, 0))
    # Paint the centre cell mid grey: it should become the worst region.
    img.paste(Image.new("RGB", (30, 30), (128, 128, 128)), (30, 30))
    report = contrast.analyze(img)
    assert report["worst_region"] == "center"


# ── Scrim rendering ──────────────────────────────────────────────────
def _photo(tmp_path: Path, color: tuple[int, int, int] = (200, 200, 200)) -> Path:
    path = tmp_path / "photo.jpg"
    Image.new("RGB", (200, 200), color).save(path, "JPEG")
    return path


def test_scrim_darkens_uniformly(tmp_path: Path) -> None:
    processor = ImageProcessor()
    plain = processor.process(_photo(tmp_path), 100, 100, output_format="png")
    dimmed = processor.process(_photo(tmp_path), 100, 100, output_format="png", scrim="0.5")

    with Image.open(io.BytesIO(plain)) as a, Image.open(io.BytesIO(dimmed)) as b:
        assert b.getpixel((50, 50))[0] < a.getpixel((50, 50))[0]


def test_scrim_light_brightens(tmp_path: Path) -> None:
    processor = ImageProcessor()
    path = _photo(tmp_path, (40, 40, 40))
    lifted = processor.process(path, 100, 100, output_format="png", scrim="light:0.5")
    with Image.open(io.BytesIO(lifted)) as img:
        assert img.getpixel((50, 50))[0] > 40


def test_scrim_gradient_is_strongest_at_the_edge(tmp_path: Path) -> None:
    processor = ImageProcessor()
    path = _photo(tmp_path)
    bottom = processor.process(path, 100, 100, output_format="png", scrim="bottom:0.8")
    top = processor.process(path, 100, 100, output_format="png", scrim="top:0.8")

    with Image.open(io.BytesIO(bottom)) as img:
        assert img.getpixel((50, 98))[0] < img.getpixel((50, 50))[0]
        assert img.getpixel((50, 2))[0] == pytest.approx(img.getpixel((50, 40))[0], abs=6)
    with Image.open(io.BytesIO(top)) as img:
        assert img.getpixel((50, 2))[0] < img.getpixel((50, 50))[0]


def test_scrim_ignores_invalid_and_zero_values(tmp_path: Path) -> None:
    processor = ImageProcessor()
    path = _photo(tmp_path)
    plain = processor.process(path, 100, 100, output_format="png")
    for spec in ("abc", "dark:abc", "0", "dark:0"):
        assert processor.process(path, 100, 100, output_format="png", scrim=spec) == plain


# ── HTTP endpoints ───────────────────────────────────────────────────
def test_mockup_endpoint(client: TestClient) -> None:
    response = client.get("/mockup/iphone/300")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    with Image.open(io.BytesIO(response.content)) as img:
        assert img.width == 300


def test_mockup_endpoint_extension_and_seed(client: TestClient) -> None:
    response = client.get("/mockup/browser/400.webp?seed=abc&url=example.com")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert "immutable" in response.headers["cache-control"]


def test_mockup_endpoint_errors(client: TestClient) -> None:
    assert client.get("/mockup/nope/300").status_code == 404
    assert client.get("/mockup/iphone/300.gif").status_code == 400


def test_mockup_endpoint_unknown_category(client: TestClient) -> None:
    assert client.get("/mockup/iphone/300/does-not-exist").status_code == 404


def test_api_mockups(client: TestClient) -> None:
    body = client.get("/api/mockups").json()
    assert {d["id"] for d in body["devices"]} == set(mockup.DEVICES)


def test_skeleton_endpoint(client: TestClient) -> None:
    response = client.get("/skeleton/card/400/300")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    with Image.open(io.BytesIO(response.content)) as img:
        assert img.size == (400, 300)


def test_skeleton_endpoint_options(client: TestClient) -> None:
    response = client.get("/skeleton/grid/400/300.webp?theme=dark&rows=3&cols=4&radius=0")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"


def test_skeleton_endpoint_errors(client: TestClient) -> None:
    assert client.get("/skeleton/nope/400/300").status_code == 400
    assert client.get("/skeleton/card/400/300?theme=neon").status_code == 400
    assert client.get("/skeleton/card/400/300.gif").status_code == 400


def test_api_skeletons(client: TestClient) -> None:
    body = client.get("/api/skeletons").json()
    assert {p["id"] for p in body["presets"]} == set(skeleton.PRESETS)
    assert body["themes"] == ["dark", "light"]


def test_contrast_endpoint(client: TestClient) -> None:
    response = client.get("/api/contrast/1")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert len(body["regions"]) == 9
    assert body["recommended_text_color"] in ("#ffffff", "#000000")


def test_contrast_endpoint_custom_grid(client: TestClient) -> None:
    body = client.get("/api/contrast/1?grid=2&target=7").json()
    assert body["grid"] == 2
    assert body["target_ratio"] == 7
    assert len(body["regions"]) == 4


def test_contrast_endpoint_text_color(client: TestClient) -> None:
    body = client.get("/api/contrast/1?text=%23000000").json()
    assert body["text_color"] == "#000000"


def test_contrast_endpoint_errors(client: TestClient) -> None:
    assert client.get("/api/contrast/999999").status_code == 404
    assert client.get("/api/contrast/1?target=99").status_code == 400
    assert client.get("/api/contrast/1?text=zzz").status_code == 400


def test_serve_image_accepts_scrim(client: TestClient) -> None:
    plain = client.get("/200/200?seed=fixed&format=png")
    dimmed = client.get("/200/200?seed=fixed&format=png&scrim=bottom:0.7")
    assert plain.status_code == dimmed.status_code == 200
    # The scrim must take part in the cache key, not return the cached plain render.
    assert plain.content != dimmed.content
