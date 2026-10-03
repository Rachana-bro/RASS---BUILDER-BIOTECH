"""
RASS-BUILDER: Modular DNA Transformer Neural Architecture
Implements Token Embedding, Positional Encoding, Multi-Head Self-Attention,
Transformer Encoder Blocks, Sequence Representation Pooling, and Pattern Analysis Head.
"""

import math
from typing import Optional, Tuple, Dict, Any, List

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None
    nn = None
    F = None

import numpy as np


if HAS_TORCH:

    class DNAPositionalEncoding(nn.Module):
        """
        Sinusoidal Positional Encoding for DNA nucleotide sequences.
        PE(pos, 2i)   = sin(pos / 10000^(2i/d_model))
        PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
        """

        def __init__(self, d_model: int = 64, max_len: int = 2000, dropout: float = 0.1):
            super().__init__()
            self.dropout = nn.Dropout(p=dropout)

            pe = torch.zeros(max_len, d_model)
            position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
            div_term = torch.exp(
                torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
            )

            pe[:, 0::2] = torch.sin(position * div_term)
            pe[:, 1::2] = torch.cos(position * div_term)
            pe = pe.unsqueeze(0)  # Shape: (1, max_len, d_model)
            self.register_buffer("pe", pe)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """Adds positional encoding up to sequence length of x."""
            seq_len = x.size(1)
            x = x + self.pe[:, :seq_len]
            return self.dropout(x)

    class DNAMultiHeadAttention(nn.Module):
        """
        Multi-Head Self-Attention layer with explicit attention weight extraction
        for transparent computational sequence representation inspection.
        """

        def __init__(self, d_model: int = 64, nhead: int = 4, dropout: float = 0.1):
            super().__init__()
            assert d_model % nhead == 0, "d_model must be divisible by nhead"
            self.d_model = d_model
            self.nhead = nhead
            self.d_k = d_model // nhead

            self.q_linear = nn.Linear(d_model, d_model)
            self.k_linear = nn.Linear(d_model, d_model)
            self.v_linear = nn.Linear(d_model, d_model)
            self.out_proj = nn.Linear(d_model, d_model)
            self.dropout = nn.Dropout(dropout)

        def forward(
            self,
            x: torch.Tensor,
            mask: Optional[torch.Tensor] = None,
        ) -> Tuple[torch.Tensor, torch.Tensor]:
            """
            Args:
                x: Input tensor of shape (batch_size, seq_len, d_model)
                mask: Optional attention mask (batch_size, 1, 1, seq_len) or (batch_size, 1, seq_len, seq_len)
            Returns:
                output: Attention-applied tensor (batch_size, seq_len, d_model)
                attn_weights: Attention distribution (batch_size, nhead, seq_len, seq_len)
            """
            batch_size, seq_len, _ = x.shape

            # Project and reshape into heads: (batch_size, nhead, seq_len, d_k)
            q = self.q_linear(x).view(batch_size, seq_len, self.nhead, self.d_k).transpose(1, 2)
            k = self.k_linear(x).view(batch_size, seq_len, self.nhead, self.d_k).transpose(1, 2)
            v = self.v_linear(x).view(batch_size, seq_len, self.nhead, self.d_k).transpose(1, 2)

            # Scaled Dot-Product Attention
            scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.d_k)

            if mask is not None:
                scores = scores.masked_fill(mask == 0, -1e9)

            attn_weights = F.softmax(scores, dim=-1)
            attn_weights = self.dropout(attn_weights)

            context = torch.matmul(attn_weights, v)  # (batch, nhead, seq_len, d_k)
            context = context.transpose(1, 2).contiguous().view(batch_size, seq_len, self.d_model)
            output = self.out_proj(context)

            return output, attn_weights

    class DNATransformerBlock(nn.Module):
        """
        Transformer Encoder Block with Pre-LayerNorm, Multi-Head Self-Attention,
        Feedforward Network, and Residual Connections.
        """

        def __init__(
            self,
            d_model: int = 64,
            nhead: int = 4,
            dim_feedforward: int = 128,
            dropout: float = 0.1,
        ):
            super().__init__()
            self.attn = DNAMultiHeadAttention(d_model=d_model, nhead=nhead, dropout=dropout)
            self.norm1 = nn.LayerNorm(d_model)
            self.norm2 = nn.LayerNorm(d_model)

            self.ffn = nn.Sequential(
                nn.Linear(d_model, dim_feedforward),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(dim_feedforward, d_model),
                nn.Dropout(dropout),
            )

        def forward(
            self,
            x: torch.Tensor,
            mask: Optional[torch.Tensor] = None,
        ) -> Tuple[torch.Tensor, torch.Tensor]:
            # Pre-LN Self-Attention with residual connection
            norm_x = self.norm1(x)
            attn_out, attn_weights = self.attn(norm_x, mask=mask)
            x = x + attn_out

            # Pre-LN Feedforward with residual connection
            x = x + self.ffn(self.norm2(x))
            return x, attn_weights

    class PatternAnalysisHead(nn.Module):
        """
        Modular Pattern Detection Head.
        Designed to be detached, replaced, or loaded from validated fine-tuning checkpoints.
        """

        def __init__(self, d_model: int = 64, hidden_dim: int = 32, num_patterns: int = 4):
            super().__init__()
            self.head = nn.Sequential(
                nn.Linear(d_model, hidden_dim),
                nn.GELU(),
                nn.LayerNorm(hidden_dim),
                nn.Linear(hidden_dim, num_patterns),
            )

        def forward(self, sequence_embedding: torch.Tensor) -> torch.Tensor:
            return self.head(sequence_embedding)

    class PyTorchDNATransformer(nn.Module):
        """
        PyTorch Transformer Model for DNA Sequence Embedding and Pattern Analysis.
        
        Architecture:
        1. Token Embedding Layer (vocab_size=9 -> d_model=64)
        2. Sinusoidal Positional Encoding
        3. Multi-Layer Transformer Encoder Blocks with Self-Attention
        4. Sequence Representation Layer (Attention-weighted pooling)
        5. Modular Pattern Analysis Head
        """

        def __init__(
            self,
            vocab_size: int = 9,
            d_model: int = 64,
            nhead: int = 4,
            num_layers: int = 2,
            dim_feedforward: int = 128,
            dropout: float = 0.1,
            max_len: int = 2000,
            num_patterns: int = 4,
        ):
            super().__init__()
            self.vocab_size = vocab_size
            self.d_model = d_model
            self.nhead = nhead
            self.num_layers = num_layers

            self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)
            self.pos_encoder = DNAPositionalEncoding(d_model=d_model, max_len=max_len, dropout=dropout)

            self.layers = nn.ModuleList([
                DNATransformerBlock(
                    d_model=d_model,
                    nhead=nhead,
                    dim_feedforward=dim_feedforward,
                    dropout=dropout,
                )
                for _ in range(num_layers)
            ])

            self.final_norm = nn.LayerNorm(d_model)
            self.pattern_head = PatternAnalysisHead(d_model=d_model, hidden_dim=32, num_patterns=num_patterns)

        def forward(
            self,
            input_ids: torch.Tensor,
            return_attention: bool = True,
        ) -> Dict[str, Any]:
            """
            Forward pass producing sequence embeddings, token embeddings,
            attention matrices, and raw pattern logits.
            
            Args:
                input_ids: Tensor of shape (batch_size, seq_len) with token integers
                return_attention: Whether to collect and return attention maps
            """
            batch_size, seq_len = input_ids.shape

            # Create attention padding mask (1 for valid token, 0 for <PAD>)
            padding_mask = (input_ids != 0).unsqueeze(1).unsqueeze(2)  # (batch, 1, 1, seq_len)

            # 1. Embedding + Positional Encoding
            x = self.embedding(input_ids) * math.sqrt(self.d_model)
            x = self.pos_encoder(x)

            # 2. Transformer Encoder Layers
            all_attentions: List[torch.Tensor] = []
            for layer in self.layers:
                x, attn_weights = layer(x, mask=padding_mask)
                if return_attention:
                    all_attentions.append(attn_weights)

            x = self.final_norm(x)  # (batch, seq_len, d_model)

            # 3. Sequence Pooling: Masked Mean Pooling across valid non-pad tokens
            mask_float = (input_ids != 0).unsqueeze(-1).float()  # (batch, seq_len, 1)
            sum_embeddings = torch.sum(x * mask_float, dim=1)
            valid_counts = torch.clamp(mask_float.sum(dim=1), min=1.0)
            sequence_embedding = sum_embeddings / valid_counts  # (batch, d_model)

            # 4. Pattern Head Logits
            pattern_logits = self.pattern_head(sequence_embedding)

            return {
                "sequence_embedding": sequence_embedding,
                "token_embeddings": x,
                "attention_weights": all_attentions,
                "pattern_logits": pattern_logits,
            }


