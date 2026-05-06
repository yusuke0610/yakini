"""
リポジトリ解析モジュール。

言語 ratio 算出・フレームワーク検出・依存関係パース（純粋関数中心）を行う。
"""

import json
import re
from typing import Dict, List

# 依存関係ファイル名のセット
DEPENDENCY_FILES = {
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "pom.xml",
    "go.mod",
}

# 依存関係 → フレームワーク名のマッピング（フレームワーク・ライブラリのみ）
DEPENDENCY_TO_FRAMEWORK: Dict[str, str] = {
    # Python 系
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "sqlalchemy": "SQLAlchemy",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "tensorflow": "TensorFlow",
    "torch": "PyTorch",
    "pytorch": "PyTorch",
    "langchain": "LangChain",
    "celery": "Celery",
    "airflow": "Airflow",
    "apache-airflow": "Airflow",
    "mlflow": "MLflow",
    "sentry-sdk": "Sentry",
    "prometheus-client": "Prometheus",
    # Node 系
    "react": "React",
    "react-dom": "React",
    "next": "Next.js",
    "vue": "Vue",
    "nuxt": "Nuxt.js",
    "angular": "Angular",
    "@angular/core": "Angular",
    "svelte": "Svelte",
    "express": "Express",
    "@nestjs/core": "NestJS",
    "gatsby": "Gatsby",
    "remix": "Remix",
    "astro": "Astro",
    "react-native": "React Native",
    "prisma": "PostgreSQL",
    "mongoose": "MongoDB",
    "redis": "Redis",
    "ioredis": "Redis",
    "graphql": "GraphQL",
    "@apollo/server": "GraphQL",
    # Java 系 (artifactId)
    "spring-boot": "Spring Boot",
    "spring-boot-starter": "Spring Boot",
    "spring-boot-starter-web": "Spring Boot",
    # Go 系
    "github.com/gin-gonic/gin": "Gin",
    "github.com/labstack/echo": "Echo",
    "github.com/gofiber/fiber": "Fiber",
    # クラウド SDK（フレームワーク扱い）
    "boto3": "AWS",
}

# 依存関係 → インフラ・クラウドプロバイダー名のマッピング
INFRA_FROM_DEPENDENCIES: Dict[str, str] = {
    "boto3": "AWS",
    "botocore": "AWS",
    "google-cloud-storage": "GCP",
    "google-cloud-run": "GCP",
    "google-cloud-bigquery": "GCP",
    "google-cloud-pubsub": "GCP",
    "azure-storage-blob": "Azure",
    "azure-identity": "Azure",
    "azure-mgmt-compute": "Azure",
    "pulumi": "Pulumi",
    "aws-cdk-lib": "AWS CDK",
    "constructs": "AWS CDK",
}

# ルートファイル → DevTools 名のマッピング
_DEVTOOL_ROOT_FILES: Dict[str, str] = {
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    ".github": "GitHub Actions",
    "Makefile": "Build Automation",
    "Jenkinsfile": "Jenkins",
    ".gitlab-ci.yml": "GitLab CI",
    ".circleci": "CircleCI",
}

# ルートファイル → インフラツール名のマッピング
_INFRA_ROOT_FILES: Dict[str, str] = {
    "terraform": "Terraform",
    ".terraform": "Terraform",
    "infra": "Terraform",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "helm": "Helm",
    "cdk.json": "AWS CDK",
    "pulumi.yaml": "Pulumi",
    "pulumi.yml": "Pulumi",
}


def compute_language_ratios(languages: Dict[str, int]) -> Dict[str, float]:
    """
    言語バイト数から各言語の比率を算出する。

    0除算ガード付き。合計バイト数が0の場合は空の辞書を返す。
    """
    total = sum(languages.values())
    if total == 0:
        return {}
    return {lang: count / total for lang, count in languages.items()}


def detect_devtools_from_root_files(root_files: List[str]) -> List[str]:
    """ルートレベルのファイル/ディレクトリ名から DevTools を検出する。重複は除去する。"""
    detected: List[str] = []
    seen: set = set()
    for fname in root_files:
        tool = _DEVTOOL_ROOT_FILES.get(fname)
        if tool and tool not in seen:
            seen.add(tool)
            detected.append(tool)
    return detected


def detect_infras_from_root_files(root_files: List[str]) -> List[str]:
    """ルートレベルのファイル/ディレクトリ名からインフラツールを検出する。重複は除去する。"""
    detected: List[str] = []
    seen: set = set()
    for fname in root_files:
        tool = _INFRA_ROOT_FILES.get(fname)
        if tool and tool not in seen:
            seen.add(tool)
            detected.append(tool)
    return detected


