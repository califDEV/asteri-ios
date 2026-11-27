load("@build_bazel_rules_swift//swift:swift.bzl", "swift_library")

swift_library(
    name = "AsteriSettingsUI",
    module_name = "AsteriSettingsUI",
    srcs = glob(["Sources/*.swift"]),
    copts = ["-warnings-as-errors"],
    deps = [
        "//submodules/AsteriFeatures",
        "//submodules/Display",
        "//submodules/ItemListUI",
        "//submodules/TelegramPresentationData",
        "//submodules/SSignalKit/SwiftSignalKit",
    ],
    visibility = ["//visibility:public"],
)
