import { Skeleton, Stack } from '@mui/material'

export const TransactionsScreenSkeleton = () => {
  return (
    <Stack spacing={2} width="100%">
      <Skeleton variant="text" height={70} width="35%" />

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
