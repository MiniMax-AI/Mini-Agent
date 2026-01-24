"""
Test Skill Loader
"""

import tempfile
from pathlib import Path

from mini_agent.tools.skill_loader import SkillLoader


def create_test_skill(skill_dir: Path, name: str, description: str, content: str):
    """Create a test skill"""
    skill_file = skill_dir / "SKILL.md"
    skill_content = f"""---
name: {name}
description: {description}
---

{content}
"""
    skill_file.write_text(skill_content, encoding="utf-8")


def test_load_valid_skill():
    """Test loading a valid skill"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()

        create_test_skill(
            skill_dir,
            "test-skill",
            "A test skill",
            "This is a test skill content.",
        )

        loader = SkillLoader(tmpdir)
        skill = loader.load_skill(skill_dir / "SKILL.md")

        assert skill is not None
        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert "This is a test skill content" in skill.content


def test_load_skill_with_metadata():
    """Test loading a skill with metadata"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()

        skill_file = skill_dir / "SKILL.md"
        skill_content = """---
name: test-skill
description: A test skill
license: MIT
allowed-tools:
  - read_file
  - write_file
metadata:
  author: Test Author
  version: "1.0"
---

Skill content here.
"""
        skill_file.write_text(skill_content, encoding="utf-8")

        loader = SkillLoader(tmpdir)
        skill = loader.load_skill(skill_file)

        assert skill is not None
        assert skill.name == "test-skill"
        assert skill.license == "MIT"
        assert skill.allowed_tools == ["read_file", "write_file"]
        assert skill.metadata["author"] == "Test Author"
        assert skill.metadata["version"] == "1.0"


def test_load_invalid_skill():
    """Test loading an invalid skill (missing frontmatter)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "invalid-skill"
        skill_dir.mkdir()

        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("No frontmatter here!", encoding="utf-8")

        loader = SkillLoader(tmpdir)
        skill = loader.load_skill(skill_file)

        assert skill is None


def test_discover_skills():
    """Test discovering multiple skills"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create multiple skills
        for i in range(3):
            skill_dir = Path(tmpdir) / f"skill-{i}"
            skill_dir.mkdir()
            create_test_skill(
                skill_dir, f"skill-{i}", f"Test skill {i}", f"Content {i}"
            )

        loader = SkillLoader(tmpdir)
        skills = loader.discover_skills()

        assert len(skills) == 3
        assert len(loader.list_skills()) == 3


def test_get_skill():
    """Test getting a loaded skill"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()
        create_test_skill(skill_dir, "test-skill", "Test", "Content")

        loader = SkillLoader(tmpdir)
        loader.discover_skills()

        skill = loader.get_skill("test-skill")
        assert skill is not None
        assert skill.name == "test-skill"

        # Test non-existent skill
        assert loader.get_skill("nonexistent") is None



def test_get_skills_metadata_prompt():
    """Test generating metadata-only prompt (Progressive Disclosure Level 1)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test skills with different names to test categorization
        # Use longer content to simulate real skills
        long_content = """
# Detailed Skill Content

This is a comprehensive skill guide with lots of detailed instructions.

## Section 1
Here are detailed instructions for using this skill.

## Section 2
More detailed content and examples.

## Section 3
Even more content to make this realistic.
""" * 3  # Make it substantial

        skills_data = [
            ("pdf", "PDF manipulation toolkit", long_content),
            ("docx", "Document creation tool", long_content),
            ("canvas-design", "Canvas design tool", long_content),
        ]

        for name, desc, content in skills_data:
            skill_dir = Path(tmpdir) / name
            skill_dir.mkdir()
            create_test_skill(skill_dir, name, desc, content)

        loader = SkillLoader(tmpdir)
        loader.discover_skills()

        # Test metadata prompt generation
        metadata_prompt = loader.get_skills_metadata_prompt()

        # Should contain skill names and descriptions
        assert "pdf" in metadata_prompt
        assert "docx" in metadata_prompt
        assert "canvas-design" in metadata_prompt
        assert "PDF manipulation toolkit" in metadata_prompt
        assert "Document creation tool" in metadata_prompt

        # Should contain Progressive Disclosure explanation
        assert "Available Skills" in metadata_prompt

        # Should NOT contain full content (only metadata)
        assert "Detailed Skill Content" not in metadata_prompt
        assert "Section 1" not in metadata_prompt
        assert "Section 2" not in metadata_prompt


def test_nested_document_path_processing():
    """Test processing of nested document references (Level 3+)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()

        # Create nested documents
        (skill_dir / "reference.md").write_text("Reference content", encoding="utf-8")
        (skill_dir / "forms.md").write_text("Forms content", encoding="utf-8")

        # Create SKILL.md with nested references
        skill_content = """---
name: test-skill
description: Test skill with nested docs
---

For advanced features, see reference.md.
If you need forms, read forms.md and follow instructions.
"""
        (skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")

        loader = SkillLoader(tmpdir)
        skill = loader.load_skill(skill_dir / "SKILL.md")

        assert skill is not None

        # Check that paths are converted to absolute and include instructions
        assert str(skill_dir / "reference.md") in skill.content
        assert str(skill_dir / "forms.md") in skill.content
        assert "use read_file" in skill.content.lower()


def test_script_path_processing():
    """Test processing of script paths in skills"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()

        # Create scripts directory
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "test_script.py").write_text("# Python script", encoding="utf-8")

        # Create SKILL.md with script reference
        skill_content = """---
name: test-skill
description: Test skill with scripts
---

Run the script: python scripts/test_script.py
"""
        (skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")

        loader = SkillLoader(tmpdir)
        skill = loader.load_skill(skill_dir / "SKILL.md")

        assert skill is not None

        # Check that script path is converted to absolute
        assert str(skill_dir / "scripts" / "test_script.py") in skill.content


def test_skill_to_prompt_includes_root_directory():
    """Test that to_prompt includes skill root directory path"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()

        skill_file = skill_dir / "SKILL.md"
        skill_content = """---
name: test-skill
description: A test skill
---

Skill content here.
"""
        skill_file.write_text(skill_content, encoding="utf-8")

        loader = SkillLoader(tmpdir)
        skill = loader.load_skill(skill_file)

        assert skill is not None

        # Test to_prompt includes root directory
        prompt = skill.to_prompt()
        assert "Skill Root Directory" in prompt
        assert str(skill_dir) in prompt
        assert "All files and references in this skill are relative to this directory" in prompt
