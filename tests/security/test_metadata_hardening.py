import stat
import zipfile

from Pagonic.core.formats.zip_reader import ZipReader


def _mark_zip_entries_encrypted(path):
    data = bytearray(path.read_bytes())
    for signature, flag_offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        position = 0
        while True:
            position = data.find(signature, position)
            if position < 0:
                break
            flags = int.from_bytes(
                data[position + flag_offset:position + flag_offset + 2],
                "little",
            )
            data[position + flag_offset:position + flag_offset + 2] = (
                flags | 0x1
            ).to_bytes(2, "little")
            position += len(signature)
    path.write_bytes(data)


def test_reader_does_not_extract_symbolic_link_metadata(tmp_path):
    archive = tmp_path / "symlink.zip"
    link_info = zipfile.ZipInfo("link")
    link_info.create_system = 3
    link_info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive, "w") as zip_file:
        zip_file.writestr(link_info, b"target.txt")

    output = tmp_path / "out"
    result = ZipReader(str(archive)).extract_all(str(output))

    assert result["success"] == []
    assert result["failed"][0]["filename"] == "link"
    assert not (output / "link").exists()


def test_reader_does_not_extract_encrypted_metadata(tmp_path):
    archive = tmp_path / "encrypted.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("secret.txt", b"secret")
    _mark_zip_entries_encrypted(archive)

    output = tmp_path / "out"
    result = ZipReader(str(archive)).extract_all(str(output))

    assert result["success"] == []
    assert result["failed"][0]["filename"] == "secret.txt"
    assert not (output / "secret.txt").exists()
