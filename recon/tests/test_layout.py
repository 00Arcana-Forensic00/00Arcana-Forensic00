from arcana_recon import layout


def _column(node, page):
    cx = node["x"] + node["w"] / 2
    if node["y"] < 110:
        return "title"
    return "left" if cx < 500 else "right"


def test_blocks_match_text_lines(page):
    nodes = layout.map_layout(page.clean)
    assert abs(len(nodes) - len(page.lines)) <= 3


def test_xy_cut_reads_left_column_before_right(page):
    nodes = layout.map_layout(page.clean)
    cols = [_column(n, page) for n in nodes]
    assert set(cols[:3]) == {"title"}
    body = [c for c in cols if c != "title"]
    first_right = body.index("right")
    assert all(c == "left" for c in body[:first_right])
    assert all(c == "right" for c in body[first_right:])
    ys = [n["y"] for n, c in zip(nodes, cols) if c == "left"]
    assert ys == sorted(ys)


def test_naive_sort_interleaves_columns(page):
    """The (y, x) sort from the original drafts mixes the two columns."""
    boxes = layout.detect_blocks(layout.binarize(page.clean))
    cols = ["left" if b[0] + b[2] / 2 < 500 else "right" for b in layout.naive_order(boxes) if b[1] >= 110]
    switches = sum(1 for a, b in zip(cols, cols[1:]) if a != b)
    assert switches > 10


def test_single_block_and_empty_page():
    assert layout.xy_cut([]) == []
    assert layout.xy_cut([(1, 2, 3, 4)]) == [(1, 2, 3, 4)]
    import numpy as np
    assert layout.map_layout(np.full((50, 50), 255, np.uint8)) == []
