#!/usr/bin/env python3

import typing as tp


t = tp.TypeVar("t")
def join(item: t, items: tp.Iterable[t]) -> tp.Iterator[t]:
    fst = True
    for it in items:
        if not fst:
            yield item
        fst = False
        yield it
