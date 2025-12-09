import { Skeleton, Stack } from '@mui/material'

export const DashboardScreenSkeleton = () => {
  return (
    <Stack spacing={2} width="100%">
      <Skeleton variant="text" height={70} width="35%" animation="wave" />

      <Stack spacing={2} direction={{ xs: 'column', md: 'row' }} width="100%">
        <Stack spacing={2} width={{ xs: '100%', md: '27%' }}>
          <Skeleton variant="rounded" height={200} width="100%" animation="wave" />

          <Skeleton variant="rounded" height={100} width="100%" animation="wave" />
        </Stack>

        <Stack spacing={2} width={{ xs: '100%', md: '73%' }}>
          <Skeleton variant="rounded" height={100} width="100%" animation="wave" />

          <Skeleton variant="rounded" height={300} width="100%" animation="wave" />

          <Skeleton variant="rounded" height={100} width="100%" animation="wave" />
        </Stack>
      </Stack>
    </Stack>
  )
}
