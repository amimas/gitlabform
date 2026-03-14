import pytest

from gitlabform.gitlab import AccessLevel
from tests.acceptance import (
    run_gitlabform,
)
from tests.acceptance.conftest import GitLabFormLogs


@pytest.fixture(scope="function")
def tags(project):
    tag_names = [
        "tag1",
        "tag2",
        "tag3",
    ]
    tags = []

    for tag_name in tag_names:
        tag = project.tags.create({"tag_name": tag_name, "ref": "main"})
        tags.append(tag)

    yield tags

    protected_tags = project.protectedtags.list()
    for protected_tag in protected_tags:
        protected_tag.delete()

    for tag in tags:
        tag.delete()


class TestTags:
    def test__tags_skipped_for_repo_disabled_project(
        self, project_for_function, gitlabform_logs: GitLabFormLogs
    ) -> None:
        # Disable repository for the project to ensure that tags processing is skipped
        # In order to disable repository, we also need to disable builds and merge requests
        # as they depend on the repository being enabled
        project_for_function.merge_requests_access_level = "disabled"
        project_for_function.builds_access_level = "disabled"
        project_for_function.repository_access_level = "disabled"
        project_for_function.save()

        config = f"""
        projects_and_groups:
          "{project_for_function.path_with_namespace}":
            tags:
              "v1.0.0":
                protected: true
        """

        try:
            run_gitlabform(config, project_for_function.path_with_namespace)
        except SystemExit as e:
            pytest.fail(f"gitlabform exited unexpectedly with code {e.code}")

        expected_log_message = f"Skipping processing tags for project '{project_for_function.path_with_namespace}' as its repository is disabled."

        assert any(
            expected_log_message in log for log in gitlabform_logs.debug
        ), "Expected log message not found in gitlabform debug logs"

    def test__protect_single_tag(self, project, tags):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              tag1:
                protected: true
                create_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            if tag.name == "tag1":
                assert tag.protected
            else:
                assert not tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 1
        assert protected_tags[0].name == "tag1"
        assert protected_tags[0].create_access_levels[0]["access_level"] == AccessLevel.MAINTAINER.value

    def test__protect_wildcard_tag(self, project, tags):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              "tag*":
                protected: true
                create_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            assert tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 1
        assert protected_tags[0].name == "tag*"
        assert protected_tags[0].create_access_levels[0]["access_level"] == AccessLevel.MAINTAINER.value

    def test__unprotect_the_same_tag(self, project, tags):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              "tag*":
                protected: true
                create_access_level: {AccessLevel.MAINTAINER.value}
        """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            assert tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 1
        assert protected_tags[0].name == "tag*"
        assert protected_tags[0].create_access_levels[0]["access_level"] == AccessLevel.MAINTAINER.value

        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              "tag*":
                protected: false
        """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            assert not tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 0

    def test__unprotect_unknown_tag(self, project, tags):
        config = f"""
        projects_and_groups:
          {project.path_with_namespace}:
            tags:
              "tag_unknown":
                protected: false
        """

        # In strict mode, processor should exit immediately
        with pytest.raises(SystemExit):
            run_gitlabform(config, project)

    def test__protect_single_tag_no_access(self, project, tags):
        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                tags:
                  tag1:
                    protected: true
                    create_access_level: {AccessLevel.NO_ACCESS.value}
            """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            if tag.name == "tag1":
                assert tag.protected
            else:
                assert not tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 1
        assert protected_tags[0].name == "tag1"
        assert protected_tags[0].create_access_levels[0]["access_level"] == AccessLevel.NO_ACCESS.value

    def test__protect_single_tag_with_access_level_names(self, project, tags):
        config = f"""
            projects_and_groups:
              {project.path_with_namespace}:
                tags:
                  tag1:
                    protected: true
                    create_access_level: maintainer
            """

        run_gitlabform(config, project)

        project_tags = project.tags.list()
        for tag in project_tags:
            if tag.name == "tag1":
                assert tag.protected
            else:
                assert not tag.protected

        protected_tags = project.protectedtags.list()
        assert len(protected_tags) == 1
        assert protected_tags[0].name == "tag1"
        assert protected_tags[0].create_access_levels[0]["access_level"] == AccessLevel.MAINTAINER.value
