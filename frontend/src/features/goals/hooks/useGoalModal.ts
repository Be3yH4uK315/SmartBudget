import { useState } from 'react'
import { MAX_TAGS_LENGTH } from '@features/goals/constants/tags'
import { Goal, GoalStatus, ModalFormValues, Priority, Tag } from '@features/goals/types'
import dayjs, { Dayjs } from 'dayjs'

export function useGoalModalForm(goal?: Goal) {
  const mode: 'create' | 'edit' = goal ? 'edit' : 'create'

  const initialValues: ModalFormValues = {
    name: goal?.name ?? '',
    targetAmount: goal?.targetAmount ?? '',
    finishDate: goal?.finishDate ?? null,
    priority: goal?.priority ?? null,
    tags: goal?.tags ?? [],
  }

  const [values, setValues] = useState<ModalFormValues>(initialValues)

  const handleChange =
    <K extends keyof Omit<ModalFormValues, 'tags' | 'priority'>>(key: K) =>
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value

      setValues((prev) => ({
        ...prev,
        [key]:
          key === 'targetAmount'
            ? value === '' || Number.isNaN(Number(value))
              ? ''
              : Number(value)
            : value,
      }))
    }

  const handleDateChange = (newValue: Dayjs | null) => {
    setValues((prev) => ({
      ...prev,
      finishDate: newValue ? newValue.format('YYYY-MM-DD') : null,
    }))
  }

  const setPriority = (priority: Priority) => {
    setValues((prev) => ({
      ...prev,
      priority: prev.priority === priority ? null : priority,
    }))
  }

  const toggleTag = (tag: Tag) => {
    setValues((prev) => {
      const exists = prev.tags.includes(tag)

      if (exists) {
        return { ...prev, tags: prev.tags.filter((t) => t !== tag) }
      }

      if (prev.tags.length >= MAX_TAGS_LENGTH) return prev

      return { ...prev, tags: [...prev.tags, tag] }
    })
  }

  const dirty =
    values.name !== initialValues.name ||
    values.targetAmount !== initialValues.targetAmount ||
    values.finishDate !== initialValues.finishDate ||
    values.priority !== initialValues.priority ||
    values.tags.length !== initialValues.tags.length ||
    values.tags.some((t) => !initialValues.tags.includes(t))

  const canSubmit = () => {
    if (!values.name.trim() || values.targetAmount === '' || values.targetAmount < 1) return false

    if (!values.finishDate) return true

    return dayjs(values.finishDate).isAfter(dayjs().startOf('day'))
  }

  const setPayload = (goalStatus?: GoalStatus) => ({
    name: values.name.trim(),
    targetAmount: Number(values.targetAmount),
    finishDate: values.finishDate,
    tags: values.tags,
    priority: values.priority,
    status: goalStatus ?? 'ongoing',
  })

  return {
    dirty,
    mode,
    values,
    handleChange,
    handleDateChange,
    setPriority,
    toggleTag,
    canSubmit,
    setPayload,
  }
}
