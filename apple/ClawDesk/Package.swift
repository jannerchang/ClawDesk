// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "ClawDesk",
    platforms: [
        .iOS(.v17),
        .macOS(.v14)
    ],
    products: [
        .executable(name: "ClawDeskApp", targets: ["ClawDeskApp"])
    ],
    targets: [
        .executableTarget(
            name: "ClawDeskApp",
            path: "Sources/ClawDeskApp"
        )
    ]
)
