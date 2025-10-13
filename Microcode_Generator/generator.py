import csv
from pathlib import Path

# Map Control Lines to Roms, Pins
CONTROL_LINES_MAP = {
    # ROM 1
    "CE": (1, 0), "CO": (1, 1), "MI": (1, 2), "RAO": (1, 3),
    "RAI": (1, 4), "ROO": (1, 5), "CDO": (1, 6), "HLT": (1, 7),
    # ROM 2
    "RegOut": (2, 0), "RegIn": (2, 1), "IIL": (2, 2), "IIH": (2, 3),
    "IOL": (2, 4), "IOH": (2, 5), "IOO": (2, 6), "IOI": (2, 7),
    # ROM 3
    "JMP": (3, 0), "JC": (3, 1), "JZ": (3, 2), "JNZ": (3, 3),
    "ALURO": (3, 4), "EndCmd": (3, 5), "IOLA": (3, 6), "FI": (3, 7),
    # ROM 4
    "ALUOP1": (4, 0), "ALUOP2": (4, 1), "JNI": (4, 2), "SPIn": (4, 3),
    "SPDOut": (4, 4), "SPAOut": (4, 5), "SPINC": (4, 6), "SPDEC": (4, 7),
    # ROM 5
    "JN": (5, 0), "JO": (5, 1), "NC1": (5, 2), "NC2": (5, 3),
    "NC3": (5, 4), "NC4": (5, 5), "NC5": (5, 6), "NC6": (5, 7),

}

