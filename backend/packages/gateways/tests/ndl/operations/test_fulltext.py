"""Tests for reading the OCR of a book in the NDL digital collections."""

import json

from gateways.ndl.models.page import NdlPage
from gateways.ndl.operations import fulltext


def test_blocks_are_read_from_the_coordinate_payload():
    payload = json.dumps(
        [
            {"contenttext": "飽之浦", "xmin": 5895, "ymin": 450, "xmax": 5959, "ymax": 634},
            {"contenttext": "", "xmin": 0, "ymin": 0, "xmax": 1, "ymax": 1},
            {"contenttext": "壊れた箱", "xmin": 0},
        ],
    )
    blocks = fulltext._blocks_from(payload)
    assert len(blocks) == 1
    assert blocks[0].text == "飽之浦"
    assert blocks[0].width == 64
    assert blocks[0].height == 184


def test_a_payload_that_is_not_a_list_yields_no_blocks():
    assert fulltext._blocks_from("not json") == []
    assert fulltext._blocks_from(None) == []


def test_the_viewer_address_points_at_the_frame():
    page = NdlPage(pid="2937057", frame=802, contents="")
    assert page.viewer_url() == "https://dl.ndl.go.jp/pid/2937057/1/802"
