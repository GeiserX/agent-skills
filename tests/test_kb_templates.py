from __future__ import annotations

import unittest
from pathlib import Path


SKILLS = Path(__file__).parents[1] / "skills"


class KnowledgeBaseTemplateTests(unittest.TestCase):
    def test_both_kb_skills_ship_the_same_adapter_template(self) -> None:
        research = SKILLS / "kb-research" / "references" / "knowledge-base.md"
        review = SKILLS / "kb-review" / "references" / "knowledge-base.md"
        self.assertEqual(
            research.read_bytes(),
            review.read_bytes(),
            "edit kb-research/references/knowledge-base.md, then copy it to kb-review",
        )


if __name__ == "__main__":
    unittest.main()
