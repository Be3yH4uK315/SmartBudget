type Debounced<T extends (...args: any[]) => void> = T & {
  cancel: () => void
}

export function debounce<T extends (...args: any[]) => void>(fn: T, delay: number): Debounced<T> {
  let timeout: ReturnType<typeof setTimeout> | null = null

  const debounced = ((...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout)
    }

    timeout = setTimeout(() => {
      fn(...args)
    }, delay)
  }) as Debounced<T>

  debounced.cancel = () => {
    if (timeout) {
      clearTimeout(timeout)
      timeout = null
    }
  }

  return debounced
}
