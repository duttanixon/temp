from app.models.user import User, UserRole, UserStatus
from app.models.customer import Customer, CustomerStatus
from app.models.audit_log import AuditLog
from app.models.device import Device, DeviceStatus, DeviceType
from app.models.solution import Solution, SolutionStatus
from app.models.customer_solution import CustomerSolution, LicenseStatus
from app.models.device_solution import DeviceSolution, DeviceSolutionStatus
from app.models.services.city_eye.human_table import City_Eye_human_table
from app.models.services.city_eye.traffic_table import City_Eye_traffic_table