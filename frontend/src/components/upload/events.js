// Deliberately omit filenames, document contents, credentials and server tokens.
export function logUploadEvent(event, details = {}) {
  console.info(`[PDF Toolkit] ${event}`, details);
}
