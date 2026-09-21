import random

l = list()
for i in range(6):
    l.append(random.randint(1, 10))
ok = sum([x for x in l if x % 2 == 1])
VAR = {
    "l": str(l),
    "ok": str(ok),
    "pasoka": str(ok * 2 + 1),
    "pasokb": str(ok + 1),
    "pasokc": str(ok - 1),
    "true": str(True),
    "false": str(False)
}
