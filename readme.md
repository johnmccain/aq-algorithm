# EECS 690 AQ Algorithm Project
### John McCain

Usage:

```bash
# you can pass options via command line parameters
python main.py <input file path> <maxstar (int)> [--debug]

# or you can omit the command line parameters and be prompted for the input file and maxstar
python main.py [--debug]
```

The input file should be in the LERS format.

The --debug flag enables additional program output for debugging purposes.

Program outputs rules to `<input filename>.without.negation.rul` and `<input filename>.with.negation.rul`, as well as displaying them through stdout

### Notes

- The seed for each concept is chosen randomly, so generated rules may not be the same for every iteration of the program.

- The heuristic used culling covers over maxstar is based on the length of the covering (eg: every iteration of `star()`, the len(covers) - maxstar longest covers are removed)

- maxstar must be at least 1

- Inconsistent data sets will be marked by a comment at the beginning of the output files noting the inconsistency.  This program will attempt to create rules for all concepts, so if only some concepts are inconsistent then the program will generate rules for the consistent concepts.

---

Written in Python 2.7