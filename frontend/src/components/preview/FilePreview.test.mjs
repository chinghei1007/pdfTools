import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'vite';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

test('server file record renders before its preview URL arrives, then renders its image', async () => {
  const vite = await createServer({ server: { middlewareMode: true }, appType: 'custom' });
  try {
    const { FilePreview } = await vite.ssrLoadModule('/src/components/preview/FilePreview.jsx');
    const pending = renderToStaticMarkup(createElement(FilePreview, { name: 'uploaded.pdf', mediaType: 'application/pdf' }));
    assert.match(pending, /PDF document/);
    const ready = renderToStaticMarkup(createElement(FilePreview, { name: 'uploaded.pdf', mediaType: 'image/png', url: '/api/thumbnail.png' }));
    assert.match(ready, /<img/);
    assert.match(ready, /src="\/api\/thumbnail.png"/);
    assert.doesNotThrow(() => renderToStaticMarkup(createElement(FilePreview, {})));
  } finally {
    await vite.close();
  }
});
