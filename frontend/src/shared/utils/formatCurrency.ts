const rubFormatter = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  minimumFractionDigits: 0,
})

export function formatCurrency(value: number | string): string {
  const num = typeof value === 'string' ? Number(value) : value

  if (Number.isNaN(num)) return '—'

  return rubFormatter.format(num)
}