def detect_infras_from_dependencies(dependencies: List[str]) -> List[str]:
    """依存関係名のリストから INFRA_FROM_DEPENDENCIES でインフラ名を検出する。

    重複を除去し、最初に出現した順序を保つ。
    """
    detected: List[str] = []
    seen: set = set()
    for dep in dependencies:
        infra = INFRA_FROM_DEPENDENCIES.get(dep.lower())
        if infra and infra not in seen:
            seen.add(infra)
            detected.append(infra)
    return detected


def detect_from_dependencies(dependencies: List[str]) -> List[str]:
    """依存関係名のリストから DEPENDENCY_TO_FRAMEWORK でフレームワーク名を検出する。

    重複を除去し、最初に出現した順序を保つ。
    """
    detected: List[str] = []
    seen: set = set()
    for dep in dependencies:
        framework = DEPENDENCY_TO_FRAMEWORK.get(dep.lower())
        if framework and framework not in seen:
            seen.add(framework)
            detected.append(framework)
    return detected


def merge_frameworks(*framework_lists: List[str]) -> List[str]:
    """複数のフレームワークリストを順序を保ったままマージし、重複を除去する。"""
    merged: List[str] = []
    seen: set = set()
    for fw_list in framework_lists:
        for fw in fw_list:
            if fw not in seen:
                seen.add(fw)
                merged.append(fw)
    return merged


def parse_requirements_txt(content: str) -> List[str]:
    """requirements.txt からパッケージ名を抽出する。"""
    packages: List[str] = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # バージョン指定子を削除: pkg>=1.0, pkg==1.0, pkg[extra]
        name = line.split(">=")[0].split("<=")[0].split("==")[0]
        name = name.split("!=")[0].split("~=")[0].split(">")[0].split("<")[0]
        name = name.split("[")[0].split(";")[0].strip()
        if name:
            packages.append(name.lower())
    return packages


def parse_pyproject_toml(content: str) -> List[str]:
    """pyproject.toml から依存関係名を抽出する（単純な行ベース）。

    以下の形式に対応:
    - PEP 621: dependencies = ["fastapi>=0.100"]
    - Poetry 単純値: fastapi = "^0.100"
    - Poetry インラインテーブル: fastapi = {extras = ["standard"], version = "^0.109.0"}
    """
    packages: List[str] = []
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped in (
            "[project.dependencies]",
            "[tool.poetry.dependencies]",
            "dependencies = [",
        ):
            in_deps = True
            continue
        if in_deps:
            # 新セクション開始: deps 解析を終了
            if stripped.startswith("["):
                in_deps = False
                continue
            # PEP 621 配列の終端
            if stripped == "]":
                in_deps = False
                continue
            # PEP 621 形式: "fastapi>=0.100"
            if stripped.startswith('"') or stripped.startswith("'"):
                name = stripped.strip("\"', ")
                name = name.split(">=")[0].split("<=")[0].split("==")[0]
                name = name.split("!=")[0].split("~=")[0].split(">")[0]
                name = name.split("<")[0].split("[")[0].split(";")[0].strip()
                if name:
                    packages.append(name.lower())
                continue
            # Poetry 形式: name = "^1.0" または name = {extras = [...], version = "..."}
            if "=" in stripped and not stripped.startswith("#"):
                name = stripped.split("=")[0].strip().lower()
                if name and name != "python":
                    packages.append(name)
    return packages


def parse_package_json(content: str) -> List[str]:
    """package.json から依存関係名を抽出する。"""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return []
    packages: List[str] = []
    for key in ("dependencies", "devDependencies"):
        deps = data.get(key)
        if isinstance(deps, dict):
            packages.extend(dep.lower() for dep in deps)
    return packages


def parse_pom_xml(content: str) -> List[str]:
    """pom.xml から artifactId の値を抽出する（基本的な正規表現）。"""
    return [m.lower() for m in re.findall(r"<artifactId>([^<]+)</artifactId>", content)]


def parse_go_mod(content: str) -> List[str]:
    """go.mod の require ブロックからモジュールパスを抽出する。"""
    modules: List[str] = []
    in_require = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_require = True
            continue
        if in_require:
            if stripped == ")":
                in_require = False
                continue
            parts = stripped.split()
            if parts:
                modules.append(parts[0].lower())
    return modules
