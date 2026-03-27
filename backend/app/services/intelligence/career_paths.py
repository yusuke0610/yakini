"""
決定論的なキャリア予測のための静的なキャリアパスグラフ。

各ロールの定義：
  - required_skills: このロールを示すスキル
  - required_categories: カバーすべきスキルのカテゴリ
  - next_roles: 可能なキャリア遷移
  - seniority: 順序付けのための数値レベル (1=ジュニア, 5=エグゼクティブ)

LLMは使用しません — 純粋なルールベースです。
"""

from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass
class RoleDefinition:
    role_name: str
    required_skills: List[str]
    required_categories: List[str]
    next_roles: List[str]
    seniority: int = 1


CAREER_ROLES: Dict[str, RoleDefinition] = {
    "Backend Engineer": RoleDefinition(
        role_name="Backend Engineer",
        required_skills=[
            "Python",
            "Go",
            "Java",
            "FastAPI",
            "Django",
            "Flask",
            "Express",
            "Spring Boot",
            "Gin",
            "Rails",
        ],
        required_categories=["language", "backend_framework"],
        next_roles=[
            "Senior Backend Engineer",
            "Full-Stack Developer",
            "Platform Engineer",
            "DevOps Engineer",
            "Tech Lead",
        ],
        seniority=2,
    ),
    "Frontend Engineer": RoleDefinition(
        role_name="Frontend Engineer",
        required_skills=[
            "JavaScript",
            "TypeScript",
            "React",
            "Vue",
            "Angular",
            "Svelte",
            "Next.js",
        ],
        required_categories=["language", "frontend_framework"],
        next_roles=["Senior Frontend Engineer", "Full-Stack Developer", "Tech Lead"],
        seniority=2,
    ),
    "Full-Stack Developer": RoleDefinition(
        role_name="Full-Stack Developer",
        required_skills=[
            "JavaScript",
            "TypeScript",
            "React",
            "Vue",
            "Angular",
            "Python",
            "Go",
            "FastAPI",
            "Django",
            "Express",
            "Next.js",
        ],
        required_categories=["language", "frontend_framework", "backend_framework"],
        next_roles=["Senior Full-Stack Developer", "Tech Lead", "Platform Engineer"],
        seniority=2,
    ),
    "Mobile Developer": RoleDefinition(
        role_name="Mobile Developer",
        required_skills=[
            "Swift",
            "Kotlin",
            "Dart",
            "React Native",
            "Flutter",
            "SwiftUI",
            "Jetpack Compose",
        ],
        required_categories=["language", "mobile"],
        next_roles=["Senior Mobile Developer", "Tech Lead"],
        seniority=2,
    ),
    "DevOps Engineer": RoleDefinition(
        role_name="DevOps Engineer",
        required_skills=[
            "Docker",
            "Kubernetes",
            "GitHub Actions",
            "GitLab CI",
            "Jenkins",
            "Terraform",
            "Ansible",
            "Shell",
        ],
        required_categories=["infrastructure", "cicd"],
        next_roles=["Platform Engineer", "SRE", "Cloud Architect"],
        seniority=2,
    ),
    "Platform Engineer": RoleDefinition(
        role_name="Platform Engineer",
        required_skills=[
            "Docker",
            "Kubernetes",
            "Terraform",
            "AWS",
            "GCP",
            "Azure",
            "Helm",
            "ArgoCD",
        ],
        required_categories=["infrastructure", "cloud"],
        next_roles=["Cloud Architect", "SRE", "Engineering Manager"],
        seniority=3,
    ),
    "Data Engineer": RoleDefinition(
        role_name="Data Engineer",
        required_skills=[
            "Python",
            "SQL",
            "Apache Spark",
            "Apache Kafka",
            "Airflow",
            "dbt",
            "BigQuery",
            "Snowflake",
            "Redshift",
        ],
        required_categories=["language", "data_engineering"],
        next_roles=["Senior Data Engineer", "ML Engineer", "Data Architect"],
        seniority=2,
    ),
    "ML Engineer": RoleDefinition(
        role_name="ML Engineer",
        required_skills=[
            "Python",
            "TensorFlow",
            "PyTorch",
            "scikit-learn",
            "Hugging Face",
            "MLflow",
            "Pandas",
            "NumPy",
            "Jupyter",
        ],
        required_categories=["language", "ml"],
        next_roles=["Senior ML Engineer", "AI Architect", "Research Engineer"],
        seniority=3,
    ),
    "SRE": RoleDefinition(
        role_name="SRE",
        required_skills=[
            "Docker",
            "Kubernetes",
            "Prometheus",
            "Grafana",
            "Terraform",
            "AWS",
            "GCP",
            "Shell",
            "OpenTelemetry",
        ],
        required_categories=["infrastructure", "monitoring", "cloud"],
        next_roles=["Cloud Architect", "Platform Engineer", "Engineering Manager"],
        seniority=3,
    ),
    "Security Engineer": RoleDefinition(
        role_name="Security Engineer",
        required_skills=[
            "OAuth",
            "JWT",
            "OpenID Connect",
            "Vault",
            "Docker",
            "Linux",
            "Shell",
        ],
        required_categories=["security"],
        next_roles=["Senior Security Engineer", "Cloud Architect"],
        seniority=3,
    ),
    "Cloud Architect": RoleDefinition(
        role_name="Cloud Architect",
        required_skills=["AWS", "GCP", "Azure", "Terraform", "Kubernetes", "Docker"],
        required_categories=["cloud", "infrastructure"],
        next_roles=["Engineering Manager", "CTO"],
        seniority=4,
    ),
    "Tech Lead": RoleDefinition(
        role_name="Tech Lead",
        required_skills=[],  # 特定のスキルではなく、幅広さによって決定されるロール
        required_categories=["language", "backend_framework"],
        next_roles=["Engineering Manager", "Staff Engineer"],
        seniority=3,
    ),
    "Senior Backend Engineer": RoleDefinition(
        role_name="Senior Backend Engineer",
        required_skills=[
            "Python",
            "Go",
            "Java",
            "FastAPI",
            "Django",
            "Docker",
            "PostgreSQL",
            "Redis",
        ],
        required_categories=["language", "backend_framework", "database"],
        next_roles=["Tech Lead", "Platform Engineer", "Staff Engineer"],
        seniority=3,
    ),
    "Senior Frontend Engineer": RoleDefinition(
        role_name="Senior Frontend Engineer",
        required_skills=["TypeScript", "React", "Vue", "Next.js"],
        required_categories=["language", "frontend_framework"],
        next_roles=["Tech Lead", "Full-Stack Developer", "Staff Engineer"],
        seniority=3,
    ),
    "Senior Full-Stack Developer": RoleDefinition(
        role_name="Senior Full-Stack Developer",
        required_skills=["TypeScript", "React", "Python", "Docker", "PostgreSQL"],
        required_categories=[
            "language",
            "frontend_framework",
            "backend_framework",
            "database",
        ],
        next_roles=["Tech Lead", "Staff Engineer", "Engineering Manager"],
        seniority=3,
    ),
    "Senior Mobile Developer": RoleDefinition(
        role_name="Senior Mobile Developer",
        required_skills=["Swift", "Kotlin", "Flutter", "React Native"],
        required_categories=["language", "mobile"],
        next_roles=["Tech Lead", "Engineering Manager"],
        seniority=3,
    ),
    "Senior Data Engineer": RoleDefinition(
        role_name="Senior Data Engineer",
        required_skills=["Python", "Apache Spark", "Airflow", "BigQuery", "Snowflake"],
        required_categories=["language", "data_engineering"],
        next_roles=["Data Architect", "ML Engineer", "Engineering Manager"],
        seniority=3,
    ),
    "Senior ML Engineer": RoleDefinition(
        role_name="Senior ML Engineer",
        required_skills=["Python", "PyTorch", "TensorFlow", "MLflow"],
        required_categories=["language", "ml"],
        next_roles=["AI Architect", "Research Engineer", "Engineering Manager"],
        seniority=4,
    ),
    "Senior Security Engineer": RoleDefinition(
        role_name="Senior Security Engineer",
        required_skills=["OAuth", "Vault", "Docker", "Kubernetes", "Linux"],
        required_categories=["security", "infrastructure"],
        next_roles=["Cloud Architect", "Engineering Manager"],
        seniority=4,
    ),
    "Staff Engineer": RoleDefinition(
        role_name="Staff Engineer",
        required_skills=[],
        required_categories=["language"],
        next_roles=["Engineering Manager", "CTO"],
        seniority=4,
    ),
    "Data Architect": RoleDefinition(
        role_name="Data Architect",
        required_skills=[
            "SQL",
            "BigQuery",
            "Snowflake",
            "Apache Spark",
            "Apache Kafka",
        ],
        required_categories=["data_engineering", "cloud"],
        next_roles=["Engineering Manager", "CTO"],
        seniority=4,
    ),
    "AI Architect": RoleDefinition(
        role_name="AI Architect",
        required_skills=["Python", "PyTorch", "TensorFlow", "LangChain"],
        required_categories=["ml", "cloud"],
        next_roles=["CTO", "Engineering Manager"],
        seniority=4,
    ),
    "Research Engineer": RoleDefinition(
        role_name="Research Engineer",
        required_skills=["Python", "PyTorch", "TensorFlow", "Jupyter", "NumPy"],
        required_categories=["ml"],
        next_roles=["AI Architect", "Senior ML Engineer"],
        seniority=4,
    ),
    "Engineering Manager": RoleDefinition(
        role_name="Engineering Manager",
        required_skills=[],
        required_categories=[],
        next_roles=["CTO"],
        seniority=4,
    ),
    "CTO": RoleDefinition(
        role_name="CTO",
        required_skills=[],
        required_categories=[],
        next_roles=[],
        seniority=5,
    ),
}


