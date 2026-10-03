VALID_BASES = {
    "A",
    "C",
    "G",
    "T",
    "N",
}


def normalize_sequence(
    sequence: str,
) -> str:

    sequence = sequence.upper().strip()

    sequence = "".join(
        base
        if base in VALID_BASES
        else "N"
        for base in sequence
    )

    return sequence


def reverse_complement(
    sequence: str,
) -> str:

    complement = {
        "A": "T",
        "T": "A",
        "C": "G",
        "G": "C",
        "N": "N",
    }

    return "".join(
        complement[base]
        for base in reversed(
            normalize_sequence(sequence)
        )
    )
