import Foundation
import UIKit
import AsteriFeatures
import AsteriSettingsUI
import Display
import SwiftSignalKit
import TelegramCore
import TelegramPresentationData
import TelegramUIPreferences

@objc(Application)
public final class Application: UIApplication {
}

@objc(AppDelegate)
public final class AppDelegate: NSObject, UIApplicationDelegate {
    public func application(_ application: UIApplication, configurationForConnecting session: UISceneSession, options: UIScene.ConnectionOptions) -> UISceneConfiguration {
        let configuration = UISceneConfiguration(name: "Default", sessionRole: session.role)
        configuration.delegateClass = SceneDelegate.self
        return configuration
    }
}

@objc(SceneDelegate)
public final class SceneDelegate: NSObject, UIWindowSceneDelegate {
    public var window: UIWindow?
    private var root: HarnessRoot?

    public func scene(_ scene: UIScene, willConnectTo session: UISceneSession, options: UIScene.ConnectionOptions) {
        guard let scene = scene as? UIWindowScene else { return }
        let window = UIWindow(windowScene: scene)
        let root = HarnessRoot()
        self.root = root
        window.rootViewController = root
        self.window = window
        window.makeKeyAndVisible()
    }

    public func scene(_ scene: UIScene, openURLContexts contexts: Set<UIOpenURLContext>) {
        for context in contexts { self.root?.perform(context.url.host ?? "") }
    }
}

/// No account/login/network fixture: only the real shared-preference database and
/// production settings screen. Its access-challenge callbacks apply only to this
/// empty harness database, never to a Telegram account or the application target.
private final class HarnessRoot: UIViewController {
    private let manager: AccountManager<TelegramAccountManagerTypes>
    private let logger: Logger
    private let data = Promise<PresentationData>()
    private let navigation: NavigationController
    private let stateURL: URL
    private var disposable: Disposable?
    private var settings = AsteriSettings.defaultSettings
    private var lastAction = "launch"
    private var error: String?
    private let launchToken = UUID().uuidString

    init() {
        precondition(Bundle.main.bundleIdentifier == "org.asteri.VisualHarness")
        let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
        self.stateURL = documents.appendingPathComponent("state.json")
        let root = documents.appendingPathComponent("preferences").path
        try! FileManager.default.createDirectory(atPath: root, withIntermediateDirectories: true)
        let logger = Logger(rootPath: root, basePath: root + "/logs")
        logger.logToFile = false
        logger.logToConsole = false
        Logger.setSharedLogger(logger)
        self.logger = logger
        initializeAccountManagement()
        self.manager = AccountManager(basePath: root + "/metadata", isTemporary: false, isReadOnly: false, useCaches: false, removeDatabaseOnError: false, accessChallenge: AccountManagerAccessChallenge(prepare: { _ in }, resolve: { current, _ in current }, finishInitialization: {}))
        let initial = defaultPresentationData()
        self.navigation = NavigationController(mode: .single, theme: NavigationControllerTheme(presentationTheme: initial.theme))
        super.init(nibName: nil, bundle: nil)
        self.data.set(.single(initial))

        let settings = self.manager.sharedData(keys: [ApplicationSpecificSharedDataKeys.asteriSettings])
        |> map { value -> AsteriSettings in
            value.entries[ApplicationSpecificSharedDataKeys.asteriSettings]?.get(AsteriSettings.self) ?? .defaultSettings
        }
        let controller = asteriSettingsController(initialPresentationData: initial, presentationData: self.data.get(), settings: settings, updateFilter: { [weak self] enabled in
            guard let self else { return }
            let _ = updateAsteriSettingsInteractively(accountManager: self.manager, { current in
                var updated = current
                updated.filterZalgo = enabled
                return updated
            }).startStandalone()
        })
        self.navigation.setViewControllers([controller], animated: false)
        self.disposable = (settings |> deliverOnMainQueue).start(next: { [weak self] value in
            guard let self else { return }
            self.settings = value
            self.writeState()
        })
    }

    required init?(coder: NSCoder) { fatalError("init(coder:) is unsupported") }

    deinit { self.disposable?.dispose() }

    override func viewDidLoad() {
        super.viewDidLoad()
        self.addChild(self.navigation)
        self.view.addSubview(self.navigation.view)
        self.navigation.didMove(toParent: self)
    }

    override func viewDidLayoutSubviews() {
        super.viewDidLayoutSubviews()
        self.navigation.view.frame = self.view.bounds
        let safe = self.view.safeAreaInsets
        self.navigation.containerLayoutUpdated(ContainerViewLayout(size: self.view.bounds.size, metrics: LayoutMetrics(widthClass: .compact, heightClass: .regular, orientation: .portrait), deviceMetrics: DeviceMetrics(screenSize: self.view.bounds.size, scale: self.view.contentScaleFactor, statusBarHeight: safe.top, onScreenNavigationHeight: safe.bottom), intrinsicInsets: UIEdgeInsets(top: 0, left: 0, bottom: safe.bottom, right: 0), safeInsets: UIEdgeInsets(top: 0, left: safe.left, bottom: 0, right: safe.right), reservedCorners: .none, division: nil, additionalInsets: .zero, statusBarHeight: safe.top, inputHeight: nil, inputHeightIsInteractivellyChanging: false, inVoiceOver: false, presentedInFormSheet: false), transition: .immediate)
    }

    func perform(_ action: String) {
        self.lastAction = action
        switch action {
        case "toggle":
            func findSwitch(_ view: UIView) -> UISwitch? {
                if let control = view as? UISwitch { return control }
                for child in view.subviews {
                    if let control = findSwitch(child) { return control }
                }
                return nil
            }
            if let control = findSwitch(self.view) {
                control.setOn(!control.isOn, animated: true)
                control.sendActions(for: .valueChanged)
            } else {
                self.error = "Production switch was not found"
            }
        case "dark", "light":
            self.overrideUserInterfaceStyle = action == "dark" ? .dark : .light
            let value = defaultPresentationData().withUpdated(theme: action == "dark" ? defaultDarkPresentationTheme : defaultPresentationTheme)
            self.data.set(.single(value))
            self.navigation.updateTheme(NavigationControllerTheme(presentationTheme: value.theme))
        default: self.error = "Unknown harness action"
        }
        self.writeState()
    }

    private func writeState() {
        let value: [String: Any] = ["filterZalgo": self.settings.filterZalgo, "lastAction": self.lastAction, "error": self.error as Any? ?? NSNull(), "accountLoginTested": false, "launchToken": self.launchToken]
        if let bytes = try? JSONSerialization.data(withJSONObject: value, options: [.prettyPrinted, .sortedKeys]) {
            try? bytes.write(to: self.stateURL, options: .atomic)
        }
    }
}
