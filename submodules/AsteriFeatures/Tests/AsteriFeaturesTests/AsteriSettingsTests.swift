import Foundation
import XCTest
import AsteriFeatures

final class AsteriSettingsTests: XCTestCase {
    func testDefaultAndOlderEmptySettingsKeepAndroidDefault() throws {
        XCTAssertTrue(AsteriSettings.defaultSettings.filterZalgo)
        XCTAssertTrue(try JSONDecoder().decode(AsteriSettings.self, from: Data("{}".utf8)).filterZalgo)
    }

    func testExplicitDisabledValueSurvivesSerializationAndRestart() throws {
        let settings = AsteriSettings(filterZalgo: false)
        let bytes = try JSONEncoder().encode(settings)
        XCTAssertEqual(try JSONDecoder().decode(AsteriSettings.self, from: bytes), settings)
        XCTAssertFalse(try JSONDecoder().decode(AsteriSettings.self, from: bytes).filterZalgo)
    }

    func testInvalidValueDoesNotSilentlyEnableOrDisableTheFeature() {
        XCTAssertThrowsError(try JSONDecoder().decode(AsteriSettings.self, from: Data("{\"filterZalgo\":1}".utf8)))
    }

    func testDisplaySelectionRetainsOriginalCharactersAndLinkTargets() {
        let key = NSAttributedString.Key("link")
        let original = NSAttributedString(string: "👋 A\u{0300}\u{0301}\u{0302} https://example.org", attributes: [key: "https://example.org"])
        let display = AsteriDisplayText(source: original, filterZalgo: true)
        XCTAssertNotEqual(display.rendered.string, original.string)
        XCTAssertEqual(display.rendered.length, original.length)
        XCTAssertEqual(display.originalSelection(in: NSRange(location: 0, length: original.length)), original)
        XCTAssertEqual(display.originalSelection(in: NSRange(location: 4, length: 3))?.string, "\u{0300}\u{0301}\u{0302}")
        XCTAssertEqual(display.rendered.attribute(key, at: 6, effectiveRange: nil) as? String, "https://example.org")
        XCTAssertNil(display.originalSelection(in: NSRange(location: NSNotFound, length: 1)))
        XCTAssertNil(display.originalSelection(in: NSRange(location: Int.max, length: Int.max)))
    }
}
