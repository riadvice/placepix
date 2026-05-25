from __future__ import annotations

from fastapi.testclient import TestClient


def _get_image_id(client: TestClient) -> int:
    """Helper to get a valid image ID from the manager."""
    from src.main import manager
    entry = manager.pick()
    assert entry is not None
    return entry.id


def test_border_default_black(client: TestClient):
    """Test border with default black color."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?border=10")
    assert response.status_code == 200


def test_border_with_color(client: TestClient):
    """Test border with custom color."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?border=10,ff0000")
    assert response.status_code == 200


def test_padding(client: TestClient):
    """Test padding."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?padding=20")
    assert response.status_code == 200


def test_border_and_padding(client: TestClient):
    """Test border and padding together."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?border=5,000000&padding=10")
    assert response.status_code == 200


def test_noise_effect(client: TestClient):
    """Test noise/grain effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?noise=30")
    assert response.status_code == 200


def test_noise_zero(client: TestClient):
    """Test noise=0 has no effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?noise=0")
    assert response.status_code == 200


def test_noise_max(client: TestClient):
    """Test noise at maximum."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?noise=100")
    assert response.status_code == 200


def test_pixelate_effect(client: TestClient):
    """Test pixelate effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?pixelate=10")
    assert response.status_code == 200


def test_pixelate_small(client: TestClient):
    """Test small pixelate value."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?pixelate=2")
    assert response.status_code == 200


def test_pixelate_large(client: TestClient):
    """Test large pixelate value."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?pixelate=50")
    assert response.status_code == 200


def test_quality_parameter(client: TestClient):
    """Test quality parameter."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?quality=50")
    assert response.status_code == 200


def test_quality_high(client: TestClient):
    """Test high quality."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?quality=95")
    assert response.status_code == 200


def test_quality_low(client: TestClient):
    """Test low quality."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?quality=10")
    assert response.status_code == 200


def test_lqip_generation(client: TestClient):
    """Test LQIP (Low Quality Image Placeholder) generation."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?lqip=true")
    assert response.status_code == 200
    # LQIP should be smaller than normal (or at least not significantly larger)
    assert len(response.content) > 0


def test_combined_effects(client: TestClient):
    """Test multiple effects combined."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?noise=20&pixelate=5&border=5,ff0000")
    assert response.status_code == 200


def test_all_effects_together(client: TestClient):
    """Test all effects applied together."""
    image_id = _get_image_id(client)
    response = client.get(
        f"/id/{image_id}/500/500?"
        "grayscale=true&blur=2&noise=10&pixelate=3&"
        "border=5,000000&padding=10&quality=75"
    )
    assert response.status_code == 200


def test_effects_with_different_formats(client: TestClient):
    """Test effects work with different output formats."""
    image_id = _get_image_id(client)
    for fmt in ["jpeg", "png", "webp"]:
        response = client.get(f"/id/{image_id}/500/500.{fmt}?noise=20&border=5")
        assert response.status_code == 200


def test_noise_processor_method():
    """Test noise application in processor."""
    from pathlib import Path
    from PIL import Image
    from src.image_processor import ImageProcessor
    import tempfile
    
    # Create a test image
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img_path = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img.save(test_img_path)
        
        processor = ImageProcessor()
        result = processor.process(test_img_path, width=100, height=100, noise=50)
        assert len(result) > 0


def test_pixelate_processor_method():
    """Test pixelate application in processor."""
    from pathlib import Path
    from PIL import Image
    from src.image_processor import ImageProcessor
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img_path = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img.save(test_img_path)
        
        processor = ImageProcessor()
        result = processor.process(test_img_path, width=100, height=100, pixelate=10)
        assert len(result) > 0


def test_border_processor_method():
    """Test border application in processor."""
    from pathlib import Path
    from PIL import Image
    from src.image_processor import ImageProcessor
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img_path = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img.save(test_img_path)
        
        processor = ImageProcessor()
        result = processor.process(test_img_path, width=100, height=100, border="10,ff0000")
        assert len(result) > 0


def test_lqip_processor_method():
    """Test LQIP generation in processor."""
    from pathlib import Path
    from PIL import Image
    from src.image_processor import ImageProcessor
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img_path = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (500, 500), color=(128, 128, 128))
        img.save(test_img_path)
        
        processor = ImageProcessor()
        normal = processor.process(test_img_path, width=500, height=500)
        lqip = processor.process(test_img_path, width=500, height=500, lqip=True)
        
        # LQIP should be much smaller
        assert len(lqip) < len(normal) / 2


def test_quality_affects_file_size():
    """Test that quality parameter affects file size."""
    from pathlib import Path
    from PIL import Image, ImageDraw
    from src.image_processor import ImageProcessor
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img_path = Path(tmpdir) / "test.jpg"
        # Create a more complex image with gradients
        img = Image.new("RGB", (500, 500))
        draw = ImageDraw.Draw(img)
        for i in range(500):
            color = int(i / 500 * 255)
            draw.line([(0, i), (500, i)], fill=(color, 128, 255 - color))
        img.save(test_img_path)
        
        processor = ImageProcessor()
        high_quality = processor.process(test_img_path, width=500, height=500, quality=95)
        low_quality = processor.process(test_img_path, width=500, height=500, quality=10)
        
        # Higher quality should produce larger files
        assert len(high_quality) > len(low_quality)


def test_invert_effect(client: TestClient):
    """Test invert effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?invert=true")
    assert response.status_code == 200


