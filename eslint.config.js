export default [
  {
    // 1. Tell ESLint your code runs in a browser environment
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: {
        // Hand-coding the standard browser globals you actually use
        window: "readonly",
        document: "readonly",
        console: "readonly",
        fetch: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
      }
    },
    // 2. Instead of importing the whole recommended ruleset,
    // we explicitly turn on the essential structural rules
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "error",
      "no-constant-condition": "warn",
      "no-duplicate-imports": "error",
      "constructor-super": "error",
      "valid-typeof": "error"
    }
  }
];