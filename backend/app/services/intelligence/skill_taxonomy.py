"""
Deterministic skill taxonomy for mapping GitHub data to normalized skills.

This module contains static mappings — no LLM usage.
"""

from typing import Dict, List, Set


# ── Skill Categories ────────────────────────────────────────────────────
# Each skill belongs to exactly one category.

SKILL_CATEGORIES: Dict[str, List[str]] = {
    "language": [
        "Python", "JavaScript", "TypeScript", "Go", "Rust", "Java", "Kotlin",
        "C", "C++", "C#", "Ruby", "PHP", "Swift", "Dart", "Scala", "Elixir",
        "Haskell", "Lua", "R", "Julia", "Shell", "SQL",
    ],
    "frontend_framework": [
        "React", "Vue", "Angular", "Svelte", "Next.js", "Nuxt.js", "Astro",
        "Gatsby", "Remix",
    ],
    "backend_framework": [
        "FastAPI", "Django", "Flask", "Express", "NestJS", "Spring Boot",
        "Rails", "Laravel", "Gin", "Echo", "Actix", "Phoenix", "ASP.NET",
        "Fiber", "SQLAlchemy", "Celery",
    ],
    "mobile": [
        "React Native", "Flutter", "SwiftUI", "Jetpack Compose", "Ionic",
    ],
    "database": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "DynamoDB",
        "Elasticsearch", "Cassandra", "Neo4j", "Firebase",
    ],
    "infrastructure": [
        "Docker", "Docker Compose", "Kubernetes", "Terraform", "Pulumi",
        "Ansible", "CloudFormation", "Helm",
    ],
    "cloud": [
        "AWS", "GCP", "Azure",
    ],
    "cicd": [
        "GitHub Actions", "GitLab CI", "Jenkins", "CircleCI", "ArgoCD",
    ],
    "monitoring": [
        "Prometheus", "Grafana", "Datadog", "Sentry", "OpenTelemetry",
    ],
    "ml": [
        "TensorFlow", "PyTorch", "scikit-learn", "Hugging Face", "LangChain",
        "MLflow", "Pandas", "NumPy", "Jupyter",
    ],
    "data_engineering": [
        "Apache Spark", "Apache Kafka", "Airflow", "dbt", "BigQuery",
        "Redshift", "Snowflake",
    ],
    "security": [
        "OAuth", "JWT", "OpenID Connect", "Vault", "SAST", "DAST",
    ],
    "other": [
        "GraphQL", "gRPC", "REST API", "WebSocket", "Nginx", "Linux",
        "Git", "Figma", "Build Automation",
    ],
}

# Reverse lookup: skill → category
_SKILL_TO_CATEGORY: Dict[str, str] = {}
for _cat, _skills in SKILL_CATEGORIES.items():
    for _s in _skills:
        _SKILL_TO_CATEGORY[_s] = _cat


def get_skill_category(skill: str) -> str:
    return _SKILL_TO_CATEGORY.get(skill, "other")


def get_all_skills() -> Set[str]:
    return set(_SKILL_TO_CATEGORY.keys())


# ── GitHub Language → Skill ─────────────────────────────────────────────
# Maps GitHub's language detection names to our normalized skill names.

LANGUAGE_TO_SKILL: Dict[str, str] = {
    "Python": "Python",
    "JavaScript": "JavaScript",
    "TypeScript": "TypeScript",
    "Go": "Go",
    "Rust": "Rust",
    "Java": "Java",
    "Kotlin": "Kotlin",
    "C": "C",
    "C++": "C++",
    "C#": "C#",
    "Ruby": "Ruby",
    "PHP": "PHP",
    "Swift": "Swift",
    "Dart": "Dart",
    "Scala": "Scala",
    "Elixir": "Elixir",
    "Haskell": "Haskell",
    "Lua": "Lua",
    "R": "R",
    "Julia": "Julia",
    "Shell": "Shell",
    "HCL": "Terraform",
    "Dockerfile": "Docker",
    "Jupyter Notebook": "Jupyter",
}


# ── Repo Topic → Skill(s) ──────────────────────────────────────────────
# Maps GitHub repository topics to skills.

