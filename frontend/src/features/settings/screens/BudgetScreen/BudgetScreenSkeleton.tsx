import { Skeleton, Stack } from '@mui/material'

export const BudgetScreenSkeleton = () => {
  return (
    <Stack spacing={2} width={{ xs: '100%', md: '70%' }}>
      {Array(2).fill(0).map(renderBlock)}

      <Skeleton variant="rounded" height={100} width="100%" animation="wave" />
    </Stack>
  )
}

function renderBlock(_: any, index: number) {
  return <Skeleton key={index} variant="rounded" height={100} width="100%" animation="wave" />
}
