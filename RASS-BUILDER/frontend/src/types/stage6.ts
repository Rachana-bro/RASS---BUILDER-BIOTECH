/**
 * RASS-BUILDER Stage 6: Variant & Pattern Results UI Data Contracts
 * Defines strict TypeScript interfaces for consuming Stage 5 structured output
 * and rendering clinical-grade variant & pattern analysis dashboards.
 */

export interface PatternResult {
  pattern_id?: string;
  pattern_name: string;
  position_start?: number;
  position_end?: number;
  region?: string;
  pattern_type: string;
  model_status: "validated" | "pending_validation" | "untrained" | string;
  confidence: number | null;
  evidence_status: string;
}

export interface VariantResult {
  variant_id: string;
  gene_locus: string;
  reference_allele: string;
  observed_allele: string;
  position: number | string;
  classification: string;
  confidence: number | null;
  evidence: string;
  validation_status: "validated" | "research_use_only" | "pending_cohort_study" | string;
}

export interface AnalysisSummary {
  sequence_length: number;
  token_count: number;
  input_format: string;
  read_id: string;
  processing_status: "completed" | "pending" | "failed" | "validation_required" | string;
  canonical_ratio?: number;
}

export interface Stage5AnalysisResult {
  stage: number;
  status: string;
  sequence_length: number;
  token_count: number;
  read_id: string;
  model: {
    name: string;
    version: string;
    checkpoint_loaded: boolean;
    checkpoint_status: string;
    framework: string;
    device: string;
  };
  embedding: {
    dimension: number;
    generated: boolean;
    norm: number;
    vector_sample: number[];
    sequence_length?: number;
    token_count?: number;
    model_name?: string;
    model_version?: string;
    checkpoint_status?: string;
  };
  attention: {
    available: boolean;
    type: string;
    note: string;
    token_labels: string[];
    token_weights: number[];
    matrix_sample: number[][];
    preview_size: number;
    total_tokens: number;
  };
  pattern_analysis: {
    status: string;
    patterns: PatternResult[];
    pattern_detected: boolean;
    model_status: string;
  };
  confidence: number | null;
  confidence_display: string;
  clinical_interpretation: boolean;
  clinical_disclaimer: string;
  tokenizer: {
    tokens: string[];
    token_ids: number[];
    special_tokens_applied: boolean;
    invalid_bases: Array<{ position: number; char: string; canonical: boolean }>;
    canonical_base_ratio: number;
  };
  // Architectural hook for future validated variant streams
  variants?: VariantResult[];
}
