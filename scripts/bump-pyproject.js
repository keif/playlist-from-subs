const VERSION_RE = /(\[project\](?:(?!\n\[)[\s\S])*?\n\s*version\s*=\s*")([^"]+)(")/;

module.exports = {
  readVersion(contents) {
    const m = contents.match(VERSION_RE);
    if (!m) throw new Error("version not found under [project] in pyproject.toml");
    return m[2];
  },
  writeVersion(contents, version) {
    const m = contents.match(VERSION_RE);
    if (!m) throw new Error("version not found under [project] in pyproject.toml");
    return contents.replace(VERSION_RE, `$1${version}$3`);
  },
};
