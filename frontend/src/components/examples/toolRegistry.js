// Preview configuration only; formats must also be enforced by the processor.
const pdf = { type: 'pdf', multiple: false };
export const toolRegistry = {
  'image-to-pdf': { type: 'image', multiple: true, formats: ['pdf'] },
  'pdf-to-image': { ...pdf, formats: ['jpg', 'png'] },
  images: { ...pdf, formats: ['jpg', 'png'] },
  metadata: { ...pdf, formats: ['json', 'txt'] },
  merge: { ...pdf, multiple: true, formats: ['pdf'] },
  split: { ...pdf, formats: ['pdf'] },
  rotate: { ...pdf, formats: ['pdf'] },
};
