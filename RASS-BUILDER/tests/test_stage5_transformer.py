"""
Unit & Integration Tests for Stage 5 — DNA Transformer / AI Analysis Layer.

Covers:
- DNA Tokenizer (normalization, lowercase, invalid bases, special tokens <PAD>, <UNK>, <START>, <END>)
- Token ID generation and bidirectional mapping
- Modular PyTorch Transformer forward pass
- Sequence embedding generation and dimensionality
- Attention computational representation extraction
- Checkpoint loading and missing checkpoint behavior
- Model interface contract (load_model, get_embeddings, detect_patterns, analyze_sequence)
- Confidence null handling (never fabricated)
- Structured Stage 5 output format
- Error handling (empty sequence, invalid bases, long sequences)
- API endpoint integration (/api/analyze/dna and /api/v1/analysis/dna)
"""

import pytest
from fastapi.testclient import TestClient

from bioinformatics.tokenizer import (
    DNATokenizer,
    STAGE5_VOCAB,
    STAGE5_ID_TO_TOKEN,
    tokenize_sequence,
    tokenize_with_padding,
)
from models.transformer import (
    HAS_TORCH,
    PyTorchDNATransformer,
    NumPyDNATransformer,
)
from models.stage5_engine import (
    Stage5DNAEngine,
    stage5_engine,
    CHECKPOINT_MISSING_MESSAGE,
    CONFIDENCE_UNAVAILABLE_MESSAGE,
    CLINICAL_DISCLAIMER_MESSAGE,
)
from models.inference import DNASequenceModel, ModelInput, ModelOutput
from main import app

client = TestClient(app)


# ==============================================================================
# 1. DNA TOKENIZER TESTS
# ==============================================================================

def test_tokenizer_normalization():
    tokenizer = DNATokenizer()
    assert tokenizer.normalize("  acgt  ") == "ACGT"
    assert tokenizer.normalize("aAcCgGtT") == "AACCGGTT"
    assert tokenizer.normalize("") == ""


def test_tokenizer_special_tokens():
    tokenizer = DNATokenizer()
    assert tokenizer.pad_token == "<PAD>"
    assert tokenizer.unk_token == "<UNK>"
    assert tokenizer.start_token == "<START>"
    assert tokenizer.end_token == "<END>"

    assert tokenizer.pad_id == 0
    assert tokenizer.unk_id == 1
    assert tokenizer.start_id == 2
    assert tokenizer.end_id == 3


def test_tokenizer_invalid_bases_detection():
    tokenizer = DNATokenizer()
    invalid = tokenizer.detect_invalid_bases("ACGT1X2Y")
    assert len(invalid) == 4
    chars = [item["char"] for item in invalid]
    assert chars == ["1", "X", "2", "Y"]
    assert invalid[0]["position"] == 4


def test_tokenizer_token_generation():
    tokenizer = DNATokenizer()
    tokens = tokenizer.tokenize("ACGT", add_special_tokens=True)
    assert tokens == ["<START>", "A", "C", "G", "T", "<END>"]

    # Replaces invalid characters with <UNK> without crashing
    tokens_unk = tokenizer.tokenize("AXT", add_special_tokens=True)
    assert tokens_unk == ["<START>", "A", "<UNK>", "T", "<END>"]


def test_tokenizer_encode_decode():
    tokenizer = DNATokenizer()
    token_ids = tokenizer.encode("ACGT", add_special_tokens=True)
    assert token_ids == [2, 4, 5, 6, 7, 3]

    # Decode preserving special tokens
    decoded_full = tokenizer.decode(token_ids, skip_special_tokens=False)
    assert decoded_full == "<START>ACGT<END>"

    # Decode skipping special tokens
    decoded_clean = tokenizer.decode(token_ids, skip_special_tokens=True)
    assert decoded_clean == "ACGT"


