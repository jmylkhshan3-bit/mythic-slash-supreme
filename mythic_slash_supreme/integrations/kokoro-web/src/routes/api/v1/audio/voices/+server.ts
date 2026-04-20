import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { voices } from "$lib/shared/resources";
import { authenticate } from "$lib/server/authenticate";

/**
 * @openapi
 * /api/v1/audio/voices:
 *   get:
 *     summary: List available voices
 *     tags:
 *       - Speech
 *     responses:
 *       200:
 *         description: List of available voices
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 type: object
 *                 properties:
 *                   id:
 *                     type: string
 *                     description: Voice ID
 *                   name:
 *                     type: string
 *                     description: Voice name
 *                   gender:
 *                     type: string
 *                     description: Voice gender
 *                   targetQuality:
 *                     type: string
 *                     description: Voice target quality
 *                   overallGrade:
 *                     type: string
 *                     description: Voice overall grade
 *                   lang:
 *                     type: object
 *                     properties:
 *                       id:
 *                         type: string
 *                         description: Language ID
 *                       name:
 *                         type: string
 *                         description: Language name
 *             example:
 *               - id: "af_heart"
 *                 name: "Heart"
 *                 gender: "Female"
 *                 targetQuality: "A"
 *                 overallGrade: "A"
 *                 lang:
 *                   id: "en-us"
 *                   name: "English (US)"
 */

export const GET: RequestHandler = async ({ request }) => {
  try {
    authenticate(request);
  } catch (e: any) {
    return json({ message: e.message }, { status: 401 });
  }

  return json(voices);
};
