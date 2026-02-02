import type { Plugin } from "@opencode-ai/plugin"
import path from "path"

/**
 * Plugin to run unit tests when a session becomes idle
 * This helps catch issues early in the development cycle
 * 
 * Always runs in blocking mode to ensure test failures are reported
 */
export const TestRunnerPlugin: Plugin = async ({ $, worktree }) => {
  return {
    event: async ({ event }) => {
      // Run tests when session becomes idle (similar to sessionEnd hook)
      if (event.type === "session.idle") {
        try {
          console.log("[TestRunner] Session idle, running unit tests (blocking)...")
          
          const scriptPath = path.join(worktree, "scripts/validate-tests.sh")
          const result = await $`bash ${scriptPath} --block ${worktree}`.quiet()
          
          if (result.exitCode !== 0) {
            console.error("[TestRunner] Unit tests failed!")
            console.error(result.stderr.toString())
          } else {
            console.log("[TestRunner] All unit tests passed!")
          }
        } catch (error) {
          console.error("[TestRunner] Error running tests:", error)
        }
      }
    },
  }
}
