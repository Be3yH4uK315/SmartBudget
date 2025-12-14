import { lazy } from 'react'
import { SvgIconTypeMap } from '@mui/material'
import { OverridableComponent } from '@mui/material/OverridableComponent'

const Supermarkets = lazy(() => import('@mui/icons-material/StorefrontOutlined'))
const FastFood = lazy(() => import('@mui/icons-material/FastfoodOutlined'))
const Cloth = lazy(() => import('@mui/icons-material/CheckroomOutlined'))
const Electronics = lazy(() => import('@mui/icons-material/BlenderOutlined'))
const BuildAndRepair = lazy(() => import('@mui/icons-material/ConstructionOutlined'))
const HomeThings = lazy(() => import('@mui/icons-material/KingBedOutlined'))
const Beauty = lazy(() => import('@mui/icons-material/SpaOutlined'))
const PetSupplies = lazy(() => import('@mui/icons-material/PetsOutlined'))
const Books = lazy(() => import('@mui/icons-material/AutoStoriesOutlined'))
const Pharmacy = lazy(() => import('@mui/icons-material/VaccinesOutlined'))
const Health = lazy(() => import('@mui/icons-material/MedicalInformationOutlined'))
const Fuel = lazy(() => import('@mui/icons-material/LocalGasStationOutlined'))
const CarService = lazy(() => import('@mui/icons-material/BuildOutlined'))
const CarParts = lazy(() => import('@mui/icons-material/SettingsOutlined'))
const Parking = lazy(() => import('@mui/icons-material/LocalParkingOutlined'))
const Subscription = lazy(() => import('@mui/icons-material/CloudDoneOutlined'))
const Games = lazy(() => import('@mui/icons-material/SportsEsportsOutlined'))
const Marketplace = lazy(() => import('@mui/icons-material/ShoppingCartOutlined'))
const PublicTransport = lazy(() => import('@mui/icons-material/DirectionsBusOutlined'))
const Taxi = lazy(() => import('@mui/icons-material/LocalTaxiOutlined'))
const JKH = lazy(() => import('@mui/icons-material/RealEstateAgentOutlined'))
const Communication = lazy(() => import('@mui/icons-material/RouterOutlined'))
const Finance = lazy(() => import('@mui/icons-material/SavingsOutlined'))
const Education = lazy(() => import('@mui/icons-material/SchoolOutlined'))
const Entertainment = lazy(() => import('@mui/icons-material/LocalActivityOutlined'))
const Sport = lazy(() => import('@mui/icons-material/FitnessCenterOutlined'))
const Trip = lazy(() => import('@mui/icons-material/AirplanemodeActiveOutlined'))
const Charity = lazy(() => import('@mui/icons-material/AutoAwesomeOutlined'))
const Flowers = lazy(() => import('@mui/icons-material/LocalFlorist'))
const Other = lazy(() => import('@mui/icons-material/ShoppingBagOutlined'))

export const CATEGORIES_ICONS_MAP = new Map<
  number,
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  React.LazyExoticComponent<OverridableComponent<SvgIconTypeMap<{}, 'svg'>>>
>([
  [0, Supermarkets],
  [1, FastFood],
  [2, Cloth],
  [3, Electronics],
  [4, BuildAndRepair],
  [5, HomeThings],
  [6, Beauty],
  [7, PetSupplies],
  [8, Books],
  [9, Pharmacy],
  [10, Health],
  [11, Fuel],
  [12, CarService],
  [13, CarParts],
  [14, Parking],
  [15, Subscription],
  [16, Games],
  [17, Marketplace],
  [18, PublicTransport],
  [19, Taxi],
  [20, JKH],
  [21, Communication],
  [22, Finance],
  [23, Education],
  [24, Entertainment],
  [25, Sport],
  [26, Trip],
  [27, Charity],
  [28, Flowers],
  [29, Other],
])

export const CATEGORY_IDS = Array.from(CATEGORIES_ICONS_MAP.keys())
