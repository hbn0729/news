#!/usr/bin/env python
"""
测试 gnews 集成脚本

用于验证 gnews 采集器是否正确配置和工作
"""

import sys
import os

# 添加项目路径到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))


def test_gnews_import():
    """测试 gnews 模块导入"""
    print("=" * 60)
    print("Test 1: Import GNews module")
    print("=" * 60)

    try:
        from app.utils.gnews import GNews

        print("OK: GNews module imported successfully")

        # 测试基本功能
        gnews = GNews(language="en", country="US", max_results=5)
        print(f"OK: GNews instance created")
        print(f"  - Available countries: {len(gnews.countries[0])}")
        print(f"  - Available languages: {len(gnews.languages[0])}")
        return True
    except Exception as e:
        print(f"FAIL: Failed to import GNews: {e}")
        return False


def test_gnews_constants():
    """测试 gnews 常量"""
    print("\n" + "=" * 60)
    print("Test 2: GNews Constants")
    print("=" * 60)

    try:
        from app.utils.gnews.utils.constants import (
            AVAILABLE_COUNTRIES,
            AVAILABLE_LANGUAGES,
            TOPICS,
            SECTIONS,
        )

        print(f"OK: Constants imported successfully")
        print(f"  - Countries: {len(AVAILABLE_COUNTRIES)}")
        print(f"  - Languages: {len(AVAILABLE_LANGUAGES)}")
        print(f"  - Topics: {len(TOPICS)}")
        print(f"  - Sections: {len(SECTIONS)}")

        # 显示财经相关主题
        finance_topics = [
            t for t in TOPICS if any(k in t for k in ["BUSINESS", "ECONOMY"])
        ]
        print(f"  - Finance-related topics: {finance_topics}")

        finance_sections = [
            k for k in SECTIONS.keys() if any(kw in k for kw in ["FINANCE", "ECONOMY"])
        ]
        print(f"  - Finance-related sections: {finance_sections}")

        return True
    except Exception as e:
        print(f"FAIL: Failed to load constants: {e}")
        return False


def test_collector_structure():
    """测试采集器结构"""
    print("\n" + "=" * 60)
    print("Test 3: Collector Structure")
    print("=" * 60)

    try:
        from app.collectors.gnews_collector import (
            GNewsCollector,
            FINANCE_TOPICS,
            FINANCE_KEYWORDS,
            _fetch_gnews_by_topic,
            _fetch_gnews_by_keyword,
        )

        print("OK: GNewsCollector imported successfully")
        print(f"  - Collector source name: {GNewsCollector.source_name}")
        print(f"  - Finance topics: {FINANCE_TOPICS}")
        print(f"  - Finance keywords (first 4): {FINANCE_KEYWORDS[:4]}")

        # 创建采集器实例
        collector = GNewsCollector()
        print(f"OK: Collector instance created")

        return True
    except Exception as e:
        print(f"FAIL: Failed to test collector: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("GNews Integration Test Suite")
    print("=" * 60)

    results = []

    # 运行测试
    results.append(("GNews Module Import", test_gnews_import()))
    results.append(("GNews Constants", test_gnews_constants()))
    results.append(("Collector Structure", test_collector_structure()))

    # 显示总结
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        symbol = "[OK]" if result else "[X]"
        print(f"{symbol} {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n[OK] All tests passed! GNews is properly integrated.")
        return 0
    else:
        print(f"\n[X] {total - passed} test(s) failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
