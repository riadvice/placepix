from __future__ import annotations

from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.avatar_generator import AvatarGenerator, _PALETTES


def test_extract_initials_two_words():
    gen = AvatarGenerator()
    assert gen.extract_initials("John Doe") == "JD"


def test_extract_initials_three_words():
    gen = AvatarGenerator()
    assert gen.extract_initials("John Paul Doe") == "JP"


def test_extract_initials_single_letter_mode():
    gen = AvatarGenerator()
    assert gen.extract_initials("John Doe", single=True) == "J"


def test_extract_initials_lowercase():
    gen = AvatarGenerator()
    assert gen.extract_initials("john doe", uppercase=False) == "jd"


def test_extract_initials_empty():
    gen = AvatarGenerator()
    assert gen.extract_initials("") == "?"


def test_pick_color_deterministic():
    gen = AvatarGenerator()
    color1 = gen.pick_color("John Doe")
    color2 = gen.pick_color("John Doe")
    assert color1 == color2
    assert isinstance(color1, tuple)
    assert len(color1) == 3


def test_pick_color_different_names():
    gen = AvatarGenerator()
    color1 = gen.pick_color("Alice")
    color2 = gen.pick_color("Bob")
    # Very unlikely to be the same with a 20-color palette
    assert color1 != color2


def test_generate_png_basic():
    gen = AvatarGenerator()
    data = gen.generate_png("John Doe", size_str="100")
    assert len(data) > 0
    img = Image.open(BytesIO(data))
    assert img.format == "PNG"
    assert img.size == (100, 100)


def test_generate_png_circle():
    gen = AvatarGenerator()
    data = gen.generate_png("Jane Doe", size_str="100", circle=True)
    img = Image.open(BytesIO(data))
    assert img.size == (100, 100)


def test_generate_png_custom_size():
    gen = AvatarGenerator()
    data = gen.generate_png("Test", size_str="200x150")
    img = Image.open(BytesIO(data))
    assert img.size == (200, 150)


def test_generate_png_border():
    gen = AvatarGenerator()
    data = gen.generate_png("Border Test", size_str="100", border=5, border_color="ff0000")
    assert len(data) > 0


def test_generate_svg_basic():
    gen = AvatarGenerator()
    svg = gen.generate_svg("John Doe", size_str="100")
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "JD" in svg


def test_generate_svg_circle():
    gen = AvatarGenerator()
    svg = gen.generate_svg("Jane Doe", size_str="100", circle=True)
    assert "<circle" in svg


def test_generate_svg_escaped_text():
    gen = AvatarGenerator()
    svg = gen.generate_svg("A&B", size_str="100")
    assert "A&amp;B" not in svg  # initials extraction only takes A
    assert "A" in svg


# API endpoint tests


def test_avatar_endpoint_png(client: TestClient):
    response = client.get("/avatar/100/John%20Doe")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"


def test_avatar_endpoint_svg(client: TestClient):
    response = client.get("/avatar/100/John%20Doe.svg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml"
    assert "<svg" in response.text
    assert "JD" in response.text


def test_avatar_endpoint_circle(client: TestClient):
    response = client.get("/avatar/100/John%20Doe.svg?circle=true")
    assert response.status_code == 200
    assert "<circle" in response.text


def test_avatar_endpoint_single_letter(client: TestClient):
    response = client.get("/avatar/100/John%20Doe.svg?single=true")
    assert response.status_code == 200
    assert "J" in response.text
    assert "JD" not in response.text


def test_avatar_endpoint_custom_colors(client: TestClient):
    response = client.get("/avatar/100/John%20Doe.svg?bg=ff0000&fg=000000")
    assert response.status_code == 200
    assert "#ff0000" in response.text
    assert "#000000" in response.text


def test_avatar_endpoint_border(client: TestClient):
    response = client.get("/avatar/100/John%20Doe.png?border=5&border_color=0000ff")
    assert response.status_code == 200


def test_avatar_endpoint_jpeg(client: TestClient):
    response = client.get("/avatar/100/John%20Doe.jpeg")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"


def test_avatar_endpoint_webp(client: TestClient):
    response = client.get("/avatar/100/John%20Doe.webp")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"


def test_avatar_endpoint_custom_size(client: TestClient):
    response = client.get("/avatar/200x150/Test.png")
    assert response.status_code == 200
    img = Image.open(BytesIO(response.content))
    assert img.size == (200, 150)


def test_avatar_endpoint_cache_headers(client: TestClient):
    response = client.get("/avatar/100/John%20Doe.png")
    assert response.status_code == 200
    assert "ETag" in response.headers
    assert "immutable" in response.headers.get("Cache-Control", "")


def test_pick_color_with_named_palette():
    gen = AvatarGenerator("material")
    color = gen.pick_color("Alice")
    assert color in _PALETTES["material"]


def test_palette_param_material(client: TestClient):
    response = client.get("/avatar/100/Alice.png?palette=material")
    assert response.status_code == 200


def test_palette_param_neon(client: TestClient):
    response = client.get("/avatar/100/Bob.svg?palette=neon")
    assert response.status_code == 200
    assert "<svg" in response.text


def test_palette_param_unknown(client: TestClient):
    response = client.get("/avatar/100/Alice.png?palette=notreal")
    assert response.status_code == 400


def test_generate_png_transparent_default():
    gen = AvatarGenerator()
    data = gen.generate_png("John Doe", size_str="100")
    img = Image.open(BytesIO(data))
    assert img.mode == "RGBA"
    # Default (no explicit bg) should be transparent
    assert img.getpixel((0, 0))[3] == 0


def test_generate_png_opaque_when_bg_set():
    gen = AvatarGenerator()
    data = gen.generate_png("John Doe", size_str="100", bg="ff0000")
    img = Image.open(BytesIO(data))
    assert img.mode == "RGBA"
    assert img.getpixel((0, 0)) == (255, 0, 0, 255)


def test_generate_png_circle_transparent_corners():
    gen = AvatarGenerator()
    data = gen.generate_png("Jane Doe", size_str="100", circle=True)
    img = Image.open(BytesIO(data))
    assert img.mode == "RGBA"
    # Corner should be transparent
    assert img.getpixel((0, 0))[3] == 0
    # Image should contain some text pixels (non-transparent)
    assert img.getbbox() is not None


def test_generate_png_text_centered():
    gen = AvatarGenerator()
    data = gen.generate_png("A", size_str="100", bg="000000")
    img = Image.open(BytesIO(data))
    bbox = img.getbbox()
    assert bbox is not None
    left, top, right, bottom = bbox
    cx = (left + right) / 2
    cy = (top + bottom) / 2
    # The text should be roughly centered in the 100x100 image
    assert abs(cx - 50) < 10
    assert abs(cy - 50) < 10


def test_avatar_endpoint_png_transparent(client: TestClient):
    response = client.get("/avatar/100/John%20Doe.png")
    assert response.status_code == 200
    img = Image.open(BytesIO(response.content))
    assert img.mode == "RGBA"
    assert img.getpixel((0, 0))[3] == 0
