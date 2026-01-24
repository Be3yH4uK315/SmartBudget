import {
  Checkbox,
  FormControl,
  MenuItem,
  Select,
  SelectChangeEvent,
  Typography,
} from '@mui/material'
import { useTranslate } from '@shared/hooks'

type Props<T extends string> = {
  value: T[]
  items: readonly T[]
  placeholder: string
  onChange: (e: SelectChangeEvent<T[]>) => void
  onClose: () => void
}

export function FiltersSelect<T extends string>({
  value,
  items,
  placeholder,
  onClose,
  onChange,
}: Props<T>) {
  const translate = useTranslate('Goals.Tags')
  return (
    <FormControl sx={{ minWidth: 200, maxWidth: 250 }}>
      <Select
        multiple
        displayEmpty
        value={value}
        onChange={onChange}
        onClose={onClose}
        renderValue={(v) =>
          v.length === 0 ? placeholder : translate('selected', { value: v.length })
        }
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
            <Checkbox checked={value.includes(item)} sx={{ color: 'primary.main' }} />
            <Typography>{translate(item)}</Typography>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  )
}
