"""
Tests for Phase 4.1: Pagination Utility
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.pagination import paginate_list


def test_paginate_list_no_page():
    """When page=None, return all items (backward compatible)"""
    data = [1, 2, 3, 4, 5]
    result = paginate_list(data, page=None)
    assert result == data, f"Expected {data}, got {result}"
    print("✅ test_paginate_list_no_page passed")


def test_paginate_list_first_page():
    """Page 1 with page_size=2 should return first 2 items"""
    data = [1, 2, 3, 4, 5]
    result = paginate_list(data, page=1, page_size=2)
    assert result["items"] == [1, 2]
    assert result["total"] == 5
    assert result["page"] == 1
    assert result["page_size"] == 2
    assert result["total_pages"] == 3
    print("✅ test_paginate_list_first_page passed")


def test_paginate_list_middle_page():
    """Page 2 with page_size=2 should return items 3,4"""
    data = [1, 2, 3, 4, 5]
    result = paginate_list(data, page=2, page_size=2)
    assert result["items"] == [3, 4]
    assert result["page"] == 2
    print("✅ test_paginate_list_middle_page passed")


def test_paginate_list_last_page():
    """Last page should return remaining items"""
    data = [1, 2, 3, 4, 5]
    result = paginate_list(data, page=3, page_size=2)
    assert result["items"] == [5]
    assert result["page"] == 3
    assert result["total_pages"] == 3
    print("✅ test_paginate_list_last_page passed")


def test_paginate_list_page_exceeds():
    """Page beyond total_pages should clamp to last page"""
    data = [1, 2, 3]
    result = paginate_list(data, page=999, page_size=2)
    assert result["page"] == 2  # clamped to last page
    assert result["items"] == [3]
    print("✅ test_paginate_list_page_exceeds passed")


def test_paginate_list_empty():
    """Empty list should return empty items with page=1"""
    data = []
    result = paginate_list(data, page=1, page_size=10)
    assert result["items"] == []
    assert result["total"] == 0
    assert result["page"] == 1
    assert result["total_pages"] == 1
    print("✅ test_paginate_list_empty passed")


def test_paginate_list_page_size_clamp():
    """Page size should be clamped between 1 and 100"""
    data = list(range(200))
    result = paginate_list(data, page=1, page_size=200)
    assert result["page_size"] == 100
    assert len(result["items"]) == 100
    print("✅ test_paginate_list_page_size_clamp passed")


def test_paginate_list_single_item():
    """Single item list"""
    data = ["only"]
    result = paginate_list(data, page=1, page_size=10)
    assert result["items"] == ["only"]
    assert result["total"] == 1
    assert result["total_pages"] == 1
    print("✅ test_paginate_list_single_item passed")


def test_paginate_list_exact_fit():
    """Items exactly fill pages"""
    data = [1, 2, 3, 4]
    result = paginate_list(data, page=2, page_size=2)
    assert result["items"] == [3, 4]
    assert result["total_pages"] == 2
    print("✅ test_paginate_list_exact_fit passed")


if __name__ == "__main__":
    test_paginate_list_no_page()
    test_paginate_list_first_page()
    test_paginate_list_middle_page()
    test_paginate_list_last_page()
    test_paginate_list_page_exceeds()
    test_paginate_list_empty()
    test_paginate_list_page_size_clamp()
    test_paginate_list_single_item()
    test_paginate_list_exact_fit()
    print("\n🎉 All pagination tests passed!")
