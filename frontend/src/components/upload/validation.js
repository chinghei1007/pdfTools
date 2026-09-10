export const inputTypes = {
  image: '.jpg,.jpeg,.png,image/jpeg,image/png',
  pdf: '.pdf,application/pdf',
};

export function validate(
  files,
  { accept = "", type, multiple = true, maxSizeBytes } = {},
) {
  if (type && !inputTypes[type]) throw new Error(`Unknown input type: ${type}`);
  if (type) accept = inputTypes[type];
  const patterns = accept
    .toLowerCase()
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
  const accepted = [];
  const errors = [];
  for (const file of files) {
    const mediaType = file.type.toLowerCase();
    const validType =
      !patterns.length ||
      patterns.some((pattern) =>
        pattern.startsWith(".")
          ? file.name.toLowerCase().endsWith(pattern)
          : pattern.endsWith("/*")
            ? mediaType.startsWith(pattern.slice(0, -1))
            : mediaType === pattern,
      );
    // Reject contradictory MIME/extension pairs as well as wrong categories.
    const mime = type === 'pdf' ? ['application/pdf'] : ['image/jpeg', 'image/png'];
    const extension = type === 'pdf' ? /\.pdf$/i : /\.(jpe?g|png)$/i;
    const matchesCategory = !type || (extension.test(file.name) && (!file.type || mime.includes(file.type.toLowerCase())));
    if (!validType || !matchesCategory) errors.push(`${file.name}: unsupported file type.`);
    else if (file.size === 0) errors.push(`${file.name}: file is empty.`);
    else if (maxSizeBytes && file.size > maxSizeBytes)
      errors.push(`${file.name}: file exceeds the size limit.`);
    else if (!multiple && accepted.length)
      errors.push(`${file.name}: select one file at a time.`);
    else accepted.push(file);
  }
  return { accepted, errors };
}

export const validateFiles = validate;
