import { Skeleton, Stack } from '@mui/material'

export const NotificationsScreenSkeleton = () => {
  return (
    <Stack spacing={1} width="100%">
      <Skeleton variant="text" height={70} width="35%" animation="wave" />

      <Stack spacing={2} width={{ xs: '100%', md: '70%' }}>
        {Array(4).fill(0).map(renderBlock)}

        <Skeleton variant="rounded" height={200} width="100%" animation="wave" />
      </Stack>
    </Stack>
  )
}

function renderBlock(_: any, index: number) {
  return <Skeleton key={index} variant="rounded" height={100} width="100%" animation="wave" />
}
