from scripts.ai_review.diff_parser import parse_unified_diff


def test_parser_tracks_added_lines() -> None:
    patches = parse_unified_diff("diff --git a/src/a.py b/src/a.py\n@@ -1 +4 @@\n-old\n+new")
    assert patches[0].path == "src/a.py"
    assert patches[0].additions[0].number == 4
    assert patches[0].additions[0].text == "new"
