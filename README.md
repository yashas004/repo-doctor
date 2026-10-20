# repo-doctor

`repo-doctor` checks the public repositories owned by a GitHub user and gives each repository a score out of five. It checks for a README with at least three common sections (About, Installation, Usage, and Contributing), a license, a `.gitignore`, repository topics, and a description.

## Installation

Requires Python 3.9 or newer.

```bash
python -m pip install .
```

To install the test dependencies too:

```bash
python -m pip install '.[test]'
```

## Usage

```bash
repo-doctor octocat
repo-doctor octocat --output report.md
```

The command prints a sortable score table in the terminal. `--output` writes the same results as a Markdown report. Set `GITHUB_TOKEN` in the environment to authenticate API requests and increase the GitHub REST API rate limit; authentication is optional.

```bash
GITHUB_TOKEN=ghp_yourtoken repo-doctor octocat
```

## Scoring

Each check is worth one point. A README passes when its headings include at least three of the common sections described above. Repository data, README contents, `.gitignore`, and topics are fetched from the GitHub REST API.

## Contributing

Run the test suite with `pytest`. Contributions are welcome; please include tests for behavior changes.
