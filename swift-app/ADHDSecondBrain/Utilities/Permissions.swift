import Cocoa
import ApplicationServices

/// TCC permission checks and request helpers for macOS.
///
/// Required permissions:
/// 1. Screen Recording — for CGWindowListCopyWindowInfo (window titles)
/// 2. Accessibility — for AXUIElement (window observation)
/// 3. Automation — for AppleScript browser URL extraction (auto-prompted)
struct Permissions {

    // MARK: - Screen Recording

    /// Check if Screen Recording permission is granted.
    static var hasScreenRecording: Bool {
        return CGPreflightScreenCaptureAccess()
    }

    /// Request Screen Recording permission.
    /// Opens System Settings → Privacy & Security → Screen Recording.
    static func requestScreenRecording() {
        CGRequestScreenCaptureAccess()
    }

    // MARK: - Accessibility

    /// Check if Accessibility permission is granted.
    static var hasAccessibility: Bool {
        return AXIsProcessTrusted()
    }

    /// Request Accessibility permission.
    /// Opens System Settings → Privacy & Security → Accessibility.
    static func requestAccessibility() {
        let options: NSDictionary = [kAXTrustedCheckOptionPrompt.takeRetainedValue(): true]
        AXIsProcessTrustedWithOptions(options)
    }

    // MARK: - Open System Settings

    /// Opens the Security & Privacy pane in System Settings.
    static func openPrivacySettings() {
        if let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy") {
            NSWorkspace.shared.open(url)
        }
    }
}
