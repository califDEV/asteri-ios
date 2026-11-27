load("@build_bazel_rules_swift//swift:swift.bzl", "swift_library", "swift_test")

swift_library(
    name = "AsteriFeatures",
    module_name = "AsteriFeatures",
    srcs = glob(["Sources/AsteriFeatures/*.swift"]),
    copts = ["-warnings-as-errors"],
    visibility = ["//visibility:public"],
)

swift_test(
    name = "AsteriFeaturesTests",
    srcs = glob(["Tests/AsteriFeaturesTests/*.swift"]),
    deps = [":AsteriFeatures"],
)
