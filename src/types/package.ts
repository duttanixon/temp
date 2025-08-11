// src/types/package.ts

/**
 * Model association for packages
 */
export interface ModelAssociation {
  model_id: string;
}

/**
 * Solution Package type definition
 * Represents a deployable package for a solution
 */
export interface SolutionPackage {
  package_id: string;
  name: string;
  version: string;
  description: string;
  solution_id: string;
  solution_name: string;
  s3_bucket: string;
  s3_key: string;
  created_at: string | null;
  updated_at: string | null;
  model_associations: ModelAssociation[];
}

/**
 * API response for package list
 */
export interface PackageListResponse {
  total: number;
  packages: SolutionPackage[];
}

/**
 * Package filter parameters
 */
export interface PackageFilters {
  solution_name?: string;
  solution_id?: string;
  skip?: number;
  limit?: number;
}
