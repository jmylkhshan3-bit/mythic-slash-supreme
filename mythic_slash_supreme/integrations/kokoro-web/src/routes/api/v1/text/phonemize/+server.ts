import { error, json } from "@sveltejs/kit";
import zod from "zod";
import { fromError } from "zod-validation-error";
import type { RequestHandler } from "./$types";
import { phonemize } from "$lib/shared/phonemizer";
import { langsIds, type LangId } from "$lib/shared/resources";
import { authenticate } from "$lib/server/authenticate";

/**
 * @openapi
 * /api/v1/text/phonemize:
 *   post:
 *     summary: Generate text phonemes
 *     tags:
 *       - Text
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             properties:
 *               lang:
 *                 type: string
 *                 description: Language ID
 *               input:
 *                 type: string
 *                 description: Input text to phonemize
 *     responses:
 *       200:
 *         description: Phonemes of the input text
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 phonemes:
 *                   type: string
 *                   description: Phonemes of the input text
 *             example:
 *               phonemes: "..."
 *       400:
 *         description: Validation error
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 message:
 *                   type: string
 *                   description: Error message
 *             example:
 *               message: "Validation error ..."
 */

const schema = zod.object({
  lang: zod.string().refine((val) => langsIds.includes(val as LangId), {
    message: `Voice not found, use one of: ${langsIds.join(", ")}`,
  }),
  input: zod.string(),
});

export const POST: RequestHandler = async ({ request }) => {
  try {
    authenticate(request);
  } catch (e: any) {
    return json({ message: e.message }, { status: 401 });
  }

  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) {
    return error(400, fromError(parsed.error).toString());
  }

  const phonemes = await phonemize(parsed.data.input, parsed.data.lang);
  return json({ phonemes });
};
