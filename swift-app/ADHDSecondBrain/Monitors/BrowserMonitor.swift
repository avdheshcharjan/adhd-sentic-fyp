import Foundation

/// Extracts the active tab URL from supported browsers using AppleScript.
///
/// Supported browsers:
/// - Chrome-based: Google Chrome, Brave, Edge, Arc, Chromium
/// - Safari: different AppleScript API
/// - Firefox: not supported (no AppleScript interface)
class BrowserMonitor {

    // MARK: - Browser Definitions

    /// Known browser bundle IDs and their AppleScript strategies.
    private enum BrowserType {
        case chromeBased(appName: String)
        case safari

        /// AppleScript to get the URL of the active tab.
        var script: String {
            switch self {
            case .chromeBased(let appName):
                return """
                tell application "\(appName)"
                    if (count of windows) > 0 then
                        return URL of active tab of front window
                    end if
                end tell
                """
            case .safari:
                return """
                tell application "Safari"
                    if (count of windows) > 0 then
                        return URL of front document
                    end if
                end tell
                """
            }
        }
    }

    /// Maps bundle identifiers to browser types.
    private static let knownBrowsers: [String: BrowserType] = [
        "com.google.Chrome":          .chromeBased(appName: "Google Chrome"),
        "com.brave.Browser":          .chromeBased(appName: "Brave Browser"),
        "com.microsoft.edgemac":      .chromeBased(appName: "Microsoft Edge"),
        "company.thebrowser.Browser": .chromeBased(appName: "Arc"),
        "org.chromium.Chromium":      .chromeBased(appName: "Chromium"),
        "com.apple.Safari":           .safari,
    ]

    // MARK: - Public API

    /// Returns true if the given bundle ID is a known browser.
    static func isBrowser(bundleIdentifier: String?) -> Bool {
        guard let id = bundleIdentifier else { return false }
        return knownBrowsers[id] != nil
    }

    /// Extracts the current URL from the browser's active tab.
    /// Returns nil if the browser is unknown or AppleScript fails.
    static func getActiveTabURL(bundleIdentifier: String?) -> String? {
        guard let id = bundleIdentifier,
              let browserType = knownBrowsers[id]
        else { return nil }

        return runAppleScript(browserType.script)
    }

    // MARK: - Private Methods

    private static func runAppleScript(_ source: String) -> String? {
        guard let script = NSAppleScript(source: source) else { return nil }

        var error: NSDictionary?
        let result = script.executeAndReturnError(&error)

        if let error = error {
            // Automation permission denied or app not running — silent fail
            let errorNumber = error[NSAppleScript.errorNumber] as? Int ?? 0
            if errorNumber != -1743 { // -1743 = user cancelled / not authorized
                print("⚠ AppleScript error for browser URL: \(error)")
            }
            return nil
        }

        return result.stringValue
    }
}
