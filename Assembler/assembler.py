#!/usr/bin/env python3
import re, sys
from pathlib import Path

# TO DO 
# ROR and ROL for rotate
# ASL for arithmetic shitft Left
# Clear Flags command
# Interupts?

# ---------- Config ----------

REGS = {
    "A":0, "B":1, "X":2, "Y":3,
    "R0":0, "R1":1, "R2":2, "R3":3,
}

OPCODE = {
    "NOP":    0b00000000,
    "MOV":    0b00000001,
    "LD":     0b00000010,
    "ST":     0b00000011,
    "LDI":    0b00000100,
    "ALU":    0b00000101,
    "JMP":    0b00000110,
    "JZ":     0b00000111,
    "JNZ":    0b00001000,
    "JC":     0b00001001,
    "JNI":    0b00001010,
    "IOO":    0b00001011,
    "IOI":    0b00001110,
    "HLT":    0b00001111,
    "ALULD1": 0b00010000,
    "ALULD2": 0b00010001,
    "CMP":    0b00010010,
    "SPIN":   0b00010011,
    "SPDOUT": 0b00010100,
    "SPAPOP": 0b00010101,
    "SPAPUSH": 0b00010110,
    "SPINC":  0b00010111,
    "SPDEC":  0b00011000,
    "FI":     0b00011001,  
    "JMPR":   0b00011011,
    "JN":     0b00011100,
    "JO":     0b00011101,
    "FPUSH":  0b00011110,
    "FPOP":   0b00011111,
    "JMPI":   0b00100000,
    "BSW":    0b00100001,
}



SUBOP1 = {"SHL":0b0011, "SHR":0b0100}
SUBOP2 = {"ADD":0b0001, "SUB":0b0010, "AND":0b0101, "OR":0b0110, "XOR":0b0111}

# Generate full 0–127 ASCII map automatically
ASCII = {chr(i): i for i in range(128)}
# Ensure explicit newline mapping
ASCII["\n"] = 10

MEM_MAX   = 1 << 16
FILL_WORD = 0x0000



# ---------- Helpers ----------

def parse_int(tok):
    t = tok.strip()
    if t.startswith(("0x","0X")): return int(t,16)
    if t.startswith(("0b","0B")): return int(t,2)
    if t.endswith("h") and re.fullmatch(r"[0-9A-Fa-f]+h", t):
        return int(t[:-1],16)
    return int(t,10)

def is_label(s):
    return re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", s) is not None

def parse_expr(expr, labels):
    e = expr.strip()
    m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\s*([+-])\s*(\S+)", e)
    if m:
        lbl, op, num = m.groups()
        base = labels.get(lbl)
        if base is None:
            raise KeyError(f"unknown label '{lbl}'")
        delta = parse_int(num)
        return base + delta if op=="+" else base - delta
    if is_label(e):
        if e not in labels:
            raise KeyError(f"unknown label '{e}'")
        return labels[e]
    return parse_int(e)

def pack_upper(opcode8, subop4=0, src=0, dest=0):
    """
    16-bit word format:
      [15:8] = 8-bit primary opcode
      [ 7:4] = 4-bit sub-opcode
      [ 3:2] = 2-bit src register
      [ 1:0] = 2-bit dest register
    """
    if not (0 <= opcode8 < 0x100):
        raise ValueError(f"opcode out of range 0..255: {opcode8}")
    if not (0 <= subop4  < 0x10):
        raise ValueError(f"sub-op out of range 0..15: {subop4}")
    return (opcode8 << 8) \
         | (subop4   << 4) \
         | ((src & 0x3) << 2) \
         |  (dest & 0x3)



def split_operands(op):
    parts, cur, depth = [], "", 0
    for ch in op:
        if ch=="[": depth+=1
        if ch=="]": depth-=1
        if ch=="," and depth==0:
            parts.append(cur.strip()); cur=""
        else:
            cur+=ch
    if cur.strip(): parts.append(cur.strip())
    return parts

# ---------- Assembler ----------

