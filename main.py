from __future__ import print_function
import sys
import os
import random
import pprint
import json
from decimal import Decimal

from VRange import VRange

debug = False
pp = pprint.PrettyPrinter(indent=4)


def is_numeric(num):
    try:
        float(num)
        return True
    except ValueError:
        return False

def is_valid_filepath(filepath):
    if debug:
        print("Checking validity of filepath ", filepath)
    try:
        return os.path.isfile(filepath)
    except:
        return False

def is_valid_maxstar(maxstar):
    if debug:
        print("Checking validity of maxstar ", maxstar)
    try:
        int(maxstar)
        if int(maxstar) < 1:
            return False
        return True
    except ValueError:
        return False


def main():
    # TODO: add dropping conditions
    global debug
    
    # get input file, set flags

    debug = ("--debug" in sys.argv)
    input_file_path = "totally not a file"
    maxstar_str = "0"

    if len(sys.argv) >= 3:
        # set defaults from 
        print("Detected arguments, setting default input file and maxstar")
        input_file_path = sys.argv[1]
        maxstar_str = sys.argv[2]

    while not is_valid_filepath(input_file_path):
        input_file_path = raw_input("Enter the name of the input file: ")
    
    with open(input_file_path) as input_file:
        input_lines = input_file.readlines()
    input_lines = [l.strip() for l in input_lines]

    while not is_valid_maxstar(maxstar_str):
        maxstar_str = raw_input("Enter the maxstar: ")
    maxstar = int(maxstar_str)
    
    training_data = parse_training_data(input_lines)
    if debug:
        print("Training Data: ", pp.pformat(training_data))

    concepts = set([case["d"][1] for case in training_data["cases"]])
    if debug:
        print("Concepts: ", pp.pformat(concepts))

    neg_rules = []
    consistent = True
    for concept in concepts:
        if debug:
            print("\n----------------------\nConcept: ", concept)
        
        positive = [case for case in training_data["cases"] if case["d"][1] == concept]
        negative = [case for case in training_data["cases"] if case["d"][1] != concept]
        if debug:
            print("Positive Cases: ", pp.pformat(positive))
        if debug:
            print("Negative Cases: ", pp.pformat(negative))
        try:
            cover = aq(positive, negative, maxstar)
        except Exception as e:
            print(e)
            # inconsistent data set, can't generate rules for this concept
            print("Data set is inconsistent, cannot generate rules for concept: ", concept)
            consistent = False
            continue
        
        neg_rules += cover

    if debug:
        print("Rules: ", pp.pformat(neg_rules))

    if debug:
        print("\n-----------------------------\nNEGATED RULES:")

    if not consistent:
        print("! The input data set is inconsistent")
    for rule in neg_rules:
        print(format_rule(rule))
    
    rules = []
    for rule in neg_rules:
        rules += de_negate_rule(rule, training_data["possible_attribute_values"])

    if debug:
        print("\n-----------------------------\nDE_NEGATED RULES:")

    for rule in rules:
        print(format_rule(rule))


def format_rule(rule):
    # (Ink - color, not black) & (Body - color, not black) -> (Attitude, plus)
    str_attrs = ["(%s, %s)" % (a[0], a[1]) for a in rule["a"]]
    attrs_str = " & ".join(str_attrs)
    dec_str = "(%s, %s)" % (rule["d"][0], rule["d"][1])
    rule_str = "%s -> %s" % (attrs_str, dec_str)
    return rule_str
    

