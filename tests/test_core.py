import base64

from repo_doctor.core import GitHubClient, audit_user, score_repository


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.headers = {}
        self.urls = []

    def get(self, url, timeout):
        self.urls.append(url)
        payload, status = self.responses[url]
        return FakeResponse(payload, status)


def test_score_requires_three_readme_sections_and_scores_all_checks():
    repo = {"name": "demo", "full_name": "octo/demo", "html_url": "https://github.com/octo/demo",
            "license": {"key": "mit"}, "description": "Example"}
    readme = "# About\n# Installation\n# Usage\n"
    result = score_repository(repo, readme, True, ["python"])
    assert result.score == 5
    assert result.maximum == 5


def test_audit_fetches_readme_gitignore_and_topics_from_mock_api():
    root = "https://api.github.com/repos/octo/demo"
    readme = base64.b64encode(b"# About\n# Installation\n# Usage\n").decode()
    responses = {
        "https://api.github.com/users/octo/repos?type=owner&per_page=100&page=1": ([{
            "name": "demo", "full_name": "octo/demo", "html_url": "https://github.com/octo/demo",
            "license": {"key": "mit"}, "description": "Example"}], 200),
        f"{root}/readme": ({"content": readme}, 200),
        f"{root}/contents/.gitignore": ({"name": ".gitignore"}, 200),
        f"{root}/topics": ({"names": ["python"]}, 200),
    }
    session = FakeSession(responses)
    scores = audit_user("octo", GitHubClient("secret", session))
    assert scores[0].score == 5
    assert session.headers["Authorization"] == "Bearer secret"
    assert len(session.urls) == 4
