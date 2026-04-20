import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { langs } from "$lib/shared/resources";
import { authenticate } from "$lib/server/authenticate";

/**
 * @openapi
 * /api/v1/audio/langs:
 *   get:
 *     summary: List available languages
 *     tags:
 *       - Speech
 *     responses:
 *       200:
 *         description: List of available languages
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 type: object
 *                 properties:
 *                   id:
 *                     type: string
 *                     description: Language ID
 *                   name:
 *                     type: string
 *                     description: Language name
 *             example:
 *               - id: "en"
 *                 name: "English"
 */

export const GET: RequestHandler = async ({ request }) => {
  try {
    authenticate(request);
  } catch (e: any) {
    return json({ message: e.message }, { status: 401 });
  }

  return json(langs);
};
