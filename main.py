from __future__ import print_function
import sys
import random
import pprint
import json

debug = False
pp = pprint.PrettyPrinter(indent=4)

def main():
    # TODO: make the program interact according to specification
    # TODO: add dropping conditions
    global debug
    
    # get input file, set flags
    if len(sys.argv) < 2:
        print("This script requires an input file.\n\tUsage: python main.py <input file path> [--debug]")
        return
    input_file_path = sys.argv[1]
    debug = ("--debug" in sys.argv)
    with open(input_file_path) as input_file:
        input_lines = input_file.readlines()
    input_lines = [l.rstrip() for l in input_lines]
    
    training_data = parse_training_data(input_lines)
    if debug:
        print("Training Data: ", pp.pformat(training_data))

    rules = aq(training_data)
    if debug:
            print("Rules: ", pp.pformat(rules))


    #deleteme
    print("\n-----------------------------\nRULES:")

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
    # TODO: Use all cutpoints strategy to deal with numerical attributes.
    # Examples of numerical values are 42, -12.45; etc

    # remove comments
    for line in lines:
        if line[0] == "!":
            lines.remove(line)
    # throw away the first line
    lines.pop(0)
    names_str = lines.pop(0).rstrip()
    names = names_str.split(" ")
    names = [n for n in names if n != "[" and n != "]" and bool(n) and not n.isspace()]
    if debug:
        print("names: ", names)

    cases = []
    for line in lines:
        vals = line.rstrip().split(" ")
        av = list(zip(names, vals))
        dv = av.pop()
        cases.append({"a": av, "d": dv})
    
    dname = names.pop()
    anames = names
    
    return {"decision": dname, "attributes": anames, "cases": cases}


def aq(data):
    concepts = set([case["d"][1] for case in data["cases"]])
    if debug:
        print("Concepts: ", pp.pformat(concepts))
    rules = []
    for concept in concepts:
        if debug:
            print("\n----------------------\nConcept: ", concept)
        
        positive = [case for case in data["cases"] if case["d"][1] == concept]
        negative = [case for case in data["cases"] if case["d"][1] != concept]
        if debug:
            print("Positive Cases: ", pp.pformat(positive))
        if debug:
            print("Negative Cases: ", pp.pformat(negative))
        
        targets = positive
        while len(targets) > 0:
            seed = random.choice(targets)
            if debug:
                print("Seed: ", pp.pformat(seed))

            pstar = star(seed, negative)

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
            chosen = candidates[0]["avlist"]
            rules.append({"a": chosen, "d": (data["decision"], concept)})

            # create new target list and seed (if len(target) > 0)
            new_targets = []
            for t in targets:
                if diff(chosen, t["a"]) is not None:
                    new_targets.append(t)
            targets = new_targets

    return rules


def star(seed, negative):
    # pstar is a list of sets of (a,v)
    pstar = []
    for ncase in negative:
        n = ncase["a"]
        if not pstar:
            # pstar is empty
            d = diff(seed["a"], n)
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
                    d = diff(seed["a"], n)
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
    returns (a,v) pairs from a that are different from b
    a should not include (a,v) pairs with an a not in b
    """
    diffs = []
    # print("DIFF:\n\ta: ", a, "\n\tb: ", b)
    for a_av in a:
        b_av = next(av for av in b if av[0] == a_av[0])
        # print("\ta_av: ", a_av, "\tb_av: ", b_av)
        if a_av[1] != b_av[1]:
            diffs.append(a_av)
    return diffs if diffs else None



if __name__ == "__main__":
    main()
