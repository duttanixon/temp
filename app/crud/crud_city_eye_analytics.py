from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer, Date, Time, case, and_, or_
from sqlalchemy.dialects.postgresql import INTERVAL, TIME
from sqlalchemy.sql.expression import literal_column, ColumnElement
from app.models.services.city_eye.human_table import CityEyeHumanTable
from app.models.services.city_eye.traffic_table import CityEyeTrafficTable
from app.schemas.services.city_eye_analytics import AnalyticsFilters, TrafficAnalyticsFilters
from datetime import datetime, time as dt_time

class CRUDCityEyeAnalytics:

    # =============================================================================
    # HUMAN ANALYTICS METHODS
    # =============================================================================

    def _get_people_columns_map(self) -> Dict[tuple, Any]:
        """
        Returns the mapping of (gender, age_group) tuples to database columns.
        Extracted to follow DRY principle.
        """
        return {
            ("male", "under_18"): CityEyeHumanTable.male_less_than_18,
            ("female", "under_18"): CityEyeHumanTable.female_less_than_18,
            ("male", "18_to_29"): CityEyeHumanTable.male_18_to_29,
            ("female", "18_to_29"): CityEyeHumanTable.female_18_to_29,
            ("male", "30_to_49"): CityEyeHumanTable.male_30_to_49,
            ("female", "30_to_49"): CityEyeHumanTable.female_30_to_49,
            ("male", "50_to_64"): CityEyeHumanTable.male_50_to_64,
            ("female", "50_to_64"): CityEyeHumanTable.female_50_to_64,
            ("male", "over_64"): CityEyeHumanTable.male_65_plus,
            ("female", "over_64"): CityEyeHumanTable.female_65_plus,
        }

    def _get_people_sum_expression(self, filters: AnalyticsFilters) -> ColumnElement:
        """
        Dynamically creates a SQLAlchemy sum expression based on gender and age_group filters.
        """
        
        people_columns_map = self._get_people_columns_map()

        selected_columns = []

        # Determine which genders and age groups to consider
        genders_to_sum = filters.genders if filters.genders else ["male", "female"]
        age_groups_to_sum = filters.age_groups if filters.age_groups else ["under_18", "18_to_29", "30_to_49", "50_to_64", "over_64"]

        for gender in genders_to_sum:
            for age_group in age_groups_to_sum:
                column = people_columns_map.get((gender.lower(), age_group.lower()))
                if column is not None:
                    selected_columns.append(column)
        
        if not selected_columns:
            # If no columns are selected (e.g., invalid filters), sum nothing (results in 0)
            return literal_column("0")

        # Create a sum expression of all selected columns
        sum_expression = selected_columns[0]
        for i in range(1, len(selected_columns)):
            sum_expression += selected_columns[i]
        
        return sum_expression

    def _apply_filters(self, query, filters: AnalyticsFilters, is_aggregation_query: bool = False):
        # Row-level filters (timestamps, devices, polygons)
        if filters.device_ids:
            query = query.filter(CityEyeHumanTable.device_id.in_(filters.device_ids))
        if filters.start_time:
            query = query.filter(CityEyeHumanTable.timestamp >= filters.start_time)
        if filters.end_time:
            # Add 1 hour to end_time to make it inclusive of the last hour
            inclusive_end_time = filters.end_time # + timedelta(hours=1)
            query = query.filter(CityEyeHumanTable.timestamp < inclusive_end_time)
        if filters.polygon_ids_in:
            query = query.filter(CityEyeHumanTable.polygon_id_in.in_(filters.polygon_ids_in))
        if filters.polygon_ids_out:
            query = query.filter(CityEyeHumanTable.polygon_id_out.in_(filters.polygon_ids_out))

        # Day of the week filtering
        if filters.days:
            # Convert day names to DOW numbers (0=Sunday, 1=Monday, ..., 6=Saturday for PostgreSQL EXTRACT(DOW ...))
            # Python's weekday() is 0=Monday, ..., 6=Sunday. So we need to map.
            day_mapping = {
                "sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3,
                "thursday": 4, "friday": 5, "saturday": 6
            }
            dow_numbers = [day_mapping[day.lower()] for day in filters.days if day.lower() in day_mapping]
            if dow_numbers:
                query = query.filter(func.extract('dow', CityEyeHumanTable.timestamp).in_(dow_numbers))
        if filters.hours:
            # Expecting hours like "10:00", "23:00". We only need the hour part.
            hour_numbers = []
            for hour_str in filters.hours:
                try:
                    hour_part = int(hour_str.split(':')[0])
                    hour_numbers.append(hour_part)
                except ValueError:
                    # Handle cases where hour_str might not be in "HH:MM" format or is invalid
                    pass # Or log a warning
            
            if hour_numbers: # Only apply filter if valid hours were parsed
                query = query.filter(func.extract('hour', CityEyeHumanTable.timestamp).in_(hour_numbers))

        return query

    def get_total_count(self, db: Session, *, filters: AnalyticsFilters) -> int:
        sum_expr = self._get_people_sum_expression(filters)
        query = db.query(func.sum(sum_expr).label("total_people"))

        # Apply row-level filters (time, device, polygon, day, hour)
        query = self._apply_filters(query, filters, is_aggregation_query=True)
        result = query.scalar()
        return result or 0

    def get_age_distribution(self, db: Session, *, filters: AnalyticsFilters) -> Dict[str, int]:
        # Get columns map for reuse
        people_columns_map = self._get_people_columns_map()
        
        # Determine which genders to include (respect gender filter)
        genders_to_sum = filters.genders if filters.genders else ["male", "female"]
        
        # Determine which age groups to include (respect age_groups filter)
        age_groups_to_sum = filters.age_groups if filters.age_groups else ["under_18", "18_to_29", "30_to_49", "50_to_64", "over_64"]
        
        # Build query with dynamic columns based on filters
        sum_expressions = {}
        for age_group in ["under_18", "18_to_29", "30_to_49", "50_to_64", "over_64"]:
            if age_group in age_groups_to_sum:
                columns_to_sum = []
                for gender in genders_to_sum:
                    column = people_columns_map.get((gender.lower(), age_group.lower()))
                    if column is not None:
                        columns_to_sum.append(column)
                
                if columns_to_sum:
                    sum_expr = columns_to_sum[0]
                    for col in columns_to_sum[1:]:
                        sum_expr += col
                    # Map age group names for output
                    output_key = f"age_{age_group}" if age_group != "under_18" and age_group != "over_64" else age_group
                    sum_expressions[output_key] = func.sum(sum_expr).label(output_key)
        
        if not sum_expressions:
            # Return all zeros if no valid columns
            return {
                "under_18": 0, "age_18_to_29": 0, "age_30_to_49": 0, "age_50_to_64": 0, "over_64": 0
            }
        
        query = db.query(*sum_expressions.values())
        query = self._apply_filters(query, filters)
        result = query.first()
        
        # Build result dict with all age groups, defaulting to 0 for excluded ones
        output = {
            "under_18": 0, "age_18_to_29": 0, "age_30_to_49": 0, "age_50_to_64": 0, "over_64": 0
        }
        
        if result:
            for key in sum_expressions.keys():
                output[key] = getattr(result, key, 0) or 0
        
        return output

    def get_gender_distribution(self, db: Session, *, filters: AnalyticsFilters) -> Dict[str, int]:
        # Get columns map for reuse
        people_columns_map = self._get_people_columns_map()
        
        # Determine which genders to include (respect gender filter)
        genders_to_sum = filters.genders if filters.genders else ["male", "female"]
        
        # Determine which age groups to include (respect age_groups filter)
        age_groups_to_sum = filters.age_groups if filters.age_groups else ["under_18", "18_to_29", "30_to_49", "50_to_64", "over_64"]
        
        # Build query with dynamic columns based on filters
        sum_expressions = {}
        for gender in ["male", "female"]:
            if gender in genders_to_sum:
                columns_to_sum = []
                for age_group in age_groups_to_sum:
                    column = people_columns_map.get((gender.lower(), age_group.lower()))
                    if column is not None:
                        columns_to_sum.append(column)
                
                if columns_to_sum:
                    sum_expr = columns_to_sum[0]
                    for col in columns_to_sum[1:]:
                        sum_expr += col
                    sum_expressions[gender] = func.sum(sum_expr).label(gender)
        
        if not sum_expressions:
            # Return all zeros if no valid columns
            return {"male": 0, "female": 0}
        
        query = db.query(*sum_expressions.values())
        query = self._apply_filters(query, filters)
        result = query.first()
        
        # Build result dict with all genders, defaulting to 0 for excluded ones
        output = {"male": 0, "female": 0}
        
        if result:
            for gender in sum_expressions.keys():
                output[gender] = getattr(result, gender, 0) or 0
        
        return output

    def get_age_gender_distribution(self, db: Session, *, filters: AnalyticsFilters) -> Dict[str, int]:
        # Get columns map for reuse
        people_columns_map = self._get_people_columns_map()
        
        # Determine which genders and age groups to include
        genders_to_sum = filters.genders if filters.genders else ["male", "female"]
        age_groups_to_sum = filters.age_groups if filters.age_groups else ["under_18", "18_to_29", "30_to_49", "50_to_64", "over_64"]
        
        # Build query with dynamic columns based on filters
        sum_expressions = {}
        
        # Define all possible combinations for consistent output structure
        all_combinations = [
            ("male", "under_18", "male_under_18", "male_less_than_18"),
            ("female", "under_18", "female_under_18", "female_less_than_18"),
            ("male", "18_to_29", "male_18_to_29", "male_18_to_29"),
            ("female", "18_to_29", "female_18_to_29", "female_18_to_29"),
            ("male", "30_to_49", "male_30_to_49", "male_30_to_49"),
            ("female", "30_to_49", "female_30_to_49", "female_30_to_49"),
            ("male", "50_to_64", "male_50_to_64", "male_50_to_64"),
            ("female", "50_to_64", "female_50_to_64", "female_50_to_64"),
            ("male", "over_64", "male_65_plus", "male_65_plus"),
            ("female", "over_64", "female_65_plus", "female_65_plus"),
        ]
        
        for gender, age_group, output_key, _ in all_combinations:
            if gender in genders_to_sum and age_group in age_groups_to_sum:
                column = people_columns_map.get((gender.lower(), age_group.lower()))
                if column is not None:
                    sum_expressions[output_key] = func.sum(column).label(output_key)
        
        if not sum_expressions:
            # Return all zeros if no valid columns
            return {
                "male_under_18": 0, "female_under_18": 0, "male_18_to_29": 0, "female_18_to_29": 0,
                "male_30_to_49": 0, "female_30_to_49": 0, "male_50_to_64": 0, "female_50_to_64": 0,
                "male_65_plus": 0, "female_65_plus": 0
            }
        
        query = db.query(*sum_expressions.values())
        query = self._apply_filters(query, filters)
        result = query.first()
        
        # Build result dict with all combinations, defaulting to 0 for excluded ones
        output = {
            "male_under_18": 0, "female_under_18": 0, "male_18_to_29": 0, "female_18_to_29": 0,
            "male_30_to_49": 0, "female_30_to_49": 0, "male_50_to_64": 0, "female_50_to_64": 0,
            "male_65_plus": 0, "female_65_plus": 0
        }
        
        if result:
            for key in sum_expressions.keys():
                output[key] = getattr(result, key, 0) or 0
        
        return output

    def get_hourly_distribution(self, db: Session, *, filters: AnalyticsFilters) -> List[Dict[str, Any]]:
        hour_part = func.extract('hour', CityEyeHumanTable.timestamp).label("hour")
        sum_expr = self._get_people_sum_expression(filters)
        query = db.query(
            hour_part,
            func.sum(sum_expr).label("count")
        )
        # Apply row-level filters (time, device, polygon, day, hour already applied in _apply_filters)
        query = self._apply_filters(query, filters, is_aggregation_query=True)
        query = query.group_by(hour_part).order_by(hour_part)

        results = query.all()
        return [{"hour": int(r.hour), "count": r.count or 0} for r in results]

    def get_time_series_data(self, db: Session, *, filters: AnalyticsFilters, interval_minutes: int = 60) -> List[Dict[str, Any]]:
        sum_expr = self._get_people_sum_expression(filters)

        if db.bind.dialect.name == 'sqlite': # type: ignore
            # SQLite does not have date_trunc, approximate by formatting
            time_bucket = func.strftime('%Y-%m-%d %H:00:00', CityEyeHumanTable.timestamp).label("time_bucket")
        else: # For PostgreSQL
            # This truncates to the hour. For other intervals, this would need to be more complex.
            time_bucket = func.date_trunc('hour', CityEyeHumanTable.timestamp).label("time_bucket")

        query = db.query(
            time_bucket,
            func.sum(sum_expr).label("count")
        )
        # Apply row-level filters (time, device, polygon, day, hour already applied in _apply_filters)
        query = self._apply_filters(query, filters, is_aggregation_query=True)
        query = query.group_by(time_bucket).order_by(time_bucket)

        results = query.all()
        return [{"timestamp": r.time_bucket, "count": r.count or 0} for r in results]

    # =============================================================================
    # TRAFFIC ANALYTICS METHODS
    # =============================================================================

    def _get_vehicles_sum_expression(self, filters: TrafficAnalyticsFilters) -> ColumnElement:
        """
        Dynamically creates a SQLAlchemy sum expression based on vehicle_types filters.
        """
        
        vehicle_columns_map = {
            "large": CityEyeTrafficTable.large,
            "normal": CityEyeTrafficTable.normal,
            "bicycle": CityEyeTrafficTable.bicycle,
            "motorcycle": CityEyeTrafficTable.motorcycle,
        }

        selected_columns = []

        # Determine which vehicle types to consider
        vehicle_types_to_sum = filters.vehicle_types if filters.vehicle_types else ["large", "normal", "bicycle", "motorcycle"]

        for vehicle_type in vehicle_types_to_sum:
            column = vehicle_columns_map.get(vehicle_type.lower())
            if column is not None:
                selected_columns.append(column)
        
        if not selected_columns:
            # If no columns are selected (e.g., invalid filters), sum nothing (results in 0)
            return literal_column("0")

        # Create a sum expression of all selected columns
        sum_expression = selected_columns[0]
        for i in range(1, len(selected_columns)):
            sum_expression += selected_columns[i]
        
        return sum_expression
    
    def _apply_traffic_filters(self, query, filters: TrafficAnalyticsFilters, is_aggregation_query: bool = False):
        # Row-level filters (timestamps, devices, polygons)
        if filters.device_ids:
            query = query.filter(CityEyeTrafficTable.device_id.in_(filters.device_ids))
        if filters.start_time:
            query = query.filter(CityEyeTrafficTable.timestamp >= filters.start_time)
        if filters.end_time:
            # Add 1 hour to end_time to make it inclusive of the last hour
            inclusive_end_time = filters.end_time # + timedelta(hours=1)
            query = query.filter(CityEyeTrafficTable.timestamp < inclusive_end_time)
        if filters.polygon_ids_in:
            query = query.filter(CityEyeTrafficTable.polygon_id_in.in_(filters.polygon_ids_in))
        if filters.polygon_ids_out:
            query = query.filter(CityEyeTrafficTable.polygon_id_out.in_(filters.polygon_ids_out))

        # Day of the week filtering
        if filters.days:
            # Convert day names to DOW numbers (0=Sunday, 1=Monday, ..., 6=Saturday for PostgreSQL EXTRACT(DOW ...))
            day_mapping = {
                "sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3,
                "thursday": 4, "friday": 5, "saturday": 6
            }
            dow_numbers = [day_mapping[day.lower()] for day in filters.days if day.lower() in day_mapping]
            if dow_numbers:
                query = query.filter(func.extract('dow', CityEyeTrafficTable.timestamp).in_(dow_numbers))
        
        if filters.hours:
            # Expecting hours like "10:00", "23:00". We only need the hour part.
            hour_numbers = []
            for hour_str in filters.hours:
                try:
                    hour_part = int(hour_str.split(':')[0])
                    hour_numbers.append(hour_part)
                except ValueError:
                    # Handle cases where hour_str might not be in "HH:MM" format or is invalid
                    pass # Or log a warning
            
            if hour_numbers: # Only apply filter if valid hours were parsed
                query = query.filter(func.extract('hour', CityEyeTrafficTable.timestamp).in_(hour_numbers))

        return query

    def get_total_traffic_count(self, db: Session, *, filters: TrafficAnalyticsFilters) -> int:
        sum_expr = self._get_vehicles_sum_expression(filters)
        query = db.query(func.sum(sum_expr).label("total_vehicles"))

        # Apply row-level filters (time, device, polygon, day, hour)
        query = self._apply_traffic_filters(query, filters, is_aggregation_query=True)
        result = query.scalar()
        return result or 0

    def get_vehicle_type_distribution(self, db: Session, *, filters: TrafficAnalyticsFilters) -> Dict[str, int]:
        # Get vehicle columns map
        vehicle_columns_map = {
            "large": CityEyeTrafficTable.large,
            "normal": CityEyeTrafficTable.normal,
            "bicycle": CityEyeTrafficTable.bicycle,
            "motorcycle": CityEyeTrafficTable.motorcycle,
        }
        
        # Determine which vehicle types to include (respect vehicle_types filter)
        # Convert to lowercase for case-insensitive matching
        vehicle_types_to_sum = [vt.lower() for vt in filters.vehicle_types] if filters.vehicle_types else ["large", "normal", "bicycle", "motorcycle"]
        
        # Build query with dynamic columns based on filters
        sum_expressions = {}
        for vehicle_type in ["large", "normal", "bicycle", "motorcycle"]:
            if vehicle_type in vehicle_types_to_sum:
                column = vehicle_columns_map.get(vehicle_type)
                if column is not None:
                    sum_expressions[vehicle_type] = func.sum(column).label(vehicle_type)
        
        if not sum_expressions:
            # Return all zeros if no valid columns
            return {
                "large": 0, "normal": 0, "bicycle": 0, "motorcycle": 0
            }
        
        query = db.query(*sum_expressions.values())
        query = self._apply_traffic_filters(query, filters)
        result = query.first()
        
        # Build result dict with all vehicle types, defaulting to 0 for excluded ones
        output = {
            "large": 0, "normal": 0, "bicycle": 0, "motorcycle": 0
        }
        
        if result:
            for vehicle_type in sum_expressions.keys():
                output[vehicle_type] = getattr(result, vehicle_type, 0) or 0
        
        return output

    def get_hourly_traffic_distribution(self, db: Session, *, filters: TrafficAnalyticsFilters) -> List[Dict[str, Any]]:
        hour_part = func.extract('hour', CityEyeTrafficTable.timestamp).label("hour")
        sum_expr = self._get_vehicles_sum_expression(filters)
        query = db.query(
            hour_part,
            func.sum(sum_expr).label("count")
        )
        # Apply row-level filters (time, device, polygon, day, hour already applied in _apply_traffic_filters)
        query = self._apply_traffic_filters(query, filters, is_aggregation_query=True)
        query = query.group_by(hour_part).order_by(hour_part)

        results = query.all()
        return [{"hour": int(r.hour), "count": r.count or 0} for r in results]
    
    def get_traffic_time_series_data(self, db: Session, *, filters: TrafficAnalyticsFilters, interval_minutes: int = 60) -> List[Dict[str, Any]]:
        sum_expr = self._get_vehicles_sum_expression(filters)

        if db.bind.dialect.name == 'sqlite': # type: ignore
            # SQLite does not have date_trunc, approximate by formatting
            time_bucket = func.strftime('%Y-%m-%d %H:00:00', CityEyeTrafficTable.timestamp).label("time_bucket")
        else: # For PostgreSQL
            # This truncates to the hour. For other intervals, this would need to be more complex.
            time_bucket = func.date_trunc('hour', CityEyeTrafficTable.timestamp).label("time_bucket")

        query = db.query(
            time_bucket,
            func.sum(sum_expr).label("count")
        )
        # Apply row-level filters (time, device, polygon, day, hour already applied in _apply_traffic_filters)
        query = self._apply_traffic_filters(query, filters, is_aggregation_query=True)
        query = query.group_by(time_bucket).order_by(time_bucket)

        results = query.all()
        return [{"timestamp": r.time_bucket, "count": r.count or 0} for r in results]


    def get_direction_counts(self, db: Session, *, filters: AnalyticsFilters) -> Dict[str, Dict[str, int]]:
        """
        Get in/out counts per polygon, excluding 'loss' counts.
        Returns: Dict with polygon_id as key and {'in_count': x, 'out_count': y} as value
        """
        # Get the sum expression for people count
        sum_expr = self._get_people_sum_expression(filters)
        
        # Query for IN counts (when polygon appears in polygon_id_in)
        in_query = db.query(
            CityEyeHumanTable.polygon_id_in.label("polygon_id"),
            func.sum(sum_expr).label("count")
        ).filter(
            CityEyeHumanTable.polygon_id_in != 'loss'  # Exclude loss
        )
        
        # Apply filters
        in_query = self._apply_filters(in_query, filters, is_aggregation_query=True)
        in_query = in_query.group_by(CityEyeHumanTable.polygon_id_in)
        
        # Query for OUT counts (when polygon appears in polygon_id_out)
        out_query = db.query(
            CityEyeHumanTable.polygon_id_out.label("polygon_id"),
            func.sum(sum_expr).label("count")
        ).filter(
            CityEyeHumanTable.polygon_id_out != 'loss'  # Exclude loss
        )
        
        # Apply filters
        out_query = self._apply_filters(out_query, filters, is_aggregation_query=True)
        out_query = out_query.group_by(CityEyeHumanTable.polygon_id_out)
        
        # Execute queries
        in_results = in_query.all()
        out_results = out_query.all()
        
        # Build result dictionary
        result = {}
        
        # Process IN counts
        for row in in_results:
            polygon_id = str(row.polygon_id)
            if polygon_id not in result:
                result[polygon_id] = {'in_count': 0, 'out_count': 0}
            result[polygon_id]['in_count'] = int(row.count or 0)
        
        # Process OUT counts
        for row in out_results:
            polygon_id = str(row.polygon_id)
            if polygon_id not in result:
                result[polygon_id] = {'in_count': 0, 'out_count': 0}
            result[polygon_id]['out_count'] = int(row.count or 0)
        
        return result


crud_city_eye_analytics = CRUDCityEyeAnalytics()