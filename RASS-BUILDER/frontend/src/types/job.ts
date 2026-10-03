/**
 * RASS-BUILDER: Stage 7 Job Processing & Queue Data Contracts
 * Defines TypeScript interfaces for asynchronous jobs, execution stages,
 * status polling, and job history.
 */

import type { Stage5AnalysisResult } from "./stage6";

export type JobStatus =
  | "QUEUED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | "RECOVERY_REQUIRED";

export type JobStage =
  | "QUEUED"
  | "DATA_INGESTION"
  | "QUALITY_CONTROL"
  | "TRANSFORMER_ANALYSIS"
  | "PATTERN_ANALYSIS"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | "RECOVERY_REQUIRED";

export interface JobCreateRequest {
  sequence?: string;
  file_path?: string;
  read_id?: string;
  format?: string;
  idempotency_key?: string;
  options?: Record<string, any>;
}

export interface JobCreateResponse {
  job_id: string;
  status: JobStatus;
  message: string;
  is_duplicate?: boolean;
}

export interface JobDetailResponse {
  job_id: string;
  status: JobStatus;
  progress: number;
  current_stage: string;
  message: string;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  input_metadata?: {
    read_id?: string;
    sequence_length?: number;
    format?: string;
    has_file?: boolean;
    pipeline_version?: string;
    [key: string]: any;
  };
  error?: string | null;
  result_reference?: Stage5AnalysisResult | null;
}

export interface JobSummary {
  job_id: string;
  status: JobStatus;
  progress: number;
  current_stage: string;
  created_at: string;
  completed_at?: string | null;
  message: string;
  read_id?: string;
  sequence_length?: number;
}
