"""
RASS-BUILDER Bioinformatics: DNA Sequence Tokenizer Module
Supports Stage 4 legacy tokenization and Stage 5 Transformer tokenization with
canonical nucleotide mapping and special tokens (<PAD>, <UNK>, <START>, <END>).
"""

from typing import Optional, List, Dict, Tuple, Any

# ==============================================================================
# STAGE 4 LEGACY TOKENIZATION (Preserved for backwards compatibility)
# ==============================================================================

BASE_TO_TOKEN = {
    "PAD": 0,
    "A": 1,
    "C": 2,
    "G": 3,
    "T": 4,
    "N": 5,
}


def tokenize_sequence(
    sequence: str,
) -> list[int]:
    """Stage 4 simple tokenization mapping A/C/G/T/N/other to integers."""
    sequence = sequence.upper()

    return [
        BASE_TO_TOKEN.get(
            base,
            BASE_TO_TOKEN["N"],
        )
        for base in sequence
    ]


def tokenize_with_padding(
    sequence: str,
    max_length: int,
) -> list[int]:
    """Stage 4 tokenization with zero padding up to max_length."""
    tokens = tokenize_sequence(
        sequence
    )

    tokens = tokens[:max_length]

    padding_length = (
        max_length - len(tokens)
    )

    tokens.extend(
        [BASE_TO_TOKEN["PAD"]]
        * padding_length
    )

    return tokens


# ==============================================================================
# STAGE 5 DNA TRANSFORMER TOKENIZER
# ==============================================================================

STAGE5_VOCAB: Dict[str, int] = {
    "<PAD>": 0,
    "<UNK>": 1,
    "<START>": 2,
    "<END>": 3,
    "A": 4,
    "C": 5,
    "G": 6,
    "T": 7,
    "N": 8,
}

STAGE5_ID_TO_TOKEN: Dict[int, str] = {v: k for k, v in STAGE5_VOCAB.items()}

CANONICAL_BASES = {"A", "C", "G", "T"}
VALID_BASES = {"A", "C", "G", "T", "N"}


