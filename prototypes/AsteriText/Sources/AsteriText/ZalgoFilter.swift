// Native Swift adaptation of exteraGram's utils/text/ZalgoFilter.java.
// Original notice:
// This is the source code of exteraGram for Android.
// We do not and cannot prevent the use of our code,
// but be respectful and credit the original author.
// Copyright @exteraGram, 2022-2026
// Licensed under the GNU GPL v. 3 or later, with the additional terms
// in ADDITIONAL_TERMS.md.
// Source: https://github.com/exteraSquad/exteraGram/blob/b4d852f48f2734a0bee1a74a0939be621612262a/TMessagesProj/src/main/java/com/exteragram/messenger/utils/text/ZalgoFilter.java

import Foundation

/// Display-only sanitation. Never replace persisted or outgoing message text.
/// UTF-16 lengths remain unchanged, preserving existing Telegram entity ranges.
public enum ZalgoFilter {
    public static func sanitized(_ text: String, enabled: Bool = true) -> String {
        guard enabled, !text.isEmpty else { return text }
        let ranges = replacementRanges(in: text)
        guard !ranges.isEmpty else { return text }
        var units = Array(text.utf16)
        for range in ranges {
            for index in range { units[index] = 0x2060 }
        }
        return String(decoding: units, as: UTF16.self)
    }

    public static func sanitized(_ text: NSAttributedString, enabled: Bool = true) -> NSAttributedString {
        guard enabled else { return text }
        let filtered = sanitized(text.string)
        guard filtered != text.string else { return text }
        let result = NSMutableAttributedString(string: filtered)
        text.enumerateAttributes(in: NSRange(location: 0, length: text.length)) { attributes, range, _ in
            result.addAttributes(attributes, range: range)
        }
        return result
    }

    private static func replacementRanges(in text: String) -> [Range<Int>] {
        var ranges: [Range<Int>] = []
        var offset = 0
        var sequenceStart: Int?
        var count = 0
        var limit = 4
        func finishSequence(at end: Int) {
            if let start = sequenceStart, count > limit { ranges.append(start..<end) }
            sequenceStart = nil
            count = 0
            limit = 4
        }
        for scalar in text.unicodeScalars {
            let width = scalar.value > 0xFFFF ? 2 : 1
            if let allowed = allowedMarks(for: scalar) {
                if sequenceStart == nil { sequenceStart = offset }
                count += 1
                limit = min(limit, allowed)
            } else {
                finishSequence(at: offset)
                if isDirectionControl(scalar.value) { ranges.append(offset..<(offset + width)) }
            }
            offset += width
        }
        finishSequence(at: offset)
        return ranges
    }

    private static func allowedMarks(for scalar: Unicode.Scalar) -> Int? {
        guard scalar.value >= 0x0300 else { return nil }
        switch scalar.properties.generalCategory {
        case .nonspacingMark, .enclosingMark:
            switch scalar.value {
            case 0x0300...0x036F, 0x1AB0...0x1AFF, 0x1DC0...0x1DFF,
                 0x20D0...0x20FF, 0xFE20...0xFE2F:
                return 2
            default: return 4
            }
        default: return nil
        }
    }

    private static func isDirectionControl(_ value: UInt32) -> Bool {
        switch value {
        case 0x061C, 0x200E, 0x200F, 0x202A...0x202E, 0x2066...0x2069: return true
        default: return false
        }
    }
}
