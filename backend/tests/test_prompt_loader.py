import pytest
from app.utils.prompt_loader import load_prompt


def test_load_prompt_success():
    """既存のプロンプトファイルが正常に読み込めること。"""
    # 実際にあるファイルを指定
    content = load_prompt("github_analysis.md")
    assert content is not None
    assert len(content) > 0
    assert "GitHub" in content or "分析" in content

def test_load_prompt_not_found():
    """存在しないファイルを指定した場合に FileNotFoundError が発生すること。"""
    with pytest.raises(FileNotFoundError):
        load_prompt("non_existent_file.md")
