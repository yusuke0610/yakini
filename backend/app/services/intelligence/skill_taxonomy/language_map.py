"""GitHub の言語検出名を正規化されたスキル名にマッピングする静的定義。"""

from typing import Dict

# GitHubの言語検出名 → 正規化スキル名
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
