export default [{
  files: ['**/*.js'],
  languageOptions: { ecmaVersion: 2022, sourceType: 'script',
    globals: { window: 'readonly', document: 'readonly', fetch: 'readonly', console: 'readonly', setTimeout: 'readonly', clearTimeout: 'readonly', setInterval: 'readonly', clearInterval: 'readonly', location: 'readonly', navigator: 'readonly', URL: 'readonly', AbortController: 'readonly', requestAnimationFrame: 'readonly', Intl: 'readonly', localStorage: 'readonly', Node: 'readonly', Event: 'readonly', CustomEvent: 'readonly', Blob: 'readonly', URLSearchParams: 'readonly', getComputedStyle: 'readonly', matchMedia: 'readonly', Promise: 'readonly', MutationObserver: 'readonly', NodeFilter: 'readonly' } },
  linterOptions: { reportUnusedDisableDirectives: 'off' },
  rules: {
    'no-undef': 'error', 'no-use-before-define': ['error', { functions: false, classes: true, variables: true }],
    'no-func-assign': 'error', 'no-loop-func': 'error', 'no-var': 'error', 'prefer-const': 'warn',
    'no-implicit-globals': 'error', 'no-redeclare': 'error', 'no-shadow': 'warn', 'no-unused-vars': 'warn',
    'no-global-assign': 'error', 'no-empty': 'warn', 'block-scoped-var': 'error', 'eqeqeq':'warn'
  }
}];
