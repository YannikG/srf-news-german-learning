/** Subset of ``GET /api/health`` JSON. */
export interface HealthPayload {
  ok: boolean;
  sidecar?: { status: string; detail?: string };
}

export type HealthState =
  | { kind: 'loading' }
  | { kind: 'ok'; payload: HealthPayload }
  | { kind: 'error'; message: string };