class Asm:
    def __init__(self, text):
        user_lines = text.splitlines()
        # Prepend prologue lines so pass1/pass2 treat them like normal source
        self.lines = user_lines
        self.labels = {}
        self.mem, self.pc, self.errors = {}, 0, []

    def err(self, ln, msg):
        self.errors.append(f"line {ln}: {msg}")

    def set_word(self, addr, val):
        if not (0 <= addr < MEM_MAX):
            raise ValueError(f"address out of range: {addr}")
        self.mem[addr] = val & 0xFFFF

    def emit_inst(self, upper, lower):
        self.set_word(self.pc, upper)
        self.set_word(self.pc+1, lower)
        self.pc += 2

    def _parse_instr(self, line, ln):
        parts = line.strip().split(None,1)
        mnem  = parts[0].upper()
        ops   = split_operands(parts[1]) if len(parts)>1 else []
        return mnem, ops

    def instr_length(self, mnem, ops, ln):
        # Single-instruction ops (2 words)
        single_2w = {
            "NOP","HLT","MOV","LD","ST","LDI","IOO","IOI",
            "JMP","JZ","JNZ","JC","JNI","JN","JO","JMPR","JMPI",
            "FI","FPOP","FPUSH","BSW","SPIN","PUSH","POP",
        }
        if mnem in single_2w:
            return 2

        # ALU burst macros:
        # SUBOP1 (e.g., SHL/SHR) expands to 2 instructions -> 4 words
        if mnem in SUBOP1:
            return 4
        # SUBOP2 (ADD/SUB/AND/OR/XOR) expands to 3 instructions -> 6 words
        if mnem in SUBOP2:
            return 6

        # CMP macro is 3 instructions -> 6 words
        if mnem == "CMP":
            return 6

        # INC/DEC families: each expands to 6 instructions -> 12 words
        if mnem in {"INCA","DECA","INCB","DECB","INCX","DECX","INCY","DECY"}:
            return 12

        # CMPMEM* families: each is 6 instructions -> 12 words
        if mnem in {"CMPMEMA","CMPMEMB","CMPMEMX","CMPMEMY"}:
            return 12

        # JSR macro: 3 instructions -> 6 words
        if mnem == "JSR":
            return 6
        # RET macro: 2 instructions -> 4 words
        if mnem == "RET":
            return 4

        # DISPTXT single-line: already fixed to 4 words per char
        if mnem == "DISPTXT":
            t = ops[1].strip("[]")
            return len(t) * 4

        # Default: assume single-instruction -> 2 words
        return 2


        return 1

    def pass1(self):
        pc, i = 0, 0
        while i < len(self.lines):
            ln = i+1
            raw = self.lines[i]
            line = raw.split(";",1)[0].split("#",1)[0].strip()
            if not line:
                i+=1; continue

            if line.endswith(":"):
                lbl = line[:-1].strip()
                if not is_label(lbl):
                    self.err(ln, f"invalid label '{lbl}'")
                elif lbl in self.labels:
                    self.err(ln, f"duplicate label '{lbl}'")
                else:
                    self.labels[lbl] = pc
                i+=1; continue

            if line.lower().startswith(".org"):
                arg = line.split(None,1)[1]
                new_pc = parse_int(arg)
                # Just move the counter; no need to call set_word in pass1
                pc = new_pc
                i += 1
                continue


            if line.lower().startswith(".word"):
                try:
                    args = line.split(None,1)[1]
                    pc  += len([w.strip() for w in args.split(",")])
                except Exception as e:
                    self.err(ln, f".word parse error: {e}")
                i+=1; continue

            # here-doc DISPTXT?
            if line.upper().startswith("DISPTXT") and "<<" in line:
                head, tag_marker, _ = line.split(",",2)
                head_parts = head.strip().split()
                if len(head_parts)!=2:
                    self.err(ln, f"bad DISPTXT syntax: '{line}'"); break
                _, _dest = head_parts
                tag = tag_marker.strip()
                if not tag.startswith("<<"):
                    self.err(ln, f"bad here-doc marker '{tag_marker}'"); break
                tag = tag[2:]

                # consume until closing tag
                block=[]
                i+=1
                while i < len(self.lines) and self.lines[i].strip()!=tag:
                    block.append(self.lines[i]); i+=1
                if i>=len(self.lines):
                    self.err(ln, f"unterminated text block '{tag}'"); break
                lines = [l.rstrip("\n") for l in block]
                indents = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
                common = min(indents) if indents else 0
                text = "\n".join(line[common:] for line in lines)
                pc  += len(text)*4
                i+=1
                continue

            # normal instruction
            mnem, ops = self._parse_instr(line, ln)
            pc += self.instr_length(mnem, ops, ln)
            i += 1

        self.pc = pc

    def pass2(self):
        self.pc, i = 0, 0        

        while i < len(self.lines):
            ln = i+1
            raw = self.lines[i]
            line = raw.split(";",1)[0].split("#",1)[0].strip()
            if not line:
                i+=1; continue

            # labels & directives…
            if line.endswith(":"):
                i+=1; continue

            if line.lower().startswith(".org"):
                arg = line.split(None,1)[1]
                new_pc = parse_int(arg) & 0xFFFF

                # Do not forward-fill. Just set pc.
                self.pc = new_pc

                i += 1
                continue



            if line.lower().startswith(".word"):
                args = line.split(None,1)[1]
                for tok in [w.strip() for w in args.split(",")]:
                    v = parse_expr(tok, self.labels)
                    self.set_word(self.pc, v); self.pc+=1
                i+=1; continue

            # here-doc DISPTXT?
            if line.upper().startswith("DISPTXT") and "<<" in line:
                head, tag_marker, addr_op = line.split(",",2)
                head_parts = head.strip().split()
                if len(head_parts)!=2:
                    self.err(ln, f"bad DISPTXT syntax: '{line}'"); break
                _, dest_reg = head_parts
                tag = tag_marker.strip()
                if not tag.startswith("<<"):
                    self.err(ln, f"bad here-doc marker '{tag_marker}'"); break
                tag = tag[2:]
                addr = parse_expr(addr_op.strip()[1:-1], self.labels) & 0xFFFF

                block=[]
                i+=1
                while i < len(self.lines) and self.lines[i].strip()!=tag:
                    block.append(self.lines[i]); i+=1
                if i>=len(self.lines):
                    self.err(ln, f"unterminated text block '{tag}'"); break

                lines = [l.rstrip("\n") for l in block]
                indents = [len(l) - len(l.lstrip()) for l in lines if l.strip()]
                common = min(indents) if indents else 0
                text = "\n".join(line[common:] for line in lines)
                d = self.parse_reg(dest_reg)
                for ch in text:
                    code = ASCII.get(ch, ord(ch))
                    self.emit_inst(pack_upper(OPCODE["LDI"],0,0,d), code)
                    self.emit_inst(pack_upper(OPCODE["IOO"],0,d,0), addr)
                i+=1
                continue

            # everything else
            try:
                self.encode_instruction(ln, raw)
            except Exception as e:
                self.err(ln, f"{e}\n    >> {raw}")
            i+=1



    def encode_instruction(self, ln, line):
        parts = line.split(None, 1)
        mnem  = parts[0].upper()
        ops   = split_operands(parts[1]) if len(parts) > 1 else []

        # NOP / HLT
        if mnem == "NOP":
            self.emit_inst(pack_upper(OPCODE["NOP"]), 0)
            return
        if mnem == "HLT":
            self.emit_inst(pack_upper(OPCODE["HLT"]), 0)
            return

        # MOV dest, src
        if mnem == "MOV":
            if len(ops) != 2:
                raise ValueError("MOV expects: MOV dest, src")
            d = self.parse_reg(ops[0]); s = self.parse_reg(ops[1])
            self.emit_inst(pack_upper(OPCODE["MOV"], 0, s, d), 0)
            return

        
        # FI
        if mnem == "FI":
            if len(ops) != 0:
                raise ValueError("FI expects: Nothing")
            self.emit_inst(pack_upper(OPCODE["FI"], 0, 0, 0), 0)
            return
        
        # FPOP
        if mnem == "FPOP":
            if len(ops) != 0:
                raise ValueError("FPOP expects: Nothing")
            self.emit_inst(pack_upper(OPCODE["FPOP"], 0, 0, 0), 0)
            return
        
        # FPUSH
        if mnem == "FPUSH":
            if len(ops) != 0:
                raise ValueError("FPUSH expects: Nothing")
            self.emit_inst(pack_upper(OPCODE["FPUSH"], 0, 0, 0), 0)
            return
        
        # LDI dest, imm
        if mnem == "LDI":
            if len(ops) != 2:
                raise ValueError("LDI expects: LDI dest, imm16")
            d = self.parse_reg(ops[0])
            # If the immediate is quoted, treat as ASCII of first character
            if (ops[1].strip().startswith('"') and ops[1].strip().endswith('"')) or (ops[1].strip().startswith("'") and ops[1].strip().endswith("'")):
                ch = ops[1].strip()[1:-1]
                if ch == "":
                    raise ValueError(f"invalid character/string literal {ops[1]}")
                imm = ASCII.get(ch[0], ord(ch[0])) & 0xFFFF
                self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, d), imm)
                return
        

            # Otherwise parse as numeric expression (labels, hex, bin, decimal)
            imm = parse_expr(ops[1].strip(), self.labels) & 0xFFFF
            self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, d), imm)
            return
        

        
        # BSW RAM/ROM
        if mnem == "BSW":
            if len(ops) != 1:
                raise ValueError("BSW expects: BSW RAM|ROM")

            arg = ops[0].strip().upper()
            if arg == "RAM":
                imm = 0x0001
            elif arg == "ROM":
                imm = 0x0000
            else:
                raise ValueError(f"BSW expects RAM or ROM, got {ops[0]}")

            # No destination register, just emit opcode + imm
            self.emit_inst(pack_upper(OPCODE["BSW"], 0, 0, 0), imm)
            return



        # LD / ST / IOO / IOI
        if mnem in ("LD","ST","IOO","IOI"):
            if len(ops) != 2 or not (ops[1].startswith("[") and ops[1].endswith("]")):
                raise ValueError(f"{mnem} expects: {mnem} reg, [addr]")
            reg = self.parse_reg(ops[0])
            addr = parse_expr(ops[1][1:-1], self.labels) & 0xFFFF
            if mnem == "LD":
                self.emit_inst(pack_upper(OPCODE["LD"], 0, 0, reg), addr)
            elif mnem == "ST":
                self.emit_inst(pack_upper(OPCODE["ST"], 0, reg, 0), addr)
            elif mnem == "IOO":
                self.emit_inst(pack_upper(OPCODE["IOO"], 0, reg, 0), addr)
            else:  # IOI
                self.emit_inst(pack_upper(OPCODE["IOI"], 0, 0, reg), addr)
            return

        # ALU burst ops
        if mnem in SUBOP1:
            if len(ops) != 2:
                raise ValueError(f"{mnem} expects: {mnem} src, dest")
            s = self.parse_reg(ops[0]); d = self.parse_reg(ops[1])
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, s, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALU"], SUBOP1[mnem], 0, d), 0)
            return

        if mnem in SUBOP2:
            if len(ops) != 3:
                raise ValueError(f"{mnem} expects: {mnem} src1, src2, dest")
            s1 = self.parse_reg(ops[0]); s2 = self.parse_reg(ops[1]); d = self.parse_reg(ops[2])
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, s1, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, s2, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALU"], SUBOP2[mnem], 0, d), 0)
            return
        # CMP
        # Equal = Z=1, C=0
        # A < B = Z=0, C=1
        # A > B = Z=0, C=0
        if mnem == "CMP":
            if len(ops) != 2:
                raise ValueError("CMP expects: CMP src1, src2")
            s1 = self.parse_reg(ops[0]); s2 = self.parse_reg(ops[1])
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, s1, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, s2, 0), 0)
            self.emit_inst(pack_upper(OPCODE["CMP"], SUBOP2["SUB"], 0, 0), 0)
            return

        if mnem == "CMPMEMA":
            if len(ops) != 1:
                raise ValueError("CMPMEMA expects: CMPMEMA [addr]")
            addr = parse_expr(ops[0][1:-1], self.labels) & 0xFFFF
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 1, 0), 0)
            self.emit_inst(pack_upper(OPCODE["LD"], 0, 0, 1), addr)  
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 0, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 1, 0), 0)
            self.emit_inst(pack_upper(OPCODE["CMP"], SUBOP2["SUB"], 0, 0), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 1), 0)
            return
        
        if mnem == "CMPMEMB":
            if len(ops) != 1:
                raise ValueError("CMPMEMB expects: CMPMEMB [addr]")
            addr = parse_expr(ops[0][1:-1], self.labels) & 0xFFFF
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 0, 0), 0)
            self.emit_inst(pack_upper(OPCODE["LD"], 0, 0, 0), addr)  
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 1, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 0, 0), 0)
            self.emit_inst(pack_upper(OPCODE["CMP"], SUBOP2["SUB"], 0, 0), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 0), 0)
            return
        
        if mnem == "CMPMEMX":
            if len(ops) != 1:
                raise ValueError("CMPMEMX expects: CMPMEMX [addr]")
            addr = parse_expr(ops[0][1:-1], self.labels) & 0xFFFF
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["LD"], 0, 0, 3), addr)  
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 2, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["CMP"], SUBOP2["SUB"], 0, 0), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 3), 0)
            return
        
        if mnem == "CMPMEMY":
            if len(ops) != 1:
                raise ValueError("CMPMEMY expects: CMPMEMY [addr]")
            addr = parse_expr(ops[0][1:-1], self.labels) & 0xFFFF
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 2, 0), 0)
            self.emit_inst(pack_upper(OPCODE["LD"], 0, 0, 2), addr)  
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 2, 0), 0)
            self.emit_inst(pack_upper(OPCODE["CMP"], SUBOP2["SUB"], 0, 0), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 2), 0)
            return

        # INCA
        if mnem == "INCA":
            if len(ops) != 0:
                raise ValueError("INCA expects: Nothing")
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 3, 0), 0)         
            self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, 3), 1)
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 0, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALU"], SUBOP2["ADD"], 0, 0), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 3), 0)
            return
        
        # DECA
        if mnem == "DECA":
            if len(ops) != 0:
                raise ValueError("DECA expects: Nothing")  
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 3, 0), 0)     
            self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, 3), 1)
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 0, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALU"], SUBOP2["SUB"], 0, 0), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 3), 0)
            return
        
        # INCB
        if mnem == "INCB":
            if len(ops) != 0:
                raise ValueError("INCB expects: Nothing")
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 3, 0), 0)          
            self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, 3), 1)
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 1, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALU"], SUBOP2["ADD"], 0, 1), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 3), 0)
            return
        
        # DECB
        if mnem == "DECB":
            if len(ops) != 0:
                raise ValueError("DECB expects: Nothing")  
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 3, 0), 0)    
            self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, 3), 1)
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 1, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALU"], SUBOP2["SUB"], 0, 1), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 3), 0)
            return
        
        # INCX
        if mnem == "INCX":
            if len(ops) != 0:
                raise ValueError("INCX expects: Nothing")
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 3, 0), 0)   
            self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, 3), 1)
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 2, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALU"], SUBOP2["ADD"], 0, 2), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 3), 0)
            return

        # DECX
        if mnem == "DECX":
            if len(ops) != 0:
                raise ValueError("DECX expects: Nothing")  
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, 3), 1)
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 2, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALU"], SUBOP2["SUB"], 0, 2), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 3), 0)
            return
        
        # INCY
        if mnem == "INCY":
            if len(ops) != 0:
                raise ValueError("INCY expects: Nothing")
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 2, 0), 0)         
            self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, 2), 1)
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 2, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALU"], SUBOP2["ADD"], 0, 3), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 2), 0)
            return

        # DECY
        if mnem == "DECY":
            if len(ops) != 0:
                raise ValueError("DECY expects: Nothing")  
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 2, 0), 0)   
            self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, 2), 1)
            self.emit_inst(pack_upper(OPCODE["ALULD1"], 0, 3, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALULD2"], 0, 2, 0), 0)
            self.emit_inst(pack_upper(OPCODE["ALU"], SUBOP2["SUB"], 0, 3), 0)
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 2), 0)
            return
        

        # PUSH
        if mnem == "PUSH":
            if len(ops) != 1:
                raise ValueError("PUSH expects: PUSH src")    
            s = self.parse_reg(ops[0])  
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, s, 0), 0)

            return
        
        # POP
        if mnem == "POP":
            if len(ops) != 1:
                raise ValueError("POP expects: POP src")    
            d = self.parse_reg(ops[0]) 
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, d), 0)
            
            return
        
        # SPIN
        if mnem == "SPIN":
            if len(ops) != 1:
                raise ValueError("SPIN expects: SPIN dest")    
            d = self.parse_reg(ops[0])  
            self.emit_inst(pack_upper(OPCODE["SPIN"], 0, d, 0), 0)
            return

        
        # Jumps
        if mnem in ("JMP","JZ","JNZ","JC","JNI","JN","JO"):
            if len(ops) != 1:
                raise ValueError(f"{mnem} expects: {mnem} addr")
            waddr = parse_expr(ops[0], self.labels)
            #baddr = (waddr * 2) & 0xFFFF
            self.emit_inst(pack_upper(OPCODE[mnem]), waddr)
            return
        
        # JMPR
        if mnem == "JMPR":
            if len(ops) != 1:
                raise ValueError("JMPR expects: JMPR src")  
            s = self.parse_reg(ops[0])            
            self.emit_inst(pack_upper(OPCODE["JMPR"], 0, s, 0), 0)   
            return
        
        # JMPI
        if mnem == "JMPI":
            if len(ops) != 0:
                raise ValueError("JMPI expects: Nothing")            
            self.emit_inst(pack_upper(OPCODE["JMPI"], 0, 0, 0), 0)   
            return
        
   
        if mnem == "JSR":
            if len(ops) != 1:
                raise ValueError("JSR expects: JSR label")

            # Target is a label stored as word address; JMP wants byte address
            target_word = parse_expr(ops[0], self.labels) & 0xFFFF
            target_byte = (target_word * 2) & 0xFFFF

            # Return address (byte) after this JSR macro (3 instructions = 12 bytes)
            ret_byte = ((self.pc + 6) * 2) & 0xFFFF



            # 1) LDI Y, ret_word
            self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, 3), ret_byte)
            # 2) PUSH Y
            self.emit_inst(pack_upper(OPCODE["SPAPUSH"], 0, 3, 0), 0)
            # 3) JMP target_byte
            self.emit_inst(pack_upper(OPCODE["JMP"]), target_byte)
            return

        if mnem == "RET":
            if len(ops) != 0:
                raise ValueError("RET expects no operands")
            # 1) POP Y
            self.emit_inst(pack_upper(OPCODE["SPAPOP"], 0, 0, 3), 0)
            # 2) JMPR Y  (JMPR jumps to the byte address in Y)
            self.emit_inst(pack_upper(OPCODE["JMPR"], 0, 3, 0), 0)
            return


        # single-line DISPTXT
        if mnem == "DISPTXT":
            if len(ops) != 3:
                raise ValueError("DISPTXT expects: DISPTXT dest, [Text], [addr]")
            d = self.parse_reg(ops[0])
            text = ops[1].strip("[]")
            addr = parse_expr(ops[2][1:-1], self.labels) & 0xFFFF
            for ch in text:
                code = ASCII.get(ch)
                if code is None:
                    self.err(ln, f"unrecognized char '{ch}'")
                    code = 0
                self.emit_inst(pack_upper(OPCODE["LDI"], 0, 0, d), code)
                self.emit_inst(pack_upper(OPCODE["IOO"], 0, d, 0), addr)
            return

        raise ValueError(f"unknown mnemonic '{mnem}'")

    def parse_reg(self, tok):
        t = tok.strip().upper()
        if t not in REGS:
            raise ValueError(f"unknown register '{tok}'")
        return REGS[t]

    def write_words_hex(self, path):
        with open(path, "w") as f:
            for addr in range(MEM_MAX):
                f.write(f"{self.mem.get(addr, FILL_WORD):04X}\n")



