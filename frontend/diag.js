const ts = require('typescript');
const fs = require('fs');
const path = 'frontend/src/components/ui/animated-characters-login-page.tsx';
const src = fs.readFileSync(path, 'utf8');
const sf = ts.createSourceFile(path, src, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
const diag = ts.getPreEmitDiagnostics(sf);
if (diag.length === 0) {
  console.log('No diagnostics');
  process.exit(0);
}
diag.forEach(d => {
  const msg = ts.flattenDiagnosticMessageText(d.messageText, '\n');
  const { line, character } = d.file.getLineAndCharacterOfPosition(d.start);
  console.log(`${d.file.fileName}:${line+1}:${character+1} - ${msg}`);
});
