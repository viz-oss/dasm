"""Format: Mach-O for Apple Silicon"""

"""
┌─────────────────────────────┐  offset 0
│ mach_header_64 (32 B)       │
│   ncmds      = 2            │  ← liczba LOAD COMMANDS
│   sizeofcmds = 176          │  ← suma ich cmdsize
├─────────────────────────────┤  offset 32
│ LC_SEGMENT_64 (152 B)       │  ← opisuje __TEXT/__text
│ LC_SYMTAB     (24 B)        │  ← opisuje tablicę symboli
├─────────────────────────────┤  offset 32 + 176 = 208
│ __text: instrukcje (words)  │  ← TU trafiają words
│   20 00 80 d2  (mov x0,#1)  │
│   c0 03 5f d6  (ret)        │
├─────────────────────────────┤
│ tablica symboli (nlist_64)  │
├─────────────────────────────┤
│ tablica stringów            │
└─────────────────────────────┘
"""

import struct
from format.base import Format

LC_SEGMENT_64 = 0x19
LC_SYMTAB     = 0x2

VM_PROT_READ    = 0x1
VM_PROT_WRITE   = 0x2
VM_PROT_EXECUTE = 0x4

S_ATTR_PURE_INSTRUCTIONS = 0x80000000
S_ATTR_SOME_INSTRUCTIONS = 0x00000400


class FormatMacho(Format):

    def __init__(self):
        self.ext = 'o'

    def _mach_header_64(self,
        ncmds: int,               # Number of commands
        sizeofcmds: int           # Total size of all commands
    ) -> bytes:
        """March-o 64 header"""
        magic: int = 0xFEEDFACF   # Magic (64-bit Mach-O)
        cputype: int = 0x0100000C # CPU_TYPE_ARM64
        cpusubtype: int = 0       # CPU_SUBTYPE_ARM64_ALL 0 (lub 2 dla arm64e)
        filetype: int = 1         # 1 (MH_OBJECT)
        flags: int = 0x2000       # Np. 0x2000 (MH_SUBSECTIONS_VIA_SYMBOLS)
        reserved: int = 0         # Reserved
        return struct.pack(
            '<8I',
            magic,
            cputype,
            cpusubtype,
            filetype,
            ncmds,
            sizeofcmds,
            flags,
            reserved
        )
        
    def _pad16(self, name: str) -> bytes:
        """Zwraca 16-bajtową nazwę, dopełnioną zerami."""
        return name.encode("utf-8")[:16].ljust(16, b"\x00")

    def _lc_segment64(self,
        fileoff: int,
        filesize: int,
        vmaddr: int = 0,
        vmsize: int = 0,
    ) -> bytes:
        """
        Buduje LC_SEGMENT_64 z jedną sekcją __text.
        fileoff/filesize dotyczą całego segmentu __TEXT (czyli kodu).
        """
        nsects = 1
        cmdsize = 72 + 80 * nsects  # 152

        # --- nagłówek segment_command_64 ---
        seg = struct.pack(
            "<II16sQQQQiiII",
            LC_SEGMENT_64,          # cmd
            cmdsize,                # cmdsize
            self._pad16("__TEXT"),  # segname
            vmaddr,                 # vmaddr
            vmsize,                 # vmsize
            fileoff,                # fileoff
            filesize,               # filesize
            VM_PROT_READ | VM_PROT_EXECUTE,  # maxprot
            VM_PROT_READ | VM_PROT_EXECUTE,  # initprot
            nsects,                 # nsects
            0,                      # flags
        )
        assert len(seg) == 72

        # --- section_64 dla __text ---
        sect = struct.pack(
            "<16s16sQQIIIIIIII",
            self._pad16("__text"),  # sectname
            self._pad16("__TEXT"),  # segname
            0,                      # addr
            filesize,               # size (rozmiar kodu w bajtach)
            fileoff,                # offset (tam, gdzie zaczyna się kod)
            2,                      # align (2^2 = 4 bajty)
            0,                      # reloff
            0,                      # nreloc
            S_ATTR_PURE_INSTRUCTIONS | S_ATTR_SOME_INSTRUCTIONS,  # flags
            0,                      # reserved1
            0,                      # reserved2
            0,                      # reserved3
        )
        assert len(sect) == 80

        return seg + sect
            
    def _lc_symtab(self,
        symoff: int,
        nsyms: int,
        stroff: int,
        strsize: int
    ) -> bytes:
        return struct.pack(
            "<IIIIII",
            LC_SYMTAB,   # cmd
            24,          # cmdsize
            symoff,      # symoff
            nsyms,       # nsyms
            stroff,      # stroff
            strsize,     # strsize
        )

    def output(self, words: list[int]) -> bytes:
        text_blob = struct.pack(f"<{len(words)}I", *words)
        text_size = len(text_blob)
        
        lc_seg_tmp = self._lc_segment64(fileoff=0, filesize=text_size, vmaddr=0, vmsize=text_size)

        sizeofcmds = len(lc_seg_tmp) + 24
        ncmds = 2
        fileoff = 32 + sizeofcmds
        text_end = fileoff + text_size
        symoff = text_end
        stroff = text_end
        strtab   = b"\x00"
        
        lc_symtab = self._lc_symtab(symoff=symoff, nsyms=0, stroff=stroff, strsize=len(strtab))

        lc_seg = self._lc_segment64(fileoff=fileoff, filesize=text_size, vmaddr=0, vmsize=text_size)
        
        header = self._mach_header_64(ncmds, sizeofcmds)
                
        return header + lc_seg + lc_symtab + text_blob + strtab

EXPORTS = FormatMacho