TOPIC_TO_SKILLS: Dict[str, List[str]] = {
    # Frameworks
    "react": ["React"],
    "reactjs": ["React"],
    "vue": ["Vue"],
    "vuejs": ["Vue"],
    "angular": ["Angular"],
    "svelte": ["Svelte"],
    "nextjs": ["Next.js"],
    "next-js": ["Next.js"],
    "nuxt": ["Nuxt.js"],
    "nuxtjs": ["Nuxt.js"],
    "astro": ["Astro"],
    "gatsby": ["Gatsby"],
    "remix": ["Remix"],
    "fastapi": ["FastAPI"],
    "django": ["Django"],
    "flask": ["Flask"],
    "express": ["Express"],
    "expressjs": ["Express"],
    "nestjs": ["NestJS"],
    "spring-boot": ["Spring Boot"],
    "spring": ["Spring Boot"],
    "rails": ["Rails"],
    "ruby-on-rails": ["Rails"],
    "laravel": ["Laravel"],
    "gin": ["Gin"],
    "actix": ["Actix"],
    "phoenix": ["Phoenix"],
    "aspnet": ["ASP.NET"],
    # Mobile
    "react-native": ["React Native"],
    "flutter": ["Flutter"],
    "swiftui": ["SwiftUI"],
    "jetpack-compose": ["Jetpack Compose"],
    "ionic": ["Ionic"],
    # Databases
    "postgresql": ["PostgreSQL"],
    "postgres": ["PostgreSQL"],
    "mysql": ["MySQL"],
    "mongodb": ["MongoDB"],
    "redis": ["Redis"],
    "sqlite": ["SQLite"],
    "dynamodb": ["DynamoDB"],
    "elasticsearch": ["Elasticsearch"],
    "neo4j": ["Neo4j"],
    "firebase": ["Firebase"],
    # Infrastructure
    "docker": ["Docker"],
    "kubernetes": ["Kubernetes"],
    "k8s": ["Kubernetes"],
    "terraform": ["Terraform"],
    "pulumi": ["Pulumi"],
    "ansible": ["Ansible"],
    "helm": ["Helm"],
    "cloudformation": ["CloudFormation"],
    # Cloud
    "aws": ["AWS"],
    "gcp": ["GCP"],
    "google-cloud": ["GCP"],
    "azure": ["Azure"],
    # CI/CD
    "github-actions": ["GitHub Actions"],
    "gitlab-ci": ["GitLab CI"],
    "jenkins": ["Jenkins"],
    "circleci": ["CircleCI"],
    "argocd": ["ArgoCD"],
    # Monitoring
    "prometheus": ["Prometheus"],
    "grafana": ["Grafana"],
    "datadog": ["Datadog"],
    "sentry": ["Sentry"],
    "opentelemetry": ["OpenTelemetry"],
    # ML / Data
    "tensorflow": ["TensorFlow"],
    "pytorch": ["PyTorch"],
    "scikit-learn": ["scikit-learn"],
    "sklearn": ["scikit-learn"],
    "huggingface": ["Hugging Face"],
    "langchain": ["LangChain"],
    "mlflow": ["MLflow"],
    "pandas": ["Pandas"],
    "numpy": ["NumPy"],
    "machine-learning": ["scikit-learn"],
    "deep-learning": ["PyTorch"],
    "spark": ["Apache Spark"],
    "apache-spark": ["Apache Spark"],
    "kafka": ["Apache Kafka"],
    "apache-kafka": ["Apache Kafka"],
    "airflow": ["Airflow"],
    "dbt": ["dbt"],
    "bigquery": ["BigQuery"],
    "snowflake": ["Snowflake"],
    # Other
    "graphql": ["GraphQL"],
    "grpc": ["gRPC"],
    "rest-api": ["REST API"],
    "websocket": ["WebSocket"],
    "nginx": ["Nginx"],
    "linux": ["Linux"],
}


# ── Description Keyword → Skill(s) ─────────────────────────────────────
# Keywords found in repo descriptions that indicate specific skill usage.
# Checked via case-insensitive substring match.

DESCRIPTION_KEYWORDS: Dict[str, List[str]] = {
    "fastapi": ["FastAPI"],
    "django": ["Django"],
    "flask": ["Flask"],
    "express": ["Express"],
    "nestjs": ["NestJS"],
    "spring boot": ["Spring Boot"],
    "react native": ["React Native"],
    "react": ["React"],
    "vue": ["Vue"],
    "angular": ["Angular"],
    "next.js": ["Next.js"],
    "nuxt": ["Nuxt.js"],
    "flutter": ["Flutter"],
    "docker": ["Docker"],
    "kubernetes": ["Kubernetes"],
    "terraform": ["Terraform"],
    "aws": ["AWS"],
    "gcp": ["GCP"],
    "google cloud": ["GCP"],
    "azure": ["Azure"],
    "postgresql": ["PostgreSQL"],
    "postgres": ["PostgreSQL"],
    "mongodb": ["MongoDB"],
    "redis": ["Redis"],
    "graphql": ["GraphQL"],
    "grpc": ["gRPC"],
    "machine learning": ["scikit-learn"],
    "deep learning": ["PyTorch"],
    "tensorflow": ["TensorFlow"],
    "pytorch": ["PyTorch"],
    "langchain": ["LangChain"],
    "kafka": ["Apache Kafka"],
    "airflow": ["Airflow"],
    "prometheus": ["Prometheus"],
    "grafana": ["Grafana"],
}
