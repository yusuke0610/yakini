"""リポジトリ説明文キーワード → スキルのマッピング定義。

大文字小文字を区別しない部分一致でチェックされる。
"""

from typing import Dict, List

# リポジトリ説明文に含まれるキーワード → スキル一覧
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
