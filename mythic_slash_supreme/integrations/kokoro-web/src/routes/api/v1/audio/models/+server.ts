import { json } from "@sveltejs/kit";
import type { RequestHandler } from "./$types";
import { models } from "$lib/shared/resources";
import { authenticate } from "$lib/server/authenticate";

/**
 * @openapi
 * /api/v1/audio/models:
 *   get:
 *     summary: List available models
 *     tags:
 *       - Speech
 *     responses:
 *       200:
 *         description: List of available models
 *         content:
 *           application/json:
 *             schema:
 *               type: array
 *               items:
 *                 type: object
 *                 properties:
 *                   id:
 *                     type: string
 *                     description: Model ID
 *                   quantization:
 *                     type: string
 *                     description: Model quantization type
 *                   size:
 *                     type: string
 *                     description: Model size in MB
 *             example:
 *               - id: "model"
 *                 quantization: "fp32"
 *                 size: "326 MB"
 */

export const GET: RequestHandler = async ({ request }) => {
  try {
    authenticate(request);
  } catch (e: any) {
    return json({ message: e.message }, { status: 401 });
  }

  return json(models);
};
