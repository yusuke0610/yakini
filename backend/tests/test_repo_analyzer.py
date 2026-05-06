"""repo_analyzer モジュールのユニットテスト。"""

from app.services.intelligence.github.repo_analyzer import (
    compute_language_ratios,
    detect_devtools_from_root_files,
    detect_from_dependencies,
    detect_infras_from_dependencies,
    detect_infras_from_root_files,
    merge_frameworks,
    parse_package_json,
    parse_pyproject_toml,
    parse_requirements_txt,
)

# ── 言語 ratio 算出テスト ────────────────────────────────────────────────


def test_compute_language_ratios_basic() -> None:
    """言語バイト数から比率が正しく算出されること。"""
    languages = {"Python": 80, "JavaScript": 20}
    ratios = compute_language_ratios(languages)
    assert abs(ratios["Python"] - 0.8) < 1e-9
    assert abs(ratios["JavaScript"] - 0.2) < 1e-9


def test_compute_language_ratios_single() -> None:
    """1言語のみの場合は比率が 1.0 となること。"""
    ratios = compute_language_ratios({"Python": 100})
    assert ratios["Python"] == 1.0


def test_compute_language_ratios_zero_guard() -> None:
    """合計バイト数が 0 の場合は空の辞書を返すこと（0除算ガード）。"""
    ratios = compute_language_ratios({})
    assert ratios == {}


def test_compute_language_ratios_all_zero_bytes() -> None:
    """全言語のバイト数が 0 の場合も空の辞書を返すこと。"""
    ratios = compute_language_ratios({"Python": 0, "Go": 0})
    assert ratios == {}


# ── フレームワーク検出テスト ─────────────────────────────────────────────


def test_detect_from_root_files_requirements_txt_fastapi() -> None:
    """requirements.txt に fastapi が含まれる場合、parse 後に FastAPI が検出されること。"""
    content = "fastapi>=0.100\nuvicorn\n"
    packages = parse_requirements_txt(content)
    assert "fastapi" in packages


def test_detect_from_root_files_package_json_react() -> None:
    """package.json に react が含まれる場合、parse 後に react が検出されること。"""
    content = '{"dependencies": {"react": "^18.0.0"}}'
    packages = parse_package_json(content)
    assert "react" in packages


def test_detect_devtools_dockerfile() -> None:
    """Dockerfile があれば Docker が DevTools として検出されること。"""
    result = detect_devtools_from_root_files(["Dockerfile"])
    assert "Docker" in result


def test_detect_devtools_github_actions() -> None:
    """.github があれば GitHub Actions が DevTools として検出されること。"""
    result = detect_devtools_from_root_files([".github"])
    assert "GitHub Actions" in result


def test_detect_devtools_docker_compose_no_duplicates() -> None:
    """docker-compose.yml と docker-compose.yaml は両方 Docker Compose に対応し重複しないこと。"""
    result = detect_devtools_from_root_files(["docker-compose.yml", "docker-compose.yaml"])
    assert result.count("Docker Compose") == 1


def test_detect_infras_terraform() -> None:
    """terraform があれば Terraform がインフラとして検出されること。"""
    result = detect_infras_from_root_files(["terraform"])
    assert "Terraform" in result


def test_detect_infras_no_duplicates() -> None:
    """terraform と .terraform は両方 Terraform に対応し重複しないこと。"""
    result = detect_infras_from_root_files(["terraform", ".terraform"])
    assert result.count("Terraform") == 1


def test_detect_infras_infra_directory() -> None:
    """infra/ ディレクトリがあれば Terraform として検出されること。"""
    result = detect_infras_from_root_files(["infra"])
    assert "Terraform" in result


def test_detect_infras_kubernetes_directories() -> None:
    """k8s / kubernetes ディレクトリがあれば Kubernetes として検出されること。"""
    assert "Kubernetes" in detect_infras_from_root_files(["k8s"])
    assert "Kubernetes" in detect_infras_from_root_files(["kubernetes"])


# ── detect_infras_from_dependencies テスト ──────────────────────────────


def test_detect_infras_from_dependencies_aws() -> None:
    """boto3 があれば AWS として検出されること。"""
    result = detect_infras_from_dependencies(["boto3"])
    assert "AWS" in result


def test_detect_infras_from_dependencies_gcp() -> None:
    """google-cloud-storage があれば GCP として検出されること。"""
    result = detect_infras_from_dependencies(["google-cloud-storage"])
    assert "GCP" in result


def test_detect_infras_from_dependencies_azure() -> None:
    """azure-storage-blob があれば Azure として検出されること。"""
    result = detect_infras_from_dependencies(["azure-storage-blob"])
    assert "Azure" in result


def test_detect_infras_from_dependencies_no_duplicate() -> None:
    """boto3 と botocore は両方 AWS にマップされ重複しないこと。"""
    result = detect_infras_from_dependencies(["boto3", "botocore"])
    assert result.count("AWS") == 1


def test_detect_infras_from_dependencies_frameworks_excluded() -> None:
    """fastapi など通常フレームワークはインフラとして検出されないこと。"""
    result = detect_infras_from_dependencies(["fastapi", "react"])
    assert result == []


# ── parse_pyproject_toml テスト ─────────────────────────────────────────


def test_parse_pyproject_toml_pep621() -> None:
    """PEP 621 形式の dependencies = [...] から依存名が抽出されること。"""
    content = '[project]\ndependencies = [\n    "fastapi>=0.100",\n    "uvicorn[standard]",\n]\n'
    result = parse_pyproject_toml(content)
    assert "fastapi" in result
    assert "uvicorn" in result


