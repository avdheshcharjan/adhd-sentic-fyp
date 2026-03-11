// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "ADHDSecondBrain",
    platforms: [.macOS(.v14)],
    targets: [
        .executableTarget(
            name: "ADHDSecondBrain",
            path: "ADHDSecondBrain",
            exclude: ["Info.plist"],
            linkerSettings: [
                .linkedFramework("IOKit"),
                .linkedFramework("ApplicationServices"),
            ]
        ),
    ]
)
