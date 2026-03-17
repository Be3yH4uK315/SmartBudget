import { Box, Skeleton, Stack } from '@mui/material'

export const NotificationsChunkScreenSkeleton = () => {
  return (
    <Stack spacing={1} width="100%">
      <Skeleton variant="text" height={50} width="35%" />

      <Box sx={{ width: '100%', justifyContent: 'end', display: 'flex' }}>
        <Skeleton variant="text" height={60} width="20%" />
      </Box>

      <Stack spacing={1}>{Array(3).fill(0).map(renderNotificationBlock)}</Stack>
    </Stack>
  )
}

function renderNotificationBlock(_: any, index: number) {
  return (
    <Stack key={index} spacing={1}>
      <Skeleton variant="text" height={60} width="35%" />

      <Skeleton height={100} width={'70%'} />

      <Skeleton height={100} width={'70%'} />

      <Skeleton height={100} width={'70%'} />
    </Stack>
  )
}
