"""Basic Pagonic API usage."""

from pathlib import Path
from tempfile import TemporaryDirectory

from Pagonic.core.formats.zip_reader import ZipReader
from Pagonic.core.formats.zip_writer import ZipWriter


def main() -> None:
    with TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        source = workspace / "hello.txt"
        archive = workspace / "hello.zip"
        output = workspace / "extracted"

        source.write_text("Hello from Pagonic!", encoding="utf-8")

        writer = ZipWriter(str(archive), compression_level=6)
        writer.add_file(str(source))
        writer.finalize()

        reader = ZipReader(str(archive))
        reader.extract_all(str(output))

        print((output / "hello.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
