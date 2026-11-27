import Foundation
import AsteriFeatures
import SwiftSignalKit
import TelegramCore

public func updateAsteriSettingsInteractively(accountManager: AccountManager<TelegramAccountManagerTypes>, _ f: @escaping (AsteriSettings) -> AsteriSettings) -> Signal<Void, NoError> {
    return accountManager.transaction { transaction -> Void in
        transaction.updateSharedData(ApplicationSpecificSharedDataKeys.asteriSettings, { entry in
            let current = entry?.get(AsteriSettings.self) ?? .defaultSettings
            return EnginePreferencesEntry(f(current))
        })
    }
}
