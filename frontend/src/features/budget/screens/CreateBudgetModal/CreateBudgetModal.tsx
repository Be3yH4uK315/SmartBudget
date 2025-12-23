import { useCreateBudget } from '@features/budget/hooks/useCreateBudget'
import { createBudget } from '@features/budget/store'
import { mapFormToCreateBudgetPayload } from '@features/budget/utils'
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline'
import {
  Button,
  Checkbox,
  FormControlLabel,
  IconButton,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { CategoryOption } from '@shared/components'
import { CATEGORIES_ICONS_MAP } from '@shared/constants/categoriesIcons'
import { useTranslate } from '@shared/hooks'
import ModalLayout from '@shared/screens/ModalProvider'
import { useAppDispatch } from '@shared/store'

type Props = {
  onClose: () => void
}

export const CreateBudgetModal = ({ onClose }: Props) => {
  const translate = useTranslate('Budget.Modal')
  const dispatch = useAppDispatch()

  const {
    values,
    availableCategories,
    totalPercent,
    remainingPercent,
    isPercentOverflow,
    canSubmit,
    setTotalLimit,
    addCategory,
    removeCategory,
    updateCategory,
    updateAmount,
    updatePercent,
    toggleAutoRenew,
  } = useCreateBudget()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const payload = mapFormToCreateBudgetPayload(values)
    dispatch(createBudget({ payload: payload }))
    console.log(payload)
    onClose()
  }

  return (
    <ModalLayout>
      <Stack spacing={3}>
        <Typography variant="h2">{translate('createTitle')}</Typography>

        <Stack>
          <form onSubmit={handleSubmit}>
            <Stack spacing={3}>
              <Stack spacing={0.5}>
                <Typography variant="h5">{translate('totalLimitTitle')}</Typography>

                <TextField
                  label={translate('totalLimit')}
                  type="number"
                  value={values.totalLimit ? values.totalLimit : ''}
                  onChange={(e) => setTotalLimit(Number(e.target.value))}
                  fullWidth
                />

                <Typography variant="caption">{translate('totalLimitSubtitle')}</Typography>
              </Stack>

              <Stack spacing={2}>
                <Stack>
                  <Typography variant="h5">{translate('categoriesTitle')}</Typography>

                  <Typography variant="caption">{translate('categoriesSubtitle')}</Typography>
                </Stack>
                {values.categories.map((row, index) => {
                  return (
                    <Stack
                      key={index}
                      sx={{
                        display: 'grid',
                        gridTemplateColumns:
                          values.totalLimit > 0 ? '2fr 1fr 1fr 0.35fr' : '2fr 2fr 0.35fr',
                        gap: 2,
                        width: '100%',
                      }}
                    >
                      <Select
                        value={row.categoryId ?? ''}
                        displayEmpty
                        onChange={(e) =>
                          updateCategory(index, {
                            categoryId: Number(e.target.value),
                          })
                        }
                        renderValue={(value) => {
                          if (!value) return translate('selectPlaceholder')
                          const Icon = CATEGORIES_ICONS_MAP.get(Number(value))!
                          return <CategoryOption value={Number(value)} Icon={Icon} />
                        }}
                      >
                        {availableCategories.concat(row.categoryId ?? []).map((id) => {
                          if (!id) return null
                          const Icon = CATEGORIES_ICONS_MAP.get(id)!
                          return (
                            <MenuItem key={id} value={id}>
                              <CategoryOption value={id} Icon={Icon} />
                            </MenuItem>
                          )
                        })}
                      </Select>

                      <TextField
                        type="number"
                        label={translate('limit')}
                        value={row.limit ? row.limit : ''}
                        onChange={(e) => updateAmount(index, Number(e.target.value))}
                        fullWidth
                      />

                      {values.totalLimit > 0 && (
                        <TextField
                          type="number"
                          label="%"
                          value={row.percent ? row.percent : ''}
                          onChange={(e) => updatePercent(index, Number(e.target.value))}
                          fullWidth
                        />
                      )}

                      <IconButton
                        onClick={() => removeCategory(index)}
                        disabled={values.categories.length === 1}
                        sx={{
                          bgcolor: 'primary.main',
                          borderRadius: '12px',
                          maxHeight: '56px',
                          '&:disabled': { bgcolor: 'grayButton.dark' },
                          ':hover': { bgcolor: 'primary.light' },
                        }}
                      >
                        <DeleteOutlineIcon />
                      </IconButton>
                    </Stack>
                  )
                })}

                {isPercentOverflow && (
                  <Typography variant="caption" color="error.main">
                    {translate('percentOverflow', {
                      value: totalPercent,
                    })}
                  </Typography>
                )}

                {values.totalLimit > 0 && !isPercentOverflow && remainingPercent > 0 && (
                  <Typography variant="caption">
                    {translate('remainingPercent', {
                      value: remainingPercent,
                    })}
                  </Typography>
                )}

                {availableCategories.length > 0 && (
                  <Button onClick={addCategory}>{translate('addCategory')}</Button>
                )}
              </Stack>

              <FormControlLabel
                control={
                  <Checkbox
                    checked={values.isAutoRenew}
                    onChange={(e) => toggleAutoRenew(e.target.checked)}
                    sx={{ color: 'text.primary', '&.Mui-checked': { color: 'text.primary' } }}
                  />
                }
                label={translate('autoRenew')}
              />

              <Button type="submit" variant="yellow" disabled={!canSubmit}>
                {translate('create')}
              </Button>
            </Stack>
          </form>
        </Stack>
      </Stack>
    </ModalLayout>
  )
}
