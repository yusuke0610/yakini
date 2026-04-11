"""スキルカテゴリ分類の定義と分類関数。"""

from typing import Dict, List, Set

# スキルカテゴリ定義: カテゴリ名 → スキル一覧
SKILL_CATEGORIES: Dict[str, List[str]] = {
    "language": [
        "Python",
        "JavaScript",
        "TypeScript",
        "Go",
        "Rust",
        "Java",
        "Kotlin",
        "C",
        "C++",
        "C#",
        "Ruby",
        "PHP",
        "Swift",
        "Dart",
        "Scala",
        "Elixir",
        "Haskell",
        "Lua",
        "R",
        "Julia",
        "Shell",
        "SQL",
    ],
    "frontend_framework": [
        "React",
        "Vue",
        "Angular",
        "Svelte",
        "Next.js",
        "Nuxt.js",
        "Astro",
        "Gatsby",
        "Remix",
    ],
    "backend_framework": [
        "FastAPI",
        "Django",
        "Flask",
        "Express",
        "NestJS",
        "Spring Boot",
        "Rails",
        "Laravel",
        "Gin",
        "Echo",
        "Actix",
        "Phoenix",
        "ASP.NET",
        "Fiber",
        "SQLAlchemy",
        "Celery",
    ],
    "mobile": [
        "React Native",
        "Flutter",
        "SwiftUI",
        "Jetpack Compose",
        "Ionic",
    ],
    "database": [
        "PostgreSQL",
        "MySQL",
        "MongoDB",
        "Redis",
        "SQLite",
        "DynamoDB",
        "Elasticsearch",
        "Cassandra",
        "Neo4j",
        "Firebase",
    ],
    "infrastructure": [
        "Docker",
        "Docker Compose",
        "Kubernetes",
        "Terraform",
        "Pulumi",
        "Ansible",
        "CloudFormation",
        "Helm",
    ],
    "cloud": [
        "AWS",
        "GCP",
        "Azure",
    ],
    "cicd": [
        "GitHub Actions",
        "GitLab CI",
        "Jenkins",
        "CircleCI",
        "ArgoCD",
    ],
    "monitoring": [
        "Prometheus",
        "Grafana",
        "Datadog",
        "Sentry",
        "OpenTelemetry",
    ],
    "ml": [
        "TensorFlow",
        "PyTorch",
        "scikit-learn",
        "Hugging Face",
        "LangChain",
        "MLflow",
        "Pandas",
        "NumPy",
        "Jupyter",
    ],
    "data_engineering": [
        "Apache Spark",
        "Apache Kafka",
        "Airflow",
        "dbt",
        "BigQuery",
        "Redshift",
        "Snowflake",
    ],
    "security": [
        "OAuth",
        "JWT",
        "OpenID Connect",
        "Vault",
        "SAST",
        "DAST",
    ],
    "other": [
        "GraphQL",
        "gRPC",
        "REST API",
        "WebSocket",
        "Nginx",
        "Linux",
        "Git",
        "Figma",
        "Build Automation",
    ],
}

# 逆引き参照: スキル名 → カテゴリ名
_SKILL_TO_CATEGORY: Dict[str, str] = {}
for _cat, _skills in SKILL_CATEGORIES.items():
    for _s in _skills:
        _SKILL_TO_CATEGORY[_s] = _cat


def get_skill_category(skill: str) -> str:
    """スキル名からカテゴリ名を返す。未知のスキルは "other" を返す。"""
    return _SKILL_TO_CATEGORY.get(skill, "other")


def get_all_skills() -> Set[str]:
    """全スキル名のセットを返す。"""
    return set(_SKILL_TO_CATEGORY.keys())