INSTRUCTIONS = {
    "NOP": (0b00000000, "CO,MI","ROO, IIH, CE", "EndCmd","","","","","","","","","","","","",""),
    "MOV": (0b00000001, "CO,MI","ROO, IIH, CE", "RegOut, RegIn","EndCmd","","","","","","","","","","","",""),
    "LD":  (0b00000010, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOLA, MI","RegIn, RAO","EndCmd","","","","","","","","",""),
    "ST":  (0b00000011, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOLA, MI","RegOut, RAI","EndCmd","","","","","","","","",""),
    "LDI": (0b00000100, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOL, RegIn","EndCmd","","","","","","","","","",""),
    "ALU": (0b00000101, "CO,MI","ROO, IIH, CE","RegIn, ALURO","FI","EndCmd","","","","","","","","","","",""),
    # "SUB": (0b000000101, "CO,MI","ROO, IIH, CE","SUB, RegIn, ALURO","FI","EndCmd","","","","","","","","","","",""),
    # "SHL": (0b000000101, "CO,MI","ROO, IIH, CE","SHL, RegIn, ALURO","EndCmd","","","","","","","","","","","",""),
    # "SHR": (0b000000101, "CO,MI","ROO, IIH, CE","SHR, RegIn, ALURO","EndCmd","","","","","","","","","","","",""),
    # "AND": (0b000000101, "CO,MI","ROO, IIH, CE","AND, RegIn, ALURO","FI","EndCmd","","","","","","","","","","",""),
    # "OR":  (0b000000101, "CO,MI","ROO, IIH, CE","OR, RegIn, ALURO","FI","EndCmd","","","","","","","","","","",""),
    # "XOR": (0b000000101, "CO,MI","ROO, IIH, CE","XOR, RegIn, ALURO","FI","EndCmd","","","","","","","","","","",""),
    "JMP": (0b00000110, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOL, JMP","EndCmd","","","","","","","","","",""),
    "JZ":  (0b00000111, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOL, JZ","EndCmd","","","","","","","","","",""),
    "JNZ": (0b00001000, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOL, JNZ","EndCmd","","","","","","","","","",""),
    "JC":  (0b00001001, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOL, JC","EndCmd","","","","","","","","","",""),
    "JNI": (0b00001010, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOL, JNI","EndCmd","","","","","","","","","",""),
    "IOO": (0b00001011, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOLA, IOO, RegOut","EndCmd","","","","","","","","","",""),
    "IOI": (0b00001110, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOLA, IOI, RegIn","FI","EndCmd","","","","","","","","",""),
    "HLT": (0b00001111, "CO,MI","ROO, IIH, CE","HLT","","","","","","","","","","","","",""),
    "ALULD1": (0b00010000, "CO,MI","ROO, IIH, CE","RegOut, ALUOP1","EndCmd","","","","","","","","","","","",""),
    "ALULD2": (0b00010001, "CO,MI","ROO, IIH, CE","RegOut, ALUOP2","EndCmd","","","","","","","","","","","",""),
    "CMP": (0b00010010, "CO,MI","ROO, IIH, CE","FI","EndCmd","","","","","","","","","","","",""),
    "SPIN": (0b00010011, "CO,MI","ROO, IIH, CE","RegOut, SPIn","EndCmd","","","","","","","","","","","",""),
    "SPDOUT": (0b00010100, "CO,MI","ROO, IIH, CE","RegIn, SPDOut","EndCmd","","","","","","","","","","","",""),
    "SPAPOP": (0b00010101, "CO,MI","ROO, IIH, CE","SPINC","MI, SPAOut","RegIn, RAO","EndCmd","","","","","","","","","",""),
    "SPAPUSH": (0b00010110, "CO,MI","ROO, IIH, CE","MI, SPAOut","RegOut, RAI","SPDEC","EndCmd","","","","","","","","","",""),
    "SPINC": (0b00010111, "CO,MI","ROO, IIH, CE","SPINC","EndCmd","","","","","","","","","","","",""),
    "SPDEC": (0b00011000, "CO,MI","ROO, IIH, CE","SPDEC","EndCmd","","","","","","","","","","","",""),
    "FI": (0b00011001, "CO,MI","ROO, IIH, CE","FI","EndCmd","","","","","","","","","","","",""),
    "LDCO": (0b00011010, "CO,MI","ROO, IIH, CE","CDO, RegIn","EndCmd","","","","","","","","","","","",""),
    "JMPR": (0b00011011, "CO,MI","ROO, IIH, CE","RegOut, IIL","IOL, JMP","EndCmd","","","","","","","","","","",""),
    "JN": (0b00011100, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOL, JN","EndCmd","","","","","","","","","",""),
    "JO":  (0b00011101, "CO,MI","ROO, IIH, CE","CO, MI","ROO, IIL, CE","IOL, JO","EndCmd","","","","","","","","","","")

}


# ===== ROM geometry =====
# Address bits: [12:5]=8 (opcode bits 15..8), [3:0]=4 (micro-step)
ADDR_BITS = 12
ROM_DEPTH = 1 << ADDR_BITS  # 4096 addresses
ROM_WIDTH = 8               # 8-bit wide per ROM
ROM_IDS = (1, 2, 3, 4, 5)      # 4 ROMs



rom_data = {rid: [0] * ROM_DEPTH for rid in ROM_IDS} # Initialise Roms with Zeros



def populate_rom_data():    
    rom_addr = 0 # Set Starting Address
    for mnemonic, (opcode, *steps) in INSTRUCTIONS.items():
        print("-----------------------------")
        print(f"Instruction: {mnemonic}")
        print(f"Opcode: {opcode:09b}")    
        print("-----------------------------\n")
        if rom_addr >0:
            rom_addr = rom_addr
        for i in range(0,16):
            rom_addr = (opcode << 4) | i
            step_byte_r1 = 0    
            step_byte_r2 = 0  
            step_byte_r3 = 0  
            step_byte_r4 = 0  
            step_byte_r5 = 0  
            sig = [s.strip() for s in steps[i].split(",")]  
            if sig != ['']:   
                print(f"Step {i}: {sig}")
                #print("------------------------")
                #print(f"Number of Control Lines in Step: {len(sig)}")
                for x in range(0,(len(sig))):

                    if sig[x] in CONTROL_LINES_MAP:
                        cmd_set = CONTROL_LINES_MAP[sig[x]]
                        #print(f"Command Set {cmd_set}")
                        #print(f"Rom Number {cmd_set[0]}")
                        #print(f"Rom Pin {bin(cmd_set[1])[2:].zfill(8)}")
                        if cmd_set[0] == 1:
                            step_byte_r1 |= (1 << cmd_set[1])
                        if cmd_set[0] == 2:
                            step_byte_r2 |= (1 << cmd_set[1])
                        if cmd_set[0] == 3:
                            step_byte_r3 |= (1 << cmd_set[1])
                        if cmd_set[0] == 4:
                            step_byte_r4 |= (1 << cmd_set[1])
                        if cmd_set[0] == 5:
                            step_byte_r5 |= (1 << cmd_set[1])


                rom_data[1][rom_addr] = step_byte_r1
                rom_data[2][rom_addr] = step_byte_r2
                rom_data[3][rom_addr] = step_byte_r3
                rom_data[4][rom_addr] = step_byte_r4
                rom_data[5][rom_addr] = step_byte_r5
                print(f"Writing {rom_data[1][rom_addr]} to ROM 1 at address {rom_addr}")
                print(f"Writing {rom_data[2][rom_addr]} to ROM 2 at address {rom_addr}")
                print(f"Writing {rom_data[3][rom_addr]} to ROM 3 at address {rom_addr}")
                print(f"Writing {rom_data[4][rom_addr]} to ROM 4 at address {rom_addr}")
                print(f"Writing {rom_data[5][rom_addr]} to ROM 5 at address {rom_addr}")
                rom_addr = rom_addr + 1
                print("\n")
            else:
                rom_addr = rom_addr + 1

def write_bin_files(output_prefix="PCB_microcode_BIN"):
    """
    Write each ROM as a raw binary file (one byte per address).
    Many EEPROM programmers accept raw .bin files.
    """
    for rom_id in ROM_IDS:
        out_path = Path(f"{output_prefix}_{rom_id}.bin")
        with out_path.open("wb") as f:
            f.write(bytes(rom_data[rom_id]))
        print(f"[ok] Wrote {out_path} ({len(rom_data[rom_id])} bytes)")

def _intel_hex_record(addr, data_bytes):
    """
    Build a single Intel HEX record (data record) for given address and bytes.
    Returns a string like ':10XXXX00...CC' with newline.
    """
    length = len(data_bytes)
    record_type = 0x00
    # address is 16-bit for data record
    hi = (addr >> 8) & 0xFF
    lo = addr & 0xFF
    checksum = (length + hi + lo + record_type + sum(data_bytes)) & 0xFF
    checksum = ((~checksum + 1) & 0xFF)
    payload = ''.join(f"{b:02X}" for b in data_bytes)
    return f":{length:02X}{addr:04X}{record_type:02X}{payload}{checksum:02X}\n"

def write_intel_hex_files(output_prefix="PCB_microcode_HEX", line_size=16):
    """
    Write each ROM as an Intel HEX file (standard format).
    Splits ROM into lines of 'line_size' bytes per record.
    """
    for rom_id in ROM_IDS:
        out_path = Path(f"{output_prefix}_{rom_id}.hex")
        with out_path.open("w") as f:
            rom = rom_data[rom_id]
            # write data records in chunks
            for addr in range(0, len(rom), line_size):
                chunk = rom[addr:addr + line_size]
                # convert chunk to bytes values (already ints)
                f.write(_intel_hex_record(addr, chunk))
            # End Of File record
            f.write(":00000001FF\n")
        print(f"[ok] Wrote {out_path} ({len(rom)} bytes)")

     

def write_hex_files(output_prefix="Logisim_microcode_HEX"):
    """
    Write each ROM to a .hex file: one byte per line, upper-case hex.
    """
    for rom_id in ROM_IDS:
        out_path = Path(f"{output_prefix}_{rom_id}.hex")
        with out_path.open("w") as f:
            for byte in rom_data[rom_id]:
                f.write(f"{byte:02X}\n")
        print(f"[ok] Wrote {out_path} ({ROM_DEPTH} lines)")


populate_rom_data()

write_hex_files()
write_bin_files()
write_intel_hex_files()