def test_tokenizer_padding_and_truncation():
    tokenizer = DNATokenizer()
    # Padding
    padded = tokenizer.encode("AC", add_special_tokens=False, max_length=5, padding=True)
    assert padded == [4, 5, 0, 0, 0]

    # Truncation
    truncated = tokenizer.encode("ACGTACGT", add_special_tokens=False, max_length=4, truncation=True)
    assert len(truncated) == 4
    assert truncated == [4, 5, 6, 7]


def test_tokenizer_bidirectional_mapping():
    tokenizer = DNATokenizer()
    mapping = tokenizer.get_vocab_mapping()
    assert mapping["token_to_id"]["<START>"] == 2
    assert mapping["id_to_token"][2] == "<START>"
    assert mapping["token_to_id"]["A"] == 4
    assert mapping["id_to_token"][4] == "A"


# ==============================================================================
# 2. TRANSFORMER ARCHITECTURE & EMBEDDINGS TESTS
# ==============================================================================

def test_transformer_forward_pass():
    if HAS_TORCH:
        import torch
        model = PyTorchDNATransformer(vocab_size=9, d_model=64, nhead=4, num_layers=2)
        model.eval()
        tokens = torch.tensor([[2, 4, 5, 6, 7, 3]], dtype=torch.long)
        outputs = model(tokens, return_attention=True)

        assert "sequence_embedding" in outputs
        assert outputs["sequence_embedding"].shape == (1, 64)
        assert "token_embeddings" in outputs
        assert outputs["token_embeddings"].shape == (1, 6, 64)
        assert "attention_weights" in outputs
        assert len(outputs["attention_weights"]) == 2  # 2 layers
        # Check last layer shape: (batch, nhead, seq_len, seq_len)
        assert outputs["attention_weights"][-1].shape == (1, 4, 6, 6)
        assert "pattern_logits" in outputs
        assert outputs["pattern_logits"].shape == (1, 4)
    else:
        model = NumPyDNATransformer(vocab_size=9, d_model=64, nhead=4)
        outputs = model.forward([2, 4, 5, 6, 7, 3])
        assert "sequence_embedding" in outputs
        assert len(outputs["sequence_embedding"]) == 64
        assert outputs["attention_matrix"].shape == (6, 6)


def test_engine_embedding_generation():
    engine = Stage5DNAEngine()
    tokens = [2, 4, 5, 6, 7, 3]  # <START> ACGT <END>
    emb_data = engine.get_embeddings(tokens)

    assert emb_data["dimension"] == 64
    assert emb_data["generated"] is True
    assert len(emb_data["vector"]) == 64
    assert len(emb_data["vector_sample"]) == 8
    assert isinstance(emb_data["norm"], float)
    assert emb_data["norm"] > 0.0
    assert emb_data["model_name"] == "RASS-DNA-Transformer"
    assert emb_data["checkpoint_loaded"] is False


def test_engine_attention_extraction():
    engine = Stage5DNAEngine()
    tokens = ["<START>", "A", "C", "G", "T", "<END>"]
    token_ids = [2, 4, 5, 6, 7, 3]
    attn_data = engine.extract_attention(token_ids, tokens)

    assert attn_data["available"] is True
    assert attn_data["type"] == "Model Attention / Computational Representation"
    assert "biological importance" in attn_data["note"]
    assert len(attn_data["token_labels"]) == 6
    assert len(attn_data["token_weights"]) == 6
    assert len(attn_data["matrix_sample"]) == 6
    assert len(attn_data["matrix_sample"][0]) == 6


# ==============================================================================
# 3. MISSING CHECKPOINT & CONFIDENCE SAFEGUARDS
# ==============================================================================

