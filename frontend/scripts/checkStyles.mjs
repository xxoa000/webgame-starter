/* CSS Module 클래스와 화면 간 스타일 연결이 누락됐는지 검사한다. */
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import ts from "typescript";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

async function listSourceFiles(directory) {
  /* 빌드 결과와 설치 폴더를 제외하고 소스 파일만 수집한다. */
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    if (["node_modules", ".next", "public"].includes(entry.name)) continue;
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) files.push(...(await listSourceFiles(target)));
    else files.push(target);
  }
  return files;
}

const files = await listSourceFiles(root);
const modules = new Map();
const requiredContexts = new Set();
const definedContexts = new Set();
const errors = [];

for (const file of files.filter((name) => name.endsWith(".module.css"))) {
  const css = await readFile(file, "utf8");
  modules.set(
    file,
    new Set([...css.matchAll(/\.([A-Za-z_][\w-]*)/g)].map((match) => match[1])),
  );
  for (const match of css.matchAll(/\[data-ui~=["']([^"']+)["']\]/g)) {
    requiredContexts.add(match[1]);
  }
}

for (const file of files.filter((name) => name.endsWith(".tsx"))) {
  const source = ts.createSourceFile(
    file,
    await readFile(file, "utf8"),
    ts.ScriptTarget.Latest,
    true,
    ts.ScriptKind.TSX,
  );
  const imports = new Map();
  for (const statement of source.statements) {
    if (!ts.isImportDeclaration(statement)) continue;
    const name = statement.importClause?.name?.text;
    const modulePath = statement.moduleSpecifier.text;
    if (name && modulePath.endsWith(".module.css")) {
      imports.set(name, path.resolve(path.dirname(file), modulePath));
    }
  }

  function visit(node) {
    /* 존재하지 않는 styles.name 참조와 부모 스타일 표식을 찾는다. */
    if (
      ts.isPropertyAccessExpression(node) &&
      ts.isIdentifier(node.expression)
    ) {
      const modulePath = imports.get(node.expression.text);
      if (modulePath && !modules.get(modulePath)?.has(node.name.text)) {
        errors.push(`${path.relative(root, file)}: ${node.getText(source)}`);
      }
    }
    if (ts.isJsxAttribute(node) && node.name.getText(source) === "data-ui") {
      function collectNames(child) {
        /* 조건부 속성에서도 선언 가능한 연결 이름을 수집한다. */
        if (ts.isStringLiteral(child)) {
          for (const value of child.text.split(/\s+/).filter(Boolean)) {
            definedContexts.add(value);
          }
        }
        ts.forEachChild(child, collectNames);
      }
      collectNames(node);
    }
    ts.forEachChild(node, visit);
  }
  visit(source);
}

for (const name of requiredContexts) {
  if (!definedContexts.has(name)) errors.push(`연결 표식 누락: ${name}`);
}
if (errors.length) {
  console.error(errors.join("\n"));
  process.exitCode = 1;
} else {
  console.log(`스타일 연결 검사 통과: CSS Modules ${modules.size}개`);
}
