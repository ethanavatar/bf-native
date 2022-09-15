#!/bin/python3

from fileinput import filename


if __name__ == "__main__":
    import sys
    from bf import run
    args = sys.argv[1:]
    if len(args) != 2:
        print("Usage: bf.py <file> <output>")
        exit(1)
    fname = args[0]
    out = args[1]

    program = ''
    with open(fname, 'r') as f:
        program = f.read()
    bytecode = run(program)
    with open(out, 'w') as f:
        f.write(bytecode)