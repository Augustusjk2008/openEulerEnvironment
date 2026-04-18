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


def test_public_scripts_do_not_hardcode_local_paths_or_conda_env():
    banned = [
        "H:\\Resources\\RTLinux\\Environment",
        "conda activate pyqt5_env",
    ]
    for relative_path in ["run.bat", "run_tests.bat", "run_tests.ps1"]:
        content = read_text(relative_path)
        for needle in banned:
            assert needle not in content


def test_vm_defaults_are_examples_not_personal_machine_values():
    banned = [
        "192.168.56.132",
        "jiangkai@",
        'username: "jiangkai"',
    ]
    for relative_path in [
        "run_tests.bat",
        "run_tests.ps1",
        "tests/integration/conftest.py",
        "tests/config/test_env.yaml",
    ]:
        content = read_text(relative_path)
        for needle in banned:
            assert needle not in content


def test_public_packaging_script_exposes_only_pyinstaller_commands():
    content = read_text("run.bat")
    assert "openEulerManage.spec" in content
    assert "cxfreeze-env" not in content
    assert "cxfreeze-build" not in content
    assert "cxfreeze-install" not in content
    assert "cxfreeze-all" not in content
    assert "setup_cxfreeze.py" not in content
    assert "requirements-cxfreeze38.txt" not in content


def test_public_repo_keeps_one_tracked_pyinstaller_spec_and_no_cxfreeze_files():
    assert (ROOT / "openEulerManage.spec").exists()
    for relative_path in [
        "setup_cxfreeze.py",
        "build_helpers/cxfreeze_config.py",
        "requirements-cxfreeze38.txt",
        "tests/unit/test_cxfreeze_config.py",
    ]:
        assert not (ROOT / relative_path).exists(), relative_path
