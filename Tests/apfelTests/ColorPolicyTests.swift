// ============================================================================
// ColorPolicyTests.swift - Coverage for the pure ANSI color-gating policy.
// ============================================================================

import Foundation
import ApfelCLI

func runColorPolicyTests() {
    // #258: NO_COLOR only counts when non-empty.
    test("NO_COLOR unset -> color allowed") {
        try assertEqual(ColorPolicy.noColorFromEnv(nil), false)
    }

    test("NO_COLOR empty string -> color allowed") {
        try assertEqual(ColorPolicy.noColorFromEnv(""), false)
    }

    test("NO_COLOR=1 -> color disabled") {
        try assertEqual(ColorPolicy.noColorFromEnv("1"), true)
    }

    test("NO_COLOR=any-non-empty -> color disabled") {
        try assertEqual(ColorPolicy.noColorFromEnv("true"), true)
    }
}
