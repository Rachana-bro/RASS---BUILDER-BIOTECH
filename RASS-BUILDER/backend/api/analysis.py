from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from bioinformatics.fastq_parser import (
    FastqRead,
    parse_fastq,
)

from bioinformatics.filtering import (
    FilterConfig,
    filter_reads,
)

from bioinformatics.normalization import (
    normalize_sequence,
)

from bioinformatics.tokenizer import (
    tokenize_sequence,
)

from models.inference import (
    DNASequenceModel,
    ModelInput,
)

from models.stage5_engine import (
    stage5_engine,
)


router = APIRouter(
    prefix="/api/v1/analysis",
    tags=["Analysis"],
)


# ==============================================================================
# STAGE 4 PREPARATION CONTRACT
# ==============================================================================

class AnalysisRequest(BaseModel):
    file_path: str
    max_reads: int = 1000
    min_quality: float = 20.0


@router.post("/prepare")
def prepare_analysis(
    request: AnalysisRequest,
):
    # Resolve file path gracefully whether called from backend/ or project root
    file_path = Path(request.file_path)
    if not file_path.exists():
        candidate_root = Path(__file__).resolve().parent.parent.parent / request.file_path
        if candidate_root.exists():
            file_path = candidate_root

    try:
        reads = []

        for read in parse_fastq(
            str(file_path)
        ):
            reads.append(read)

            if (
                len(reads)
                >= request.max_reads
            ):
                break

    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    config = FilterConfig(
        min_mean_quality=request.min_quality,
        min_length=1,
    )

    passed_reads, filter_metrics = (
        filter_reads(
            reads,
            config,
        )
    )

    sequences = []

    for read in passed_reads:
        normalized = normalize_sequence(
            read.sequence
        )

        tokens = tokenize_sequence(
            normalized
        )

        sequences.append(
            {
                "read_id": read.read_id,
                "sequence": normalized,
                "tokens": tokens,
                "length": len(normalized),
            }
        )

    model = DNASequenceModel()

    model_preview = None

    if sequences:
        model_input = ModelInput(
            sequence=sequences[0]["sequence"],
            tokens=sequences[0]["tokens"],
        )

        model_preview = (
            model.predict(
                model_input
            ).__dict__
        )

    return {
        "status": "prepared",
        "input": {
            "requested_reads":
                request.max_reads,
            "processed_reads":
                len(reads),
        },
        "filtering": filter_metrics,
        "sequences": sequences,
        "model": model_preview,
    }


# ==============================================================================
# STAGE 5 DNA TRANSFORMER ANALYSIS ENDPOINT
# ==============================================================================

class Stage5AnalysisRequest(BaseModel):
    sequence: str = Field(..., description="Raw or normalized DNA sequence (A, C, G, T, N)")
    read_id: Optional[str] = Field("READ_001", description="Identifier of the sequence read")
    tokens: Optional[List[int]] = Field(None, description="Optional pre-tokenized IDs from Stage 4")
    max_length: Optional[int] = Field(5000, description="Maximum sequence length limit")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Execution options")


def run_stage5_dna_analysis(request: Stage5AnalysisRequest) -> Dict[str, Any]:
    """
    Executes Stage 5 Transformer Pipeline on input DNA sequence:
    1. Validates sequence presence and length limits
    2. Runs DNA Tokenizer (<START>, <END>, <PAD>, <UNK>)
    3. Runs Transformer Forward Pass for Sequence Embedding
    4. Computes Multi-Head Self-Attention Computational Representation
    5. Evaluates Pattern Detection and Checkpoint Validation status
    6. Returns structured Stage 5 result object
    """
    if not request.sequence or not request.sequence.strip():
        raise HTTPException(
            status_code=400,
            detail="DNA sequence cannot be empty.",
        )

    clean_seq = request.sequence.strip()
    if len(clean_seq) > 10000:
        raise HTTPException(
            status_code=400,
            detail=f"Sequence length ({len(clean_seq)} bp) exceeds maximum supported limit of 10000 bp.",
        )

    try:
        result = stage5_engine.analyze_sequence(
            sequence=clean_seq,
            read_id=request.read_id,
            max_length=request.max_length or 5000,
            options=request.options,
        )
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=400,
            detail=str(val_err),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"DNA Transformer processing failed: {str(exc)}",
        )


@router.post("/dna", tags=["Stage 5 Transformer"])
def analyze_dna_v1(request: Stage5AnalysisRequest):
    """Stage 5 endpoint accessible via /api/v1/analysis/dna"""
    return run_stage5_dna_analysis(request)
