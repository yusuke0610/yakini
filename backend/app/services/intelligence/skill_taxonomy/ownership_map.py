"""スキル「所有」判定のためのマッピング定義。

GitHub リポジトリの言語比率・トピック・ルートファイル・検出フレームワークから
ユーザーが保有しているスキルを特定する際に参照する辞書群を集約する。

position_scorer の ``_detect_owned_skills`` と ``_find_missing_skills`` の入力で利用される。
"""

from typing import Dict, Tuple

# 言語バイト比率からスキルへのマッピング（``LANG_SKILL_THRESHOLD`` 以上で保有とみなす）
LANG_SKILL_MAP: Dict[str, str] = {
    "Python": "Python", "Java": "Java", "Go": "Go",
    "Rust": "Rust", "Ruby": "Ruby", "PHP": "PHP",
    "TypeScript": "TypeScript", "JavaScript": "JavaScript",
    "CSS": "CSS", "HTML": "HTML", "SCSS": "CSS",
    "HCL": "Terraform", "Shell": "Shell",
    "Kotlin": "Kotlin", "C#": "C#",
}

# GitHub トピックからスキルへのマッピング（単一スキル）
TOPIC_SKILL_MAP: Dict[str, str] = {
    "react": "React", "vue": "Vue", "angular": "Angular",
    "nextjs": "Next.js", "docker": "Docker",
    "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "terraform": "Terraform", "aws": "AWS",
    "gcp": "GCP", "azure": "Azure",
    "ci-cd": "CI/CD", "graphql": "GraphQL",
    "rest": "REST API", "api": "REST API",
    "database": "SQL", "sql": "SQL",
}

# リポジトリルートファイルからスキルへのマッピング
FILE_SKILL_MAP: Dict[str, str] = {
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker",
    "docker-compose.yaml": "Docker",
    ".github": "CI/CD",
    "Jenkinsfile": "CI/CD",
    ".gitlab-ci.yml": "CI/CD",
    ".circleci": "CI/CD",
    "terraform": "Terraform",
    ".terraform": "Terraform",
}

# 検出フレームワーク → 代表スキル名のマッピング
FRAMEWORK_SKILL_MAP: Dict[str, str] = {
    "Docker": "Docker",
    "Docker Compose": "Docker",
    "GitHub Actions": "CI/CD",
    "Jenkins": "CI/CD",
    "GitLab CI": "CI/CD",
    "CircleCI": "CI/CD",
    "Terraform": "Terraform",
    # フロントエンドフレームワーク
    "React": "React",
    "React Native": "React",
    "Next.js": "React",
    "Gatsby": "React",
    "Remix": "React",
    "Vue": "Vue",
    "Nuxt.js": "Vue",
    "Angular": "Angular",
    "Svelte": "Svelte",
    "Astro": "Astro",
    # バックエンドフレームワーク
    "FastAPI": "REST API",
    "Django": "REST API",
    "Flask": "REST API",
    "Express": "REST API",
    "NestJS": "REST API",
    "Spring Boot": "REST API",
    "Gin": "REST API",
    "Echo": "REST API",
    "Fiber": "REST API",
    # データベース
    "PostgreSQL": "SQL",
    "MongoDB": "SQL",
    "Redis": "SQL",
    # クラウド SDK
    "AWS": "AWS",
    "GCP": "GCP",
    "Azure": "Azure",
    # GraphQL
    "GraphQL": "GraphQL",
}

# 検出フレームワーク → position_weights.json で参照されるトピック語のマッピング。
# リポジトリに topic タグが無いケースでも依存関係から推定できるよう、
# position_scorer の topic 判定に合成的に注入する。
FRAMEWORK_TO_TOPICS: Dict[str, Tuple[str, ...]] = {
    # フロントエンド
    "React": ("react", "frontend", "web"),
    "React Native": ("react", "frontend"),
    "Next.js": ("nextjs", "react", "frontend", "web"),
    "Gatsby": ("gatsby", "react", "frontend"),
    "Remix": ("remix", "react", "frontend"),
    "Vue": ("vue", "frontend", "web"),
    "Nuxt.js": ("nuxt", "vue", "frontend"),
    "Angular": ("angular", "frontend", "web"),
    "Svelte": ("svelte", "frontend"),
    "Astro": ("astro", "frontend"),
    # バックエンド
    "FastAPI": ("fastapi", "api", "backend"),
    "Django": ("django", "backend", "api"),
    "Flask": ("flask", "backend"),
    "Express": ("express", "backend", "api"),
    "NestJS": ("nestjs", "backend", "api"),
    "Spring Boot": ("spring", "backend", "api"),
    "Gin": ("backend", "api"),
    "Echo": ("backend", "api"),
    "Fiber": ("backend", "api"),
    # データベース / API
    "PostgreSQL": ("database",),
    "MongoDB": ("database",),
    "Redis": ("database",),
    "GraphQL": ("graphql", "api"),
    # インフラ / SRE
    "Docker": ("docker",),
    "Docker Compose": ("docker",),
    "GitHub Actions": ("ci-cd",),
    "Jenkins": ("ci-cd",),
    "GitLab CI": ("ci-cd",),
    "CircleCI": ("ci-cd",),
    "Terraform": ("terraform", "iac"),
    # クラウド
    "AWS": ("aws", "cloud"),
    "GCP": ("gcp", "cloud"),
    "Azure": ("azure", "cloud"),
}

# 言語比率がこの閾値以上で「保有」とみなす
LANG_SKILL_THRESHOLD = 0.01
