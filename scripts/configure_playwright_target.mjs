import { readFileSync, writeFileSync } from 'node:fs'

const targetUrl = process.argv[2]
const configPath = process.argv[3] ?? 'playwright.config.ts'

if (!targetUrl) {
  throw new Error('usage: configure_playwright_target.mjs <base-url> [config-path]')
}

const parsedUrl = new URL(targetUrl)
if (!['http:', 'https:'].includes(parsedUrl.protocol)) {
  throw new Error('the Playwright target must use http or https')
}

const quotedTargetUrl = `'${targetUrl.replaceAll('\\', '\\\\').replaceAll("'", "\\'")}'`
const declaration =
  `const testahBaseURL =\n` +
  `  process.env.TESTAH_BASE_URL ?? ${quotedTargetUrl}`
const quotedUrlPattern = String.raw`(?:'(?:\\.|[^'\\\r\n])*'|"(?:\\.|[^"\\\r\n])*")`
const declarationPattern = new RegExp(
  String.raw`const testahBaseURL\s*=\s*\n?\s*process\.env\.TESTAH_BASE_URL\s*\?\?\s*${quotedUrlPattern}`,
)
const inlineBaseUrlPattern = new RegExp(
  String.raw`baseURL:\s*process\.env\.TESTAH_BASE_URL\s*\?\?\s*${quotedUrlPattern}`,
)

let config = readFileSync(configPath, 'utf8')
if (declarationPattern.test(config)) {
  config = config.replace(declarationPattern, declaration)
} else {
  const configStart = 'export default defineConfig({'
  if (!config.includes(configStart) || !inlineBaseUrlPattern.test(config)) {
    throw new Error('playwright.config.ts does not match a supported Testah config')
  }
  config = config.replace(
    configStart,
    `${declaration}\n\n${configStart}\n` +
      `  metadata: {\n` +
      `    testah: {\n` +
      `      baseURL: testahBaseURL,\n` +
      `    },\n` +
      `  },`,
  )
  config = config.replace(inlineBaseUrlPattern, 'baseURL: testahBaseURL')
}

if (
  !config.includes('metadata:') ||
  config.match(/baseURL: testahBaseURL/g)?.length !== 2
) {
  throw new Error('playwright.config.ts is missing Testah report metadata')
}

writeFileSync(configPath, config, 'utf8')
