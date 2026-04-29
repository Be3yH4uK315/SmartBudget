import { Skeleton, Stack } from '@mui/material'

export const NotificationsScreenSkeleton = () => {
  return <Stack spacing={1}>{Array(3).fill(0).map(renderNotificationBlock)}</Stack>
}

function renderNotificationBlock(_: any, index: number) {
  return (
    <Stack key={index} spacing={1}>
      <Skeleton variant="text" height={60} width="35%" />

      <Skeleton height={100} width={'100%'} />

      <Skeleton height={100} width={'100%'} />

      <Skeleton height={100} width={'100%'} />
    </Stack>
  )
}
