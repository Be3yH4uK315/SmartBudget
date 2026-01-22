import { Priority, Tag } from '@features/goals/types'
import { Box, Typography } from '@mui/material'
import { useTranslate } from '@shared/hooks'

type Props = {
  tag: Tag | Priority
}

export const GoalTag = ({ tag }: Props) => {
  const translate = useTranslate('Goals.Tags')

  return (
    <Box
      component="span"
      sx={{
        px: 1.5,
        py: 0,
        bgcolor: 'primary.main',
        borderRadius: '6px',
        width: 'max-content',
        height: 'min-content',
        display: 'inline-flex',
      }}
    >
      {tag && (
        <Typography variant="caption" sx={{ color: '#333' }}>
          {translate(tag)}
        </Typography>
      )}
    </Box>
  )
}
