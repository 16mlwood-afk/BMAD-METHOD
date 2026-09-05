// Golden-case regression lock for tools/lib/standards-corpus.js (fork-gap 2026-07-25).
//
// WHY THIS TEST EXISTS — it gates the "I ran it and it worked" verification path.
//
// While authoring the helper, its own MANDATE header contained the literal glob
// `custom/skills*` followed by a slash. Inside a block comment that sequence IS the
// comment terminator, so the header silently ended mid-sentence and the rest of the
// file became executable garbage — the module would not parse at all. Nothing in the
// fork caught it: markdownlint does not read .js, eslint was not run on the new file
// yet, and a reader skims a comment block without tokenizing it. It was found only by
// running the module by hand.
//
// That is a bad place for a load-bearing check to live: the helper is now the single
// corpus source for FOUR gates, two of which (check:completion --strict,
// validate:close-out) are ARMED in npm test and the pre-commit fast-path. A helper that
// fails to parse takes every one of them down at once, on every commit.
//
// The class is broader than one typo: any doc-heavy header can close its own comment
// (`*/` appears in globs, regexes, and file paths). So this asserts the two properties
// that no amount of careful reading can guarantee:
//   P1 the module PARSES and can be required (catches the comment-terminator class).
//   P2 collectStandardsCorpus() returns the documented shape {files, roots, missingRoots},
//      so a consumer destructuring it cannot silently receive undefined.
//
// Deliberately NOT asserted: exact file counts or specific root membership. Those change
// whenever a workflow is added and would make this a maintenance tax that gets deleted —
// the contract under test is the SHAPE and the parse, not the corpus census.

const path = require('node:path');

let passed = 0;
let failed = 0;
function ok(name, cond) {
  console.log(`  ${cond ? '✓' : '✗'} ${name}`);
  cond ? passed++ : failed++;
}

console.log('\nstandards-corpus helper — parse + shape lock\n');

// --- P1: the module parses and loads -----------------------------------------
// A require() of an unparseable module throws SyntaxError at load. This is the
// assertion that would have caught the `custom/skills*/` comment terminator.
let mod = null;
let loadError = null;
try {
  mod = require(path.join(__dirname, '..', 'tools', 'lib', 'standards-corpus.js'));
} catch (error) {
  loadError = error;
}

ok('P1 imports without a parse error', loadError === null);
if (loadError) {
  console.log(`      ${loadError.name}: ${loadError.message}`);
}

ok('P1 exports collectStandardsCorpus as a function', !!mod && typeof mod.collectStandardsCorpus === 'function');

// --- P2: the returned shape matches the documented contract ------------------
if (mod && typeof mod.collectStandardsCorpus === 'function') {
  let result = null;
  let callError = null;
  try {
    result = mod.collectStandardsCorpus();
  } catch (error) {
    callError = error;
  }

  ok('P2 collectStandardsCorpus() does not throw', callError === null);
  if (callError) {
    console.log(`      ${callError.name}: ${callError.message}`);
  }

  const isObject = !!result && typeof result === 'object' && !Array.isArray(result);
  ok('P2 returns a plain object', isObject);

  for (const key of ['files', 'roots', 'missingRoots']) {
    ok(`P2 result.${key} is an array`, isObject && Array.isArray(result[key]));
  }

  // The helper's contract says it never throws on a missing root — it reports it.
  // Guard the invariant that roots + missingRoots account for every configured root,
  // so a silently-dropped root can't masquerade as "nothing configured".
  const configured = Array.isArray(mod.CORPUS_ROOTS) ? mod.CORPUS_ROOTS.length : -1;
  ok(
    'P2 roots + missingRoots account for every configured root',
    isObject && configured > 0 && result.roots.length + result.missingRoots.length === configured,
  );

  // The generated port is excluded BY DECISION (see the helper header). If it ever
  // leaks in, every gate starts flagging ports instead of sources.
  ok(
    'P2 the generated skills-native port is never in the corpus',
    isObject && result.files.every((f) => !f.includes(`${path.sep}skills-native${path.sep}`)),
  );
}

console.log(`\n  ${passed} passed, ${failed} failed\n`);
process.exit(failed === 0 ? 0 : 1);
