from app_metadata import APP_DISPLAY_NAME, APP_RELEASE_LABEL, APP_VERSION


def test_public_release_version_is_current():
    assert APP_VERSION == "0.0.8"
    assert APP_RELEASE_LABEL == "v0.0.8"


def test_public_display_name_is_stable():
    assert APP_DISPLAY_NAME == "RTopenEuler 系统管理工具"