def get_role(role_name: str) -> RoleDefinition | None:
    return CAREER_ROLES.get(role_name)


def get_all_role_names() -> List[str]:
    return list(CAREER_ROLES.keys())


def get_entry_roles() -> List[str]:
    """シニアリティレベル 2 のロール（典型的な開始点）。"""
    return [name for name, role in CAREER_ROLES.items() if role.seniority == 2]


@dataclass
class RoleMatch:
    role_name: str
    skill_overlap: Set[str]
    category_coverage: float
    match_score: float


def match_skills_to_roles(
    user_skills: Set[str],
    user_categories: Set[str],
) -> List[RoleMatch]:
    """ユーザーのスキルが各ロールの定義とどの程度一致するかをスコアリングします。"""
    matches: List[RoleMatch] = []

    for name, role in CAREER_ROLES.items():
        if not role.required_skills and not role.required_categories:
            continue

        # スキルの重複
        role_skills = set(role.required_skills)
        overlap = user_skills & role_skills
        skill_score = len(overlap) / max(len(role_skills), 1)

        # カテゴリのカバー率
        role_cats = set(role.required_categories)
        cat_overlap = user_categories & role_cats
        cat_score = len(cat_overlap) / max(len(role_cats), 1)

        # 重み付けスコア：スキルの一致 60% + カテゴリのカバー率 40%
        score = 0.6 * skill_score + 0.4 * cat_score

        if score > 0:
            matches.append(
                RoleMatch(
                    role_name=name,
                    skill_overlap=overlap,
                    category_coverage=cat_score,
                    match_score=round(score, 3),
                )
            )

    matches.sort(key=lambda m: m.match_score, reverse=True)
    return matches
