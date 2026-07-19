#!/usr/bin/env python3
"""간이 65816 디스어셈블러 (M/X 플래그 지정 가능). 루틴 분석용."""
import sys

# opcode -> (mnemonic, mode)
# mode: imp, imm(m/x 가변은 immM/immX), immb(항상8), rel, rel16, dp, dpx, dpy,
#       abs, absx, absy, ind, indx, indy, indl, indly, long, longx, sr, sry, blockmove, absind, absindx
OPS = {
0x00:("BRK","immb"),0x01:("ORA","indx"),0x02:("COP","immb"),0x03:("ORA","sr"),
0x04:("TSB","dp"),0x05:("ORA","dp"),0x06:("ASL","dp"),0x07:("ORA","indl"),
0x08:("PHP","imp"),0x09:("ORA","immM"),0x0A:("ASL","imp"),0x0B:("PHD","imp"),
0x0C:("TSB","abs"),0x0D:("ORA","abs"),0x0E:("ASL","abs"),0x0F:("ORA","long"),
0x10:("BPL","rel"),0x11:("ORA","indy"),0x12:("ORA","ind"),0x13:("ORA","sry"),
0x14:("TRB","dp"),0x15:("ORA","dpx"),0x16:("ASL","dpx"),0x17:("ORA","indly"),
0x18:("CLC","imp"),0x19:("ORA","absy"),0x1A:("INC","imp"),0x1B:("TCS","imp"),
0x1C:("TRB","abs"),0x1D:("ORA","absx"),0x1E:("ASL","absx"),0x1F:("ORA","longx"),
0x20:("JSR","abs"),0x21:("AND","indx"),0x22:("JSL","long"),0x23:("AND","sr"),
0x24:("BIT","dp"),0x25:("AND","dp"),0x26:("ROL","dp"),0x27:("AND","indl"),
0x28:("PLP","imp"),0x29:("AND","immM"),0x2A:("ROL","imp"),0x2B:("PLD","imp"),
0x2C:("BIT","abs"),0x2D:("AND","abs"),0x2E:("ROL","abs"),0x2F:("AND","long"),
0x30:("BMI","rel"),0x31:("AND","indy"),0x32:("AND","ind"),0x33:("AND","sry"),
0x34:("BIT","dpx"),0x35:("AND","dpx"),0x36:("ROL","dpx"),0x37:("AND","indly"),
0x38:("SEC","imp"),0x39:("AND","absy"),0x3A:("DEC","imp"),0x3B:("TSC","imp"),
0x3C:("BIT","absx"),0x3D:("AND","absx"),0x3E:("ROL","absx"),0x3F:("AND","longx"),
0x40:("RTI","imp"),0x41:("EOR","indx"),0x42:("WDM","immb"),0x43:("EOR","sr"),
0x44:("MVP","blockmove"),0x45:("EOR","dp"),0x46:("LSR","dp"),0x47:("EOR","indl"),
0x48:("PHA","imp"),0x49:("EOR","immM"),0x4A:("LSR","imp"),0x4B:("PHK","imp"),
0x4C:("JMP","abs"),0x4D:("EOR","abs"),0x4E:("LSR","abs"),0x4F:("EOR","long"),
0x50:("BVC","rel"),0x51:("EOR","indy"),0x52:("EOR","ind"),0x53:("EOR","sry"),
0x54:("MVN","blockmove"),0x55:("EOR","dpx"),0x56:("LSR","dpx"),0x57:("EOR","indly"),
0x58:("CLI","imp"),0x59:("EOR","absy"),0x5A:("PHY","imp"),0x5B:("TCD","imp"),
0x5C:("JML","long"),0x5D:("EOR","absx"),0x5E:("LSR","absx"),0x5F:("EOR","longx"),
0x60:("RTS","imp"),0x61:("ADC","indx"),0x62:("PER","rel16"),0x63:("ADC","sr"),
0x64:("STZ","dp"),0x65:("ADC","dp"),0x66:("ROR","dp"),0x67:("ADC","indl"),
0x68:("PLA","imp"),0x69:("ADC","immM"),0x6A:("ROR","imp"),0x6B:("RTL","imp"),
0x6C:("JMP","absind"),0x6D:("ADC","abs"),0x6E:("ROR","abs"),0x6F:("ADC","long"),
0x70:("BVS","rel"),0x71:("ADC","indy"),0x72:("ADC","ind"),0x73:("ADC","sry"),
0x74:("STZ","dpx"),0x75:("ADC","dpx"),0x76:("ROR","dpx"),0x77:("ADC","indly"),
0x78:("SEI","imp"),0x79:("ADC","absy"),0x7A:("PLY","imp"),0x7B:("TDC","imp"),
0x7C:("JMP","absindx"),0x7D:("ADC","absx"),0x7E:("ROR","absx"),0x7F:("ADC","longx"),
0x80:("BRA","rel"),0x81:("STA","indx"),0x82:("BRL","rel16"),0x83:("STA","sr"),
0x84:("STY","dp"),0x85:("STA","dp"),0x86:("STX","dp"),0x87:("STA","indl"),
0x88:("DEY","imp"),0x89:("BIT","immM"),0x8A:("TXA","imp"),0x8B:("PHB","imp"),
0x8C:("STY","abs"),0x8D:("STA","abs"),0x8E:("STX","abs"),0x8F:("STA","long"),
0x90:("BCC","rel"),0x91:("STA","indy"),0x92:("STA","ind"),0x93:("STA","sry"),
0x94:("STY","dpx"),0x95:("STA","dpx"),0x96:("STX","dpy"),0x97:("STA","indly"),
0x98:("TYA","imp"),0x99:("STA","absy"),0x9A:("TXS","imp"),0x9B:("TXY","imp"),
0x9C:("STZ","abs"),0x9D:("STA","absx"),0x9E:("STZ","absx"),0x9F:("STA","longx"),
0xA0:("LDY","immX"),0xA1:("LDA","indx"),0xA2:("LDX","immX"),0xA3:("LDA","sr"),
0xA4:("LDY","dp"),0xA5:("LDA","dp"),0xA6:("LDX","dp"),0xA7:("LDA","indl"),
0xA8:("TAY","imp"),0xA9:("LDA","immM"),0xAA:("TAX","imp"),0xAB:("PLB","imp"),
0xAC:("LDY","abs"),0xAD:("LDA","abs"),0xAE:("LDX","abs"),0xAF:("LDA","long"),
0xB0:("BCS","rel"),0xB1:("LDA","indy"),0xB2:("LDA","ind"),0xB3:("LDA","sry"),
0xB4:("LDY","dpx"),0xB5:("LDA","dpx"),0xB6:("LDX","dpy"),0xB7:("LDA","indly"),
0xB8:("CLV","imp"),0xB9:("LDA","absy"),0xBA:("TSX","imp"),0xBB:("TYX","imp"),
0xBC:("LDY","absx"),0xBD:("LDA","absx"),0xBE:("LDX","absy"),0xBF:("LDA","longx"),
0xC0:("CPY","immX"),0xC1:("CMP","indx"),0xC2:("REP","immb"),0xC3:("CMP","sr"),
0xC4:("CPY","dp"),0xC5:("CMP","dp"),0xC6:("DEC","dp"),0xC7:("CMP","indl"),
0xC8:("INY","imp"),0xC9:("CMP","immM"),0xCA:("DEX","imp"),0xCB:("WAI","imp"),
0xCC:("CPY","abs"),0xCD:("CMP","abs"),0xCE:("DEC","abs"),0xCF:("CMP","long"),
0xD0:("BNE","rel"),0xD1:("CMP","indy"),0xD2:("CMP","ind"),0xD3:("CMP","sry"),
0xD4:("PEI","dp"),0xD5:("CMP","dpx"),0xD6:("DEC","dpx"),0xD7:("CMP","indly"),
0xD8:("CLD","imp"),0xD9:("CMP","absy"),0xDA:("PHX","imp"),0xDB:("STP","imp"),
0xDC:("JML","absindl"),0xDD:("CMP","absx"),0xDE:("DEC","absx"),0xDF:("CMP","longx"),
0xE0:("CPX","immX"),0xE1:("SBC","indx"),0xE2:("SEP","immb"),0xE3:("SBC","sr"),
0xE4:("CPX","dp"),0xE5:("SBC","dp"),0xE6:("INC","dp"),0xE7:("SBC","indl"),
0xE8:("INX","imp"),0xE9:("SBC","immM"),0xEA:("NOP","imp"),0xEB:("XBA","imp"),
0xEC:("CPX","abs"),0xED:("SBC","abs"),0xEE:("INC","abs"),0xEF:("SBC","long"),
0xF0:("BEQ","rel"),0xF1:("SBC","indy"),0xF2:("SBC","ind"),0xF3:("SBC","sry"),
0xF4:("PEA","abs"),0xF5:("SBC","dpx"),0xF6:("INC","dpx"),0xF7:("SBC","indly"),
0xF8:("SED","imp"),0xF9:("SBC","absy"),0xFA:("PLX","imp"),0xFB:("XCE","imp"),
0xFC:("JSR","absindx"),0xFD:("SBC","absx"),0xFE:("INC","absx"),0xFF:("SBC","longx"),
}

