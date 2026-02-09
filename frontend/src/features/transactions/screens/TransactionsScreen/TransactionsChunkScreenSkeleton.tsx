import { Skeleton, Stack } from '@mui/material'

export const TransactionsChunkScreenSkeleton = () => {
  return (
    <Stack spacing={1.5} width="100%">
      <Skeleton variant="text" height={50} width="35%" />

      <Stack spacing={1} direction={'row'}>
        <Skeleton variant="text" height={60} width="15%" />
        <Skeleton variant="text" height={60} width="15%" />
        <Skeleton variant="text" height={60} width="15%" />
      </Stack>

      <Stack spacing={1}>{Array(5).fill(0).map(renderTransactionBlock)}</Stack>
    </Stack>
  )
}

function renderTransactionBlock(_: any, index: number) {
  return (
    <Stack key={index} spacing={1}>
      <Skeleton variant="text" height={60} width="35%" />

      <Skeleton height={40} width={'70%'} />

      <Skeleton height={40} width={'70%'} />

      <Skeleton height={40} width={'70%'} />
    </Stack>
  )
}
