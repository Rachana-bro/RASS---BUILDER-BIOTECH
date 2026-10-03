from dataclasses import dataclass
from typing import Iterator


@dataclass
class FastqRead:
    read_id: str
    sequence: str
    quality_string: str


def parse_fastq(file_path: str) -> Iterator[FastqRead]:
    """
    Parse a FASTQ file using the standard four-line record format.

    FASTQ:
        @read_id
        sequence
        +
        quality
    """

    with open(file_path, "r", encoding="utf-8") as file:
        line_number = 0

        while True:
            header = file.readline()

            if not header:
                break

            sequence = file.readline()
            separator = file.readline()
            quality = file.readline()

            line_number += 4

            if not sequence or not separator or not quality:
                raise ValueError(
                    f"Incomplete FASTQ record near line {line_number}"
                )

            header = header.strip()
            sequence = sequence.strip()
            separator = separator.strip()
            quality = quality.strip()

            if not header.startswith("@"):
                raise ValueError(
                    f"Invalid FASTQ header near line {line_number - 3}"
                )

            if separator != "+":
                raise ValueError(
                    f"Invalid FASTQ separator near line {line_number - 1}"
                )

            if len(sequence) != len(quality):
                raise ValueError(
                    f"Sequence/quality length mismatch near line "
                    f"{line_number - 3}"
                )

            read_id = header[1:].split()[0]

            yield FastqRead(
                read_id=read_id,
                sequence=sequence.upper(),
                quality_string=quality,
            )


def count_reads(file_path: str) -> int:
    return sum(1 for _ in parse_fastq(file_path))