def parse_training_data(lines):
    # remove comments
    for line in lines:
        if not line or line.strip()[0] == "!":
            lines.remove(line)
    # throw away the first line
    lines.pop(0)
    names_str = lines.pop(0).strip()
    names = names_str.split(" ")
    names = [n for n in names if n != "[" and n != "]" and bool(n) and not n.isspace()]
    if debug:
        print("names: ", names)

    cases = []
    for line in lines:
        vals = line.strip().split(" ")
        av = list(zip(names, vals))
        dv = av.pop()
        cases.append({"a": av, "d": dv})
    
    dname = names.pop()
    anames = names

    # ALL CUTPOINTS
    # determine which attrs are numeric
    numeric_attr_names = []
    for av in cases[0]["a"]:
        if is_numeric(av[1]):
            numeric_attr_names.append(av[0])

    if debug:
        print("numeric_attr_names: ", numeric_attr_names)
    
    # pull out numeric attributes
    numeric_attrs = {n_name: [] for n_name in numeric_attr_names}
    for case in cases:
        attrs = list(case["a"])
        for attr in attrs:
            if attr[0] in numeric_attr_names:
                numeric_attrs[attr[0]].append(attr)
    if debug:
        print("numeric_attrs: ", pp.pformat(numeric_attrs))
    
    # find all cutpoints
    cutpoints = {n_name: [] for n_name in numeric_attr_names}
    for (name, avlist) in numeric_attrs.items():
        vals = sorted(list(set([Decimal(av[1]) for av in avlist])))
        low = vals[0]
        high = vals[len(vals) - 1]
        cutpoints_nums = [(vals[i] + vals[i + 1]) / 2 for i in range(0, len(vals) - 1)]
        cutpoints[name] = [VRange(low, i) for i in cutpoints_nums] + [VRange(i, high) for i in cutpoints_nums]

    # add cutpoint attrs
    cutpoint_attrs = set()
    for case in cases:
        attrs = list(case["a"])
        for attr in case["a"]:
            if attr[0] in numeric_attr_names:
                for cutpoint in cutpoints[attr[0]]:
                    cutpoint_attrs.add("%s %s" % (attr[0], str(cutpoint)))
                    attrs.append(("%s %s" % (attr[0], str(cutpoint)), str(Decimal(attr[1]) in cutpoint)[0]))
        case["a"] = [attr for attr in attrs if attr[0] not in numeric_attr_names]

    anames += cutpoint_attrs

    if debug:
        print("Cases with all cutpoints: ", pp.pformat(cases))

    anames = [aname for aname in anames if aname not in numeric_attr_names]

    # find all possible values for each attribute
    possible_values = {a: [] for a in anames}
    for attr in anames:
        pvalues = set()
        for case in cases:
            av = next(av for av in case["a"] if av[0] == attr)
            pvalues.add(av[1])
        possible_values[attr] = list(pvalues)

    return {"decision": dname, "attributes": anames, "possible_attribute_values": possible_values, "cases": cases}


def aq(positive, negative, maxstar):
    rules = []
    targets = positive
    while len(targets) > 0:
        seed = random.choice(targets)
        if debug:
            print("Seed: ", pp.pformat(seed))

        pstar = star(seed, negative, maxstar)

        if debug:
            print("PStar: ", pp.pformat(pstar))

        # now we choose the most covering, smallest list in pstar
        candidates = [{"avlist": avlist} for avlist in pstar]
        for candidate in candidates:
            # compute # of positives covered
            num_covered = 0
            for t in targets:
                if diff(candidate["avlist"], t["a"]) is None:
                    num_covered += 1
            candidate["covered"] = num_covered 

        candidates.sort(reverse=True, key=lambda x: (x["covered"], 1.0 / len(x["avlist"])))
        best = candidates[0]["avlist"]
        rules.append({"a": best, "d": seed["d"]})

        # create new target list and seed (if len(targets) > 0)
        new_targets = []
        for t in targets:
            if diff(best, t["a"]) is not None:
                new_targets.append(t)
        targets = new_targets

    return rules


