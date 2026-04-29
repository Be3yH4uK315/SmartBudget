import { Skeleton, Stack } from '@mui/material'

export const CurrentGoalScreenSkeleton = () => {
  return (
    <Stack spacing={2} width="100%">
      <Stack>
        <Skeleton variant="text" height={70} width="35%" animation="wave" />

        <Skeleton variant="text" height={30} width="15%" animation="wave" />
      </Stack>

      <Stack spacing={2} direction={{ xs: 'column', md: 'row' }} width="100%">
        <Skeleton
          variant="rounded"
          height={150}
          sx={{ width: { xs: '100%', md: '27%' } }}
          animation="wave"
        />

        <Stack spacing={2} width={{ xs: '100%', md: '73%' }}>
          <Skeleton variant="rounded" height={300} width="100%" animation="wave" />

          <Stack direction={'row'} spacing={2}>
            {Array(3).fill(0).map(renderBlock)}
          </Stack>

          <Skeleton variant="rounded" height={70} width="100%" animation="wave" />

          <Skeleton variant="rounded" height={50} width="100%" animation="wave" />
        </Stack>
      </Stack>
    </Stack>
  )
}

function renderBlock(_: any, index: number) {
  return <Skeleton key={index} variant="rounded" height={100} width="100%" animation="wave" />
}
