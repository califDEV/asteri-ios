import Foundation
import UIKit
import AsteriFeatures
import Display
import ItemListUI
import SwiftSignalKit
import TelegramPresentationData

private struct AsteriSettingsStrings {
    let general: String
    let filter: String
    let explanation: String
    let preview: String
    let about: String
    let attribution: String

    init(languageCode: String) {
        let language = languageCode.lowercased().split(separator: "-").first.map(String.init) ?? "en"
        switch language {
        case "ru":
            self.general = "ТЕКСТ СООБЩЕНИЙ"
            self.filter = "Защита от Zalgo"
            self.explanation = "Скрывает чрезмерные диакритические знаки и управляющие символы направления текста в сообщениях. Обычные диакритики и эмодзи сохраняются. Исходный текст для копирования и отправки не меняется."
            self.preview = "Предпросмотр"
            self.about = "О ПРИЛОЖЕНИИ"
            self.attribution = "Asteri — независимый неофициальный клиент на основе Telegram для iOS и кода exteraGram. Функция защиты от Zalgo адаптирована из exteraGram (© exteraGram, 2022–2026), GPLv3+. Полный перенос функций и поддержка Android-плагинов пока не завершены."
        case "uk":
            self.general = "ТЕКСТ ПОВІДОМЛЕНЬ"
            self.filter = "Захист від Zalgo"
            self.explanation = "Приховує надмірні діакритичні знаки та керівні символи напрямку тексту в повідомленнях. Звичайні діакритики й емодзі зберігаються. Вихідний текст для копіювання та надсилання не змінюється."
            self.preview = "Попередній перегляд"
            self.about = "ПРО ЗАСТОСУНОК"
            self.attribution = "Asteri — незалежний неофіційний клієнт на основі Telegram для iOS та коду exteraGram. Захист від Zalgo адаптовано з exteraGram (© exteraGram, 2022–2026), GPLv3+. Повне перенесення функцій і підтримка Android-плагінів ще не завершені."
        default:
            self.general = "MESSAGE TEXT"
            self.filter = "Zalgo protection"
            self.explanation = "Hides excessive combining marks and text direction controls in messages. Normal accents and emoji are preserved. The original text used for copying and sending stays unchanged."
            self.preview = "Preview"
            self.about = "ABOUT"
            self.attribution = "Asteri is an independent, unofficial client based on Telegram for iOS and code from exteraGram. Zalgo protection is adapted from exteraGram (© exteraGram, 2022–2026), GPLv3+. The full feature port and Android plugin compatibility are still in progress."
        }
    }
}

private enum AsteriSettingsEntry: ItemListNodeEntry {
    case header(Int32, String)
    case filter(String, Bool)
    case text(Int32, String)
    case source

    var stableId: Int32 {
        switch self {
        case let .header(id, _), let .text(id, _): return id
        case .filter: return 1
        case .source: return 6
        }
    }

    var section: ItemListSectionId {
        return self.stableId < 4 ? 0 : 1
    }

    static func < (lhs: AsteriSettingsEntry, rhs: AsteriSettingsEntry) -> Bool {
        return lhs.stableId < rhs.stableId
    }

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {
        switch self {
        case let .header(_, title):
            return ItemListSectionHeaderItem(presentationData: presentationData, text: title, sectionId: self.section)
        case let .filter(title, enabled):
            let update = arguments as! (Bool) -> Void
            return ItemListSwitchItem(presentationData: presentationData, systemStyle: .glass, title: title, value: enabled, sectionId: self.section, style: .blocks, updated: update)
        case let .text(_, text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
        case .source:
            return ItemListDisclosureItem(presentationData: presentationData, systemStyle: .glass, icon: nil, title: "exteraGram", label: "GitHub", labelStyle: .text, sectionId: self.section, style: .blocks, disclosureStyle: .arrow, action: {
                if let url = URL(string: "https://github.com/exteraSquad/exteraGram") {
                    UIApplication.shared.open(url, options: [:], completionHandler: nil)
                }
            })
        }
    }
}

/// Context-free construction also lets the visual harness exercise the shipping rows.
public func asteriSettingsController(initialPresentationData: PresentationData, presentationData: Signal<PresentationData, NoError>, settings: Signal<AsteriSettings, NoError>, updateFilter: @escaping (Bool) -> Void) -> ViewController {
    let state = combineLatest(presentationData, settings)
    |> deliverOnMainQueue
    |> map { data, settings -> (ItemListControllerState, (ItemListNodeState, (Bool) -> Void)) in
        let strings = AsteriSettingsStrings(languageCode: data.strings.baseLanguageCode)
        let sample = "Z\u{0337}\u{030C}\u{034D}a\u{0338}\u{0304}\u{031C}l\u{0338}\u{0302}\u{031E}g\u{0337}\u{034D}\u{031D}o\u{0336}\u{0313}\u{0329}  ·  Привіт 👋  ·  café"
        let entries: [AsteriSettingsEntry] = [
            .header(0, strings.general),
            .filter(strings.filter, settings.filterZalgo),
            .text(2, strings.explanation),
            .text(3, strings.preview + ": " + ZalgoFilter.sanitized(sample, enabled: settings.filterZalgo)),
            .header(4, strings.about),
            .text(5, strings.attribution),
            .source,
        ]
        let controller = ItemListControllerState(presentationData: ItemListPresentationData(data), title: .text("Asteri"), leftNavigationButton: nil, rightNavigationButton: nil, backNavigationButton: ItemListBackButton(title: data.strings.Common_Back), animateChanges: false)
        let list = ItemListNodeState(presentationData: ItemListPresentationData(data), entries: entries, style: .blocks, emptyStateItem: nil, animateChanges: false)
        return (controller, (list, updateFilter))
    }
    return ItemListController(presentationData: ItemListPresentationData(initialPresentationData), updatedPresentationData: presentationData |> map(ItemListPresentationData.init), state: state, tabBarItem: nil)
}
