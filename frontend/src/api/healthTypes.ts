/** Sidecar slice from ``GET /api/health`` when ``SIDECAR_BASE_URL`` is set. */
export interface SidecarHealthPayload {
  status: string;
  detail?: string;
  /** Present when inspect returned 200 with a parseable ``ollama`` object. */
  ollama?: { state: string; name?: string };
}

/** PONS feature flag from ``GET /api/health``. */
export interface PonsHealthPayload {
  available: boolean;
}

/** Subset of ``GET /api/health`` JSON. */
export interface HealthPayload {
  ok: boolean;
  pons?: PonsHealthPayload;
  sidecar?: SidecarHealthPayload;
}

export type HealthState =
  | { kind: 'loading' }
  | { kind: 'ok'; payload: HealthPayload }
  | { kind: 'error'; message: string };
