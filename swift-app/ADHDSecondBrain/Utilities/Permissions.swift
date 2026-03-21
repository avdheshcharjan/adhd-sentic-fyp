import Cocoa
import ApplicationServices

/// TCC permission checks and request helpers for macOS.
///
/// Required permissions (supplement Section 2 — reduced from blueprint):
/// 1. Accessibility — for AXUIElement window title reading + observer (one-time grant, no re-auth)
/// 2. Automation — for AppleScript browser URL extraction (auto-prompted per browser)
///
/// Screen Recording is NOT required. Window titles are read via AXUIElement
/// instead of CGWindowListCopyWindowInfo.
/// Anti-pattern #6: NEVER use Screen Recording for core monitoring.
struct Permissions {

    // MARK: - Accessibility

    /// Live check — `AXIsProcessTrusted()` re-evaluates each call on macOS 13+.
    /// If the user toggles the switch in System Settings the next call returns the new value.
    static var hasAccessibility: Bool {
        AXIsProcessTrusted()
    }

    /// Prompt the system dialog for Accessibility permission.
    static func requestAccessibility() {
        let options: NSDictionary = [kAXTrustedCheckOptionPrompt.takeRetainedValue(): true]
        AXIsProcessTrustedWithOptions(options)
    }

    // MARK: - Automation

    /// There is no public API to query Automation (AppleScript) permission.
    /// We probe by sending a no-op AppleScript to "System Events". Only a
    /// successful execution with a non-nil result proves the permission is granted.
    /// Any error at all (TCC denied, System Events not running, etc.) = not granted.
    static var hasAutomation: Bool {
        guard let script = NSAppleScript(source: """
            tell application "System Events"
                return name of first process whose frontmost is true
            end tell
            """) else {
            return false
        }
        var errorInfo: NSDictionary?
        let result = script.executeAndReturnError(&errorInfo)
        // Any error means permission is not granted (or System Events unavailable)
        if errorInfo != nil {
            return false
        }
        return result.stringValue != nil
    }

    /// Trigger the Automation permission prompt by running a harmless
    /// AppleScript against System Events. macOS will show the TCC dialog
    /// if permission hasn't been granted yet.
    static func requestAutomation() {
        let script = NSAppleScript(source: """
            tell application "System Events"
                return name of first process whose frontmost is true
            end tell
            """)
        var errorInfo: NSDictionary?
        script?.executeAndReturnError(&errorInfo)
    }

    // MARK: - Open System Settings

    /// Opens the Privacy & Security pane in System Settings.
    static func openPrivacySettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy") {
            NSWorkspace.shared.open(url)
        }
    }

    /// Opens the Automation pane directly in System Settings.
    static func openAutomationSettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Automation") {
            NSWorkspace.shared.open(url)
        }
    }
}
