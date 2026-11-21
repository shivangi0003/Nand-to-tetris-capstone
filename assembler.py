"""
assembler.py  -  a two-pass assembler for the Hack computer.

Usage:   python assembler.py Prog.asm        ->  creates Prog.hack
         python assembler.py Prog.asm Out.hack   (choose the output name)

Extra feature (K mod 3 = 2): if the same label is written twice, the
assembler prints a warning with both line numbers and keeps the first one.
"""

import sys

# ---------------------------------------------------------------------------
# Encoding tables (from the Hack machine language specification)
# ---------------------------------------------------------------------------

# comp field: 7 bits = a-bit + c1..c6.  a=0 uses A, a=1 uses M.
COMP = {
    "0": "0101010", "1": "0111111", "-1": "0111010",
    "D": "0001100", "A": "0110000", "!D": "0001101", "!A": "0110001",
    "-D": "0001111", "-A": "0110011", "D+1": "0011111", "A+1": "0110111",
    "D-1": "0001110", "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
    "A-D": "0000111", "D&A": "0000000", "D|A": "0010101",
    "M": "1110000", "!M": "1110001", "-M": "1110011", "M+1": "1110111",
    "M-1": "1110010", "D+M": "1000010", "D-M": "1010011", "M-D": "1000111",
    "D&M": "1000000", "D|M": "1010101",
}

# dest field: 3 bits = d1 d2 d3  (A, D, M)
DEST = {
    "": "000", "M": "001", "D": "010", "MD": "011",
    "A": "100", "AM": "101", "AD": "110", "AMD": "111",
}

# jump field: 3 bits
JUMP = {
    "": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}


class AsmError(Exception):
    """A mistake in the .asm file. Carries the line number."""


def predefined_symbols():
    table = {"SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
             "SCREEN": 16384, "KBD": 24576}
    for i in range(16):
        table["R%d" % i] = i
    return table


def clean(line):
    """Remove the // comment and all spaces. Returns '' for a blank line."""
    return line.split("//")[0].replace(" ", "").replace("\t", "").strip()


# ---------------------------------------------------------------------------
# Pass 1: find labels
# ---------------------------------------------------------------------------

def first_pass(lines):
    """
    Walk through the source, count real instructions (labels do not count),
    and store each (LABEL) with the ROM address of the NEXT instruction.
    Returns (symbols, instructions) where instructions is a list of
    (source_line_number, text) with comments, blanks and labels removed.
    """
    symbols = predefined_symbols()
    label_lines = {}          # label -> source line where it was first written
    instructions = []

    for number, raw in enumerate(lines, start=1):
        text = clean(raw)
        if text == "":
            continue
        if text.startswith("("):
            if not text.endswith(")") or len(text) < 3:
                raise AsmError("Line %d: bad label '%s'" % (number, text))
            name = text[1:-1]
            # --- extra feature: warn if the same label is written twice ---
            if name in label_lines:
                print("Warning: line %d: label '%s' is already defined on line %d "
                      "(keeping the first one)" % (number, name, label_lines[name]))
                continue
            label_lines[name] = number
            symbols[name] = len(instructions)   # address of next instruction
        else:
            instructions.append((number, text))

    return symbols, instructions


# ---------------------------------------------------------------------------
# Pass 2: translate to 16-bit binary
# ---------------------------------------------------------------------------

def encode_a(number, text, symbols, state):
    """A-instruction '@value' -> 0 + 15-bit address."""
    value = text[1:]
    if value == "":
        raise AsmError("Line %d: '@' has no value" % number)
    if value.isdigit():
        address = int(value)
    else:
        if value[0].isdigit():
            raise AsmError("Line %d: invalid symbol '%s'" % (number, value))
        if value not in symbols:                 # new variable
            symbols[value] = state["next_var"]
            state["next_var"] += 1
        address = symbols[value]
    if address > 32767:
        raise AsmError("Line %d: address %d is too big (max 32767)" % (number, address))
    return "0" + format(address, "015b")


def encode_c(number, text):
    """C-instruction 'dest=comp;jump' -> 111 + comp + dest + jump."""
    dest, jump = "", ""
    comp = text
    if "=" in comp:
        dest, comp = comp.split("=", 1)
    if ";" in comp:
        comp, jump = comp.split(";", 1)
    if comp not in COMP:
        raise AsmError("Line %d: invalid instruction '%s' (unknown comp '%s')" % (number, text, comp))
    if dest not in DEST:
        raise AsmError("Line %d: invalid instruction '%s' (unknown dest '%s')" % (number, text, dest))
    if jump not in JUMP:
        raise AsmError("Line %d: invalid instruction '%s' (unknown jump '%s')" % (number, text, jump))
    return "111" + COMP[comp] + DEST[dest] + JUMP[jump]


def second_pass(instructions, symbols):
    state = {"next_var": 16}      # first variable gets RAM address 16
    output = []
    for number, text in instructions:
        if text.startswith("@"):
            output.append(encode_a(number, text, symbols, state))
        else:
            output.append(encode_c(number, text))
    return output


def assemble(path_in, path_out):
    with open(path_in) as f:
        lines = f.read().splitlines()
    symbols, instructions = first_pass(lines)
    binary = second_pass(instructions, symbols)
    with open(path_out, "w") as f:
        f.write("\n".join(binary) + ("\n" if binary else ""))
    return len(binary)


def main():
    if len(sys.argv) < 2:
        print("Usage: python assembler.py Prog.asm [Out.hack]")
        sys.exit(1)
    path_in = sys.argv[1]
    path_out = sys.argv[2] if len(sys.argv) > 2 else (
        path_in[:-4] if path_in.endswith(".asm") else path_in) + ".hack"
    try:
        count = assemble(path_in, path_out)
    except FileNotFoundError:
        print("Error: cannot find file '%s'" % path_in)
        sys.exit(1)
    except AsmError as e:
        print("Error: %s" % e)
        sys.exit(1)
    print("Assembled %d instructions -> %s" % (count, path_out))


if __name__ == "__main__":
    main()
