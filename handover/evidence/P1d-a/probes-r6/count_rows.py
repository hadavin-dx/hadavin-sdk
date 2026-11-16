"""Count the rows (by class) and the mutants of the P1d-a ticket. Usage: python count_rows.py <ticket.md>"""
import re, sys


def counts(text):
    rows = {"fb": 0, "pb": 0, "ow": 0}
    ids = []
    muts = []
    for line in text.split("\n"):
        m = re.match(r"^\| ([A-Z][A-Za-z0-9]*) \| (fb|pb|ow) \|", line)
        if m:
            rows[m.group(2)] += 1
            ids.append(m.group(1))
        m = re.match(r"^\| (A\d+[a-z]?) \| (GATE|CH|SL|RD|RM) ", line)
        if m:
            muts.append(m.group(1))
    assert len(ids) == len(set(ids)), [i for i in ids if ids.count(i) > 1]
    assert len(muts) == len(set(muts)), [i for i in muts if muts.count(i) > 1]
    return {"rows": sum(rows.values()), **rows, "mutants": len(muts)}


if __name__ == "__main__":
    print(counts(open(sys.argv[1], encoding="utf-8").read()))
