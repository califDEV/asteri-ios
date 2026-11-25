import Foundation
import XCTest
import AsteriText

final class ZalgoFilterTests: XCTestCase {
    private let joiner = "\u{2060}"

    func testPlainTextAndNormalDiacriticsRemainUnchanged() {
        for text in ["", "Hello", "Привіт", "مرحبا", "é", "e\u{0301}", "a\u{0300}\u{0301}"] {
            XCTAssertEqual(ZalgoFilter.sanitized(text), text)
        }
    }

    func testEntireExcessiveSequenceIsReplaced() {
        let text = "A\u{0300}\u{0301}\u{0302}B"
        XCTAssertEqual(ZalgoFilter.sanitized(text), "A" + String(repeating: joiner, count: 3) + "B")
        XCTAssertEqual(ZalgoFilter.sanitized(text).utf16.count, text.utf16.count)
    }

    func testNonZalgoScriptAllowsFourMarksButNotFive() {
        let mark = "\u{064B}"
        let allowed = "ب" + String(repeating: mark, count: 4)
        XCTAssertEqual(ZalgoFilter.sanitized(allowed), allowed)
        XCTAssertEqual(ZalgoFilter.sanitized("ب" + String(repeating: mark, count: 5)),
                       "ب" + String(repeating: joiner, count: 5))
    }

    func testMixedMarkRunUsesTheStricterLimit() {
        XCTAssertEqual(ZalgoFilter.sanitized("a\u{064B}\u{0301}\u{064C}"),
                       "a" + String(repeating: joiner, count: 3))
    }

    func testDirectionControlsAreReplacedWithoutMovingOffsets() {
        for value: UInt32 in [0x061C, 0x200E, 0x200F, 0x202A, 0x202B, 0x202C, 0x202D,
                             0x202E, 0x2066, 0x2067, 0x2068, 0x2069] {
            XCTAssertEqual(ZalgoFilter.sanitized("a" + String(Unicode.Scalar(value)!) + "b"), "a" + joiner + "b")
        }
    }

    func testEmojiVariationSelectorsAndJoinersArePreserved() {
        let text = "👨‍👩‍👧‍👦 👍🏽 ❤️ 1️⃣"
        XCTAssertEqual(ZalgoFilter.sanitized(text), text)
    }

    func testSupplementaryMarksPreserveTwoUTF16UnitsEach() {
        let text = "𝄞" + String(repeating: "\u{1D185}", count: 5) + "z"
        XCTAssertEqual(ZalgoFilter.sanitized(text), "𝄞" + String(repeating: joiner, count: 10) + "z")
        XCTAssertEqual(ZalgoFilter.sanitized(text).utf16.count, text.utf16.count)
    }

    func testDisabledModePreservesTheOriginalTextAndAttributedObject() {
        let text = "a\u{0300}\u{0301}\u{0302}\u{202E}"
        XCTAssertEqual(ZalgoFilter.sanitized(text, enabled: false), text)
        let attributed = NSAttributedString(string: text)
        XCTAssertTrue(ZalgoFilter.sanitized(attributed, enabled: false) === attributed)
        let plain = NSAttributedString(string: "plain")
        XCTAssertTrue(ZalgoFilter.sanitized(plain) === plain)
    }

    func testAttributesAndOriginalObjectArePreserved() {
        let key = NSAttributedString.Key("AsteriTestAttribute")
        let source = NSMutableAttributedString(string: "a\u{0300}\u{0301}\u{0302}b", attributes: [key: "base"])
        source.addAttribute(key, value: "marks", range: NSRange(location: 1, length: 3))
        let filtered = ZalgoFilter.sanitized(source)
        XCTAssertEqual(filtered.string, "a" + String(repeating: joiner, count: 3) + "b")
        XCTAssertEqual(source.string, "a\u{0300}\u{0301}\u{0302}b")
        for position in 0..<source.length {
            XCTAssertEqual(filtered.attribute(key, at: position, effectiveRange: nil) as? String,
                           source.attribute(key, at: position, effectiveRange: nil) as? String)
        }
    }

    func testLongInputPreservesEveryEntityOffset() {
        let text = String(repeating: "x\u{0300}\u{0301}\u{0302}", count: 4096)
        let output = ZalgoFilter.sanitized(text)
        XCTAssertEqual(output, String(repeating: "x" + String(repeating: joiner, count: 3), count: 4096))
        XCTAssertEqual(output.utf16.count, text.utf16.count)
    }
}
