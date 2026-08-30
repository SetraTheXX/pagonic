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
- workflow: `.github/workflows/publish.yml`
- environment: the matching `testpypi` or `pypi` name

No API token or package secret is required by the workflow.

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

Replace `VERSION` with the published version. The smoke test should be run on
both Windows and Linux before adding the PyPI install command to the public
README.
