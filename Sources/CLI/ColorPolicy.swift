// ============================================================================
// ColorPolicy.swift - Pure ANSI color-gating policy.
//
// Kept in ApfelCLI (FoundationModels-free) so the gating rules are
// unit-testable. Output.swift wires the process's real isatty()/env/flag
// state into these pure decisions.
// ============================================================================

import Foundation

/// Pure decisions for whether apfel should emit ANSI color codes.
public enum ColorPolicy {
    /// True when `NO_COLOR` is present AND non-empty.
    ///
    /// Per https://no-color.org and apfel's man page, only a non-empty value
    /// disables color; an empty `NO_COLOR=` must not (#258).
    public static func noColorFromEnv(_ value: String?) -> Bool {
        value.map { !$0.isEmpty } ?? false
    }
}
