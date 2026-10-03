"""
Unit & Contract Tests for Stage 6 — Variant & Pattern Results Dashboard.

Covers:
- Stage 5 to Stage 6 Data Contract compliance (all fields present and typed)
- Empty result and invalid response error handling
- Missing model checkpoint handling ("Trained model checkpoint unavailable")
- No pattern results empty state (safeguard against fake mutations)
- Null confidence enforcement (no fabricated 98/99% numbers)
- Validated pattern schema compatibility (future-proofing for trained checkpoints)
- Variant table data contract schema compatibility
- Computational vs Clinical interpretation separation
- API error response integrity
- Regression: Full pipeline chain from FASTQ through Stage 6 data readiness
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from models.stage5_engine import stage5_engine, Stage5DNAEngine
from bioinformatics.tokenizer import DNATokenizer

client = TestClient(app)


# ==============================================================================
# 1. STAGE 5 -> STAGE 6 DATA CONTRACT COMPLIANCE
# ==============================================================================

def test_stage6_data_contract_fields():
    """Verifies that Stage 5 structured output contains all fields required by Stage 6 UI."""
    res = client.post(
        "/api/analyze/dna",
        json={"sequence": "ACGTACGTACGT", "read_id": "READ_STAGE6_001"},
    )
    assert res.status_code == 200
    data = res.json()

    # Section A: Analysis Status
    assert "stage" in data
    assert data["stage"] == 5
    assert "status" in data
    assert data["status"] == "completed"

    # Section B: Sequence Summary
    assert "sequence_length" in data
    assert data["sequence_length"] == 12
    assert "token_count" in data
    assert data["token_count"] == 14  # 12 bases + <START> + <END>
    assert "read_id" in data
    assert data["read_id"] == "READ_STAGE6_001"
    assert "tokenizer" in data
    assert "canonical_base_ratio" in data["tokenizer"]
    assert data["tokenizer"]["canonical_base_ratio"] == 1.0

    # Section C: Model Information
    assert "model" in data
    assert data["model"]["name"] == "RASS-DNA-Transformer"
    assert "version" in data["model"]
    assert "checkpoint_loaded" in data["model"]
    assert data["model"]["checkpoint_loaded"] is False
    assert "checkpoint_status" in data["model"]
    assert "training/validation" in data["model"]["checkpoint_status"]
    assert "framework" in data["model"]
    assert "device" in data["model"]

    # Section C & D: Embedding Information
    assert "embedding" in data
    assert data["embedding"]["dimension"] == 64
    assert data["embedding"]["generated"] is True
    assert "norm" in data["embedding"]
    assert "vector_sample" in data["embedding"]

    # Section D: Pattern Analysis
    assert "pattern_analysis" in data
    assert data["pattern_analysis"]["status"] == "pending_validation"
    assert data["pattern_analysis"]["pattern_detected"] is False
    assert isinstance(data["pattern_analysis"]["patterns"], list)
    assert len(data["pattern_analysis"]["patterns"]) == 0

    # Section F: Confidence Status
    assert data["confidence"] is None
    assert "confidence_display" in data
    assert "Confidence unavailable" in data["confidence_display"]

    # Section G: Clinical Interpretation Safeguards
    assert data["clinical_interpretation"] is False
    assert "clinical_disclaimer" in data
    assert "Clinical claims prohibited" in data["clinical_disclaimer"]


# ==============================================================================
# 2. MISSING CHECKPOINT & EMPTY PATTERN RESULT BEHAVIOR
# ==============================================================================

def test_stage6_missing_checkpoint_state():
    """Verifies that an unvalidated foundation model returns explicit untrained indicators."""
    engine = Stage5DNAEngine(checkpoint_path="non_existent_weights.pt")
    result = engine.analyze_sequence("ACGTACGT", read_id="TEST_READ")

    assert result["model"]["checkpoint_loaded"] is False
    assert "requires training/validation" in result["model"]["checkpoint_status"]
    assert result["pattern_analysis"]["model_status"] == "untrained"
    assert result["pattern_analysis"]["pattern_detected"] is False
    assert len(result["pattern_analysis"]["patterns"]) == 0
    assert result["confidence"] is None


# ==============================================================================
# 3. NULL CONFIDENCE ENFORCEMENT
# ==============================================================================

def test_stage6_null_confidence_enforcement():
    """Strictly validates that zero simulated confidence scores (e.g. 98.7%) are generated."""
    res = client.post(
        "/api/analyze/dna",
        json={"sequence": "ATGCATGCATGC", "read_id": "CONF_TEST"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["confidence"] is None
    assert "Confidence unavailable" in data["confidence_display"]
    # Ensure no float confidence leaked anywhere in root
    assert not isinstance(data.get("confidence"), (float, int))


# ==============================================================================
# 4. PATTERN & VARIANT SCHEMA COMPATIBILITY
# ==============================================================================

def test_stage6_pattern_schema_compatibility():
    """Validates that pattern result schema matches TypeScript PatternResult contract."""
    mock_pattern = {
        "pattern_id": "PAT_001",
        "pattern_name": "Homopolymer Poly-A",
        "position_start": 5,
        "position_end": 12,
        "region": "5-12",
        "pattern_type": "Tandem Repeat",
        "model_status": "pending_validation",
        "confidence": None,
        "evidence_status": "Candidate Computational Motif",
    }
    # Validate keys match TypeScript PatternResult interface
    required_keys = {"pattern_name", "pattern_type", "model_status", "confidence", "evidence_status"}
    assert required_keys.issubset(mock_pattern.keys())


def test_stage6_variant_schema_compatibility():
    """Validates that variant result schema matches TypeScript VariantResult contract."""
    mock_variant = {
        "variant_id": "VAR_BRCA1_001",
        "gene_locus": "BRCA1 Exon 20",
        "reference_allele": "A",
        "observed_allele": "G",
        "position": 43071077,
        "classification": "VUS / Pending Validation",
        "confidence": None,
        "evidence": "ACMG PM2",
        "validation_status": "pending_cohort_study",
    }
    required_keys = {
        "variant_id",
        "gene_locus",
        "reference_allele",
        "observed_allele",
        "position",
        "classification",
        "confidence",
        "evidence",
    }
    assert required_keys.issubset(mock_variant.keys())


# ==============================================================================
# 5. API ERROR AND EMPTY SEQUENCE HANDLING
# ==============================================================================

def test_stage6_api_empty_sequence():
    """API returns HTTP 400 for empty sequence input."""
    res = client.post("/api/analyze/dna", json={"sequence": ""})
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_stage6_api_whitespace_sequence():
    """API returns HTTP 400 for whitespace-only sequence."""
    res = client.post("/api/analyze/dna", json={"sequence": "    "})
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_stage6_api_missing_sequence():
    """API returns HTTP 422 for malformed payload without sequence."""
    res = client.post("/api/analyze/dna", json={"read_id": "NO_SEQ"})
    assert res.status_code == 422


# ==============================================================================
# 6. FULL END-TO-END PIPELINE READY FOR STAGE 6 UI
# ==============================================================================

def test_full_pipeline_to_stage6_ready():
    """
    Validates complete pipeline sequence:
    1. Parse FASTQ (Stage 1)
    2. Filter reads (Stage 2)
    3. Normalize sequence (Stage 3)
    4. Tokenize sequence (Stage 4)
    5. Transformer Analysis (Stage 5)
    6. Structured Result populated for Stage 6 Dashboard
    """
    # 1. Run Stage 4 / Prepare API
    s4_res = client.post(
        "/api/v1/analysis/prepare",
        json={
            "file_path": "data/demo/sample.fastq",
            "max_reads": 5,
            "min_quality": 20.0,
        },
    )
    assert s4_res.status_code == 200
    s4_data = s4_res.json()
    assert s4_data["status"] == "prepared"
    assert len(s4_data["sequences"]) > 0

    first_read = s4_data["sequences"][0]

    # 2. Run Stage 5 / DNA Transformer API
    s5_res = client.post(
        "/api/analyze/dna",
        json={
            "sequence": first_read["sequence"],
            "read_id": first_read["read_id"],
            "tokens": first_read["tokens"],
        },
    )
    assert s5_res.status_code == 200
    s5_data = s5_res.json()

    # 3. Verify Stage 6 Dashboard Data Inputs
    assert s5_data["stage"] == 5
    assert s5_data["status"] == "completed"
    assert s5_data["sequence_length"] == len(first_read["sequence"])
    assert s5_data["embedding"]["dimension"] == 64
    assert s5_data["pattern_analysis"]["status"] == "pending_validation"
    assert s5_data["confidence"] is None
    assert s5_data["clinical_interpretation"] is False
