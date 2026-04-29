import {
  Checkbox,
  FormControl,
  MenuItem,
  Radio,
  Select,
  SelectChangeEvent,
  SxProps,
  Typography,
} from '@mui/material'
import { useTranslate } from '@shared/hooks'

type Props<T extends string> = {
  multiple?: boolean
  translateItemKey: string
  translateKey: string
  placeholderKey: string
  value: T | null | T[]
  items: readonly T[]
  onChange: (e: SelectChangeEvent<any>) => void
  onClose?: () => void
  formSx?: SxProps
}

export function FiltersSelect<T extends string>({
  multiple = false,
  translateItemKey,
  translateKey,
  placeholderKey,
  value,
  items,
  onChange,
  onClose,
  formSx,
}: Props<T>) {
  const translateItem = useTranslate(translateItemKey)
  const translate = useTranslate(translateKey)

  const selectedArray = Array.isArray(value) ? value : []
  const selectedSingle = !Array.isArray(value) ? value : null

  return (
    <FormControl sx={{ minWidth: 125, maxWidth: 250, ...formSx }}>
      <Select
        multiple={multiple}
        displayEmpty
        value={value}
        onChange={onChange}
        onClose={onClose}
        renderValue={(value) => {
          if (multiple) {
            const arr = Array.isArray(value) ? (value as T[]) : []
            if (arr.length === 0) {
              return translate(placeholderKey)
            } else return translate('selected', { value: arr.length })
          }

          const single = value as T | ''
          return single !== '' ? translateItem(single) : translate(placeholderKey)
        }}
        size="small"
        sx={{
          height: 'max-content',
          bgcolor: 'surface.light',
          '& .MuiOutlinedInput-notchedOutline': { borderWidth: 1 },
          '& .MuiSelect-select': { py: 1 },
        }}
      >
        {items.map((item) => (
          <MenuItem key={item} value={item}>
            {multiple ? (
              <Checkbox checked={selectedArray.includes(item)} sx={{ color: 'primary.main' }} />
            ) : (
              <Radio checked={selectedSingle === item} sx={{ color: 'primary.main' }} />
            )}

            <Typography>{item ? translateItem(item) : translateItem('empty')}</Typography>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  )
}
