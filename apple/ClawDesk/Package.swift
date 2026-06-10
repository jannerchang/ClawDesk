// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "ClawDesk",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .library(name: "ClawDeskApp", targets: ["ClawDeskApp"])
    ],
    targets: [
        .target(
            name: "ClawDeskApp",
            path: "Sources/ClawDeskApp"
        )
    ]
)
