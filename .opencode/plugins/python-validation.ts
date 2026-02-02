import type { Plugin } from "@opencode-ai/plugin"
import path from "path"

/**
 * Plugin to validate Python files after edit/write operations
 * Runs Black (formatting), Ruff (linting), and mypy (type checking)
 *
 * Behavior:
 * - After file edits: Non-blocking (runs in background)
 * - On session idle: Blocking (validates all recently edited files)
 */
export const PythonValidationPlugin: Plugin = async ({ $, worktree }) => {
  // Track edited Python files for session-end validation
  const editedFiles = new Set<string>()

  const validatePythonFile = async (filePath: string, blocking: boolean) => {
    // Only process Python files
    if (!filePath.endsWith(".py")) {
      return
    }

    // Resolve to absolute path
    const absolutePath = path.isAbsolute(filePath)
      ? filePath
      : path.join(worktree, filePath)

    try {
      const scriptPath = path.join(worktree, "scripts/validate-python.sh")
      const blockingFlag = blocking ? "--block" : "--no-block"

      if (blocking) {
        console.log(`[PythonValidation] Validating ${filePath} (blocking)...`)
        const result = await $`bash ${scriptPath} ${blockingFlag} ${absolutePath}`.quiet()

        if (result.exitCode !== 0) {
          console.error(`[PythonValidation] Validation failed for ${filePath}`)
          console.error(result.stderr.toString())
        } else {
          console.log(`[PythonValidation] Validation passed for ${filePath}`)
        }
      } else {
        // Non-blocking: fire and forget
        console.log(`[PythonValidation] Validating ${filePath} (non-blocking)...`)
        $`bash ${scriptPath} ${blockingFlag} ${absolutePath}`.quiet().catch(() => {
          // Ignore errors in non-blocking mode
        })
      }
    } catch (error) {
      if (blocking) {
        console.error(`[PythonValidation] Error validating ${filePath}:`, error)
      }
    }
  }

  return {
    // After edit/write: Non-blocking validation
    "tool.execute.after": async (input) => {
      if (input.tool !== "edit" && input.tool !== "write") {
        return
      }

      const filePath = input.args?.filePath || input.args?.path
      if (filePath && typeof filePath === "string" && filePath.endsWith(".py")) {
        // Track for session-end validation
        const absolutePath = path.isAbsolute(filePath)
          ? filePath
          : path.join(worktree, filePath)
        editedFiles.add(absolutePath)

        // Run non-blocking validation
        await validatePythonFile(filePath, false)
      }
    },

    // On session idle: Blocking validation of all edited files
    event: async ({ event }) => {
      if (event.type === "session.idle" && editedFiles.size > 0) {
        console.log(`[PythonValidation] Session idle, validating ${editedFiles.size} edited file(s)...`)

        for (const filePath of editedFiles) {
          await validatePythonFile(filePath, true)
        }

        // Clear the set after validation
        editedFiles.clear()
      }
    },
  }
}
