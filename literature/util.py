"""
Helper classes that aren't tied to any game objects.
"""

from typing import (
    cast,
    List
)


class PrintableDict(dict):
    """ A `dict` that prints itself nicely. """

    def _repr_helper(self, indent=0):
        res = []
        for k in sorted(cast(List, self.keys())):
            v = self.get(k)
            if isinstance(v, dict):
                res.append('{0}:'.format(k))
                res.append(PrintableDict(v)._repr_helper(indent + 4))
            elif isinstance(v, list):
                res.append('{0}: {1}'.format(k, sorted(v)))
            else:
                res.append('{0}: {1}'.format(repr(k), repr(v)))
        return '\n'.join(' ' * indent + r for r in res)

    def __repr__(self):
        return self._repr_helper()
