// ============================================================================
// SamplingDecision.swift — Pure mapping from request sampling params to a mode
// Part of ApfelCore — shared with the executable, unit-testable without
// FoundationModels (whose GenerationOptions.SamplingMode lives in the SDK).
// ============================================================================

import Foundation

/// A FoundationModels-free description of which sampling mode a request maps to.
///
/// The executable's `makeGenerationOptions` translates this into the SDK's
/// `GenerationOptions.SamplingMode`. Keeping the decision pure lets the unit
/// runner (which cannot import FoundationModels) exercise the policy directly.
public enum SamplingDecision: Sendable, Equatable {
    /// Deterministic greedy decoding (always pick the most likely token).
    case greedy
    /// Nucleus (top-p) sampling with the given probability threshold and seed.
    case nucleus(probabilityThreshold: Double, seed: UInt64?)
    /// Top-k random sampling with a fixed k and the given seed.
    case topK(top: Int, seed: UInt64)
    /// No explicit sampling mode — defer to the model default.
    case defaultMode

    /// Maps OpenAI-style sampling parameters to a sampling decision.
    ///
    /// Policy:
    /// - `top_p` present -> nucleus(top_p, seed) (honors #168).
    /// - else `temperature == 0` -> greedy (deterministic at temperature 0).
    /// - else a `seed` -> topK(top: 50, seed) (existing reproducible behavior).
    /// - else -> defaultMode.
    public static func resolve(
        temperature: Double?,
        topP: Double?,
        seed: UInt64?
    ) -> SamplingDecision {
        if let topP {
            return .nucleus(probabilityThreshold: topP, seed: seed)
        }
        if let temperature, temperature == 0 {
            return .greedy
        }
        if let seed {
            return .topK(top: 50, seed: seed)
        }
        return .defaultMode
    }
}