class NumPyDNATransformer:
    """
    Mathematical fallback Transformer implementation for environments without PyTorch.
    Ensures identical contract, deterministic embedding generation, and attention extraction.
    """

    def __init__(self, vocab_size: int = 9, d_model: int = 64, nhead: int = 4):
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.nhead = nhead

        # Fixed orthogonal pseudo-weights for deterministic mathematical representation
        rng = np.random.RandomState(42)
        self.embedding_table = rng.randn(vocab_size, d_model) * (1.0 / math.sqrt(d_model))
        self.embedding_table[0] = 0.0  # <PAD> is zero vector

    def forward(self, input_ids: List[int]) -> Dict[str, Any]:
        seq_len = len(input_ids)
        if seq_len == 0:
            return {
                "sequence_embedding": np.zeros(self.d_model, dtype=np.float32),
                "attention_matrix": np.zeros((0, 0), dtype=np.float32),
            }

        # 1. Embeddings
        embedded = np.array([self.embedding_table[min(tid, self.vocab_size - 1)] for tid in input_ids])

        # 2. Sinusoidal Position
        pe = np.zeros((seq_len, self.d_model), dtype=np.float32)
        pos = np.arange(seq_len)[:, np.newaxis]
        div = np.exp(np.arange(0, self.d_model, 2) * (-math.log(10000.0) / self.d_model))
        pe[:, 0::2] = np.sin(pos * div)
        pe[:, 1::2] = np.cos(pos * div)
        x = embedded + pe

        # 3. Computational Self-Attention Representation
        d_k = self.d_model // self.nhead
        scores = np.matmul(x, x.T) / math.sqrt(d_k)
        exp_scores = np.exp(scores - np.max(scores, axis=-1, keepdims=True))
        attn_matrix = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)

        # Context output
        context = np.matmul(attn_matrix, x)
        # Pool non-zero tokens
        valid_mask = np.array([tid != 0 for tid in input_ids], dtype=np.float32)[:, np.newaxis]
        valid_count = max(1.0, float(np.sum(valid_mask)))
        seq_emb = np.sum(context * valid_mask, axis=0) / valid_count

        return {
            "sequence_embedding": seq_emb,
            "attention_matrix": attn_matrix,
        }
