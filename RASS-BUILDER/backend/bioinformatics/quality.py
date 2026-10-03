import math
from typing import List


def decode_phred33(quality_string: str) -> List[int]:
    """
    Decode standard Phred+33 FASTQ quality characters.
    """

    return [
        ord(character) - 33
        for character in quality_string
    ]


def phred_to_error_probability(phred: float) -> float:
    """
    Convert Phred quality score to base-call error probability.

    P_error = 10 ^ (-Q / 10)
    """

    return 10 ** (-phred / 10)


def error_probability_to_phred(error_probability: float) -> float:
    """
    Convert error probability back to Phred score.
    """

    if error_probability <= 0:
        return 42.0

    return -10 * math.log10(error_probability)


def calculate_gc_content(sequence: str) -> float:
    if not sequence:
        return 0.0

    gc_count = sum(
        1
        for base in sequence
        if base in {"G", "C"}
    )

    return (gc_count / len(sequence)) * 100


def calculate_quality_metrics(reads: list) -> dict:
    if not reads:
        return {
            "read_count": 0,
            "mean_quality": 0,
            "q20_percent": 0,
            "q30_percent": 0,
            "q40_percent": 0,
            "mean_gc_percent": 0,
            "mean_read_length": 0,
            "per_cycle_quality": [],
        }

    all_quality_scores = []
    gc_values = []
    read_lengths = []

    cycle_scores = {}

    for read in reads:
        quality_scores = decode_phred33(
            read.quality_string
        )

        all_quality_scores.extend(quality_scores)

        gc_values.append(
            calculate_gc_content(read.sequence)
        )

        read_lengths.append(
            len(read.sequence)
        )

        for cycle, score in enumerate(
            quality_scores,
            start=1
        ):
            cycle_scores.setdefault(cycle, [])
            cycle_scores[cycle].append(score)

    total_bases = len(all_quality_scores)

    mean_quality = (
        sum(all_quality_scores) / total_bases
        if total_bases
        else 0
    )

    q20_percent = (
        sum(score >= 20 for score in all_quality_scores)
        / total_bases
        * 100
        if total_bases
        else 0
    )

    q30_percent = (
        sum(score >= 30 for score in all_quality_scores)
        / total_bases
        * 100
        if total_bases
        else 0
    )

    q40_percent = (
        sum(score >= 40 for score in all_quality_scores)
        / total_bases
        * 100
        if total_bases
        else 0
    )

    per_cycle_quality = [
        {
            "cycle": cycle,
            "mean_quality": round(
                sum(scores) / len(scores),
                2
            ),
        }
        for cycle, scores in sorted(
            cycle_scores.items()
        )
    ]

    return {
        "read_count": len(reads),
        "total_bases": total_bases,
        "mean_quality": round(mean_quality, 2),
        "q20_percent": round(q20_percent, 2),
        "q30_percent": round(q30_percent, 2),
        "q40_percent": round(q40_percent, 2),
        "mean_gc_percent": round(
            sum(gc_values) / len(gc_values),
            2
        ),
        "mean_read_length": round(
            sum(read_lengths) / len(read_lengths),
            2
        ),
        "per_cycle_quality": per_cycle_quality,
    }