def oplen(mode, m, x):
    base={"imp":1,"immb":2,"rel":2,"rel16":3,"dp":2,"dpx":2,"dpy":2,"abs":3,"absx":3,
    "absy":3,"ind":2,"indx":2,"indy":2,"indl":2,"indly":2,"long":4,"longx":4,"sr":2,
    "sry":2,"blockmove":3,"absind":3,"absindx":3,"absindl":3}
    if mode=="immM": return 3 if m==0 else 2
    if mode=="immX": return 3 if x==0 else 2
    return base[mode]

def fmt(mode,b,pc,m,x):
    o=b[1:]
    def w16(): return o[0]|(o[1]<<8)
    def w24(): return o[0]|(o[1]<<8)|(o[2]<<16)
    if mode=="imp": return ""
    if mode=="immb": return f"#${o[0]:02X}"
    if mode in("immM","immX"):
        wide=(mode=="immM" and m==0) or (mode=="immX" and x==0)
        return f"#${w16():04X}" if wide else f"#${o[0]:02X}"
    if mode=="rel":
        d=o[0]-256 if o[0]>=128 else o[0]; return f"${(pc+2+d)&0xFFFF:04X}"
    if mode=="rel16":
        d=w16(); d=d-65536 if d>=32768 else d; return f"${(pc+3+d)&0xFFFF:04X}"
    if mode=="dp": return f"${o[0]:02X}"
    if mode=="dpx": return f"${o[0]:02X},X"
    if mode=="dpy": return f"${o[0]:02X},Y"
    if mode=="abs": return f"${w16():04X}"
    if mode=="absx": return f"${w16():04X},X"
    if mode=="absy": return f"${w16():04X},Y"
    if mode=="ind": return f"(${o[0]:02X})"
    if mode=="indx": return f"(${o[0]:02X},X)"
    if mode=="indy": return f"(${o[0]:02X}),Y"
    if mode=="indl": return f"[${o[0]:02X}]"
    if mode=="indly": return f"[${o[0]:02X}],Y"
    if mode=="long": return f"${w24():06X}"
    if mode=="longx": return f"${w24():06X},X"
    if mode=="sr": return f"${o[0]:02X},S"
    if mode=="sry": return f"(${o[0]:02X},S),Y"
    if mode=="blockmove": return f"${o[0]:02X},${o[1]:02X}"
    if mode=="absind": return f"(${w16():04X})"
    if mode=="absindx": return f"(${w16():04X},X)"
    if mode=="absindl": return f"[${w16():04X}]"
    return "?"

