export type TestahSourceProvenance = {
  sourceCommit: string | null
  sourceFingerprint: string
}

export function sourceProvenance(root?: string): TestahSourceProvenance
export function sourceFingerprint(root?: string): string
