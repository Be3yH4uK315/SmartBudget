const percentFormatter = new Intl.NumberFormat('ru-RU', {
  style: 'percent',
  currency: 'RUB',
  minimumFractionDigits: 1,
})

export function formatPercent(value: number | string): string {
  const num = typeof value === 'string' ? Number(value) : value

  if (Number.isNaN(num)) return '—'

  return `${percentFormatter.format(num)}`
}
