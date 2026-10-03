
from bioinformatics.fastq_parser import FastqRead
from bioinformatics.filtering import (
    FilterConfig,
    calculate_n_fraction,
    calculate_mean_quality,
    passes_quality_filter,
    filter_reads,
)
from bioinformatics.normalization import normalize_sequence, reverse_complement
from bioinformatics.tokenizer import tokenize_sequence, tokenize_with_padding, BASE_TO_TOKEN
from models.inference import DNASequenceModel, ModelInput, ModelOutput
from models.job import AnalysisJob
from datetime import datetime


def test_calculate_n_fraction():
    assert calculate_n_fraction("") == 1.0
    assert calculate_n_fraction("ACGT") == 0.0
    assert calculate_n_fraction("ACNT") == 0.25
    assert calculate_n_fraction("NNNN") == 1.0


def test_calculate_mean_quality():
    # 'I' in Phred+33 is ord('I') - 33 = 73 - 33 = 40
    assert calculate_mean_quality("IIII") == 40.0
    assert calculate_mean_quality("") == 0.0


def test_passes_quality_filter():
    config = FilterConfig(min_mean_quality=20.0, min_length=1, max_n_fraction=0.05)
    good_read = FastqRead(read_id="r1", sequence="ACGT", quality_string="IIII")
    assert passes_quality_filter(good_read, config) is True

    # High N fraction
    bad_n = FastqRead(read_id="r2", sequence="ANNT", quality_string="IIII")
    assert passes_quality_filter(bad_n, config) is False

    # Low quality (! is Phred 0)
    low_qual = FastqRead(read_id="r3", sequence="ACGT", quality_string="!!!!")
    assert passes_quality_filter(low_qual, config) is False


def test_filter_reads():
    config = FilterConfig(min_mean_quality=20.0, min_length=1, max_n_fraction=0.05)
    reads = [
        FastqRead(read_id="r1", sequence="ACGT", quality_string="IIII"),
        FastqRead(read_id="r2", sequence="NNNN", quality_string="IIII"),
    ]
    passed, metrics = filter_reads(reads, config)
    assert len(passed) == 1
    assert passed[0].read_id == "r1"
    assert metrics["input_reads"] == 2
    assert metrics["passed_reads"] == 1
    assert metrics["failed_reads"] == 1
    assert metrics["pass_rate"] == 50.0


def test_normalization():
    assert normalize_sequence("acgt") == "ACGT"
    assert normalize_sequence(" acgtX ") == "ACGTN"
    assert reverse_complement("ACGT") == "ACGT"
    assert reverse_complement("AAAA") == "TTTT"
    assert reverse_complement("ACGTN") == "NACGT"


def test_tokenizer():
    assert tokenize_sequence("ACGTN") == [1, 2, 3, 4, 5]
    assert tokenize_sequence("X") == [5]
    padded = tokenize_with_padding("AC", 5)
    assert padded == [1, 2, 0, 0, 0]
    truncated = tokenize_with_padding("ACGTACGT", 4)
    assert truncated == [1, 2, 3, 4]


def test_model_interface():
    model = DNASequenceModel()
    assert model.name == "RASS-DNA-Transformer"
    inp = ModelInput(sequence="ACGT", tokens=[1, 2, 3, 4])
    output = model.predict(inp)
    assert isinstance(output, ModelOutput)
    assert output.status == "model_not_loaded"
    assert output.model_name == "RASS-DNA-Transformer"
    assert "Transformer inference engine" in output.message


def test_analysis_job():
    job = AnalysisJob(
        job_id="job_001",
        status="QUEUED",
        created_at=datetime.now(),
        progress=0,
        message="Job queued",
    )
    assert job.job_id == "job_001"
    assert job.status == "QUEUED"