def test_parse_pyproject_toml_poetry_simple() -> None:
    """Poetry の name = "version" 形式から依存名が抽出されること。"""
    content = "[tool.poetry.dependencies]\npython = \"^3.11\"\nfastapi = \"^0.109.0\"\n"
    result = parse_pyproject_toml(content)
    assert "fastapi" in result
    assert "python" not in result


def test_parse_pyproject_toml_poetry_extras_inline_table() -> None:
    """Poetry の extras インラインテーブル形式が正しく解析されること。"""
    content = '[tool.poetry.dependencies]\nfastapi = {extras = ["standard"], version = "^0.109.0"}\n'
    result = parse_pyproject_toml(content)
    assert "fastapi" in result


def test_parse_pyproject_toml_section_restart_stops_parsing() -> None:
    """新しいセクション開始で deps 解析が終了し、dev deps が混入しないこと。"""
    content = (
        "[tool.poetry.dependencies]\n"
        "fastapi = \"^0.109.0\"\n"
        "\n"
        "[tool.poetry.dev-dependencies]\n"
        "pytest = \"^7.0\"\n"
    )
    result = parse_pyproject_toml(content)
    assert "fastapi" in result
    assert "pytest" not in result


def test_parse_pyproject_toml_no_deps_section() -> None:
    """deps セクションが存在しない pyproject.toml では空リストが返ること。"""
    content = "[tool.ruff]\nline-length = 100\n"
    result = parse_pyproject_toml(content)
    assert result == []


def test_detect_devtools_empty_input() -> None:
    """空リストを渡した場合は空リストが返ること。"""
    result = detect_devtools_from_root_files([])
    assert result == []


def test_detect_devtools_unknown_file() -> None:
    """未知のファイル名は無視されること。"""
    result = detect_devtools_from_root_files(["unknown_file.xyz"])
    assert result == []


# ── requirements.txt パーステスト ────────────────────────────────────────


def test_parse_requirements_txt_basic() -> None:
    """基本的なパッケージ名が抽出されること。"""
    content = "fastapi>=0.100\nuvicorn\nsqlalchemy==2.0\n"
    result = parse_requirements_txt(content)
    assert "fastapi" in result
    assert "uvicorn" in result
    assert "sqlalchemy" in result


def test_parse_requirements_txt_ignores_comments() -> None:
    """コメント行は無視されること。"""
    content = "# コメント\nfastapi\n"
    result = parse_requirements_txt(content)
    assert "fastapi" in result
    assert len([r for r in result if r.startswith("#")]) == 0


def test_parse_requirements_txt_empty_input() -> None:
    """空文字列では空リストが返ること。"""
    result = parse_requirements_txt("")
    assert result == []


# ── package.json パーステスト ────────────────────────────────────────────


def test_parse_package_json_dependencies_and_dev() -> None:
    """dependencies と devDependencies の両方が抽出されること。"""
    content = '{"dependencies": {"react": "^18"}, "devDependencies": {"jest": "^29"}}'
    result = parse_package_json(content)
    assert "react" in result
    assert "jest" in result


def test_parse_package_json_invalid_json() -> None:
    """不正な JSON では空リストが返ること。"""
    result = parse_package_json("not json")
    assert result == []


def test_parse_package_json_empty_deps() -> None:
    """依存関係が空の場合は空リストが返ること。"""
    result = parse_package_json('{"name": "my-app"}')
    assert result == []


# ── detect_from_dependencies テスト（Issue #203） ────────────────────────


def test_detect_from_dependencies_react_and_nextjs() -> None:
    """react と next が React / Next.js として検出されること。"""
    result = detect_from_dependencies(["react", "react-dom", "next"])
    assert "React" in result
    assert "Next.js" in result
    # react と react-dom はどちらも React にマップされ重複しないこと
    assert result.count("React") == 1


def test_detect_from_dependencies_fastapi() -> None:
    """fastapi が FastAPI として検出されること。"""
    result = detect_from_dependencies(["fastapi", "uvicorn"])
    assert "FastAPI" in result


def test_detect_from_dependencies_case_insensitive() -> None:
    """大文字混じりの依存名でも検出できること。"""
    result = detect_from_dependencies(["Django", "Spring-Boot"])
    assert "Django" in result
    assert "Spring Boot" in result


def test_detect_from_dependencies_unknown_ignored() -> None:
    """マッピングに無い依存は無視されること。"""
    result = detect_from_dependencies(["unknown-lib", "my-internal-pkg"])
    assert result == []


def test_detect_from_dependencies_empty() -> None:
    """空リストでは空リストが返ること。"""
    assert detect_from_dependencies([]) == []


# ── merge_frameworks テスト ─────────────────────────────────────────────


def test_merge_frameworks_preserves_order_and_dedupes() -> None:
    """複数ソースの framework リストを順序保持してマージ・重複除去できること。"""
    root_fw = ["Docker", "GitHub Actions"]
    dep_fw = ["React", "Docker", "FastAPI"]
    result = merge_frameworks(root_fw, dep_fw)
    # root 側の順序が先
    assert result.index("Docker") < result.index("React")
    # 重複は 1 回だけ
    assert result.count("Docker") == 1
    assert set(result) == {"Docker", "GitHub Actions", "React", "FastAPI"}


def test_merge_frameworks_empty_inputs() -> None:
    """空リストのみでも空リストが返ること。"""
    assert merge_frameworks([], []) == []
