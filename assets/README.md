# README assets

These files support the repository README and are not runtime dependencies.

- `pagonic-demo.tape` is the reproducible VHS source for the animated terminal
  demo. It creates a small synthetic ZIP in a unique temporary directory,
  demonstrates inspection, verification failure, and safe-extraction refusal,
  then removes only that temporary directory.
- `pagonic-demo.gif` is the rendered README preview from the tape. It shows the
  current `0.5.1` CLI version, inspection, verification refusal, and safe-
  extraction refusal at a deliberately readable pace. Regenerate it from the
  repository root with `vhs assets/pagonic-demo.tape`.

The demo fixture is synthetic and is not a real malware sample. Keep generated
archives and local render output outside the repository unless they are the
deliberate README assets listed here.