class DNATokenizer:
    """
    Standard DNA Tokenizer for Transformer Sequence Models.
    
    Features:
    - Normalizes raw sequence inputs (whitespace stripping, uppercase conversion)
    - Detects invalid bases and replaces with <UNK> without fabricating biology
    - Adds sequence demarcation special tokens (<START>, <END>, <PAD>, <UNK>)
    - Maintains bidirectional mappings between tokens and integer IDs
    - Supports configurable padding and truncation
    """

    def __init__(
        self,
        vocab: Optional[Dict[str, int]] = None,
        max_seq_len: int = 5000,
    ):
        self.vocab = vocab or dict(STAGE5_VOCAB)
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        self.max_seq_len = max_seq_len

        self.pad_token = "<PAD>"
        self.unk_token = "<UNK>"
        self.start_token = "<START>"
        self.end_token = "<END>"

        self.pad_id = self.vocab[self.pad_token]
        self.unk_id = self.vocab[self.unk_token]
        self.start_id = self.vocab[self.start_token]
        self.end_id = self.vocab[self.end_token]

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    def normalize(self, sequence: str) -> str:
        """Strips surrounding whitespace and converts sequence to uppercase."""
        if sequence is None:
            return ""
        return sequence.strip().upper()

    def detect_invalid_bases(self, sequence: str) -> List[Dict[str, Any]]:
        """
        Scans sequence and identifies positions of characters outside canonical {A, C, G, T, N}.
        Returns detailed list of detected invalid characters with 0-based indices.
        """
        norm_seq = self.normalize(sequence)
        invalid = []
        for idx, char in enumerate(norm_seq):
            if char not in VALID_BASES:
                invalid.append({
                    "position": idx,
                    "char": char,
                    "canonical": False,
                })
        return invalid

    def validate_sequence(
        self,
        sequence: str,
        max_length: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates sequence integrity.
        Returns (is_valid, error_message).
        """
        if sequence is None or not sequence.strip():
            return False, "DNA sequence cannot be empty."

        clean = sequence.strip()
        limit = max_length or self.max_seq_len
        if len(clean) > limit:
            return (
                False,
                f"Sequence length ({len(clean)} bp) exceeds maximum supported limit of {limit} bp.",
            )

        return True, None

    def tokenize(
        self,
        sequence: str,
        add_special_tokens: bool = True,
    ) -> List[str]:
        """
        Splits sequence into individual string tokens, replacing invalid characters with <UNK>.
        Optionally prefixes <START> and appends <END>.
        """
        norm_seq = self.normalize(sequence)
        tokens: List[str] = []

        if add_special_tokens:
            tokens.append(self.start_token)

        for base in norm_seq:
            if base in self.vocab:
                tokens.append(base)
            else:
                tokens.append(self.unk_token)

        if add_special_tokens:
            tokens.append(self.end_token)

        return tokens

    def encode(
        self,
        sequence: str,
        add_special_tokens: bool = True,
        max_length: Optional[int] = None,
        padding: bool = False,
        truncation: bool = True,
    ) -> List[int]:
        """
        Converts sequence into list of integer token IDs.
        Handles special tokens, optional truncation, and optional padding.
        """
        tokens = self.tokenize(sequence, add_special_tokens=add_special_tokens)
        token_ids = [self.vocab.get(t, self.unk_id) for t in tokens]

        target_len = max_length or self.max_seq_len

        if truncation and len(token_ids) > target_len:
            if add_special_tokens and len(token_ids) > 1:
                # Retain the <END> token at the truncated boundary
                token_ids = token_ids[: target_len - 1] + [self.end_id]
            else:
                token_ids = token_ids[:target_len]

        if padding and len(token_ids) < target_len:
            pad_count = target_len - len(token_ids)
            token_ids.extend([self.pad_id] * pad_count)

        return token_ids

    def decode(
        self,
        token_ids: List[int],
        skip_special_tokens: bool = False,
    ) -> str:
        """Converts list of token IDs back into string representation."""
        special_ids = {self.pad_id, self.unk_id, self.start_id, self.end_id}
        parts: List[str] = []

        for tid in token_ids:
            if skip_special_tokens and tid in special_ids:
                continue
            token_str = self.id_to_token.get(tid, self.unk_token)
            parts.append(token_str)

        return "".join(parts)

    def get_token_details(
        self,
        sequence: str,
        add_special_tokens: bool = True,
    ) -> Dict[str, Any]:
        """
        Produces comprehensive tokenization telemetry for Stage 5 inspection.
        """
        norm_seq = self.normalize(sequence)
        tokens = self.tokenize(norm_seq, add_special_tokens=add_special_tokens)
        token_ids = [self.vocab.get(t, self.unk_id) for t in tokens]
        invalid_bases = self.detect_invalid_bases(norm_seq)

        canonical_count = sum(1 for b in norm_seq if b in CANONICAL_BASES)
        valid_ratio = round(canonical_count / max(1, len(norm_seq)), 4) if norm_seq else 0.0

        return {
            "raw_length": len(sequence),
            "normalized_sequence": norm_seq,
            "tokens": tokens,
            "token_ids": token_ids,
            "token_count": len(token_ids),
            "special_tokens_applied": add_special_tokens,
            "invalid_bases": invalid_bases,
            "invalid_base_count": len(invalid_bases),
            "canonical_base_ratio": valid_ratio,
            "vocabulary_size": self.vocab_size,
        }

    def get_vocab_mapping(self) -> Dict[str, Any]:
        """Returns vocabulary dictionary and metadata for documentation/UI display."""
        return {
            "token_to_id": dict(self.vocab),
            "id_to_token": dict(self.id_to_token),
            "special_tokens": {
                "pad": {"token": self.pad_token, "id": self.pad_id},
                "unk": {"token": self.unk_token, "id": self.unk_id},
                "start": {"token": self.start_token, "id": self.start_id},
                "end": {"token": self.end_token, "id": self.end_id},
            },
        }