def disasm(data, start, count, m=1, x=1, pcbase=None):
    i=start; pc = pcbase if pcbase is not None else start
    for _ in range(count):
        op=data[i]
        mn,mode=OPS.get(op,("???","imp"))
        ln=oplen(mode,m,x)
        b=data[i:i+ln]
        operand=fmt(mode,b,pc,m,x)
        raw=" ".join(f"{c:02X}" for c in b)
        print(f"  {pc:04X}: {raw:<12} {mn} {operand}")
        # 플래그 추적 (SEP/REP)
        if op==0xC2:  # REP
            v=b[1]
            if v&0x20: m=0
            if v&0x10: x=0
        elif op==0xE2:  # SEP
            v=b[1]
            if v&0x20: m=1
            if v&0x10: x=1
        i+=ln; pc+=ln

if __name__=="__main__":
    rom=open(sys.argv[1],"rb").read()
    fileoff=int(sys.argv[2],0)
    count=int(sys.argv[3]) if len(sys.argv)>3 else 40
    m=int(sys.argv[4]) if len(sys.argv)>4 else 1
    x=int(sys.argv[5]) if len(sys.argv)>5 else 1
    pcbase=int(sys.argv[6],0) if len(sys.argv)>6 else None
    disasm(rom,fileoff,count,m,x,pcbase)
