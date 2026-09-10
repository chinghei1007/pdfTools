export function validateFiles(
  files,
  { accept = "", multiple = true, maxSizeBytes } = {},
) {
  const patterns = accept
    .toLowerCase()
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
  const accepted = [];
  const errors = [];
  for (const file of files) {
    const type = file.type.toLowerCase();
    const validType =
      !patterns.length ||
      patterns.some((pattern) =>
        pattern.startsWith(".")
          ? file.name.toLowerCase().endsWith(pattern)
          : pattern.endsWith("/*")
            ? type.startsWith(pattern.slice(0, -1))
            : type === pattern,
      );
    if (!validType) errors.push(`${file.name}: unsupported file type.`);
    else if (maxSizeBytes && file.size > maxSizeBytes)
      errors.push(`${file.name}: file exceeds the size limit.`);
    else if (!multiple && accepted.length)
      errors.push(`${file.name}: select one file at a time.`);
    else accepted.push(file);
  }
  return { accepted, errors };
}
