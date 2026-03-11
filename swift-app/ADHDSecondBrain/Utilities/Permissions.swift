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

    /// Check if Accessibility permission is granted.
    /// Required for AXUIElement window title reading and AXObserver.
    static var hasAccessibility: Bool {
        return AXIsProcessTrusted()
    }

    /// Request Accessibility permission.
    /// Opens System Settings -> Privacy & Security -> Accessibility.
    static func requestAccessibility() {
        let options: NSDictionary = [kAXTrustedCheckOptionPrompt.takeRetainedValue(): true]
        AXIsProcessTrustedWithOptions(options)
    }

    // MARK: - Open System Settings

    /// Opens the Privacy & Security pane in System Settings.
    static func openPrivacySettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy") {
            NSWorkspace.shared.open(url)
        }
    }
}
