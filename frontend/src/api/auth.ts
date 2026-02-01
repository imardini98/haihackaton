import { requestJson } from './http';

export type AuthResponse = {
  access_token: string;
  token_type?: string;
  user_id: string;
  email: string;
};

export type SignInRequest = {
  email: string;
  password: string;
};

export async function signIn(payload: SignInRequest): Promise<AuthResponse> {
  return requestJson<AuthResponse>('/api/v1/auth/signin', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

