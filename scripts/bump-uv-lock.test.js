const assert = require("node:assert/strict");
const updater = require("./bump-uv-lock.js");

const SAMPLE = `version = 1
revision = 3
requires-python = ">=3.11"

[[package]]
name = "flask"
version = "3.0.0"
source = { registry = "https://pypi.org/simple" }

[[package]]
name = "yt-sub-playlist"
version = "4.1.0"
source = { editable = "." }

[package.metadata]
requires-dist = []
`;

// readVersion finds the yt-sub-playlist version, not flask's
assert.equal(
  updater.readVersion(SAMPLE),
  "4.1.0",
  "readVersion returns yt-sub-playlist version, not flask's"
);

// writeVersion updates only the yt-sub-playlist [[package]] block
const bumped = updater.writeVersion(SAMPLE, "4.2.0");
assert.match(
  bumped,
  /name = "yt-sub-playlist"\s*\nversion = "4\.2\.0"/,
  "writeVersion bumps yt-sub-playlist version"
);
assert.match(
  bumped,
  /name = "flask"\s*\nversion = "3\.0\.0"/,
  "writeVersion leaves flask version alone"
);

// readVersion throws when the project package is missing
assert.throws(
  () => updater.readVersion(`[[package]]\nname = "flask"\nversion = "3.0.0"\n`),
  /yt-sub-playlist package not found/,
  "readVersion throws when yt-sub-playlist package is missing"
);

assert.throws(
  () => updater.writeVersion(`[[package]]\nname = "flask"\nversion = "3.0.0"\n`, "5.0.0"),
  /yt-sub-playlist package not found/,
  "writeVersion throws when yt-sub-playlist package is missing"
);

console.log("ok - bump-uv-lock updater");
