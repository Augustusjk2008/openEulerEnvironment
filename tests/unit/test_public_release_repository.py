from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_public_root_files_exist():
    assert (ROOT / "README.md").exists()
    assert (ROOT / "LICENSE").exists()
    assert (ROOT / ".github" / "workflows" / "ci.yml").exists()


def test_gitignore_keeps_packaging_specs_and_ignores_local_coverage():
    content = read_text(".gitignore")
    assert ".coverage" in content
    assert "*.spec" not in content


def test_coveragerc_has_no_absolute_workspace_path():
    content = read_text(".coveragerc")
    assert "H:\\WorkSpace\\PythonWorkspace\\openEulerEnvironment\\src\\" not in content


def test_requirements_include_public_runtime_dependencies():
    content = read_text("requirements.txt")
    assert "PyQt-Fluent-Widgets" in content
    assert "python-docx" in content


def test_user_manual_uses_current_version_and_no_missing_public_images():
    content = read_text("docs/00.本程序怎么使用.md")
    assert "v0.0.8" in content
    for missing_image in [
        "login_page.png",
        "ftp_page.png",
        "data_visualization_page.png",
        "data_visualization_remote_dialog.png",
    ]:
        assert missing_image not in content
