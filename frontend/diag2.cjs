const ts = require('typescript');
const root = ['src/components/ui/animated-characters-login-page.tsx'];
const options = {jsx: ts.JsxEmit.Preserve, target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ESNext};
const program = ts.createProgram(root, options);
const diags = ts.getPreEmitDiagnostics(program);
if (!diags.length) {
  console.log('No diagnostics');
  process.exit(0);
}
diags.forEach(d => {
  const msg = ts.flattenDiagnosticMessageText(d.messageText, '\n');
  const file = d.file ? d.file.fileName : 'unknown';
  const { line, character } = d.file ? d.file.getLineAndCharacterOfPosition(d.start) : {line:0,character:0};
  console.log(`${file}:${line+1}:${character+1} - ${msg}`);
});
