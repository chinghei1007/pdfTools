const base = "/api/v1";
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

export async function downloadFile(entry) {
  const response = await fetch(entry.downloadUrl, { credentials: "same-origin" });
  if (!response.ok) throw new Error(`Download failed (${response.status}).`);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = entry.name || "download";
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
