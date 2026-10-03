"""
RASS-BUILDER: Stage 10 FASTA File Parser & Validator
Validates and parses standard single- or multi-record FASTA genomic files.
"""

from dataclasses import dataclass
from typing import Iterator


@dataclass
class FastaRecord:
    record_id: str
    sequence: str


def parse_fasta(file_path: str) -> Iterator[FastaRecord]:
    """
    Parses a FASTA format file into FastaRecord items.
    Validates that file starts with '>' and contains valid sequence lines.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        current_id = None
        current_seq_parts = []
        line_num = 0

        for line in file:
            line_num += 1
            stripped = line.strip()
            if not stripped:
                continue

            if stripped.startswith(">"):
                if current_id is not None:
                    seq = "".join(current_seq_parts).upper()
                    if not seq:
                        raise ValueError(f"Empty sequence for FASTA record '{current_id}'.")
                    yield FastaRecord(record_id=current_id, sequence=seq)
                    current_seq_parts = []
                current_id = stripped[1:].split()[0]
                if not current_id:
                    raise ValueError(f"Empty record identifier in FASTA line {line_num}.")
            else:
                if current_id is None:
                    raise ValueError(f"Malformed FASTA file: sequence data appears before header at line {line_num}.")
                current_seq_parts.append(stripped)

        if current_id is not None:
            seq = "".join(current_seq_parts).upper()
            if not seq:
                raise ValueError(f"Empty sequence for FASTA record '{current_id}'.")
            yield FastaRecord(record_id=current_id, sequence=seq)
        elif line_num == 0:
            raise ValueError("Uploaded FASTA file is empty.")
        else:
            raise ValueError("Malformed FASTA file: missing '>' header.")