def star(seed, negative, maxstar):
    # pstar is a list of sets of (a,v)
    pstar = []
    for ncase in negative:
        if len(pstar) > maxstar:
            if debug:
                print("Trimming pstar, len(pstar) = %d, maxstar = %d" % (len(pstar), maxstar))
            # remove worst len(pstar) - maxstar rules
            pstar.sort(key=len)
            pstar = pstar[:maxstar]

        n = ncase["a"]
        if not pstar:
            # pstar is empty
            d = neg_diff(seed["a"], n)
            if d is None:
                # TODO: handle inconsistent data set
                raise Exception(
                    "Inconsistent dataset! Concept %s" % (seed[0]))
            pstar = [set([av]) for av in d]
        else:
            for p in pstar:
                d = diff(p, n)
                if d is None:
                    # n is not covered by p
                    d = neg_diff(seed["a"], n)
                    if d is None:
                        # TODO: handle inconsistent data set
                        raise Exception(
                            "Inconsistent dataset! Concept %s" % (seed[0]))
                    else:
                        # merge d into pstar
                        pstar.remove(p)
                        # that's every permutation of d elements into p
                        for c in d:
                            pstar.append(p.union(set([c])))
    # remove duplicates
    pstar = set([frozenset(p) for p in pstar])
    return pstar


def diff(a, b):
    """
    returns (a,v) pairs from a that exclude b
    """
    diffs = []
    # print("DIFF:\n\ta: ", a, "\n\tb: ", b)
    for a_av in a:
        bmatches = [av for av in b if av[0] == a_av[0]]
        for b_av in bmatches:
            # print("\ta_av: ", a_av, "\tb_av: ", b_av)
            if not match(a_av, b_av):
                diffs.append(a_av)
    return diffs if diffs else None


def neg_diff(a, b):
    """
    returns negated (a,v) pairs of b that include a
    """
    diffs = []
    # print("DIFF:\n\ta: ", a, "\n\tb: ", b)
    for a_av in a:
        bmatches = [av for av in b if av[0] == a_av[0]]
        for b_av in bmatches:
            # print("\ta_av: ", a_av, "\tb_av: ", b_av)
            if not match(a_av, b_av):
                if type(b_av[1]) is tuple:
                    diffs.append(b_av)
                else:
                    diffs.append((b_av[0], ("not", b_av[1])))
    return diffs if diffs else None


def match(x, y):
    if x[0] != y[0]:
        # attributes are not the same
        return False
    if type(x[1]) is tuple:
        # x is negated
        if type(y[1]) is tuple:
            # x and y are negated CHECK THIS
            return x[1][1] == y[1][1]
            pass
        else:
            # x is negated, y is not
            return x[1][1] != y[1]
    else:
        # x is not negated
        if type(y[1]) is tuple:
            # x is not negated, y is
            return x[1] != y[1][1]
        else:
            # neither x or y are negated
            return x[1] == y[1]

def de_negate_rule(rule, possible_values):
    attr_names = set([av[0] for av in rule["a"]])
    attr_lists = {aname: [] for aname in attr_names}
    dn_attr_lists = {aname: [] for aname in attr_names}

    for av in rule["a"]:
        attr_lists[av[0]].append(av)
    
    for aname in attr_lists:
        alist = attr_lists[aname]
        for val in possible_values[aname]:
            if neg_diff([(aname, val)], alist) is None:
                dn_attr_lists[aname].append((aname, val))

    noperm_avs = []
    perm_avs = {}
    for aname in dn_attr_lists:
        alist = dn_attr_lists[aname]
        if len(alist) == 1:
            noperm_avs += alist
        else:
            perm_avs[aname] = alist

    permuted = [noperm_avs]
    for aname in perm_avs:
        alist = perm_avs[aname]
        npermuted = []
        for q in permuted:
            for r in alist:
                npermuted.append(list(q) + [r])
        permuted = npermuted

    rules = [{"a": p, "d": rule["d"]} for p in permuted]
    return rules

def de_negate(av, possible_values):
    de_negated = []
    for val in possible_values[av[0]]:
        if match(av, (av[0], val)):
            de_negated.append((av[0], val))
    return de_negated

if __name__ == "__main__":
    main()
