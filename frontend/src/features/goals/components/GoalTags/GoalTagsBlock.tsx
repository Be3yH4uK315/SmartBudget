import { Priority, Tag } from '@features/goals/types'
import { StyledBox } from '@shared/components'
import { GoalTag } from './GoalTag'

type Props = {
  tags: Tag[]
  priority: Priority
}

export const GoalTagsBlock = ({ tags, priority }: Props) => {
  return (
    <StyledBox>
      {priority && <GoalTag tag={priority} />}

      {tags.map((t) => (
        <GoalTag key={t} tag={t} />
      ))}
    </StyledBox>
  )
}
