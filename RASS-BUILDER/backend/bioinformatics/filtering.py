from dataclasses import dataclass

from bioinformatics.fastq_parser import FastqRead
from bioinformatics.quality import decode_phred33


@dataclass
class FilterConfig:
    min_mean_quality: float = 20.0
    min_length: int = 1
    max_n_fraction: float = 0.05


def calculate_n_fraction(sequence: str) -> float:
    if not sequence:
        return 1.0

    return sequence.count("N") / len(sequence)


def calculate_mean_quality(
    quality_string: str,
) -> float:

    scores = decode_phred33(
        quality_string
    )

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def passes_quality_filter(
    read: FastqRead,
    config: FilterConfig,
) -> bool:

    if len(read.sequence) < config.min_length:
        return False

    if (
        calculate_n_fraction(read.sequence)
        > config.max_n_fraction
    ):
        return False

    if (
        calculate_mean_quality(
            read.quality_string
        )
        < config.min_mean_quality
    ):
        return False

    return True


def filter_reads(
    reads: list[FastqRead],
    config: FilterConfig | None = None,
) -> tuple[list[FastqRead], dict]:

    if config is None:
        config = FilterConfig()

    passed = []
    failed = []

    for read in reads:

        if passes_quality_filter(
            read,
            config,
        ):
            passed.append(read)
        else:
            failed.append(read)

    total = len(reads)

    return passed, {
        "input_reads": total,
        "passed_reads": len(passed),
        "failed_reads": len(failed),
        "pass_rate": round(
            (
                len(passed) / total * 100
                if total
                else 0
            ),
            2,
        ),
    }
