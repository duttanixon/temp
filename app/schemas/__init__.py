from app.schemas.user import User, UserCreate, UserUpdate, UserProfile, UserPasswordChange, UserAdminView
from app.schemas.customer import Customer, CustomerCreate, CustomerUpdate, CustomerAdminView, CustomerBasic
from app.schemas.token import Token, TokenPayload
from app.schemas.solution import SolutionCreate, SolutionUpdate, Solution, SolutionAdminView
from app.schemas.customer_solution import CustomerSolutionUpdate, CustomerSolution, CustomerSolutionAdminView, CustomerSolutionCreate
from app.schemas.device_metrics import MetricsResponse
from app.schemas.services.city_eye_analytics import (
    TotalCount,
    HourlyCount,
    TimeSeriesData,
    DetectionZoneDirection,
    PerDeviceDirectionData,
    AgeDistribution,
    GenderDistribution,
    AgeGenderDistribution,
    VehicleTypeDistribution,
    AnalyticsFilters,
    TrafficAnalyticsFilters,
    PerDeviceAnalyticsData,
    PerDeviceTrafficAnalyticsData,
    DeviceAnalyticsItem,
    DeviceTrafficAnalyticsItem,
    DeviceDirectionItem,
    CityEyeAnalyticsPerDeviceResponse,
    CityEyeTrafficAnalyticsPerDeviceResponse,
    CityEyeDirectionPerDeviceResponse
)