def write_bin_image(asm, path_prefix):
    out_path = Path(f"{path_prefix}_rom.bin")
    with out_path.open("wb") as f:
        for addr in range(MEM_MAX):
            word = asm.mem.get(addr, FILL_WORD) & 0xFFFF
            lo = word & 0xFF
            hi = (word >> 8) & 0xFF
            f.write(bytes((lo, hi)))
    print(f"[ok] Wrote {out_path} ({MEM_MAX*2} bytes)")



def _intel_hex_record_byteaddr(addr, data_bytes):
    """
    Build Intel HEX data record for byte address 'addr' and iterable of data bytes.
    Returns record string with trailing newline.
    """
    length = len(data_bytes)
    record_type = 0x00
    hi = (addr >> 8) & 0xFF
    lo = addr & 0xFF
    checksum = (length + hi + lo + record_type + sum(data_bytes)) & 0xFF
    checksum = ((~checksum + 1) & 0xFF)
    payload = ''.join(f"{b:02X}" for b in data_bytes)
    return f":{length:02X}{addr:04X}{record_type:02X}{payload}{checksum:02X}\n"

def write_intel_hex_image(asm, path_prefix, line_size=16):
    """
    Write Intel HEX file where the assembler memory is emitted as bytes (LSB,MSB per word).
    Output file: {path_prefix}.ihex
    """
    size_words = MEM_MAX
    # build flat byte array
    byte_array = bytearray()
    for addr in range(size_words):
        word = asm.mem.get(addr, FILL_WORD) & 0xFFFF
        byte_array.append(word & 0xFF)        # low byte first
        byte_array.append((word >> 8) & 0xFF) # high byte
    out_path = Path(f"{path_prefix}_rom.hex")
    with out_path.open("w") as f:
        for base in range(0, len(byte_array), line_size):
            chunk = byte_array[base:base+line_size]
            f.write(_intel_hex_record_byteaddr(base, chunk))
        # EOF record
        f.write(":00000001FF\n")
    print(f"[ok] Wrote {out_path} ({len(byte_array)} bytes)")

def assemble_file(user_in_path, out_path):
    boot_text = Path("boot.asm").read_text(encoding="utf-8")
    user_text = Path(user_in_path).read_text(encoding="utf-8")
    prologue_text = Path("isr_prologue.asm").read_text(encoding="utf-8")
    epilogue_text = Path("isr_epilogue.asm").read_text(encoding="utf-8")

    # Combine: boot, user, then ISR scaffold
    combined_text = boot_text + "\n" + prologue_text + "\n" + user_text + "\n" + epilogue_text

    a = Asm(combined_text)
    a.pass1()   # pass1 sees both files in order
    a.pass2()          # pass2 emits both files in order

    if a.errors:
        print("Errors:")
        for e in a.errors:
            print(" -", e)
        sys.exit(1)

    a.write_words_hex(out_path)
    base = out_path.rsplit('.', 1)[0]
    write_bin_image(a, base)
    write_intel_hex_image(a, base)
    print(f"[ok] Wrote {out_path} and companion binary/ihex images")





if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: assembler.py input.asm output.hex")
        sys.exit(1)
    assemble_file(sys.argv[1], sys.argv[2])
