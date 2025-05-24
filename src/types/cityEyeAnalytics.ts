export interface AnalyticsFilters {
    device_ids?: string[];
    start_time: string;
    end_time: string;
    polygon_ids_in?: string[];
    polygon_ids_out?: string[];
    genders?: string[]; // e.g., ["male", "female"]
    age_groups?: string[]; // e.g., ["under_18", "18_to_29"]
  }

export interface TotalCount {
    total_count: number;
  }

export interface AgeDistribution {
    under_18: number;
    age_18_to_29: number;
    age_30_to_49: number;
    age_50_to_64: number;
    over_64: number;
}

export interface GenderDistribution {
    male: number;
    female: number;
}

export interface AgeGenderDistribution {
    male_under_18: number;
    female_under_18: number;
    male_18_to_29: number;
    female_18_to_29: number;
    male_30_to_49: number;
    female_30_to_49: number;
    male_50_to_64: number;
    female_50_to_64: number;
    male_65_plus: number;
    female_65_plus: number;
}

export interface HourlyCount {
    hour: number;
    count: number;
}

export interface TimeSeriesData {
    timestamp: string; // ISO 8601 format
    count: number;
}

export interface CityEyeAnalyticsData {
    total_count?: TotalCount;
    age_distribution?: AgeDistribution;
    gender_distribution?: GenderDistribution;
    age_gender_distribution?: AgeGenderDistribution;
    hourly_distribution?: HourlyCount[];
    time_series_data?: TimeSeriesData[];
}

export type CityEyeAnalyticsResponse = CityEyeAnalyticsData;