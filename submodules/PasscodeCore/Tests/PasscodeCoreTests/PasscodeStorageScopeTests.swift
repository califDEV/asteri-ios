import XCTest
@testable import PasscodeCore

@available(macOS 10.15, *)
final class PasscodeStorageScopeTests: XCTestCase {
    private func configuration(role: PasscodeConfiguration.ProcessRole = .mainApp, storage: PasscodeConfiguration.CredentialStorage = .sharedAppGroup) -> PasscodeConfiguration {
        return PasscodeConfiguration(appGroupIdentifier: "group.org.asteri.tests", processRole: role, credentialStorage: storage)
    }

    func testDefaultModeStillRequiresTheSharedGroup() throws {
        let environment = PasscodeEnvironment()
        try environment.configure(self.configuration(), privateAccessGroup: { "TEAMID0000.org.asteri.tests" })
        XCTAssertEqual(try environment.sharedAccessGroup(), "group.org.asteri.tests")
        XCTAssertEqual(try environment.credentialAccessGroup(), "group.org.asteri.tests")
    }

    func testPrivateCredentialsUseOnlyTheAppsOwnGroup() throws {
        let environment = PasscodeEnvironment()
        try environment.configure(self.configuration(storage: .privateApplication), privateAccessGroup: { "TEAMID0000.org.asteri.tests" })
        XCTAssertEqual(try environment.credentialAccessGroup(), "TEAMID0000.org.asteri.tests")
        XCTAssertEqual(try environment.privateAccessGroup(), "TEAMID0000.org.asteri.tests")
        XCTAssertThrowsError(try environment.sharedAccessGroup())
    }

    func testExtensionsCannotOptIntoPrivateApplicationStorage() {
        let environment = PasscodeEnvironment()
        XCTAssertThrowsError(try environment.configure(self.configuration(role: .appExtension, storage: .privateApplication)))
        XCTAssertThrowsError(try environment.credentialAccessGroup())
    }

    func testUnavailablePrivateKeychainDoesNotFallBackToSharedOrUnscopedAccess() throws {
        let environment = PasscodeEnvironment()
        try environment.configure(self.configuration(storage: .privateApplication), privateAccessGroup: { nil })
        XCTAssertThrowsError(try environment.credentialAccessGroup())
        XCTAssertThrowsError(try environment.sharedAccessGroup())
        XCTAssertThrowsError(try environment.privateAccessGroup())
    }

    func testStorageModeCannotChangeAfterInitialization() throws {
        let environment = PasscodeEnvironment()
        try environment.configure(self.configuration(), privateAccessGroup: { "TEAMID0000.org.asteri.tests" })
        XCTAssertThrowsError(try environment.configure(self.configuration(storage: .privateApplication), privateAccessGroup: { "TEAMID0000.org.asteri.tests" }))
        XCTAssertEqual(try environment.credentialAccessGroup(), "group.org.asteri.tests")
    }
}
