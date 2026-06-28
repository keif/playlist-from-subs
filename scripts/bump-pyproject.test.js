const assert = require("node:assert/strict");
const updater = require("./bump-pyproject.js");

const SAMPLE = `[project]
name = "yt-sub-playlist"
version = "4.1.0"
description = "x"

[tool.something]
version = "9.9.9"
`;

// readVersion finds the [project] version, not other tables
assert.equal(updater.readVersion(SAMPLE), "4.1.0", "readVersion returns project version");

// writeVersion updates only the [project] version
const bumped = updater.writeVersion(SAMPLE, "4.2.0");
assert.match(bumped, /\[project\][\s\S]*?version = "4\.2\.0"/, "writeVersion bumps project version");
assert.match(bumped, /\[tool\.something\][\s\S]*?version = "9\.9\.9"/, "writeVersion leaves other tables alone");

// readVersion throws on missing [project] version
assert.throws(
  () => updater.readVersion(`[tool.x]\nversion = "1.0.0"\n`),
  /version not found/,
  "readVersion throws when [project] version is missing",
);

// writeVersion throws on missing [project] version
assert.throws(
  () => updater.writeVersion(`[tool.x]\nversion = "1.0.0"\n`, "5.0.0"),
  /version not found/,
  "writeVersion throws when [project] version is missing",
);

// regex anchors to [project] even when later tables have version keys
const PROJECT_LACKS_VERSION = `[project]
name = "x"

[tool.something]
version = "9.9.9"
`;
assert.throws(
  () => updater.readVersion(PROJECT_LACKS_VERSION),
  /version not found/,
  "readVersion does not match version in [tool.*] when [project] lacks one",
);

console.log("ok - bump-pyproject updater");
