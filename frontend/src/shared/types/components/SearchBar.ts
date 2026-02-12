export type ApiFunc<T> = (q: string, signal: AbortSignal, searchLimit: number) => Promise<T[]>
