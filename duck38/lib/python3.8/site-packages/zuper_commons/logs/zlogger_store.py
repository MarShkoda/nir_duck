from typing import Optional

from zuper_commons.logs.zlogger import ZLoggerInterface


class ZLoggerStore(ZLoggerInterface):
    def __init__(self, up: Optional[ZLoggerInterface]):
        self.up = up
        self.records = []
        self.record = True

    def info(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs: object) -> None:
        from zuper_commons.timing import now_utc

        record = {"msg": _msg, "args": list(args), "kwargs": kwargs, "t": now_utc()}
        if self.up:
            r = self.up.info(_msg=_msg, *args, stacklevel=stacklevel + 1, **kwargs)
            record["record"] = r
        if self.record:
            self.records.append(record)

    def debug(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs: object) -> None:
        from zuper_commons.timing import now_utc

        record = {"msg": _msg, "args": list(args), "kwargs": kwargs, "t": now_utc()}
        if self.up:
            r = self.up.debug(_msg=_msg, *args, stacklevel=stacklevel + 1, **kwargs)
            record["record"] = r
        if self.record:
            self.records.append(record)

    def warn(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs) -> None:
        from zuper_commons.timing import now_utc

        record = {"msg": _msg, "args": list(args), "kwargs": kwargs, "t": now_utc()}
        if self.up:
            r = self.up.warn(_msg=_msg, *args, stacklevel=stacklevel + 1, **kwargs)
            record["record"] = r
        if self.record:
            self.records.append(record)

    def warning(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs) -> None:
        from zuper_commons.timing import now_utc

        record = {"msg": _msg, "args": list(args), "kwargs": kwargs, "t": now_utc()}
        if self.up:
            r = self.up.warning(_msg=_msg, *args, stacklevel=stacklevel + 1, **kwargs)
            record["record"] = r
        if self.record:
            self.records.append(record)

    def error(self, _msg: str = None, *args, stacklevel: int = 0, **kwargs: object) -> None:
        from zuper_commons.timing import now_utc

        record = {"msg": _msg, "args": list(args), "kwargs": kwargs, "t": now_utc()}
        if self.up:
            r = self.up.error(_msg=_msg, *args, stacklevel=stacklevel + 1, **kwargs)
            record["record"] = r
        if self.record:
            self.records.append(record)

    def getChild(self, child_name: str) -> "ZLoggerInterface":
        return self.up.getChild(child_name)
