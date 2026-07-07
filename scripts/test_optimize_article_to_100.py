#!/usr/bin/env python3

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).with_name("optimize-article-to-100.py")


def load_module():
    spec = importlib.util.spec_from_file_location("optimize_article_to_100", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ScoreArticleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_readability_can_reach_full_25_points(self):
        content = """# 标题

## 学习目标

- 理解 J-lens 的用途

## 目录

- 条目一

## 方法

这是一段中文 technical explanation，用来满足中英文空格规则。

| 列一 | 列二 |
| --- | --- |
| A | B |

```python
print('example')
```

## 为什么重要

这里解释为什么这件事有价值，也给出一个示例。

## 自测题

练习：请说明你的判断。

## 进阶方向

常见问题：如果报错，该如何排查？

参考：https://example.com
"""

        score, total = self.module.score_article(content)

        self.assertEqual(score["可读性"], 25)
        self.assertEqual(total, 100)


if __name__ == "__main__":
    unittest.main()