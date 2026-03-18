from app import models


def test_generate_project_key_is_name_slug():
    project = models.Project(name="My Awesome Project")
    assert project.project_key == "my-awesome-project"


def test_generate_project_key_same_name_same_key():
    # Without a random suffix, the same name always produces the same key.
    # Uniqueness per user is enforced by the DB constraint, not randomness.
    project1 = models.Project(name="duplicate")
    project2 = models.Project(name="duplicate")

    assert project1.project_key == project2.project_key == "duplicate"


def test_generate_project_key_special_chars():
    project = models.Project(name="Project! With @ Special # Chars")
    assert project.project_key == "project-with-special-chars"


def test_name_is_trimmed_on_save():
    project = models.Project(name="  My Project  ")
    assert project.name == "My Project"
    assert project.project_key == "my-project"


def test_name_internal_whitespace_is_collapsed_on_save():
    project = models.Project(name="spaces  everywhere")
    assert project.name == "spaces everywhere"
    assert project.project_key == "spaces-everywhere"


def test_rename_syncs_project_key():
    project = models.Project(name="Original")
    assert project.project_key == "original"

    project.name = "Renamed Project"
    assert project.name == "Renamed Project"
    assert project.project_key == "renamed-project"
