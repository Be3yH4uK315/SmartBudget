import { useState } from 'react'
import { useSearch } from '@features/transactions/hooks'
import { Search } from '@mui/icons-material'
import { Autocomplete, Box, CircularProgress, InputAdornment, TextField } from '@mui/material'
import { StyledPaper } from '@shared/components'
import { useTheme, useTranslate } from '@shared/hooks'
import { ApiFunc } from '@shared/types/components'

type Props<T> = {
  apiFunc: ApiFunc<T>
  getOptionLabel: (option: T) => string
  renderOption: (props: React.HTMLAttributes<HTMLLIElement>, option: T) => React.ReactNode
}

export function SearchBar<T>({ apiFunc, getOptionLabel, renderOption }: Props<T>) {
  const translate = useTranslate('Transactions.SearchBar')
  const theme = useTheme()

  const [inputValue, setInputValue] = useState<string>('')

  const { results, isLoading, debouncedSearch, clearResults } = useSearch<T>(apiFunc)

  const handleInputChange = (_: any, value: string, reason: string) => {
    setInputValue(value)

    if (reason !== 'input') return

    if (value.trim().length < 2) {
      debouncedSearch.cancel()
      clearResults()
      return
    }

    debouncedSearch(value)
  }

  const handleSelect = () => {
    debouncedSearch.cancel()
    clearResults()
    setInputValue('')
  }

  const bgColor = theme.colorMode === 'light' ? 'surface.dark' : 'surface.light'

  return (
    <Autocomplete
      options={results}
      value={null}
      inputValue={inputValue}
      filterOptions={(x) => x}
      noOptionsText={isLoading ? '' : translate('emptyResult')}
      open={!!inputValue.trim()}
      onInputChange={handleInputChange}
      popupIcon={false}
      onChange={handleSelect}
      getOptionLabel={getOptionLabel}
      slotProps={{
        paper: {
          component: (props) => (
            <StyledPaper
              elevation={0}
              {...props}
              paperSx={{
                mt: 1,
                '& .MuiAutocomplete-noOptions': {
                  color: 'text.primary',
                  textAlign: 'center',
                  py: 2,
                },
              }}
            >
              {isLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress size={20} />
                </Box>
              ) : (
                <>{props.children}</>
              )}
            </StyledPaper>
          ),
        },
      }}
      renderOption={(props, option) => renderOption(props, option)}
      renderInput={(params) => (
        <TextField
          {...params}
          placeholder={translate('placeholder')}
          hiddenLabel
          slotProps={{
            input: {
              ...params.InputProps,
              startAdornment: (
                <InputAdornment position="start" sx={{ pl: 1 }}>
                  <Search sx={{ color: 'gray.main' }} />
                </InputAdornment>
              ),
            },
          }}
          sx={{
            '& .MuiOutlinedInput-root': {
              backgroundColor: bgColor,
              borderRadius: '12px',
              pr: 1.5,

              ':hover': {
                backgroundColor: bgColor,
              },

              '& fieldset': {
                borderColor: bgColor,
              },

              '&:hover fieldset': {
                borderColor: bgColor,
              },

              '&.Mui-focused fieldset': {
                borderColor: bgColor,
              },
            },
          }}
        />
      )}
    />
  )
}
