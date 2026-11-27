load("@build_bazel_rules_swift//swift:swift.bzl", "swift_library", "swift_test")

swift_library(
    name = "PasscodeCore",
    module_name = "PasscodeCore",
    srcs = glob(["Sources/**/*.swift"]),
    copts = ["-warnings-as-errors"],
    deps = [
        "//submodules/SSignalKit/SwiftSignalKit",
        "//submodules/TelegramCore",
    ],
    visibility = ["//visibility:public"],
)

# Host tests compile the same production security sources, excluding only the
# TelegramCore account-manager adapter, which is validated by the full app build.
swift_library(
    name = "PasscodeStorageScopeTestLib",
    module_name = "PasscodeCore",
    testonly = True,
    srcs = glob(["Sources/*.swift"], exclude = ["Sources/AccountManagerIntegration.swift"]),
    # Match the upstream SwiftPM host-test policy: macOS-only legacy SecKeychain
    # migration APIs retain visible deprecation warnings. The production iOS
    # target above still treats every warning as an error.
    copts = ["-enable-testing"],
    deps = ["//submodules/SSignalKit/SwiftSignalKit"],
)

swift_test(
    name = "PasscodeStorageScopeTests",
    srcs = ["Tests/PasscodeCoreTests/PasscodeStorageScopeTests.swift"],
    deps = [":PasscodeStorageScopeTestLib"],
)
