from app import models
from app.core.config import settings


def test_generate_project_key_format():
    project = models.Project(name="My Awesome Project")

    # Format: slug-suffix
    assert project.project_key.startswith("my-awesome-project-")

    # Suffix length check (hex token)
    suffix_part = project.project_key.replace("my-awesome-project-", "")
    assert len(suffix_part) == settings.PROJECT_SUFFIX_LENGTH


def test_generate_project_key_uniqueness():
    name = "duplicate"
    project1 = models.Project(name=name)
    project2 = models.Project(name=name)

    assert project1.project_key != project2.project_key


def test_generate_project_key_special_chars():
    project = models.Project(name="Project! With @ Special # Chars")

    # Slugify should strip special chars
    assert project.project_key.startswith("project-with-special-chars-")
