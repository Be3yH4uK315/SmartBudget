import { Skeleton, Stack } from '@mui/material'

export const BudgetScreenSkeleton = () => {
  return (
    <Stack width={'100%'} spacing={2} pt={4}>
      <Skeleton variant="text" height={70} width="20%" animation="wave" />

      <Stack spacing={2} direction={{ xs: 'column', md: 'row' }} width={{ xs: '100%', md: '100%' }}>
        <Skeleton variant="rounded" height={150} width="40%" animation="wave" />

        <Stack width={'100%'} spacing={2}>
          <Stack
            spacing={2}
            direction={{ xs: 'column', md: 'row' }}
            width={{ xs: '100%', md: '100%' }}
          >
            <Stack spacing={2} width={'50%'}>
              {Array(3).fill(0).map(renderBlock)}
            </Stack>

            <Skeleton variant="rounded" height={300} width="50%" animation="wave" />
          </Stack>
          <Skeleton variant="rounded" height={250} width="100%" animation="wave" />
        </Stack>
      </Stack>
    </Stack>
  )
}

function renderBlock(_: any, index: number) {
  return <Skeleton key={index} variant="rounded" height={'100%'} width="100%" animation="wave" />
}
