import { CableOutlined, SettingsOutlined, TimelineOutlined } from '@mui/icons-material'
import {
  Timeline,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineItem,
  TimelineOppositeContent,
  TimelineSeparator,
} from '@mui/lab'
import { Stack, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'

export const StepBlock = () => {
  const translate = useTranslate('PublicPage.Steps')
  return (
    <Timeline position="alternate">
      <TimelineItem>
        <TimelineOppositeContent sx={{ py: '12px', px: 2 }}>
          <Typography variant="h5">{translate('First.step')}</Typography>
        </TimelineOppositeContent>

        <TimelineSeparator>
          <TimelineDot sx={{ bgcolor: 'secondary.main', p: 1 }}>
            <SettingsOutlined sx={{ color: '#fff' }} />
          </TimelineDot>

          <TimelineConnector />
        </TimelineSeparator>

        <TimelineContent sx={{ py: '12px', px: 2 }}>
          <Stack>
            <Typography variant="h6">{translate('First.title')}</Typography>

            <Typography variant="caption">{translate('First.subtitle')}</Typography>
          </Stack>
        </TimelineContent>
      </TimelineItem>

      <TimelineItem>
        <TimelineOppositeContent sx={{ py: '12px', px: 2 }}>
          <Typography variant="h5">{translate('Second.step')}</Typography>
        </TimelineOppositeContent>

        <TimelineSeparator>
          <TimelineDot sx={{ bgcolor: 'secondary.main', p: 1 }}>
            <CableOutlined sx={{ color: '#fff' }} />
          </TimelineDot>

          <TimelineConnector />
        </TimelineSeparator>

        <TimelineContent sx={{ py: '12px', px: 2 }}>
          <Stack>
            <Typography variant="h6">{translate('Second.title')}</Typography>

            <Typography variant="caption">{translate('Second.subtitle')}</Typography>
          </Stack>
        </TimelineContent>
      </TimelineItem>

      <TimelineItem>
        <TimelineOppositeContent sx={{ py: '12px', px: 2 }}>
          <Typography variant="h5">{translate('Third.step')}</Typography>
        </TimelineOppositeContent>

        <TimelineSeparator>
          <TimelineDot sx={{ bgcolor: 'secondary.main', p: 1 }}>
            <TimelineOutlined sx={{ color: '#fff' }} />
          </TimelineDot>

          <TimelineConnector />
        </TimelineSeparator>

        <TimelineContent sx={{ py: '12px', px: 2 }}>
          <Stack>
            <Typography variant="h6">{translate('Third.title')}</Typography>

            <Typography variant="caption">{translate('Third.subtitle')}</Typography>
          </Stack>
        </TimelineContent>
      </TimelineItem>

      <Stack alignItems={'center'}>
        <Typography variant="h6">{translate('Fourth.title')}</Typography>
      </Stack>
    </Timeline>
  )
}
