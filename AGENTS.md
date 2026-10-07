# Agent instructions

## Contribution preflight

Before changing the repository, inspect all contribution, governance, pull request,
and AI/LLM policies. Work on a non-default feature branch. Never open a pull request
for the user. The user must personally review, understand, and test every change,
write the pull request description and other communications, choose the truthful AI
disclosure, and open the pull request.

## Release model

Package versions come exclusively from Git tags through `setuptools-scm`. Do not add
or edit a version string in project files. Stable release tags must have the exact
form `vX.Y.Z`, for example `v3.5.1`.

Publishing is performed by `.github/workflows/python-publish.yml` when a GitHub
Release is published. The workflow checks out the release tag, verifies that its
commit belongs to `master`, runs the tests on Python 3.12, builds and validates one
wheel and one source distribution, verifies that the wheel version equals the tag,
and stores the distributions as an artifact. A separate job publishes that artifact
to PyPI using Trusted Publishing after approval in the protected `pypi` environment.

## Making a release

Only make a release when the user explicitly requests it and supplies or approves
the version number. A release must not include unmerged local work.

1. Fetch `origin` and all tags, then verify the checkout is clean.
2. Verify the proposed `vX.Y.Z` tag does not exist locally, on GitHub, or on PyPI.
3. Verify the `pypi` GitHub environment requires approval and the PyPI Trusted
   Publisher is configured for this workflow and environment.
4. Verify the target is the current `origin/master` commit and its CI run succeeded.
5. Review every commit since the previous release and prepare accurate release notes
   in a temporary file outside the repository.
6. Create the GitHub Release targeting the full `origin/master` commit SHA. Publishing
   the release creates its tag and starts the PyPI workflow.
7. Wait for the workflow's build job. Never bypass or weaken the `pypi` environment
   approval requirement; leave approval to the user.
8. After approval, wait for publication to finish. Verify the version and both
   distribution files on PyPI, then report the GitHub Release, workflow run, and PyPI
   links to the user.

Suggested release command after completing the checks:

```shell
gh release create vX.Y.Z \
  --repo robmarkcole/HASS-data-detective \
  --target FULL_ORIGIN_MASTER_SHA \
  --title "vX.Y.Z" \
  --notes-file /absolute/path/to/release-notes.md
```

## Failure recovery

PyPI versions and distribution filenames are immutable. Never enable `skip-existing`,
move or reuse a published release tag, delete a published PyPI version, or rerun a
release from a different commit. Diagnose the failure, fix it through the normal
feature-branch and human-reviewed pull-request process, and publish a new patch
version. A failed GitHub release that uploaded nothing to PyPI should still normally
be superseded by a new patch release to preserve a clear audit trail.
