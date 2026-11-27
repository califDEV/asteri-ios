import Foundation
import AsteriFeatures
import AsteriSettingsUI
import AccountContext
import Display
import SwiftSignalKit
import TelegramCore
import TelegramUIPreferences

func makeAsteriSettingsController(context: AccountContext) -> ViewController {
    let settings = context.sharedContext.accountManager.sharedData(keys: [ApplicationSpecificSharedDataKeys.asteriSettings])
    |> map { data -> AsteriSettings in
        return data.entries[ApplicationSpecificSharedDataKeys.asteriSettings]?.get(AsteriSettings.self) ?? .defaultSettings
    }
    return asteriSettingsController(initialPresentationData: context.sharedContext.currentPresentationData.with { $0 }, presentationData: context.sharedContext.presentationData, settings: settings, updateFilter: { enabled in
        let _ = updateAsteriSettingsInteractively(accountManager: context.sharedContext.accountManager, { current in
            var updated = current
            updated.filterZalgo = enabled
            return updated
        }).startStandalone()
    })
}
