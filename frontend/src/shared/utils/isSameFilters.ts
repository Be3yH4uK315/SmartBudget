export function isEqualValue(a: unknown, b: unknown): boolean {
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false
    const setA = new Set(a)
    return b.every((item) => setA.has(item))
  }

  return a === b
}

export function isSameFilters<T extends Record<string, any>>(a: T, b: T): boolean {
  const keysA = Object.keys(a)
  const keysB = Object.keys(b)

  if (keysA.length !== keysB.length) return false

  return keysA.every((key) => isEqualValue(a[key], b[key]))
}
