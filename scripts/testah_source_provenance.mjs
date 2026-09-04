import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative, sep } from 'node:path'

const sourceFiles = ['targets.yaml', 'playwright.config.ts']
const sourceDirectories = ['tests', 'requirements']

export function sourceProvenance(root = process.cwd()) {
  return {
    sourceCommit: sourceCommit(root),
    sourceFingerprint: sourceFingerprint(root),
  }
}

export function sourceFingerprint(root = process.cwd()) {
  const entries = []
  for (const path of sourceFiles) {
    entries.push(fileEntry(root, path))
  }
  for (const directory of sourceDirectories) {
    const absoluteDirectory = join(root, directory)
    if (!isDirectory(absoluteDirectory)) {
      entries.push([`${directory}/`, null])
      continue
    }
    collectFiles(root, absoluteDirectory, entries)
  }
  entries.sort(([left], [right]) => left.localeCompare(right))

  const digest = createHash('sha256')
  for (const [path, content] of entries) {
    digest.update(path)
    digest.update('\0')
    digest.update(content === null ? 'missing' : 'file')
    digest.update('\0')
    if (content !== null) digest.update(content)
    digest.update('\0')
  }
  return digest.digest('hex')
}

function sourceCommit(root) {
  try {
    return execFileSync('git', ['rev-parse', 'HEAD'], {
      cwd: root,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    }).trim()
  } catch {
    return null
  }
}

function collectFiles(root, directory, entries) {
  for (const entry of readdirSync(directory, { withFileTypes: true })) {
    const absolutePath = join(directory, entry.name)
    if (entry.isDirectory()) {
      collectFiles(root, absolutePath, entries)
    } else if (entry.isFile()) {
      entries.push(fileEntry(root, relative(root, absolutePath)))
    }
  }
}

function fileEntry(root, path) {
  const normalizedPath = path.split(sep).join('/')
  try {
    const absolutePath = join(root, path)
    return statSync(absolutePath).isFile()
      ? [normalizedPath, readFileSync(absolutePath)]
      : [normalizedPath, null]
  } catch {
    return [normalizedPath, null]
  }
}

function isDirectory(path) {
  try {
    return statSync(path).isDirectory()
  } catch {
    return false
  }
}
