import { env } from "$env/dynamic/public";
import { dev } from "$app/environment";

/**
 * Umami is a web analytics tool that is focused on user privacy
 * and simplicity. It does not use cookies and it does not collect
 * personal data.
 *
 * This module provides a simple interface to load the Umami script
 * and track events.
 *
 * This module respects the KW_PUBLIC_NO_TRACK environment variable
 * and the development mode, if the tracking is disabled or the app
 * is running in development mode it will not load the script or
 * track events.
 */

const UMAMI_SCRIPT_URL = "https://anl.worldscode.com/script.js";
const UMAMI_WEBSITE_ID = "e39763f4-3409-437e-ab78-25239fcd6d6e";

/**
 * Check if the tracking should be enabled or not based on
 * the KW_PUBLIC_NO_TRACK environment variable and if the
 * application is running in development mode
 */
function shouldTrack(): boolean {
  if (env.KW_PUBLIC_NO_TRACK === "true") return false;
  if (dev) return false;
  return true;
}

/**
 * Load the Umami analytics anonymous tracking script
 *
 * It will **not** load the script if:
 *
 * - The tracking is disabled
 * - The app is running in development mode
 * - The script is already loaded
 *
 * https://umami.is
 */
function loadScript() {
  if (!shouldTrack()) return;
  if (document.querySelector(`script[src="${UMAMI_SCRIPT_URL}"]`)) return;

  const el = document.createElement("script");
  el.setAttribute("src", UMAMI_SCRIPT_URL);
  el.setAttribute("data-website-id", UMAMI_WEBSITE_ID);
  document.body.appendChild(el);
}

/**
 * Umami is an interface that represents the Umami tracking object
 * that includes the tracker functions
 *
 * https://umami.is/docs/tracker-functions
 */
interface Umami {
  track: (event: string, eventData?: object) => void;
  identify: (sessionData: object) => void;
}

/**
 * Get the Umami instance, it will retry every second until the umami
 * script is loaded, if the tracking is disabled it will return a mock
 * object
 */
async function getUmamiInstance(): Promise<Umami> {
  if (!shouldTrack()) {
    return {
      track: (_event: string, _eventData?: object) => {},
      identify: (_sessionData: object) => {},
    };
  }

  while (true) {
    if (typeof (window as any).umami !== "undefined") break;
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  return (window as any).umami as Umami;
}

/**
 * Track an event with Umami
 *
 * If the tracking is disabled it will do nothing
 *
 * https://umami.is/docs/tracker-functions
 *
 * @param event The event name
 * @param eventData The event data
 */
const track = async (event: string, eventData?: object) => {
  const umami = await getUmamiInstance();
  umami.track(event, eventData);
};

/**
 * Identify a session with Umami
 *
 * If the tracking is disabled it will do nothing
 *
 * https://umami.is/docs/tracker-functions
 *
 * @param sessionData The session data
 */
const identify = async (sessionData: object) => {
  const umami = await getUmamiInstance();
  umami.identify(sessionData);
};

const umami = {
  loadScript,
  track,
  identify,
};

export { umami };
export default umami;
