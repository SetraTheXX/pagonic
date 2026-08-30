# Package publishing

Pagonic is published only from a manually selected version tag whose name
matches the version in `pyproject.toml`. The workflow itself is dispatched from
`main`, then checks out and verifies that immutable source tag. It builds the
wheel and source distribution in a restricted job, transfers those exact
artifacts, and publishes them in a separate job with PyPI Trusted Publishing.

## One-time setup

Configure two GitHub environments with the exact names `testpypi` and `pypi`.
Their deployment branch policy should allow the `main` branch, because the
workflow is dispatched from `main` while checking out the selected source tag.
The `pypi` environment has a required reviewer as an additional publication
guard.

Then configure a PyPI and a TestPyPI trusted publisher for:

- owner: `SetraTheXX`
- repository: `pagonic`
- workflow: `.github/workflows/publish.yml` (enter `publish.yml` in the
  publisher form's workflow filename field)
- environment: the matching `testpypi` or `pypi` name

No API token or package secret is required by the workflow.

## v0.5.0 publication record

The `v0.5.0` package was published after the TestPyPI-first gate completed:

- [TestPyPI workflow run](https://github.com/SetraTheXX/pagonic/actions/runs/33342421000)
  completed successfully.
- [PyPI workflow run](https://github.com/SetraTheXX/pagonic/actions/runs/33342530857)
  completed successfully after the `pypi` environment review.
- The package is live at [PyPI](https://pypi.org/project/pagonic/) and
  [TestPyPI](https://test.pypi.org/project/pagonic/).
- Clean package-install smoke tests passed on Windows and Linux (WSL Ubuntu)
  for `pip check`, `pagonic --version`, `inspect --json`, `verify`, and
  `safe-extract --dry-run`.

The publish action pin was updated to PyPA `v1.14.2` in commit
[`b4edbe9`](https://github.com/SetraTheXX/pagonic/commit/b4edbe978a41ac86aa4759f7fd9e3dd0e59fa475)
after the older action rejected the release's current core metadata format.
The package source and version were unchanged.

Because `v0.5.0` is immutable and was built from the release tag before this
publication follow-up, its embedded project description is the pre-publication
README snapshot. This does not affect installation or runtime behavior; the
next routine patch release that changes package metadata should carry the
current README and project URLs.

## Publish sequence

1. Create and push a matching tag, for example `v0.5.1` for package version
   `0.5.1`.
2. Run **Publish package** manually from `main`, enter the matching source tag,
   and select `testpypi`.
3. Install from TestPyPI in a clean virtual environment and run the CLI smoke
   checks before considering a PyPI publication.
4. Run the same workflow from `main` with the same source tag and `pypi`
   selected only after the TestPyPI smoke test and release audit pass.

The workflow rejects dispatches outside `main`, non-`v` source tags, missing or
different checked-out tags, and tags that do not match the package version. It
also rejects a distribution directory that does not contain exactly one wheel
and one source distribution.

## TestPyPI smoke test

Use a clean virtual environment and include the normal PyPI index so runtime
dependencies can still be resolved:

```text
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pagonic==VERSION
python -m pip check
pagonic --version
pagonic inspect sample.zip --json
pagonic verify sample.zip
```

Replace `VERSION` with the published version. Repeat the smoke test on both
Windows and Linux for future release candidates before promoting a package to
PyPI.