def test_missing_checkpoint_behavior():
    engine = Stage5DNAEngine(checkpoint_path="non_existent_model.pt")
    assert engine.checkpoint_loaded is False
    assert engine.checkpoint_status == CHECKPOINT_MISSING_MESSAGE

    patterns = engine.detect_patterns([0.1] * 64, "ACGT", [2, 4, 5, 6, 7, 3])
    assert patterns["pattern_detected"] is False
    assert patterns["patterns"] == []
    assert patterns["confidence"] is None
    assert patterns["model_status"] == "untrained"
    assert patterns["status"] == "pending_validation"
    assert patterns["confidence_message"] == CONFIDENCE_UNAVAILABLE_MESSAGE


def test_analyze_sequence_structure():
    engine = Stage5DNAEngine()
    result = engine.analyze_sequence("ACGTACGTACGT", read_id="TEST_001")

    # Match Requirement 8 structured schema exactly
    assert result["stage"] == 5
    assert result["status"] == "completed"
    assert result["sequence_length"] == 12
    assert result["token_count"] == 14  # 12 bases + <START> + <END>
    assert result["read_id"] == "TEST_001"

    # Model metadata
    assert result["model"]["name"] == "RASS-DNA-Transformer"
    assert result["model"]["checkpoint_loaded"] is False
    assert result["model"]["checkpoint_status"] == CHECKPOINT_MISSING_MESSAGE

    # Embedding metadata
    assert result["embedding"]["dimension"] == 64
    assert result["embedding"]["generated"] is True
    assert len(result["embedding"]["vector_sample"]) == 8

    # Attention metadata
    assert result["attention"]["type"] == "Model Attention / Computational Representation"

    # Pattern analysis metadata
    assert result["pattern_analysis"]["status"] == "pending_validation"
    assert result["pattern_analysis"]["patterns"] == []
    assert result["pattern_analysis"]["pattern_detected"] is False
    assert result["pattern_analysis"]["model_status"] == "untrained"

    # Confidence must be null
    assert result["confidence"] is None
    assert result["confidence_display"] == CONFIDENCE_UNAVAILABLE_MESSAGE
    assert result["clinical_interpretation"] is False
    assert "Clinical claims prohibited" in result["clinical_disclaimer"]


# ==============================================================================
# 4. ERROR HANDLING TESTS
# ==============================================================================

def test_error_empty_sequence():
    engine = Stage5DNAEngine()
    with pytest.raises(ValueError) as excinfo:
        engine.analyze_sequence("")
    assert "DNA sequence cannot be empty" in str(excinfo.value)

    with pytest.raises(ValueError):
        engine.analyze_sequence("   ")


def test_error_extremely_long_sequence():
    engine = Stage5DNAEngine()
    long_seq = "A" * 6000
    with pytest.raises(ValueError) as excinfo:
        engine.analyze_sequence(long_seq, max_length=5000)
    assert "exceeds maximum supported limit" in str(excinfo.value)


# ==============================================================================
# 5. API ENDPOINT TESTS (POST /api/analyze/dna & /api/v1/analysis/dna)
# ==============================================================================

