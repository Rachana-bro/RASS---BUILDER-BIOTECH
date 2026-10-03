import { getAuthHeaders } from "./auth";
const API_BASE_URL =
  (import.meta.env?.VITE_API_BASE_URL as string) ||
  (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
    ? window.location.origin
    : "http://localhost:8000");


export async function getHealth() {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/health`
  );

  if (!response.ok) {
    throw new Error("Backend unavailable");
  }

  return response.json();
}


export async function uploadFastq(
  file: File
) {
  const formData = new FormData();
  formData.append("file", file);

  const authHeaders = getAuthHeaders() as Record<string, string>;
  const headers: Record<string, string> = {};
  if (authHeaders["Authorization"]) {
    headers["Authorization"] = authHeaders["Authorization"];
  }

  const response = await fetch(
    `${API_BASE_URL}/api/v1/uploads/fastq`,
    {
      method: "POST",
      headers,
      body: formData,
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "FASTQ upload failed" }));
    throw new Error(
      error.detail || "FASTQ upload failed"
    );
  }

  return response.json();
}


export async function prepareAnalysis(
  filePath: string,
  maxReads = 1000,
  minQuality = 20
) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/analysis/prepare`,
    {
      method: "POST",
      headers: getAuthHeaders(),
      body: JSON.stringify({
        file_path: filePath,
        max_reads: maxReads,
        min_quality: minQuality,
      }),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Analysis preparation failed" }));
    throw new Error(
      error.detail ||
      "Analysis preparation failed"
    );
  }

  return response.json();
}



export type {
  Stage5AnalysisResult,
  PatternResult,
  VariantResult,
  AnalysisSummary,
} from "../types/stage6";
import type { Stage5AnalysisResult } from "../types/stage6";

export type Stage5Result = Stage5AnalysisResult;


export async function analyzeDnaSequence(
  sequence: string,
  readId: string = "READ_001",
  options?: Record<string, any>
): Promise<Stage5Result> {
  const response = await fetch(`${API_BASE_URL}/api/analyze/dna`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({
      sequence,
      read_id: readId,
      options: options || {},
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Network error" }));
    throw new Error(error.detail || "DNA Transformer analysis failed");
  }

  return response.json();
}


// ==============================================================================
// STAGE 7 ASYNCHRONOUS JOBS API
// ==============================================================================

export type {
  JobStatus,
  JobStage,
  JobCreateRequest,
  JobCreateResponse,
  JobDetailResponse,
  JobSummary,
} from "../types/job";
import type {
  JobCreateRequest,
  JobCreateResponse,
  JobDetailResponse,
  JobSummary,
} from "../types/job";

export async function createJob(
  request: JobCreateRequest
): Promise<JobCreateResponse> {
  const response = await fetch(`${API_BASE_URL}/api/jobs`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to queue job" }));
    throw new Error(error.detail || "Job creation failed");
  }

  return response.json();
}

export async function getJobStatus(
  jobId: string
): Promise<JobDetailResponse> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/${encodeURIComponent(jobId)}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Job status check failed" }));
    throw new Error(error.detail || `Job '${jobId}' unavailable`);
  }

  return response.json();
}

export async function getJobResult(
  jobId: string
): Promise<Stage5AnalysisResult> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/${encodeURIComponent(jobId)}/result`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to retrieve job result" }));
    throw new Error(error.detail || "Failed to retrieve job result");
  }

  return response.json();
}

export async function cancelJob(
  jobId: string
): Promise<JobDetailResponse> {
  const response = await fetch(`${API_BASE_URL}/api/jobs/${encodeURIComponent(jobId)}/cancel`, {
    method: "POST",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to cancel job" }));
    throw new Error(error.detail || "Job cancellation failed");
  }

  return response.json();
}

export async function listJobs(
  limit: number = 20
): Promise<JobSummary[]> {
  const response = await fetch(`${API_BASE_URL}/api/jobs?limit=${limit}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to fetch job history" }));
    throw new Error(error.detail || "Job history unavailable");
  }

  return response.json();
}


