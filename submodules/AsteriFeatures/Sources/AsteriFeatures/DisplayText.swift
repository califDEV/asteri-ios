import Foundation

/// Keeps the unmodified attributed source for selection/copy/quote operations.
/// Replacement is exactly length-preserving in UTF-16, as are Telegram entities.
public struct AsteriDisplayText {
    public let source: NSAttributedString
    public let rendered: NSAttributedString

    public init(source: NSAttributedString, filterZalgo: Bool) {
        self.source = source
        self.rendered = ZalgoFilter.sanitized(source, enabled: filterZalgo)
    }

    public func originalSelection(in range: NSRange) -> NSAttributedString? {
        guard range.location != NSNotFound, range.location >= 0, range.length >= 0,
              range.location <= self.source.length,
              range.length <= self.source.length - range.location else {
            return nil
        }
        return self.source.attributedSubstring(from: range)
    }
}
