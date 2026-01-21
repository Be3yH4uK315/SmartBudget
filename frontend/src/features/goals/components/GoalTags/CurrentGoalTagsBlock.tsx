import { Priority, Tag } from '@features/goals/types'
import { Button, Stack, Typography } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { useTranslate } from '@shared/hooks'
import { GoalTagsBlock } from './GoalTagsBlock'

type Props = {
  tags: Tag[]
  priority: Priority | null
  onClick: () => void
}

export const CurrentGoalTagsBlock = ({ tags, priority, onClick }: Props) => {
  const translate = useTranslate('CurrentGoal.TagsBlock')

  return (
    <StyledPaper>
      <Stack spacing={2}>
        <Stack>
          <Typography variant="h4">{translate('title')}</Typography>

          {(tags.length > 0 || priority) && <Typography>{translate('subtitle')}</Typography>}

          {tags.length === 0 && !priority && <Typography>{translate('noTagsSubtitle')}</Typography>}
        </Stack>

        {(tags.length > 0 || priority) && <GoalTagsBlock tags={tags} priority={priority} />}

        {tags.length === 0 && !priority && <Button onClick={onClick}>{translate('button')}</Button>}
      </Stack>
    </StyledPaper>
  )
}
