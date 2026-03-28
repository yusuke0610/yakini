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

# 依存関係 → フレームワーク名のマッピング
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
    "boto3": "AWS",
    "google-cloud-storage": "GCP",
    "azure-storage-blob": "Azure",
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
}

# ルートファイル → スキル名のマッピング
_ROOT_FILE_SKILLS: Dict[str, str] = {
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
    "docker-compose.yaml": "Docker Compose",
    ".github": "GitHub Actions",
    "terraform": "Terraform",
    ".terraform": "Terraform",
    "Makefile": "Build Automation",
    "Jenkinsfile": "Jenkins",
    ".gitlab-ci.yml": "GitLab CI",
    ".circleci": "CircleCI",
    "go.mod": "Go",
    "Gemfile": "Ruby",
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


def detect_from_root_files(root_files: List[str]) -> List[str]:
    """ルートレベルのファイル/ディレクトリ名からスキルを検出する。重複は除去する。"""
    detected: List[str] = []
    seen: set = set()
    for fname in root_files:
        skill = _ROOT_FILE_SKILLS.get(fname)
        if skill and skill not in seen:
            seen.add(skill)
            detected.append(skill)
    return detected


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
    """pyproject.toml から依存関係名を抽出する（単純な行ベース）。"""
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
            if stripped.startswith("[") or (
                not stripped.startswith('"')
                and not stripped.startswith("'")
                and "=" in stripped
                and not stripped.startswith("#")
                and "]" not in stripped
            ):
                # poetry 形式: name = "^1.0"
                name = stripped.split("=")[0].strip().lower()
                if name and name != "python":
                    packages.append(name)
                continue
            if stripped.startswith('"') or stripped.startswith("'"):
                # PEP 621 形式: "fastapi>=0.100"
                name = stripped.strip("\"', ")
                name = name.split(">=")[0].split("<=")[0].split("==")[0]
                name = name.split("!=")[0].split("~=")[0].split(">")[0]
                name = name.split("<")[0].split("[")[0].split(";")[0].strip()
                if name:
                    packages.append(name.lower())
                continue
            if stripped == "]" or (stripped.startswith("[") and stripped != "]"):
                in_deps = False
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
