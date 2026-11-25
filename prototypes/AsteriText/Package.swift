// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AsteriText",
    platforms: [.iOS(.v15), .macOS(.v13)],
    products: [.library(name: "AsteriText", targets: ["AsteriText"])],
    targets: [
        .target(name: "AsteriText"),
        .testTarget(name: "AsteriTextTests", dependencies: ["AsteriText"])
    ]
)
