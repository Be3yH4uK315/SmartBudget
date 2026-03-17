export type DateBlock<T> = {
  date: string
  items: T[]
}

type MergeBlocksProps<T> = {
  currentBlocks: DateBlock<T>[]
  newBlocks: DateBlock<T>[]
}

export function groupByDate<T extends { date: string }>(items: T[]): DateBlock<T>[] {
  return items.reduce<DateBlock<T>[]>((blocks, item) => {
    const date = item.date.split('T')[0]
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