def test_api_analyze_dna_success():
    res = client.post(
        "/api/analyze/dna",
        json={
            "sequence": "ACGTACGTACGTACGT",
            "read_id": "READ_API_001",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["stage"] == 5
    assert data["status"] == "completed"
    assert data["sequence_length"] == 16
    assert data["token_count"] == 18
    assert data["model"]["checkpoint_loaded"] is False
    assert data["embedding"]["dimension"] == 64
    assert data["embedding"]["generated"] is True
    assert data["pattern_analysis"]["status"] == "pending_validation"
    assert data["confidence"] is None
    assert data["clinical_interpretation"] is False
    assert data["attention"]["type"] == "Model Attention / Computational Representation"


def test_api_analyze_dna_v1_alias():
    res = client.post(
        "/api/v1/analysis/dna",
        json={
            "sequence": "TGCATGCATGCA",
            "read_id": "READ_API_002",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["stage"] == 5
    assert data["sequence_length"] == 12
    assert data["confidence"] is None


def test_api_analyze_dna_empty_sequence():
    res = client.post(
        "/api/analyze/dna",
        json={
            "sequence": "",
            "read_id": "READ_EMPTY",
        },
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


def test_api_analyze_dna_malformed_json():
    # Missing required 'sequence' field
    res = client.post(
        "/api/analyze/dna",
        json={"read_id": "READ_NO_SEQ"},
    )
    assert res.status_code == 422


def test_api_analyze_dna_extremely_long():
    res = client.post(
        "/api/analyze/dna",
        json={
            "sequence": "C" * 12000,
            "read_id": "READ_TOO_LONG",
        },
    )
    assert res.status_code == 400
    assert "exceeds" in res.json()["detail"].lower()


# ==============================================================================
# 6. MODEL INTERFACE & COMPATIBILITY
# ==============================================================================

def test_model_interface_stage4_stage5():
    model = DNASequenceModel()
    assert model.name == "RASS-DNA-Transformer"

    # Stage 4 preview contract remains intact
    s4_input = ModelInput(sequence="ACGT", tokens=[1, 2, 3, 4])
    s4_output = model.predict(s4_input)
    assert isinstance(s4_output, ModelOutput)
    assert s4_output.status == "model_not_loaded"

    # Stage 5 analysis method callable on the model
    s5_res = model.analyze_sequence("ACGTACGT")
    assert s5_res["stage"] == 5
    assert s5_res["status"] == "completed"
    assert s5_res["confidence"] is None


# ==============================================================================
# 7. END-TO-END STAGE 4 -> STAGE 5 PIPELINE INTEGRATION
# ==============================================================================

def test_stage4_to_stage5_pipeline_integration():
    """
    Validates seamless pipeline progression:
    FASTQ -> Stage 4 Filtering/Normalization/Tokenization -> Stage 5 DNA Transformer
    """
    # 1. Run Stage 4 Preparation
    s4_res = client.post(
        "/api/v1/analysis/prepare",
        json={
            "file_path": "data/demo/sample.fastq",
            "max_reads": 10,
            "min_quality": 20.0,
        },
    )
    assert s4_res.status_code == 200
    s4_data = s4_res.json()
    assert s4_data["status"] == "prepared"
    assert len(s4_data["sequences"]) > 0

    first_seq_record = s4_data["sequences"][0]
    raw_seq = first_seq_record["sequence"]
    read_id = first_seq_record["read_id"]
    assert len(raw_seq) > 0

    # 2. Feed Stage 4 output sequence directly into Stage 5 Transformer endpoint
    s5_res = client.post(
        "/api/analyze/dna",
        json={
            "sequence": raw_seq,
            "read_id": read_id,
            "tokens": first_seq_record["tokens"],
        },
    )
    assert s5_res.status_code == 200
    s5_data = s5_res.json()

    # 3. Verify complete Stage 5 Output Contract
    assert s5_data["stage"] == 5
    assert s5_data["status"] == "completed"
    assert s5_data["read_id"] == read_id
    assert s5_data["sequence_length"] == len(raw_seq)
    assert s5_data["token_count"] == len(raw_seq) + 2  # <START> + seq + <END>

    # Model metadata
    assert s5_data["model"]["name"] == "RASS-DNA-Transformer"
    assert s5_data["model"]["checkpoint_loaded"] is False
    assert "training/validation" in s5_data["model"]["checkpoint_status"]

    # Embedding metadata
    assert s5_data["embedding"]["dimension"] == 64
    assert s5_data["embedding"]["generated"] is True
    assert len(s5_data["embedding"]["vector_sample"]) == 8

    # Attention metadata
    assert s5_data["attention"]["available"] is True
    assert s5_data["attention"]["type"] == "Model Attention / Computational Representation"

    # Pattern and confidence safeguards
    assert s5_data["pattern_analysis"]["status"] == "pending_validation"
    assert s5_data["pattern_analysis"]["pattern_detected"] is False
    assert s5_data["confidence"] is None
    assert s5_data["clinical_interpretation"] is False

