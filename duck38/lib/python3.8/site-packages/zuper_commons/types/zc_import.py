# -*- coding: utf-8 -*-

import traceback

from zuper_commons.text import indent

__all__ = ["import_name"]


def import_name(name: str) -> object:
    """
        Loads the python object with the given name.

        Note that "name" might be "module.module.name" as well.
    """
    try:
        return __import__(name, fromlist=["dummy"])
    except ImportError:
        # split in (module, name) if we can
        if "." in name:
            tokens = name.split(".")
            field = tokens[-1]
            module_name = ".".join(tokens[:-1])

            if False:  # previous method
                pass
                # try:
                #     module = __import__(module_name, fromlist=['dummy'])
                # except ImportError as e:
                #     msg = ('Cannot load %r (tried also with %r):\n' %
                #            (name, module_name))
                #     msg += '\n' + indent(
                #         '%s\n%s' % (e, traceback.format_exc(e)), '> ')
                #     raise ValueError(msg)
                #
                # if not field in module.__dict__:
                #     msg = 'No field  %r\n' % field
                #     msg += ' found in %r.' % module
                #     raise ValueError(msg)
                #
                # return module.__dict__[field]
            else:
                # other method, don't assume that in "M.x", "M" is a module.
                # It could be a class as well, and "x" be a staticmethod.
                try:
                    module = import_name(module_name)
                except ImportError as e:
                    msg = "Cannot load %r (tried also with %r):\n" % (name, module_name)
                    msg += "\n" + indent("%s\n%s" % (e, traceback.format_exc()), "> ")
                    raise ValueError(msg) from None

                if isinstance(module, type):
                    if hasattr(module, field):
                        return getattr(module, field)
                    else:
                        msg = f"No field {field!r} found in type {module!r}."
                        raise KeyError(msg) from None

                if not field in module.__dict__:
                    msg = f"No field {field!r} found in module {module!r}."
                    msg += f'Known: {sorted(module.__dict__)} '
                    raise KeyError(msg) from None

                f = module.__dict__[field]

                # "staticmethod" are not functions but descriptors, we need
                # extra magic
                if isinstance(f, staticmethod):
                    return f.__get__(module, None)
                else:
                    return f

        else:
            msg = "Cannot import name %r." % name
            msg += indent(traceback.format_exc(), "> ")
            raise ValueError(msg)
