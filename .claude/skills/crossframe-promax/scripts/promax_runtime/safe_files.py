from __future__ import annotations

import os
from pathlib import Path
import stat


def read_stable_regular_file(
    path: Path | str,
    *,
    within_root: Path | str | None = None,
    require_single_link: bool = True,
) -> bytes:
    target = Path(path)
    root = Path(within_root).resolve() if within_root is not None else None

    def resolve_inside() -> Path:
        resolved = target.resolve(strict=True)
        if root is not None:
            resolved.relative_to(root)
        return resolved

    try:
        resolve_inside()
        path_stat = target.stat()
    except (OSError, RuntimeError, ValueError) as error:
        raise ValueError(f"file does not resolve inside its trusted root: {target}") from error
    if target.is_symlink() or not stat.S_ISREG(path_stat.st_mode):
        raise ValueError(f"file must be a regular non-symlink file: {target}")
    if require_single_link and path_stat.st_nlink != 1:
        raise ValueError(f"file must not be hard linked: {target}")

    try:
        with target.open("rb") as handle:
            opened = os.fstat(handle.fileno())
            if not stat.S_ISREG(opened.st_mode):
                raise ValueError(f"opened handle is not a regular file: {target}")
            if require_single_link and opened.st_nlink != 1:
                raise ValueError(f"opened file must not be hard linked: {target}")
            resolve_inside()
            if target.is_symlink() or not os.path.samestat(opened, target.stat()):
                raise ValueError(f"file path changed while opening: {target}")
            data = handle.read()
            after_read = os.fstat(handle.fileno())
            if (
                not os.path.samestat(opened, after_read)
                or after_read.st_size != opened.st_size
                or after_read.st_mtime_ns != opened.st_mtime_ns
                or (require_single_link and after_read.st_nlink != 1)
            ):
                raise ValueError(f"file changed while reading: {target}")
            resolve_inside()
            if target.is_symlink() or not os.path.samestat(after_read, target.stat()):
                raise ValueError(f"file path changed while reading: {target}")
    except ValueError:
        raise
    except (OSError, RuntimeError) as error:
        raise ValueError(f"cannot read stable regular file: {target}") from error
    return data
