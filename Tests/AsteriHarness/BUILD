load("@build_bazel_rules_swift//swift:swift.bzl", "swift_library")
load("@build_bazel_rules_apple//apple:ios.bzl", "ios_application")
load("//build-system/bazel-utils:plist_fragment.bzl", "plist_fragment")

plist_fragment(
    name = "InfoPlist",
    extension = "plist",
    template = """
    <key>CFBundleName</key><string>Asteri Harness</string>
    <key>CFBundleDisplayName</key><string>Asteri QA</string>
    <key>CFBundleShortVersionString</key><string>1.0</string>
    <key>CFBundleVersion</key><string>1</string>
    <key>UILaunchScreen</key><dict/>
    <key>UISupportedInterfaceOrientations</key><array><string>UIInterfaceOrientationPortrait</string></array>
    <key>CFBundleURLTypes</key><array><dict><key>CFBundleURLSchemes</key><array><string>asteri-harness</string></array></dict></array>
    <key>UIApplicationSceneManifest</key><dict>
      <key>UIApplicationSupportsMultipleScenes</key><false/>
      <key>UISceneConfigurations</key><dict>
        <key>UIWindowSceneSessionRoleApplication</key><array><dict>
          <key>UISceneConfigurationName</key><string>Default</string>
          <key>UISceneDelegateClassName</key><string>SceneDelegate</string>
        </dict></array>
      </dict>
    </dict>
    """,
)

swift_library(
    name = "HarnessLib",
    module_name = "AsteriHarnessLib",
    srcs = glob(["Sources/*.swift"]),
    deps = [
        "//submodules/AsteriFeatures",
        "//submodules/AsteriSettingsUI",
        "//submodules/Display",
        "//submodules/TelegramCore",
        "//submodules/TelegramPresentationData",
        "//submodules/TelegramUIPreferences",
        "//submodules/SSignalKit/SwiftSignalKit",
    ],
)

ios_application(
    name = "AsteriHarness",
    bundle_id = "org.asteri.VisualHarness",
    families = ["iphone"],
    minimum_os_version = "15.0",
    infoplists = [":InfoPlist"],
    app_icons = ["//Telegram:Asteri_icon"],
    resources = [
        "//Telegram:AppStringResources",
        "//Telegram:GeneratedPresentationStrings/Resources/PresentationStrings.data",
    ],
    deps = ["//Tests/Common:Main", ":HarnessLib"],
    linkopts = ["-framework", "MediaPlayer"],
)
