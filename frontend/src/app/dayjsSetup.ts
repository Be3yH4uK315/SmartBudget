import 'dayjs/locale/ru'
import 'dayjs/locale/uz'
import 'dayjs/locale/zh'
import dayjs from 'dayjs'
import customParseFormat from 'dayjs/plugin/customParseFormat'
import isBetween from 'dayjs/plugin/isBetween'
import isToday from 'dayjs/plugin/isToday'
import localeData from 'dayjs/plugin/localeData'
import localizedFormat from 'dayjs/plugin/localizedFormat'
import utc from 'dayjs/plugin/utc'
import weekday from 'dayjs/plugin/weekday'

dayjs.extend(isBetween)
dayjs.extend(isToday)
dayjs.extend(localizedFormat)
dayjs.extend(customParseFormat)
dayjs.extend(weekday)
dayjs.extend(localeData)
dayjs.extend(utc)
