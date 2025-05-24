from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer, Date, Time, case, and_, or_
from sqlalchemy.dialects.postgresql import INTERVAL, TIME
from sqlalchemy.sql.expression import literal_column, ColumnElement
from app.models.services.city_eye.human_table import City_Eye_human_table
from app.schemas.services.city_eye_analytics import AnalyticsFilters
from datetime import datetime, time as dt_time

class CRUDCityEyeAnalytics:

    def _get_people_sum_expression(self, filters: AnalyticsFilters) -> ColumnElement:
        """
        Dynamically creates a SQLAlchemy sum expression based on gender and age_group filters.
        """
        
        people_columns_map = {
            ("male", "under_18"): City_Eye_human_table.male_less_than_18,
            ("female", "under_18"): City_Eye_human_table.female_less_than_18,
            ("male", "18_to_29"): City_Eye_human_table.male_18_to_29,
            ("female", "18_to_29"): City_Eye_human_table.female_18_to_29,
            ("male", "30_to_49"): City_Eye_human_table.male_30_to_49,
            ("female", "30_to_49"): City_Eye_human_table.female_30_to_49,
            ("male", "50_to_64"): City_Eye_human_table.male_50_to_64,
            ("female", "50_to_64"): City_Eye_human_table.female_50_to_64,
            ("male", "over_64"): City_Eye_human_table.male_65_plus, # Assuming "over_64" maps to "65_plus" columns
            ("female", "over_64"): City_Eye_human_table.female_65_plus,
        }

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
            query = query.filter(City_Eye_human_table.device_id.in_(filters.device_ids))
        if filters.start_time:
            query = query.filter(City_Eye_human_table.timestamp >= filters.start_time)
        if filters.end_time:
            # Add 1 hour to end_time to make it inclusive of the last hour
            inclusive_end_time = filters.end_time # + timedelta(hours=1)
            query = query.filter(City_Eye_human_table.timestamp < inclusive_end_time)
        if filters.polygon_ids_in:
            query = query.filter(City_Eye_human_table.polygon_id_in.in_(filters.polygon_ids_in))
        if filters.polygon_ids_out:
            query = query.filter(City_Eye_human_table.polygon_id_out.in_(filters.polygon_ids_out))

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
                query = query.filter(func.extract('dow', City_Eye_human_table.timestamp).in_(dow_numbers))
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
                query = query.filter(func.extract('hour', City_Eye_human_table.timestamp).in_(hour_numbers))

        return query

    def _apply_age_gender_filter(self, query, filters: AnalyticsFilters):
        pass 


    def get_total_count(self, db: Session, *, filters: AnalyticsFilters) -> int:
        sum_expr = self._get_people_sum_expression(filters)
        query = db.query(func.sum(sum_expr).label("total_people"))

        # Apply row-level filters (time, device, polygon, day, hour)
        query = self._apply_filters(query, filters, is_aggregation_query=True)
        result = query.scalar()
        return result or 0

    def get_age_distribution(self, db: Session, *, filters: AnalyticsFilters) -> Dict[str, int]:
        query = db.query(
            func.sum(City_Eye_human_table.male_less_than_18 + City_Eye_human_table.female_less_than_18).label("under_18"),
            func.sum(City_Eye_human_table.male_18_to_29 + City_Eye_human_table.female_18_to_29).label("age_18_to_29"),
            func.sum(City_Eye_human_table.male_30_to_49 + City_Eye_human_table.female_30_to_49).label("age_30_to_49"),
            func.sum(City_Eye_human_table.male_50_to_64 + City_Eye_human_table.female_50_to_64).label("age_50_to_64"),
            func.sum(City_Eye_human_table.male_65_plus + City_Eye_human_table.female_65_plus).label("over_64")
        )
        query = self._apply_filters(query, filters)
        result = query.first()
        return {
            "under_18": result.under_18 or 0,
            "age_18_to_29": result.age_18_to_29 or 0,
            "age_30_to_49": result.age_30_to_49 or 0,
            "age_50_to_64": result.age_50_to_64 or 0,
            "over_64": result.over_64 or 0,
        } if result else {
            "under_18": 0, "age_18_to_29": 0, "age_30_to_49": 0, "age_50_to_64": 0, "over_64": 0
        }

    def get_gender_distribution(self, db: Session, *, filters: AnalyticsFilters) -> Dict[str, int]:
        query = db.query(
            func.sum(
                City_Eye_human_table.male_less_than_18 +
                City_Eye_human_table.male_18_to_29 +
                City_Eye_human_table.male_30_to_49 +
                City_Eye_human_table.male_50_to_64 +
                City_Eye_human_table.male_65_plus
            ).label("male"),
            func.sum(
                City_Eye_human_table.female_less_than_18 +
                City_Eye_human_table.female_18_to_29 +
                City_Eye_human_table.female_30_to_49 +
                City_Eye_human_table.female_50_to_64 +
                City_Eye_human_table.female_65_plus
            ).label("female")
        )
        query = self._apply_filters(query, filters)
        result = query.first()
        return {
            "male": result.male or 0,
            "female": result.female or 0,
        } if result else {"male": 0, "female": 0}

    def get_age_gender_distribution(self, db: Session, *, filters: AnalyticsFilters) -> Dict[str, int]:
        query = db.query(
            func.sum(City_Eye_human_table.male_less_than_18).label("male_under_18"),
            func.sum(City_Eye_human_table.female_less_than_18).label("female_under_18"),
            func.sum(City_Eye_human_table.male_18_to_29).label("male_18_to_29"),
            func.sum(City_Eye_human_table.female_18_to_29).label("female_18_to_29"),
            func.sum(City_Eye_human_table.male_30_to_49).label("male_30_to_49"),
            func.sum(City_Eye_human_table.female_30_to_49).label("female_30_to_49"),
            func.sum(City_Eye_human_table.male_50_to_64).label("male_50_to_64"),
            func.sum(City_Eye_human_table.female_50_to_64).label("female_50_to_64"),
            func.sum(City_Eye_human_table.male_65_plus).label("male_65_plus"),
            func.sum(City_Eye_human_table.female_65_plus).label("female_65_plus")
        )
        query = self._apply_filters(query, filters)
        result = query.first()
        return {
            "male_under_18": result.male_under_18 or 0,
            "female_under_18": result.female_under_18 or 0,
            "male_18_to_29": result.male_18_to_29 or 0,
            "female_18_to_29": result.female_18_to_29 or 0,
            "male_30_to_49": result.male_30_to_49 or 0,
            "female_30_to_49": result.female_30_to_49 or 0,
            "male_50_to_64": result.male_50_to_64 or 0,
            "female_50_to_64": result.female_50_to_64 or 0,
            "male_65_plus": result.male_65_plus or 0,
            "female_65_plus": result.female_65_plus or 0,
        } if result else {
            "male_under_18": 0, "female_under_18": 0, "male_18_to_29": 0, "female_18_to_29": 0,
            "male_30_to_49": 0, "female_30_to_49": 0, "male_50_to_64": 0, "female_50_to_64": 0,
            "male_65_plus": 0, "female_65_plus": 0
        }

    def get_hourly_distribution(self, db: Session, *, filters: AnalyticsFilters) -> List[Dict[str, Any]]:
        hour_part = func.extract('hour', City_Eye_human_table.timestamp).label("hour")
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
            time_bucket = func.strftime('%Y-%m-%d %H:00:00', City_Eye_human_table.timestamp).label("time_bucket")
        else: # For PostgreSQL
            # This truncates to the hour. For other intervals, this would need to be more complex.
            time_bucket = func.date_trunc('hour', City_Eye_human_table.timestamp).label("time_bucket")


        query = db.query(
            time_bucket,
            func.sum(sum_expr).label("count")
        )
        # Apply row-level filters (time, device, polygon, day, hour already applied in _apply_filters)
        query = self._apply_filters(query, filters, is_aggregation_query=True)
        query = query.group_by(time_bucket).order_by(time_bucket)

        results = query.all()
        return [{"timestamp": r.time_bucket, "count": r.count or 0} for r in results]


crud_city_eye_analytics = CRUDCityEyeAnalytics()