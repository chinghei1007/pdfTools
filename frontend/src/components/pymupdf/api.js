const base = "/api/v1/pymupdf";
export async function request(path, body, signal) {
  const multipart = body instanceof FormData;
  const response = await fetch(`${base}${path}`, {
    method: body === undefined ? "GET" : "POST",
    credentials: "same-origin",
    signal,
    headers:
      body === undefined
        ? {}
        : {
            "X-Toolkit-Request": "1",
            ...(multipart ? {} : { "Content-Type": "application/json" }),
          },
    body:
      body === undefined ? undefined : multipart ? body : JSON.stringify(body),
  });
  const result = await response.json().catch(() => null);
  if (!response.ok)
    throw new Error(
      typeof result?.detail === "string"
        ? result.detail
        : `Request failed (${response.status}). Check the service is running.`,
    );
  return result;
}
