import AirplanemodeActiveOutlined from '@mui/icons-material/AirplanemodeActiveOutlined'
import AutoAwesomeOutlined from '@mui/icons-material/AutoAwesomeOutlined'
import AutoStoriesOutlined from '@mui/icons-material/AutoStoriesOutlined'
import BlenderOutlined from '@mui/icons-material/BlenderOutlined'
import BuildOutlined from '@mui/icons-material/BuildOutlined'
import CheckroomOutlined from '@mui/icons-material/CheckroomOutlined'
import CloudDoneOutlined from '@mui/icons-material/CloudDoneOutlined'
import ConstructionOutlined from '@mui/icons-material/ConstructionOutlined'
import DirectionsBusOutlined from '@mui/icons-material/DirectionsBusOutlined'
import FastfoodOutlined from '@mui/icons-material/FastfoodOutlined'
import FitnessCenterOutlined from '@mui/icons-material/FitnessCenterOutlined'
import KingBedOutlined from '@mui/icons-material/KingBedOutlined'
import LocalActivityOutlined from '@mui/icons-material/LocalActivityOutlined'
import LocalFlorist from '@mui/icons-material/LocalFlorist'
import LocalGasStationOutlined from '@mui/icons-material/LocalGasStationOutlined'
import LocalParkingOutlined from '@mui/icons-material/LocalParkingOutlined'
import LocalTaxiOutlined from '@mui/icons-material/LocalTaxiOutlined'
import MedicalInformationOutlined from '@mui/icons-material/MedicalInformationOutlined'
import PetsOutlined from '@mui/icons-material/PetsOutlined'
import RealEstateAgentOutlined from '@mui/icons-material/RealEstateAgentOutlined'
import RouterOutlined from '@mui/icons-material/RouterOutlined'
import SavingsOutlined from '@mui/icons-material/SavingsOutlined'
import SchoolOutlined from '@mui/icons-material/SchoolOutlined'
import SettingsOutlined from '@mui/icons-material/SettingsOutlined'
import ShoppingBagOutlined from '@mui/icons-material/ShoppingBagOutlined'
import ShoppingCartOutlined from '@mui/icons-material/ShoppingCartOutlined'
import SpaOutlined from '@mui/icons-material/SpaOutlined'
import SportsEsportsOutlined from '@mui/icons-material/SportsEsportsOutlined'
import StorefrontOutlined from '@mui/icons-material/StorefrontOutlined'
import VaccinesOutlined from '@mui/icons-material/VaccinesOutlined'
import { SvgIconTypeMap } from '@mui/material'
import { OverridableComponent } from '@mui/material/OverridableComponent'

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
type IconComponent = OverridableComponent<SvgIconTypeMap<{}, 'svg'>>

export const CATEGORIES_ICONS_MAP = new Map<number, IconComponent>([
  [1, StorefrontOutlined],
  [2, FastfoodOutlined],
  [3, CheckroomOutlined],
  [4, BlenderOutlined],
  [5, ConstructionOutlined],
  [6, KingBedOutlined],
  [7, SpaOutlined],
  [8, PetsOutlined],
  [9, AutoStoriesOutlined],
  [10, VaccinesOutlined],
  [11, MedicalInformationOutlined],
  [12, LocalGasStationOutlined],
  [13, BuildOutlined],
  [14, SettingsOutlined],
  [15, LocalParkingOutlined],
  [16, CloudDoneOutlined],
  [17, SportsEsportsOutlined],
  [18, ShoppingCartOutlined],
  [19, DirectionsBusOutlined],
  [20, LocalTaxiOutlined],
  [21, RealEstateAgentOutlined],
  [22, RouterOutlined],
  [23, SavingsOutlined],
  [24, SchoolOutlined],
  [25, LocalActivityOutlined],
  [26, FitnessCenterOutlined],
  [27, AirplanemodeActiveOutlined],
  [28, AutoAwesomeOutlined],
  [29, LocalFlorist],
  [30, ShoppingBagOutlined],
])

export const CATEGORY_IDS = Array.from(CATEGORIES_ICONS_MAP.keys())
