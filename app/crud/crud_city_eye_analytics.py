from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer, Date, Time, case, and_
from sqlalchemy.dialects.postgresql import INTERVAL
from app.models.services.city_eye.human_table import City_Eye_human_table
from app.schemas.services.city_eye_analytics import AnalyticsFilters

class CRUDCityEyeAnalytics:

    def _apply_filters(self, query, filters: AnalyticsFilters):
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

        # Gender and Age filters need to be applied carefully
        # For sum operations, we can sum the relevant columns
        # For counts that depend on these, it might be more complex or require subqueries
        # For now, these filters are primarily for high-level filtering if the frontend sends them
        # and the query itself will handle the specific aggregation based on the route.

        return query

    def get_total_count(self, db: Session, *, filters: AnalyticsFilters) -> int:
        query = db.query(
            func.sum(
                City_Eye_human_table.male_less_than_18 +
                City_Eye_human_table.female_less_than_18 +
                City_Eye_human_table.male_18_to_29 +
                City_Eye_human_table.female_18_to_29 +
                City_Eye_human_table.male_30_to_49 +
                City_Eye_human_table.female_30_to_49 +
                City_Eye_human_table.male_50_to_64 +
                City_Eye_human_table.female_50_to_64 +
                City_Eye_human_table.male_65_plus +
                City_Eye_human_table.female_65_plus
            ).label("total_people")
        )
        query = self._apply_filters(query, filters)
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
        total_people_expr = (
                City_Eye_human_table.male_less_than_18 + City_Eye_human_table.female_less_than_18 +
                City_Eye_human_table.male_18_to_29 + City_Eye_human_table.female_18_to_29 +
                City_Eye_human_table.male_30_to_49 + City_Eye_human_table.female_30_to_49 +
                City_Eye_human_table.male_50_to_64 + City_Eye_human_table.female_50_to_64 +
                City_Eye_human_table.male_65_plus + City_Eye_human_table.female_65_plus
            )

        query = db.query(
            hour_part,
            func.sum(total_people_expr).label("count")
        )
        query = self._apply_filters(query, filters)
        query = query.group_by(hour_part).order_by(hour_part)

        results = query.all()
        return [{"hour": int(r.hour), "count": r.count or 0} for r in results]

    def get_time_series_data(self, db: Session, *, filters: AnalyticsFilters, interval_minutes: int = 60) -> List[Dict[str, Any]]:
        # For simplicity, we'll group by hour for now if interval is 60
        total_people_expr = (
            City_Eye_human_table.male_less_than_18 + City_Eye_human_table.female_less_than_18 +
            City_Eye_human_table.male_18_to_29 + City_Eye_human_table.female_18_to_29 +
            City_Eye_human_table.male_30_to_49 + City_Eye_human_table.female_30_to_49 +
            City_Eye_human_table.male_50_to_64 + City_Eye_human_table.female_50_to_64 +
            City_Eye_human_table.male_65_plus + City_Eye_human_table.female_65_plus
        )

        # Group by hour: Truncate timestamp to the hour
        # This assumes the `timestamp` column is of a type that supports date_trunc
        if db.bind.dialect.name == 'sqlite':
            time_bucket = func.strftime('%Y-%m-%d %H:00:00', City_Eye_human_table.timestamp).label("time_bucket")
        else:
            time_bucket = func.date_trunc('hour', City_Eye_human_table.timestamp).label("time_bucket")


        query = db.query(
            time_bucket,
            func.sum(total_people_expr).label("count")
        )
        query = self._apply_filters(query, filters)
        query = query.group_by(time_bucket).order_by(time_bucket)

        results = query.all()
        return [{"timestamp": r.time_bucket, "count": r.count or 0} for r in results]

crud_city_eye_analytics = CRUDCityEyeAnalytics()