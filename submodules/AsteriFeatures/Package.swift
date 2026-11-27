// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AsteriFeatures",
    platforms: [.iOS(.v15), .macOS(.v13)],
    products: [.library(name: "AsteriFeatures", targets: ["AsteriFeatures"])],
    targets: [
        .target(name: "AsteriFeatures"),
        .testTarget(name: "AsteriFeaturesTests", dependencies: ["AsteriFeatures"])
    ]
)
