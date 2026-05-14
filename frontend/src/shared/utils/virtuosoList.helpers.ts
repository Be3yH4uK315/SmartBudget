import dayjs from 'dayjs'

export type DateBlock<T> = {
  date: string
  items: T[]
}

type MergeBlocksProps<T> = {
  currentBlocks: DateBlock<T>[]
  newBlocks: DateBlock<T>[]
}

export function groupByDate<T extends { date: string }>(items: T[]): DateBlock<T>[] {
  const sortedItems = [...items].sort((a, b) => {
    const dateA = dayjs.utc(a.date).local().valueOf()
    const dateB = dayjs.utc(b.date).local().valueOf()
    return dateB - dateA
  })

  return sortedItems.reduce<DateBlock<T>[]>((blocks, item) => {
    const localDate = dayjs.utc(item.date).local()
    const date = localDate.format('YYYY-MM-DD')
    const lastBlock = blocks[blocks.length - 1]

    if (lastBlock && lastBlock.date === date) {
      lastBlock.items.push(item)
    } else {
      blocks.push({
        date,
        items: [item],
      })
    }

    return blocks
  }, [])
}

export function normalizeBlocks<T>(blocks: DateBlock<T>[]) {
  const groups: string[] = []
  const groupCounts: number[] = []
  const items: T[] = []

  for (const block of blocks) {
    groups.push(block.date)
    groupCounts.push(block.items.length)
    items.push(...block.items)
  }

  return { groups, groupCounts, items }
}

export function mergeDateBlocks<T>({
  currentBlocks,
  newBlocks,
}: MergeBlocksProps<T>): DateBlock<T>[] {
  if (!currentBlocks.length) return newBlocks
  if (!newBlocks.length) return currentBlocks

  return [
    ...currentBlocks.slice(0, -1),
    {
      date: currentBlocks[currentBlocks.length - 1].date,
      items: [...currentBlocks[currentBlocks.length - 1].items, ...newBlocks[0].items],
    },
    ...newBlocks.slice(1),
  ]
}
