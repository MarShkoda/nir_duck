__all__ = [
    "Path",
    "AbsPath",
    "RelPath",

    "AbsDirPath",
    "AbsFilePath",

    "RelDirPath",
    "RelFilePath",

    "DirPath",
    "FilePath",
]

if False:
    from typing import NewType, Union

    Path = NewType("Path", str)
    AbsPath = NewType("AbsPath", Path)
    RelPath = NewType("RelPath", Path)

    AbsDirPath = NewType("AbsDirPath", AbsPath)
    AbsFilePath = NewType("AbsFilePath", AbsPath)

    RelDirPath = NewType("RelDirPath", RelPath)
    RelFilePath = NewType("RelFilePath", RelPath)

    DirPath = Union[AbsDirPath, RelDirPath]
    FilePath = Union[AbsFilePath, RelFilePath]
    # DirEntryName = NewType("DirEntryName", RelPath)
else:
    AbsPath = AbsFilePath = AbsDirPath = str
    Path = DirPath = FilePath = str
    RelPath = RelDirPath = RelFilePath = str
    pass
