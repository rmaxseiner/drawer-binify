export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface DrawerDimensions {
  name: string;
  width: number;
  depth: number;
  height: number;
}

export interface Bin {
  id: number;
  width: number;
  depth: number;
  height: number;
  is_standard: boolean;
  drawer_id: number;
}

export interface BinOptions {
  standard_bins: Bin[];
  non_standard_bins: Bin[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}