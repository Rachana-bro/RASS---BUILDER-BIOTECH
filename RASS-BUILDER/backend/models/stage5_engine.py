"""
RASS-BUILDER: Stage 5 DNA Transformer Analysis Engine
Integrates DNA Tokenizer, PyTorch Multi-Head Self-Attention Transformer,
Numerical Embedding Extraction, Computational Attention Mapping, and
Pattern Detection with strict scientific safeguards (no simulated clinical claims).
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import numpy as np

from bioinformatics.tokenizer import DNATokenizer, STAGE5_VOCAB
from models.transformer import HAS_TORCH, PyTorchDNATransformer, NumPyDNATransformer

if HAS_TORCH:
    import torch


CHECKPOINT_MISSING_MESSAGE = (
    "Model checkpoint not available — analysis model requires training/validation."
)
CONFIDENCE_UNAVAILABLE_MESSAGE = (
    "Confidence unavailable — validated model required."
)
CLINICAL_DISCLAIMER_MESSAGE = (
    "Stage 5 technical foundation ready for validated model checkpoint. "
    "Clinical claims prohibited without certified training and regulatory validation."
)


class Stage5DNAEngine:
    """
    Modular execution engine for Stage 5 DNA Sequence Transformer Processing.
    """

    name = "RASS-DNA-Transformer"
    version = "0.5.0-foundation"

    def __init__(
        self,
        checkpoint_path: Optional[Union[str, Path]] = None,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
    ):
        self.tokenizer = DNATokenizer()
        self.d_model = d_model
        self.nhead = nhead
        self.num_layers = num_layers

        self.has_torch = HAS_TORCH
        self.device = "cpu"
        self.checkpoint_loaded = False
        self.checkpoint_status = CHECKPOINT_MISSING_MESSAGE
        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else None

        # Instantiate Architecture
        if self.has_torch:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = PyTorchDNATransformer(
                vocab_size=self.tokenizer.vocab_size,
                d_model=self.d_model,
                nhead=self.nhead,
                num_layers=self.num_layers,
                dropout=0.0,
            ).to(self.device)
            self.model.eval()
        else:
            self.model = NumPyDNATransformer(
                vocab_size=self.tokenizer.vocab_size,
                d_model=self.d_model,
                nhead=self.nhead,
            )

        # Attempt to load checkpoint if one was provided or exists at standard location
        self.load_model(self.checkpoint_path)

    def load_model(self, checkpoint_path: Optional[Union[str, Path]] = None) -> bool:
        """
        Attempts to load model weights from a valid checkpoint file.
        If no checkpoint exists or loading fails, explicitly marks model as untrained.
        Never substitutes random weights for real predictions.
        """
        target_path = checkpoint_path or self.checkpoint_path

        import os
        env_model_path = os.environ.get("RASS_MODEL_PATH")
        if target_path is None and env_model_path:
            target_path = Path(env_model_path)

        if target_path is None:
            default_candidate = Path(__file__).resolve().parent / "checkpoints" / "stage5_transformer.pt"
            if default_candidate.exists():
                target_path = default_candidate

        if target_path is None or not Path(target_path).exists():
            self.checkpoint_loaded = False
            if target_path and env_model_path and Path(target_path) == Path(env_model_path):
                self.checkpoint_status = f"Configured model checkpoint not found at: {target_path}"
            else:
                self.checkpoint_status = CHECKPOINT_MISSING_MESSAGE
            return False

        try:
            if self.has_torch:
                state_dict = torch.load(target_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
                self.checkpoint_loaded = True
                self.checkpoint_status = f"Loaded checkpoint from {target_path}"
                return True
            else:
                self.checkpoint_loaded = False
                self.checkpoint_status = "PyTorch required for checkpoint deserialization."
                return False
        except Exception as error:
            self.checkpoint_loaded = False
            self.checkpoint_status = f"Failed to load checkpoint: {error}"
            return False

    def get_embeddings(
        self,
        token_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Computes the sequence embedding vector via Transformer forward pass.
        Returns numerical representation and metadata.
        """
        if not token_ids:
            return {
                "dimension": self.d_model,
                "generated": False,
                "vector": [],
                "norm": 0.0,
                "sample": [],
            }

        if self.has_torch:
            with torch.no_grad():
                tensor_in = torch.tensor(
                    [token_ids], dtype=torch.long, device=self.device
                )
                outputs = self.model(tensor_in, return_attention=False)
                embedding_tensor = outputs["sequence_embedding"].squeeze(0).cpu()
                emb_array = embedding_tensor.numpy()
        else:
            outputs = self.model.forward(token_ids)
            emb_array = outputs["sequence_embedding"]

        norm_val = float(np.linalg.norm(emb_array))
        sample_vals = [round(float(v), 5) for v in emb_array[:8].tolist()]

        return {
            "dimension": int(self.d_model),
            "generated": True,
            "norm": round(norm_val, 4),
            "vector_sample": sample_vals,
            "vector": [round(float(v), 5) for v in emb_array.tolist()],
            "model_name": self.name,
            "model_version": self.version,
            "checkpoint_loaded": self.checkpoint_loaded,
            "checkpoint_status": self.checkpoint_status,
        }

    def extract_attention(
        self,
        token_ids: List[int],
        tokens: List[str],
    ) -> Dict[str, Any]:
        """
        Extracts internal Transformer multi-head self-attention layer representation.
        Strictly labeled as Computational Representation, not biological significance.
        """
        seq_len = len(token_ids)
        if seq_len == 0:
            return {
                "available": False,
                "type": "Model Attention / Computational Representation",
                "note": "No tokens available for attention mapping.",
                "token_labels": [],
                "token_weights": [],
                "matrix_sample": [],
            }

        if self.has_torch:
            with torch.no_grad():
                tensor_in = torch.tensor(
                    [token_ids], dtype=torch.long, device=self.device
                )
                outputs = self.model(tensor_in, return_attention=True)
                attentions = outputs["attention_weights"]
                if attentions:
                    # Last layer attention: shape (1, nhead, seq_len, seq_len)
                    last_layer = attentions[-1].squeeze(0).cpu().numpy()
                    # Average over attention heads: shape (seq_len, seq_len)
                    attn_matrix = np.mean(last_layer, axis=0)
                else:
                    attn_matrix = np.eye(seq_len, dtype=np.float32)
        else:
            outputs = self.model.forward(token_ids)
            attn_matrix = outputs["attention_matrix"]

        # Token-level incoming attention weight profile (column mean: how much attention each position receives)
        token_weights = np.mean(attn_matrix, axis=0)
        token_weights_list = [round(float(w), 4) for w in token_weights.tolist()]

        # Preview matrix (capped at 32x32 for manageable payload transfer)
        max_preview = min(32, seq_len)
        matrix_preview = [
            [round(float(attn_matrix[i, j]), 4) for j in range(max_preview)]
            for i in range(max_preview)
        ]

        return {
            "available": True,
            "type": "Model Attention / Computational Representation",
            "note": (
                "Attention values reflect internal Transformer layer weight distribution, "
                "not validated biological importance."
            ),
            "token_labels": tokens[:max_preview],
            "token_weights": token_weights_list[:max_preview],
            "matrix_sample": matrix_preview,
            "preview_size": max_preview,
            "total_tokens": seq_len,
        }

    def detect_patterns(
        self,
        embeddings: List[float],
        sequence: str,
        token_ids: List[int],
    ) -> Dict[str, Any]:
        """
        Modular pattern detection interface.
        If untrained or no checkpoint: returns pending_validation and null confidence.
        If a validated checkpoint is loaded: queries model classification pipeline.
        """
        if not self.checkpoint_loaded:
            return {
                "pattern_detected": False,
                "patterns": [],
                "confidence": None,
                "model_status": "untrained",
                "status": "pending_validation",
                "message": CHECKPOINT_MISSING_MESSAGE,
                "confidence_message": CONFIDENCE_UNAVAILABLE_MESSAGE,
            }

        # Future pipeline for validated checkpoint:
        # In a validated deployment, this uses self.model.pattern_head with validated weights.
        return {
            "pattern_detected": False,
            "patterns": [],
            "confidence": None,
            "model_status": "trained_uncalibrated",
            "status": "pending_validation",
            "message": "Model checkpoint active — awaiting clinical cohort calibration.",
        }

    def analyze_sequence(
        self,
        sequence: str,
        read_id: Optional[str] = "READ_001",
        max_length: int = 5000,
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Complete Stage 5 Analysis Pipeline:
        Processed DNA Sequence
                ↓
        DNA Tokenization
                ↓
        Token IDs
                ↓
        DNA Transformer
                ↓
        Sequence Embeddings
                ↓
        Attention / Sequence Representation
                ↓
        Pattern Detection
                ↓
        Confidence / Model Metadata
                ↓
        Structured Analysis Result
        """
        is_valid, err_msg = self.tokenizer.validate_sequence(sequence, max_length=max_length)
        if not is_valid:
            raise ValueError(err_msg)

        # 1. Tokenization
        token_details = self.tokenizer.get_token_details(sequence, add_special_tokens=True)
        token_ids = token_details["token_ids"]
        tokens = token_details["tokens"]

        # 2. Transformer Embeddings
        embedding_data = self.get_embeddings(token_ids)

        # 3. Attention Mapping
        attention_data = self.extract_attention(token_ids, tokens)

        # 4. Pattern Detection
        pattern_data = self.detect_patterns(
            embeddings=embedding_data["vector"],
            sequence=token_details["normalized_sequence"],
            token_ids=token_ids,
        )

        # 5. Confidence
        confidence_value = (
            None if not self.checkpoint_loaded else pattern_data.get("confidence")
        )

        framework_str = f"PyTorch v{torch.__version__}" if self.has_torch else "NumPy Fallback"

        # 6. Structured Stage 5 Result Object (Requirement 8)
        return {
            "stage": 5,
            "status": "completed",
            "sequence_length": len(token_details["normalized_sequence"]),
            "token_count": len(token_ids),
            "read_id": read_id or "READ_001",
            "model": {
                "name": self.name,
                "version": self.version,
                "checkpoint_loaded": self.checkpoint_loaded,
                "checkpoint_status": self.checkpoint_status,
                "framework": framework_str,
                "device": self.device,
            },
            "embedding": {
                "dimension": embedding_data["dimension"],
                "generated": embedding_data["generated"],
                "norm": embedding_data["norm"],
                "vector_sample": embedding_data["vector_sample"],
                "sequence_length": len(token_details["normalized_sequence"]),
                "token_count": len(token_ids),
                "model_name": self.name,
                "model_version": self.version,
                "checkpoint_status": self.checkpoint_status,
            },
            "attention": attention_data,
            "pattern_analysis": {
                "status": pattern_data["status"],
                "patterns": pattern_data["patterns"],
                "pattern_detected": pattern_data["pattern_detected"],
                "model_status": pattern_data["model_status"],
            },
            "confidence": confidence_value,
            "confidence_display": (
                CONFIDENCE_UNAVAILABLE_MESSAGE if confidence_value is None else str(confidence_value)
            ),
            "clinical_interpretation": False,
            "clinical_disclaimer": CLINICAL_DISCLAIMER_MESSAGE,
            "tokenizer": {
                "tokens": tokens,
                "token_ids": token_ids,
                "special_tokens_applied": True,
                "invalid_bases": token_details["invalid_bases"],
                "canonical_base_ratio": token_details["canonical_base_ratio"],
            },
        }


# Singleton engine instance for application reuse
stage5_engine = Stage5DNAEngine()
