from ui.resource_utils import get_asset_path


def test_get_asset_path_returns_none_when_asset_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("ui.resource_utils.get_program_dir", lambda: str(tmp_path))
    assert get_asset_path("logo.png") is None


def test_get_asset_path_returns_absolute_path_when_asset_exists(tmp_path, monkeypatch):
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    logo = assets_dir / "logo.png"
    logo.write_bytes(b"logo")

    monkeypatch.setattr("ui.resource_utils.get_program_dir", lambda: str(tmp_path))

    assert get_asset_path("logo.png") == str(logo)