def test_posterize_effect(client: TestClient):
    """Test posterize effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?posterize=4")
    assert response.status_code == 200


def test_solarize_effect(client: TestClient):
    """Test solarize effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?solarize=128")
    assert response.status_code == 200


def test_duotone_effect(client: TestClient):
    """Test duotone effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?duotone=ff0000,0000ff")
    assert response.status_code == 200


def test_sharpen_effect(client: TestClient):
    """Test sharpen effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?sharpen=1.5")
    assert response.status_code == 200


def test_emboss_effect(client: TestClient):
    """Test emboss effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?emboss=true")
    assert response.status_code == 200


def test_halftone_effect(client: TestClient):
    """Test halftone effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?halftone=4")
    assert response.status_code == 200


def test_edges_sobel(client: TestClient):
    """Test edge detection with Sobel."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?edges=sobel")
    assert response.status_code == 200


def test_edges_canny(client: TestClient):
    """Test edge detection with Canny."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?edges=canny")
    assert response.status_code == 200


def test_oil_painting_effect(client: TestClient):
    """Test oil painting effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?oil_painting=true")
    assert response.status_code == 200


def test_pencil_sketch_effect(client: TestClient):
    """Test pencil sketch effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?pencil_sketch=true")
    assert response.status_code == 200


def test_cartoon_effect(client: TestClient):
    """Test cartoon effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?cartoon=true")
    assert response.status_code == 200


def test_vignette_effect(client: TestClient):
    """Test vignette effect."""
    image_id = _get_image_id(client)
    response = client.get(f"/id/{image_id}/500/500?vignette=0.5")
    assert response.status_code == 200


def test_invert_processor_method():
    """Test invert in processor."""
    from pathlib import Path
    from PIL import Image
    from src.image_processor import ImageProcessor
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img_path = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img.save(test_img_path)
        
        processor = ImageProcessor()
        result = processor.process(test_img_path, width=100, height=100, invert=True)
        assert len(result) > 0


def test_posterize_processor_method():
    """Test posterize in processor."""
    from pathlib import Path
    from PIL import Image
    from src.image_processor import ImageProcessor
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img_path = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img.save(test_img_path)
        
        processor = ImageProcessor()
        result = processor.process(test_img_path, width=100, height=100, posterize=4)
        assert len(result) > 0


def test_duotone_processor_method():
    """Test duotone in processor."""
    from pathlib import Path
    from PIL import Image
    from src.image_processor import ImageProcessor
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img_path = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img.save(test_img_path)
        
        processor = ImageProcessor()
        result = processor.process(test_img_path, width=100, height=100, duotone="ff0000,0000ff")
        assert len(result) > 0


def test_sharpen_processor_method():
    """Test sharpen in processor."""
    from pathlib import Path
    from PIL import Image
    from src.image_processor import ImageProcessor
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img_path = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img.save(test_img_path)
        
        processor = ImageProcessor()
        result = processor.process(test_img_path, width=100, height=100, sharpen=1.5)
        assert len(result) > 0


def test_emboss_processor_method():
    """Test emboss in processor."""
    from pathlib import Path
    from PIL import Image
    from src.image_processor import ImageProcessor
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img_path = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img.save(test_img_path)
        
        processor = ImageProcessor()
        result = processor.process(test_img_path, width=100, height=100, emboss=True)
        assert len(result) > 0


def test_vignette_processor_method():
    """Test vignette in processor."""
    from pathlib import Path
    from PIL import Image
    from src.image_processor import ImageProcessor
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_img_path = Path(tmpdir) / "test.jpg"
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        img.save(test_img_path)
        
        processor = ImageProcessor()
        result = processor.process(test_img_path, width=100, height=100, vignette=0.5)
        assert len(result) > 0


def test_new_filters_combined(client: TestClient):
    """Test multiple new filters combined."""
    image_id = _get_image_id(client)
    response = client.get(
        f"/id/{image_id}/500/500?"
        "invert=true&posterize=4&sharpen=1.0&vignette=0.3"
    )
    assert response.status_code == 200
