"""career_analysis.prompt_builder のユニットテスト（Issue #203）。

LLM に GitHub 分析結果を渡す際、検出フレームワークが専用行で明示されることを検証する。
"""

from types import SimpleNamespace

from app.services.career_analysis.prompt_builder import build_user_prompt


def _make_cache(analysis_result: dict) -> SimpleNamespace:
    """GitHubAnalysisCache 相当のダックタイプオブジェクトを生成する。"""
    return SimpleNamespace(analysis_result=analysis_result)


def test_detected_frameworks_section_included():
    """analysis_result に detected_frameworks が含まれる場合、
    「検出フレームワーク」行がプロンプトに含まれること。"""
    cache = _make_cache(
        {
            "position_scores": {
                "backend": 40,
                "frontend": 60,
                "sre": 10,
                "cloud": 5,
                "fullstack": 45,
                "missing_skills": [],
            },
            "languages": {"TypeScript": 80000, "Python": 20000},
            "detected_frameworks": ["React", "Next.js", "FastAPI"],
            "repositories": [],
        }
    )
    prompt = build_user_prompt(
        target_position="フルスタックエンジニア",
        resume=None,
        analysis_cache=cache,
        blog_cache=None,
        merged_stacks_text="",
    )
    assert "検出フレームワーク: React, Next.js, FastAPI" in prompt


def test_empty_frameworks_does_not_emit_line():
    """detected_frameworks が空の場合は「検出フレームワーク:」行が出力されないこと。"""
    cache = _make_cache(
        {
            "position_scores": {},
            "languages": {"Python": 1000},
            "detected_frameworks": [],
            "repositories": [],
        }
    )
    prompt = build_user_prompt(
        target_position="バックエンドエンジニア",
        resume=None,
        analysis_cache=cache,
        blog_cache=None,
        merged_stacks_text="",
    )
    assert "検出フレームワーク:" not in prompt


def test_missing_detected_frameworks_key_is_safe():
    """古いキャッシュで detected_frameworks キーが無くても例外にならないこと。"""
    cache = _make_cache(
        {
            "position_scores": {},
            "languages": {"Python": 1000},
            "repositories": [],
        }
    )
    # 例外を出さず、フレームワーク行も含まれないこと
    prompt = build_user_prompt(
        target_position="バックエンドエンジニア",
        resume=None,
        analysis_cache=cache,
        blog_cache=None,
        merged_stacks_text="",
    )
    assert "検出フレームワーク:" not in prompt
