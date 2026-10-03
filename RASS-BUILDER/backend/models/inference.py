from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class ModelInput:
    sequence: str
    tokens: list[int]


@dataclass
class ModelOutput:
    status: str
    model_name: str
    message: str


class DNASequenceModel:
    """
    Stage 4 & Stage 5 DNA Sequence Model Interface.
    Maintains backward compatibility with Stage 4 contract while providing
    full access to the Stage 5 Transformer engine.
    """

    name = "RASS-DNA-Transformer"
    version = "0.5.0-foundation"

    def __init__(self):
        # Lazy import of stage5_engine to prevent circular dependencies
        from models.stage5_engine import stage5_engine
        self._engine = stage5_engine

    def predict(
        self,
        model_input: ModelInput,
    ) -> ModelOutput:
        """Stage 4 preview contract."""
        return ModelOutput(
            status="model_not_loaded",
            model_name=self.name,
            message=(
                "Transformer inference engine "
                "will be connected in the model "
                "integration stage."
            ),
        )

    def analyze_sequence(
        self,
        sequence: str,
        read_id: Optional[str] = "READ_001",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Stage 5 full Transformer sequence analysis."""
        return self._engine.analyze_sequence(
            sequence=sequence,
            read_id=read_id,
            options=options,
        )

    def get_embeddings(self, tokens: List[int]) -> Dict[str, Any]:
        """Stage 5 embedding extraction."""
        return self._engine.get_embeddings(tokens)

    def detect_patterns(self, embeddings: List[float], sequence: str, tokens: List[int]) -> Dict[str, Any]:
        """Stage 5 pattern detection."""
        return self._engine.detect_patterns(embeddings, sequence, tokens)
