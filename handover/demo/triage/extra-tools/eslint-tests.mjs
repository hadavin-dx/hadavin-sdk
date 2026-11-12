export default [{ files: ['**/*.js'],
  languageOptions: { ecmaVersion: 2022, sourceType: 'commonjs', globals: { require:'readonly', process:'readonly', console:'readonly', module:'writable', setTimeout:'readonly', clearTimeout:'readonly', __dirname:'readonly', Promise:'readonly' } },
  rules: { 'no-console':'warn','no-unused-vars':'warn','no-empty':'warn','no-undef':'error','eqeqeq':'warn','no-var':'warn','no-eval':'error','no-implied-eval':'error','no-redeclare':'error','no-shadow':'warn','no-self-compare':'error','no-loop-func':'error','no-constant-condition':'warn' } }];
