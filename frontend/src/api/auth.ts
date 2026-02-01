import { requestJson } from './http';

export type AuthResponse = {
  access_token: string;
  token_type?: string;
  user_id: string;
  email: string;
};

export type UserResponse = {
  id: string;
  email: string;
};

export type SignInRequest = {
  email: string;
  password: string;
};

export type SignUpRequest = {
  email: string;
  password: string;
};

export async function signIn(payload: SignInRequest): Promise<AuthResponse> {
  return requestJson<AuthResponse>('/api/v1/auth/signin', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function signUp(payload: SignUpRequest): Promise<AuthResponse> {
  return requestJson<AuthResponse>('/api/v1/auth/signup', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getMe(accessToken: string): Promise<UserResponse> {
  return requestJson<UserResponse>('/api/v1/auth/me', {
    method: 'GET',
    token: accessToken,
  });
}

