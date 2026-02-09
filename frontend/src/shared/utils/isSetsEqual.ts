export const isSetsEqual = (a: number[], b: number[]) => {
  if (a.length !== b.length) return false
  const setA = new Set(a)
  const setB = new Set(b)
  for (const v of setA) if (!setB.has(v)) return false
  return true
}
