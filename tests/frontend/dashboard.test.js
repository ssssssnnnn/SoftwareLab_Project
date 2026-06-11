import { describe, it, expect, beforeEach } from 'vitest';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import vm from 'vm';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

global.window = {
  addEventListener: () => {},
  navigator: {
    clipboard: {
      writeText: async () => {}
    }
  },
  alert: () => {},
  clearInterval: () => {}
};

global.document = {
  getElementById: () => ({
    addEventListener: () => {},
    value: 'ALL'
  })
};

// Trick to load vanilla JS file into Node environment for testing
const jsCode = fs.readFileSync(path.resolve(__dirname, '../../src/static/dashboard.js'), 'utf8');
vm.runInThisContext(jsCode); // Evaluates code in VM making functions available

describe('dashboard.js utility tests', () => {
  it('should generate correct pip snippet for PyPI type', () => {
    const result = generateConfigSnippet('https://pypi.tuna.tsinghua.edu.cn/simple', 'PyPI');
    expect(result).toBe('pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple');
  });

  it('should generate correct npm snippet for NPM type', () => {
    const result = generateConfigSnippet('https://registry.npmmirror.com', 'NPM');
    expect(result).toBe('npm config set registry https://registry.npmmirror.com');
  });

  it('should fallback gracefully for unknown types', () => {
    const result = generateConfigSnippet('https://example.com', 'UNKNOWN');
    expect(result).toContain('# No directive mapping variant found');
  });
});