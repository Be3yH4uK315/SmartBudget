import React from 'react'
import { Box, Button, Paper, Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'
import { CenterLabel, FilterType, PieDataItem } from '@shared/types/components'
import { CategoryBlock } from './CategoryBlock'
import { PieChartWithCenterLabel } from './PieChartWithCenterLabel'

type Props = {
  title: string
  activeType?: FilterType
  pieData: PieDataItem[]
  centerLabel?: CenterLabel
  toggleFilter?: (type: FilterType) => void
}

export const TransactionsPieBlock = React.memo(
  ({ title, activeType, pieData, centerLabel, toggleFilter }: Props) => {
    const translate = useTranslate('TransactionsPieBlock')

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
            flex: 1,
            textAlign: 'center',
          }}
        >
          <Typography fontWeight={600}>{translate('fallback')}</Typography>
        </Paper>
      )
    }

    return (
      <Paper sx={{ p: 3, borderRadius: '24px', flex: '1 1 0%', display: 'flex' }} elevation={2}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ flex: '1 1 0%' }}>
          <Stack spacing={1.5}>
            <Typography variant="h4">{title}</Typography>

            {activeType && toggleFilter && (
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
            )}

            {pieData.length > 0 && (
              <Box
                sx={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 1.5,
                  alignItems: 'center',
                }}
              >
                {pieData.map((d) => (
                  <CategoryBlock key={d.value} category={d} />
                ))}
              </Box>
            )}
          </Stack>
          {pieData.length === 0 && renderFallback()}

          {pieData.length > 0 && (
            <Box
              sx={{
                display: 'flex',
                ml: { xs: 0, md: 'auto !important' },
                mt: { xs: 2, md: 0 },
                width: { xs: 'auto', md: 250 },
                height: { md: 250 },
              }}
            >
              <PieChartWithCenterLabel
                pieData={pieData}
                innerRadius={80}
                width={200}
                height={200}
                centerLabel={centerLabel && centerLabel}
              />
            </Box>
          )}
        </Stack>
      </Paper>
    )
  },
)
