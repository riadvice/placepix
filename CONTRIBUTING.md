# Contributing to PlacePix

Thanks for your interest in contributing!

## Quick Start

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Start the server (creates venv automatically)
./run.sh

# 3. Run tests
./run_tests.sh
```

Linux users may need OpenCV system libraries:
```bash
sudo apt-get install libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
```

Place sample images in `./images/` (subdirectories become categories).

## Code Style

- Follow **PEP 8** conventions.
- Keep functions focused and modular.
- Add tests for new features and bug fixes.
- Update the **README** if user-facing behavior changes.

## Project Structure

| Path | Description |
|------|-------------|
| `src/main.py` | FastAPI app, routes, and request handlers |
| `src/image_processor.py` | Image resizing, filters, and effects (Pillow/OpenCV) |
| `src/image_manager.py` | File/S3 image loading, caching, and metadata |
| `src/config.py` | Pydantic settings and environment variable mapping |
| `src/admin.py` | CLI stats tool (`placepix-stats`) |
| `src/ai_generator.py` | OVHcloud AI Endpoints integration |
| `src/metrics.py` | Request metrics and analytics |
| `tests/` | pytest test suite |
| `templates/` | Jinja2 HTML templates |
| `static/` | CSS, JS, and localized JSON strings |

## Submitting Changes

1. Open an issue to discuss large changes before writing code.
2. Fork the repo and create a feature branch.
3. Ensure tests pass.
4. Submit a pull request with a clear description of the change.

## License

By contributing, you agree that your contributions will be licensed under the **MIT License**.
