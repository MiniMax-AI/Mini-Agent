"""Test for Markdown link path processing in skill loader."""

import tempfile
from pathlib import Path

from ye_linghua.tools.skill_loader import SkillLoader


def test_markdown_link_processing():
    """Test that Markdown links in skill content are converted to absolute paths."""
    
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        skills_dir = Path(tmpdir) / "skills"
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir(parents=True)
        
        # Create subdirectories
        (skill_dir / "reference").mkdir()
        (skill_dir / "scripts").mkdir()
        
        # Create various referenced files
        doc_file = skill_dir / "reference.md"
        doc_file.write_text("# Reference Documentation")
        
        ref_file = skill_dir / "reference" / "guide.md"
        ref_file.write_text("# Guide")
        
        script_file = skill_dir / "scripts" / "helper.js"
        script_file.write_text("// Helper script")
        
        # Create SKILL.md with various Markdown link formats
        skill_content = """---
name: test-skill
description: Test skill for Markdown link processing
---

# Test Skill

## Instructions

1. Read [`reference.md`](reference.md) for basic documentation.
2. Load [Guide](./reference/guide.md) for detailed instructions.
3. Use [helper script](scripts/helper.js) for automation.
4. See [another reference](./reference.md) without prefix word.
"""
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(skill_content)
        
        # Load the skill
        loader = SkillLoader(skills_dir=str(skills_dir))
        skills = loader.discover_skills()
        
        # Verify skill was loaded
        assert len(skills) == 1
        skill = skills[0]
        
        # Test 1: Simple filename link
        assert str(doc_file) in skill.content, f"Test 1 failed: Simple filename link not converted"
        assert "](reference.md)" not in skill.content, "Test 1 failed: Relative path not replaced"
        
        # Test 2: Link with ./ prefix
        assert str(ref_file) in skill.content, f"Test 2 failed: ./reference/ link not converted"
        assert "](./reference/guide.md)" not in skill.content, "Test 2 failed: ./reference/ path not replaced"
        
        # Test 3: Link with directory path
        assert str(script_file) in skill.content, f"Test 3 failed: scripts/ link not converted"
        assert "](scripts/helper.js)" not in skill.content, "Test 3 failed: scripts/ path not replaced"
        
        # Test 4: Verify helpful instruction is added
        assert skill.content.count("(use read_file to access)") >= 3, "Helpful instruction not added to all links"
        
        print("✅ All tests passed!")
        print(f"   ✓ Simple filename: {doc_file}")
        print(f"   ✓ With ./ prefix: {ref_file}")
        print(f"   ✓ Directory path: {script_file}")
        print(f"   ✓ Helpful instructions added")


if __name__ == "__main__":
    test_markdown_link_processing()

