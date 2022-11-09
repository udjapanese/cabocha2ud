# -*- coding: utf-8 -*-

"""
Functions for checking Dependencies
"""


def collect_ancestors(_id: int, tree: list[int], ancestors: list[int]) -> list[int]:
    """
    Usage: ancestors = collect_ancestors(nodeid, nodes, [])
    
    `tree` format is [-1] + [child1, child2, child3, ...], root is 0
    """
    pid = tree[_id]
    if pid == 0:
        ancestors.append(0)
        return ancestors
    if pid in ancestors:  # ループしている場合はそのまま返す
        return ancestors
    ancestors.append(pid)
    return collect_ancestors(pid, tree, ancestors)


def get_caused_nonprojectivities(iid: int, tree: list[int]) -> list[int]:
    """
    iid ノードに対して非交差(non-projective)が発生するノード（子）を返します

    `tree` format is [-1] + [child1, child2, child3, ...], root is 0
    """
    ancestors = collect_ancestors(iid, tree, [])
    pid = tree[iid]
    if pid < iid:
        left = range(pid + 1, iid)
        right = range(iid + 1, len(tree))
    else:
        left = range(1, iid)
        right = range(iid + 1, pid)
    leftna = [x for x in left if tree[x] not in ancestors]
    rightna = [x for x in right if tree[x] not in ancestors]
    leftcross = [x for x in leftna if tree[x] > iid]
    rightcross = [x for x in rightna if tree[x] < iid]
    if pid < iid:
        rightcross = [x for x in rightcross if tree[x] > pid]
    else:
        leftcross = [x for x in leftcross if tree[x] < pid]
    return sorted(leftcross + rightcross)
