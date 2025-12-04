import React, { useMemo } from 'react'
import { Box, Button, Paper, Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import dayjs from 'dayjs'
import { CategoryBlock } from './CategoryBlock'
import { PieChartWithCenterLabel } from './TransactionsPie'

type Props = {
  categories: normalizedCategory[]
  total: number
  activeType: FilterType
  toggleFilter: (type: FilterType) => void
}

export const TransactionsBlock = React.memo(
  ({ categories, total, activeType, toggleFilter }: Props) => {
    const translate = useTranslate('Dashboard.Transactions')

    const title = `${translate('transactions')} ${translate(`month.${dayjs().month()}`)}`

    const pieLabel = translate(activeType).toLowerCase()

    const pieData = useMemo<Omit<normalizedCategory, 'lightColor'>[]>(
      () => categories.map(({ lightColor, ...rest }) => rest),
      [categories],
    )

    function renderFallback() {
      return (
        <Paper
          sx={{
            p: 3,
            borderRadius: '24px',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            whiteSpace: 'wrap',
            minHeight: '200px',
          }}
        >
          <Typography variant="h4">{translate('fallback')}</Typography>
        </Paper>
      )
    }

    if (categories.length === 0) return renderFallback()

    return (
      <Paper sx={{ p: 3, borderRadius: '24px', flex: '1 1 0%', display: 'flex' }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ flex: '1 1 0%' }}>
          <Stack spacing={1.5}>
            <Typography variant="h4">{title}</Typography>

            <Stack direction={'row'} spacing={1}>
              {(['expense', 'income'] as const).map((type) => (
                <Button
                  key={type}
                  variant="white"
                  sx={(theme) => ({
                    borderColor: activeType === type ? theme.palette.primary.main : 'transparent',
                  })}
                  onClick={() => toggleFilter(type)}
                >
                  {translate(type)}
                </Button>
              ))}
            </Stack>

            <Box
              sx={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 1.5,
                alignItems: 'center',
              }}
            >
              {categories.map((c) => (
                <CategoryBlock key={c.value} category={c} />
              ))}
            </Box>
          </Stack>

          <Box
            sx={{
              display: 'flex',
              ml: { xs: 0, md: 'auto !important' },
              mt: { xs: 2, md: 0 },
              width: { xs: 'auto', md: 200 },
              height: { md: 200 },
            }}
          >
            <PieChartWithCenterLabel
              data={pieData}
              total={total}
              innerRadius={80}
              width={200}
              height={200}
              label={pieLabel}
            />
          </Box>
        </Stack>
      </Paper>
    )
  },
)
