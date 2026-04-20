import { env } from "$env/dynamic/private";

/**
 * Authenticate the request by checking the Authorization header.
 * If the header is missing or the token is invalid, an error is thrown.
 *
 * @param request - Incoming request
 */
export function authenticate(request: Request) {
  if (!env.KW_SECRET_API_KEY) return;

  let authToken = request.headers.get("Authorization");
  if (!authToken) {
    throw new Error("Authorization header is missing");
  }

  authToken = authToken.replace("Bearer ", "");
  authToken = authToken.replace("bearer ", "");

  if (authToken !== env.KW_SECRET_API_KEY) {
    throw new Error("Unauthorized");
  }
}
