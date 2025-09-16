module.exports = {
  root: true,
  env: { browser: true, es2024: true, node: true },
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  extends: [
    "eslint:recommended",
    "plugin:import/recommended",
    "plugin:promise/recommended",
    "plugin:n/recommended",
    "plugin:security/recommended",
    "plugin:jsx-a11y/recommended",
    "prettier"
  ],
  rules: {
    "no-console": ["warn", { allow: ["warn", "error"] }],
    "import/no-unresolved": "off",
  },
  ignorePatterns: [
    "static/**",
    "**/*.py",
    "**/*.html",
    "**/*.css"
  ]
};

