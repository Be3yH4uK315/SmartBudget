import { Box, Skeleton, Stack } from '@mui/material'

export const GoalsScreenSkeleton = () => {
  return (
    <Box width={'100%'}>
      <Stack width={{ xs: '100%', md: '70%' }} spacing={2} alignContent={'flex-start'}>
        <Skeleton variant="text" height={70} width="35%" animation="wave" />

        <Skeleton variant="rounded" height={70} width="100%" animation="wave" />

        <Stack direction={'row'} spacing={2}>
          {Array(3).fill(0).map(renderStatsBlock)}
        </Stack>

        <Skeleton variant="rounded" height={70} width="100%" animation="wave" />

        {Array(3).fill(0).map(renderGoalBlock)}
      </Stack>
    </Box>
  )
}

function renderStatsBlock(_: any, index: number) {
  return <Skeleton key={index} variant="rounded" height={100} width="100%" animation="wave" />
}

function renderGoalBlock(_: any, index: number) {
  return <Skeleton key={index} variant="rounded" height={150} width="100%" animation="wave" />
}
